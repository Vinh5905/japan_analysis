CREATE EXTENSION IF NOT EXISTS postgis;
CREATE SCHEMA IF NOT EXISTS enrichment;
CREATE TABLE IF NOT EXISTS raw.mlit_datasets (
    dataset_key text PRIMARY KEY,
    prefecture_code text NOT NULL,
    city_code text NOT NULL,
    source_url text NOT NULL,
    metadata_url text NOT NULL,
    zip_sha256 text NOT NULL,
    metadata_sha256 text NOT NULL,
    city_metadata_sha256 text NOT NULL,
    zip_object_path text NOT NULL,
    metadata_object_path text NOT NULL,
    manifest_object_path text NOT NULL,
    fiscal_year integer,
    source_modified_date date,
    source_as_of_date date,
    city_metadata jsonb NOT NULL,
    retrieved_at timestamptz NOT NULL DEFAULT now(),
    last_checked_at timestamptz NOT NULL DEFAULT now(),
    validation_status text NOT NULL,
    feature_count integer NOT NULL CHECK (feature_count > 0),
    UNIQUE (prefecture_code, city_code, zip_sha256, city_metadata_sha256)
);
CREATE TABLE IF NOT EXISTS raw.mlit_zoning_polygons (
    dataset_key text NOT NULL REFERENCES raw.mlit_datasets (dataset_key),
    source_file text NOT NULL,
    feature_ordinal integer NOT NULL,
    geometry jsonb NOT NULL,
    properties jsonb NOT NULL,
    PRIMARY KEY (dataset_key, source_file, feature_ordinal)
);
CREATE TABLE IF NOT EXISTS enrichment.zoning_runs (
    run_id text PRIMARY KEY,
    dataset_key text NOT NULL REFERENCES raw.mlit_datasets (dataset_key),
    city_code text NOT NULL,
    matching_version text NOT NULL,
    input_fingerprint text NOT NULL,
    status text NOT NULL DEFAULT 'prepared',
    created_at timestamptz NOT NULL DEFAULT now(),
    quality_checked_at timestamptz,
    quality_passed boolean NOT NULL DEFAULT false,
    review jsonb,
    publication_sequence bigint UNIQUE,
    published_at timestamptz,
    UNIQUE (dataset_key, matching_version, input_fingerprint)
);
CREATE TABLE IF NOT EXISTS enrichment.zoning_run_inputs (
    run_id text NOT NULL REFERENCES enrichment.zoning_runs (run_id),
    building_key text NOT NULL,
    building_name text,
    address_query text,
    geography_key text,
    latitude double precision,
    longitude double precision,
    location_status text,
    coordinate_level text,
    provider text,
    place_id text,
    location_fingerprint text NOT NULL,
    PRIMARY KEY (run_id, building_key)
);
CREATE TABLE IF NOT EXISTS enrichment.zoning_run_tasks (
    run_id text NOT NULL REFERENCES enrichment.zoning_runs (run_id),
    task_id bigint NOT NULL,
    building_key text NOT NULL,
    data_hash text,
    PRIMARY KEY (run_id, task_id)
);
CREATE TABLE IF NOT EXISTS enrichment.zoning_publication_pointer (
    city_code text PRIMARY KEY,
    run_id text NOT NULL REFERENCES enrichment.zoning_runs (run_id)
);
CREATE SEQUENCE IF NOT EXISTS enrichment.zoning_publication_sequence;
CREATE TABLE IF NOT EXISTS enrichment.zoning_publication_audit (
    event_id bigserial PRIMARY KEY,
    city_code text NOT NULL,
    previous_run_id text REFERENCES enrichment.zoning_runs (run_id),
    run_id text NOT NULL REFERENCES enrichment.zoning_runs (run_id),
    action text NOT NULL,
    reason text NOT NULL,
    accepted_null_buildings jsonb NOT NULL DEFAULT '[]',
    occurred_at timestamptz NOT NULL DEFAULT now()
);
-- Run inputs/tasks are immutable after creation, including unpublished candidates.
CREATE OR REPLACE FUNCTION enrichment.reject_snapshot_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Zoning snapshots are immutable';
END
$$;
DROP TRIGGER IF EXISTS immutable_inputs ON enrichment.zoning_run_inputs;
CREATE TRIGGER immutable_inputs BEFORE UPDATE OR DELETE ON enrichment.zoning_run_inputs
FOR EACH ROW EXECUTE FUNCTION enrichment.reject_snapshot_mutation();
DROP TRIGGER IF EXISTS immutable_tasks ON enrichment.zoning_run_tasks;
CREATE TRIGGER immutable_tasks BEFORE UPDATE OR DELETE ON enrichment.zoning_run_tasks
FOR EACH ROW EXECUTE FUNCTION enrichment.reject_snapshot_mutation();

CREATE OR REPLACE FUNCTION enrichment.protect_published_run()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF OLD.publication_sequence IS NOT NULL AND NEW IS DISTINCT FROM OLD THEN
        RAISE EXCEPTION 'Published run metadata is immutable';
    END IF;
    RETURN NEW;
END
$$;
DROP TRIGGER IF EXISTS immutable_published_run ON enrichment.zoning_runs;
CREATE TRIGGER immutable_published_run BEFORE UPDATE ON enrichment.zoning_runs
FOR EACH ROW EXECUTE FUNCTION enrichment.protect_published_run();
DROP TRIGGER IF EXISTS immutable_raw_features ON raw.mlit_zoning_polygons;
CREATE TRIGGER immutable_raw_features BEFORE UPDATE OR DELETE
ON raw.mlit_zoning_polygons
FOR EACH ROW EXECUTE FUNCTION enrichment.reject_snapshot_mutation();

CREATE TABLE IF NOT EXISTS raw.mlit_source_checks (
    check_id bigserial PRIMARY KEY,
    dataset_key text NOT NULL REFERENCES raw.mlit_datasets (dataset_key),
    checked_at timestamptz NOT NULL DEFAULT now(),
    source_url text NOT NULL,
    metadata_url text NOT NULL,
    manifest_object_path text NOT NULL,
    source_modified_date date,
    reused boolean NOT NULL
);

CREATE OR REPLACE FUNCTION enrichment.protect_dataset_content()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF (to_jsonb(NEW) - 'last_checked_at' - 'validation_status') IS DISTINCT FROM
       (to_jsonb(OLD) - 'last_checked_at' - 'validation_status') THEN
        RAISE EXCEPTION 'Dataset content is immutable';
    END IF;
    RETURN NEW;
END
$$;
DROP TRIGGER IF EXISTS immutable_dataset_content ON raw.mlit_datasets;
CREATE TRIGGER immutable_dataset_content BEFORE UPDATE ON raw.mlit_datasets
FOR EACH ROW EXECUTE FUNCTION enrichment.protect_dataset_content();
DROP TRIGGER IF EXISTS immutable_publication_audit
ON enrichment.zoning_publication_audit;
CREATE TRIGGER immutable_publication_audit BEFORE UPDATE OR DELETE
ON enrichment.zoning_publication_audit
FOR EACH ROW EXECUTE FUNCTION enrichment.reject_snapshot_mutation();

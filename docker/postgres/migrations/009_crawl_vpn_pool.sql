BEGIN;

CREATE TABLE IF NOT EXISTS crawl_vpns (
    vpn_id BIGSERIAL PRIMARY KEY,
    filename TEXT NOT NULL UNIQUE CHECK (filename ~ '^[A-Za-z0-9_.-]+\.ovpn$'),
    relative_path TEXT NOT NULL UNIQUE CHECK (relative_path = filename),
    sha256 TEXT NOT NULL CHECK (sha256 ~ '^[a-f0-9]{64}$'),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    total_requests BIGINT NOT NULL DEFAULT 0 CHECK (total_requests >= 0),
    activation_successes BIGINT NOT NULL DEFAULT 0 CHECK (activation_successes >= 0),
    activation_failures BIGINT NOT NULL DEFAULT 0 CHECK (activation_failures >= 0),
    last_attempt_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE crawl_runs ADD COLUMN IF NOT EXISTS vpn_id BIGINT REFERENCES crawl_vpns (
    vpn_id
);
ALTER TABLE crawl_runs ADD COLUMN IF NOT EXISTS vpn_snapshot JSONB;

CREATE TABLE IF NOT EXISTS crawl_vpn_attempts (
    attempt_id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES crawl_runs (run_id),
    vpn_id BIGINT NOT NULL REFERENCES crawl_vpns (vpn_id),
    snapshot JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (
        status IN ('pending', 'success', 'failed', 'interrupted')
    ),
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    UNIQUE (run_id, vpn_id)
);

CREATE TABLE IF NOT EXISTS crawl_vpn_requests (
    request_id UUID PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES crawl_runs (run_id),
    vpn_id BIGINT NOT NULL REFERENCES crawl_vpns (vpn_id),
    stage TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS crawl_vpn_requests_run_idx ON crawl_vpn_requests (run_id);
CREATE INDEX IF NOT EXISTS crawl_vpn_attempts_pending_idx ON crawl_vpn_attempts (
    run_id
) WHERE status
= 'pending';

-- A single idempotent transaction records each downloader attempt and its counter.
-- Historical HTML totals cannot be backfilled into HTTP request counts.
CREATE OR REPLACE FUNCTION record_crawl_vpn_request(
    p_request UUID, p_run BIGINT, p_vpn BIGINT, p_stage TEXT
)
RETURNS BOOLEAN LANGUAGE plpgsql AS $$
DECLARE added INTEGER;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM crawl_runs r JOIN crawl_vpn_attempts a
        ON a.run_id=r.run_id AND a.vpn_id=r.vpn_id
        WHERE r.run_id=p_run AND r.vpn_id=p_vpn AND r.pipeline_status='running'
          AND r.cleanup_confirmed_at IS NULL AND a.status='success') THEN
        RAISE EXCEPTION 'No verified VPN context for run';
    END IF;
    INSERT INTO crawl_vpn_requests(request_id,run_id,vpn_id,stage)
        VALUES(p_request,p_run,p_vpn,p_stage) ON CONFLICT(request_id) DO NOTHING;
    GET DIAGNOSTICS added = ROW_COUNT;
    IF added=1 THEN
        UPDATE crawl_vpns SET total_requests=total_requests+1 WHERE vpn_id=p_vpn;
    ELSIF NOT EXISTS (SELECT 1 FROM crawl_vpn_requests WHERE request_id=p_request
        AND run_id=p_run AND vpn_id=p_vpn AND stage=p_stage) THEN
        RAISE EXCEPTION 'Request identity reused with different context';
    END IF;
    RETURN added=1;
END $$;

COMMIT;

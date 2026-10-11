"""Local DB regressions: cache, dry run, failed refresh and error propagation."""

from unittest.mock import patch
from loaders.suumo_batch_loader import (
    load_source_postgres_config,
    load_warehouse_postgres_config,
    postgres_connection,
)
from loaders import suumo_building_backfill as loader


def fingerprints():
    """Capture both enrichment and source metadata to detect accidental mutations."""
    with postgres_connection(load_warehouse_postgres_config()) as c:
        audit = c.execute(
            "select count(*), md5(string_agg(to_jsonb(r)::text,'' order by source_id,task_id)) from raw.suumo_building_name_backfill r"
        ).fetchone()
    with postgres_connection(load_source_postgres_config()) as c:
        source = {}
        for table, key in [
            ("crawl_tasks", "task_id"),
            ("raw_snapshots", "raw_snapshot_id"),
            ("load_batches", "batch_id"),
        ]:
            source[table] = c.execute(
                f"select count(*), md5(string_agg(to_jsonb(r)::text,'' order by {key})) from {table} r"
            ).fetchone()
    return audit, source


def main():
    """Use already-backfilled local snapshots; no new crawler tasks are created."""
    before = fingerprints()
    with patch.object(
        loader,
        "read_snapshot",
        side_effect=AssertionError("Cache hit must not read HTML"),
    ):
        result = loader.backfill()
        assert result["cache_hit"] == before[0][0] and result["processed"] == 0, result
    assert fingerprints() == before
    with patch.object(
        loader, "read_snapshot", side_effect=OSError("Fixture storage outage")
    ):
        result = loader.backfill(limit=1, force=True)
        assert result["errors"] == 1, result
    assert fingerprints() == before, (
        "A failed refresh erased or updated successful audit data"
    )
    with (
        patch.object(
            loader,
            "ensure_table",
            side_effect=AssertionError("dry run cannot execute DDL"),
        ),
        patch.object(
            loader, "persist_result", side_effect=AssertionError("dry run cannot write")
        ),
        patch.object(loader, "read_snapshot", side_effect=OSError("Fixture outage")),
    ):
        result = loader.backfill(limit=1, force=True, dry_run=True)
        assert result["processed"] == 1 and result["dry_run"], result
    assert fingerprints() == before
    for target in ("extract_building_identity", "persist_result"):
        with patch.object(
            loader, target, side_effect=RuntimeError(f"Fixture {target} failure")
        ):
            try:
                loader.backfill(limit=1, force=True)
            except RuntimeError as error:
                assert f"Fixture {target}" in str(error)
            else:
                raise AssertionError("Code/warehouse errors must fail the command")
        assert fingerprints() == before
    print(
        "PASS: 5 backfill scenarios; source tasks/snapshots/batches and successful audit unchanged"
    )


if __name__ == "__main__":
    main()

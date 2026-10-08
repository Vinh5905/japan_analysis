"""Generate an atomic, fingerprinted manifest without connecting to the warehouse."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

REFRESH_COMMAND = "make -C pipeline dbt-airflow-manifest"


def project_fingerprint(project: Path) -> str:
    digest = hashlib.sha256()
    files = []
    for folder in ("models", "macros", "tests", "seeds", "snapshots", "analyses", "dbt_packages"):
        root = project / folder
        if root.exists():
            files.extend(p for p in root.rglob("*") if p.is_file() and p.suffix in {".sql", ".yml", ".yaml", ".csv", ".py"})
    files.extend(project / name for name in (
        "dbt_project.yml", "profiles.yml", "packages.yml", "dependencies.yml", "package-lock.yml"
    ) if (project / name).exists())
    for path in sorted(files):
        digest.update(str(path.relative_to(project)).encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    # Only a digest is stored: never persist credentials in an artifact.
    for name in ("WAREHOUSE_POSTGRES_HOST", "WAREHOUSE_POSTGRES_PORT", "WAREHOUSE_DB",
                 "PIPELINE_POSTGRES_USER", "PIPELINE_POSTGRES_PASSWORD"):
        digest.update(name.encode())
        digest.update(os.getenv(name, "").encode())
        digest.update(b"\0")
    return digest.hexdigest()


def load_manifest(project: Path) -> dict:
    path = project / "target/airflow/manifest.json"
    if not path.exists():
        raise RuntimeError(f"Missing Airflow manifest {path}. Run: {REFRESH_COMMAND}")
    manifest = json.loads(path.read_text())
    if "_airflow" not in manifest:
        raise RuntimeError(f"Manifest has no fingerprint. Run: {REFRESH_COMMAND}")
    return manifest


def assert_fresh(project: Path, expected: str) -> None:
    current = load_manifest(project)["_airflow"]["fingerprint"]
    if current != expected or project_fingerprint(project) != expected:
        raise RuntimeError(f"dbt code/config changed since this DAG was parsed. Run: {REFRESH_COMMAND}")


def refresh_manifest(project: Path) -> None:
    destination = project / "target/airflow"
    destination.mkdir(parents=True, exist_ok=True)
    before = project_fingerprint(project)
    with tempfile.TemporaryDirectory(prefix="parse-", dir=destination) as temporary:
        subprocess.run([
            "/opt/airflow/dbt_venv/bin/dbt", "parse", "--no-partial-parse",
            "--project-dir", str(project), "--profiles-dir", str(project),
            "--target-path", temporary, "--log-path", str(Path(temporary) / "logs"),
        ], check=True)
        if project_fingerprint(project) != before:
            raise RuntimeError("dbt files changed during parse; refresh manifest again")
        path = Path(temporary) / "manifest.json"
        manifest = json.loads(path.read_text())
        manifest["_airflow"] = {"fingerprint": before}
        path.write_text(json.dumps(manifest))
        os.replace(path, destination / "manifest.json")
    print(f"Airflow manifest refreshed: {destination / 'manifest.json'}")


if __name__ == "__main__":
    refresh_manifest(Path(os.getenv("DBT_PROJECT_DIR", "/opt/airflow/dbt")))

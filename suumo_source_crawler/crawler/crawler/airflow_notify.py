from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping

import requests


@dataclass(frozen=True)
class AirflowNotifyConfig:
    """Store optional Airflow REST API settings for source event notification."""

    enabled: bool
    api_base_url: str
    dag_id: str
    username: str
    password: str
    timeout_seconds: float


def parse_bool(value: str | None) -> bool:
    """Parse environment booleans used by crawler runtime flags."""

    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def load_airflow_notify_config() -> AirflowNotifyConfig:
    """Load optional Airflow notification settings from environment."""

    return AirflowNotifyConfig(
        enabled=parse_bool(os.getenv("AIRFLOW_NOTIFY_ENABLED", "false")),
        api_base_url=os.getenv("AIRFLOW_API_BASE_URL", "http://airflow-webserver:8080").rstrip("/"),
        dag_id=os.getenv("AIRFLOW_DAG_ID", "suumo_load_to_warehouse"),
        username=os.getenv("AIRFLOW_USERNAME", "admin"),
        password=os.getenv("AIRFLOW_PASSWORD", "admin_change_me"),
        timeout_seconds=float(os.getenv("AIRFLOW_NOTIFY_TIMEOUT_SECONDS", "10")),
    )


def notify_airflow_batch_ready(
    config: AirflowNotifyConfig,
    batch_result: Mapping[str, object],
) -> dict[str, object]:
    """Trigger the Airflow load DAG after a source load_batch is ready."""

    batch_id = int(batch_result["batch_id"])
    if not config.enabled:
        return {
            "enabled": False,
            "notified": False,
            "reason": "AIRFLOW_NOTIFY_ENABLED is false",
        }

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    dag_run_id = f"suumo_batch_{batch_id}_{timestamp}"
    url = f"{config.api_base_url}/api/v1/dags/{config.dag_id}/dagRuns"
    payload = {
        "dag_run_id": dag_run_id,
        "conf": {
            "batch_id": batch_id,
            "file_path": batch_result.get("file_path"),
            "source_id": batch_result.get("source_id"),
            "triggered_by": "suumo_page",
        },
    }

    response = requests.post(
        url,
        json=payload,
        auth=(config.username, config.password),
        timeout=config.timeout_seconds,
    )
    response.raise_for_status()

    return {
        "enabled": True,
        "notified": True,
        "dag_id": config.dag_id,
        "dag_run_id": dag_run_id,
        "status_code": response.status_code,
    }

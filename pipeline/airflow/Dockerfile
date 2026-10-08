ARG AIRFLOW_BASE_IMAGE=apache/airflow:2.10.5-python3.12
ARG AIRFLOW_VERSION=2.10.5
ARG PYTHON_VERSION=3.12
FROM ${AIRFLOW_BASE_IMAGE}

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*
USER airflow

COPY pipeline/airflow/dbt-requirements.txt /dbt-requirements.txt
RUN --mount=type=cache,target=/home/airflow/.cache/pip,uid=50000,gid=0 \
    python -m venv /opt/airflow/dbt_venv \
    && /opt/airflow/dbt_venv/bin/pip install --retries 10 --timeout 120 \
    -r /dbt-requirements.txt

COPY pipeline/airflow/requirements.txt /requirements.txt
RUN --mount=type=cache,target=/home/airflow/.cache/pip,uid=50000,gid=0 \
    case "${PYTHON_VERSION}" in \
      *.*.*) AIRFLOW_CONSTRAINT_PYTHON_VERSION="${PYTHON_VERSION%.*}" ;; \
      *) AIRFLOW_CONSTRAINT_PYTHON_VERSION="${PYTHON_VERSION}" ;; \
    esac \
    && pip install --retries 10 --timeout 120 \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${AIRFLOW_CONSTRAINT_PYTHON_VERSION}.txt" \
    -r /requirements.txt

ENV PATH="${PATH}:/opt/airflow/dbt_venv/bin"

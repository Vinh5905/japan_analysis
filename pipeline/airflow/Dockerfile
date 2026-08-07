ARG AIRFLOW_BASE_IMAGE=apache/airflow:2.10.5-python3.12
ARG AIRFLOW_VERSION=2.10.5
ARG PYTHON_VERSION=3.12
FROM ${AIRFLOW_BASE_IMAGE}

COPY pipeline/airflow/requirements.txt /requirements.txt
RUN pip install --no-cache-dir \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt" \
    -r /requirements.txt

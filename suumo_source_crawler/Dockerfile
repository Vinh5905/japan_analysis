# syntax=docker/dockerfile:1.7
ARG PYTHON_IMAGE=python:3.12.4-slim-bookworm
FROM ${PYTHON_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN --mount=type=cache,id=suumo-source-crawler-apt-cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=suumo-source-crawler-apt-lib,target=/var/lib/apt,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean \
    && apt-get update \
    && apt-get install -y --no-install-recommends curl libpq5 netcat-openbsd postgresql-client

COPY requirements.txt /tmp/requirements.txt
RUN --mount=type=cache,id=suumo-source-crawler-pip,target=/root/.cache/pip \
    pip install --upgrade pip \
    && pip install -r /tmp/requirements.txt

COPY docker/python/healthcheck.py /usr/local/bin/python-healthcheck
COPY docker/python/bin/ /usr/local/bin/

# Dev images bind-mount the source tree, but the same command wrappers are kept
# here so local and release usage share names: crawl-links/html/page.
RUN chmod +x /usr/local/bin/python-healthcheck \
    /usr/local/bin/crawl-links \
    /usr/local/bin/crawl-html \
    /usr/local/bin/crawl-page \
    /usr/local/bin/crawler-init \
    /usr/local/bin/crawler-shell \
    /usr/local/bin/manual-rerun-failed-html \
    /usr/local/bin/minio-preview

CMD ["python", "-m", "http.server", "8000"]

ARG POSTGRES_BASE_IMAGE=postgres:16.3-bookworm@sha256:d0f363f8366fbc3f52d172c6e76bc27151c3d643b870e1062b4e8bfe65baf609
FROM ${POSTGRES_BASE_IMAGE}
# Preserve the PostgreSQL server supplied by the base image; installing extension
# packages must never silently upgrade the server within an existing volume.
RUN apt-mark hold postgresql-16 postgresql-client-16 \
 && apt-get update \
 && apt-get install -y --no-install-recommends postgresql-16-postgis-3 postgresql-16-postgis-3-scripts \
 && dpkg-query -W postgresql-16 postgresql-16-postgis-3 postgresql-16-postgis-3-scripts > /usr/local/share/postgis-packages.txt \
 && rm -rf /var/lib/apt/lists/*

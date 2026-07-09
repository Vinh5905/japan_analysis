#!/bin/sh
set -eu

MC_ALIAS=local
MINIO_URL="http://${MINIO_HOST}:${MINIO_API_PORT}"

mc alias set "${MC_ALIAS}" "${MINIO_URL}" "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}"

OLD_IFS="${IFS}"
IFS=","
for bucket in ${MINIO_DEFAULT_BUCKETS}; do
  bucket_name="${bucket#"${bucket%%[![:space:]]*}"}"
  bucket_name="${bucket_name%"${bucket_name##*[![:space:]]}"}"
  if [ -n "${bucket_name}" ]; then
    mc mb --ignore-existing "${MC_ALIAS}/${bucket_name}"
  fi
done
IFS="${OLD_IFS}"

mc ls "${MC_ALIAS}"

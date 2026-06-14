#!/usr/bin/env bash

set -euo pipefail

# Run this script on the Tulip host.
# It pulls completed PCAP files from a remote machine and atomically moves
# them to the directory watched by the Tulip assembler.

REMOTE_USER="${REMOTE_USER:-root}"
REMOTE_HOST="${REMOTE_HOST:-10.0.0.2}"
REMOTE_PCAP_DIR="${REMOTE_PCAP_DIR:-/var/tmp/tulip-pcaps}"

# This must match TRAFFIC_DIR_HOST in .env (or a subdirectory of it).
TULIP_TRAFFIC_DIR="${TULIP_TRAFFIC_DIR:-/tmp/tulip-traffic}"
STAGING_DIR="${STAGING_DIR:-/tmp/tulip-traffic-inbox}"

RSYNC_SSH_OPTS="${RSYNC_SSH_OPTS:--o StrictHostKeyChecking=accept-new}"
DELETE_REMOTE_AFTER_PULL="${DELETE_REMOTE_AFTER_PULL:-0}"

mkdir -p "${TULIP_TRAFFIC_DIR}" "${STAGING_DIR}"

echo "[sync] remote=${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PCAP_DIR}"
echo "[sync] staging=${STAGING_DIR}"
echo "[sync] target=${TULIP_TRAFFIC_DIR}"

RSYNC_ARGS=(
  -az
  --partial
  --append-verify
  --prune-empty-dirs
  --include='*/'
  --include='*.pcap'
  --exclude='*'
  -e "ssh ${RSYNC_SSH_OPTS}"
)

if [[ "${DELETE_REMOTE_AFTER_PULL}" == "1" ]]; then
  RSYNC_ARGS+=(--remove-source-files)
fi

rsync "${RSYNC_ARGS[@]}" \
  "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PCAP_DIR}/" \
  "${STAGING_DIR}/"

shopt -s nullglob
for f in "${STAGING_DIR}"/*.pcap; do
  # Atomic rename on same filesystem prevents partial reads by inotify consumers.
  mv "${f}" "${TULIP_TRAFFIC_DIR}/"
done

echo "[sync] done"

#!/usr/bin/env bash

set -euo pipefail

# Run this script on the remote machine where traffic is generated.
# It creates rotating PCAP files that can be pulled by Tulip host.

IFACE="${IFACE:-eth0}"
REMOTE_PCAP_DIR="${REMOTE_PCAP_DIR:-/var/tmp/tulip-pcaps}"
ROTATE_SECONDS="${ROTATE_SECONDS:-60}"
SNAPLEN="${SNAPLEN:-0}"

# Optional BPF, example: export BPF_FILTER='host 10.60.4.1 and port 5000'
BPF_FILTER="${BPF_FILTER:-}"

mkdir -p "${REMOTE_PCAP_DIR}"

echo "[capture] interface=${IFACE}"
echo "[capture] out=${REMOTE_PCAP_DIR}"
echo "[capture] rotate=${ROTATE_SECONDS}s"

if [[ -n "${BPF_FILTER}" ]]; then
  exec tcpdump \
    -i "${IFACE}" \
    -s "${SNAPLEN}" \
    -G "${ROTATE_SECONDS}" \
    -w "${REMOTE_PCAP_DIR}/traffic_%Y-%m-%d_%H-%M-%S.pcap" \
    "${BPF_FILTER}"
else
  exec tcpdump \
    -i "${IFACE}" \
    -s "${SNAPLEN}" \
    -G "${ROTATE_SECONDS}" \
    -w "${REMOTE_PCAP_DIR}/traffic_%Y-%m-%d_%H-%M-%S.pcap"
fi

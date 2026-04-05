#!/bin/bash
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

require_root() {
  if [ "$(id -u)" -ne 0 ]; then
    echo "Run this script as root: sudo $0" >&2
    exit 1
  fi
}

require_root

echo
echo "[1/3] Running radio host bootstrap"
REBOOT_ON_COMPLETE=0 "${SCRIPT_DIR}/build-radio-host.sh"

echo
echo "[2/3] Running VISR app bootstrap"
"${SCRIPT_DIR}/install-visr.sh"

echo
echo "[3/3] Rebooting now so the Wi-Fi driver, Docker stack, and services come up cleanly"
sleep 3
reboot

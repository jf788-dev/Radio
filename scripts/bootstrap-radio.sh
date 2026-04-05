#!/bin/bash
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo
echo "[1/2] Running radio host bootstrap"
"${SCRIPT_DIR}/build-radio-host.sh"

echo
echo "[2/2] Running VISR app bootstrap"
"${SCRIPT_DIR}/install-visr.sh"

echo "Full radio bootstrap complete. Reboot before using the radio."

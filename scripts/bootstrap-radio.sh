#!/bin/bash
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

"${SCRIPT_DIR}/build-radio-host.sh"
"${SCRIPT_DIR}/install-visr.sh"

echo "Full radio bootstrap complete. Reboot before using the radio."

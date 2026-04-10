#!/bin/bash
set -eu

APP_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec /usr/bin/env python3 "${APP_ROOT}/scripts/wfb_boot.py" "$@"

#!/bin/bash
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
RESUME_UNIT="/etc/systemd/system/visr-bootstrap-resume.service"
STATE_DIR="/var/lib/visr-bootstrap"
STATE_FILE="${STATE_DIR}/pending"

require_root() {
  if [ "$(id -u)" -ne 0 ]; then
    echo "Run this script as root: sudo $0" >&2
    exit 1
  fi
}

install_resume_unit() {
  install -d -m 755 "$STATE_DIR"
  touch "$STATE_FILE"

  cat >"$RESUME_UNIT" <<EOF
[Unit]
Description=VISR bootstrap resume
After=network-online.target
Wants=network-online.target
ConditionPathExists=${STATE_FILE}

[Service]
Type=oneshot
WorkingDirectory=${REPO_ROOT}
ExecStart=${SCRIPT_DIR}/bootstrap-radio.sh --resume

[Install]
WantedBy=multi-user.target
EOF

  systemctl daemon-reload
  systemctl enable visr-bootstrap-resume.service
}

cleanup_resume_unit() {
  rm -f "$STATE_FILE"
  systemctl disable visr-bootstrap-resume.service 2>/dev/null || true
  rm -f "$RESUME_UNIT"
  systemctl daemon-reload
}

require_root

if [ "${1:-}" = "--resume" ]; then
  echo
  echo "[resume] Running VISR app bootstrap"
  "${SCRIPT_DIR}/install-visr.sh"
  cleanup_resume_unit
  echo "Full radio bootstrap complete."
  exit 0
fi

echo
echo "[1/2] Running radio host bootstrap"
install_resume_unit
REBOOT_ON_COMPLETE=1 "${SCRIPT_DIR}/build-radio-host.sh"

echo "Host bootstrap returned without reboot; running app bootstrap directly."
"${SCRIPT_DIR}/install-visr.sh"
cleanup_resume_unit
echo "Full radio bootstrap complete."

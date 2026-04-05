#!/bin/bash
set -eu

APP_ROOT="${APP_ROOT:-/opt/visr}"
SYSTEMD_DIR="/etc/systemd/system"
VENV_DIR="${APP_ROOT}/venv"
SERVICE_USER="${SERVICE_USER:-pi}"
SOURCE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IPRADIO_DIR="/etc/ipradio"
IPRADIO_BASE_CFG="${IPRADIO_DIR}/base.cfg"
IPRADIO_CURRENT_KEY_PATH="${IPRADIO_DIR}/current_key.json"
IPRADIO_KEY_INDEX_PATH="${IPRADIO_DIR}/keys/index.json"
LIVE_WFB_CFG="/etc/wifibroadcast.cfg"
LIVE_GS_KEY="/etc/gs.key"
LIVE_DRONE_KEY="/etc/drone.key"
BUNDLED_TEST_KEY_DIR="${APP_ROOT}/config/keys/test-default"
TOTAL_STEPS=6
STEP=0

print_step() {
  STEP=$((STEP + 1))
  echo
  echo "[${STEP}/${TOTAL_STEPS}] $1"
}

require_root() {
  if [ "$(id -u)" -ne 0 ]; then
    echo "Run this installer as root: sudo $0" >&2
    exit 1
  fi
}

install_unit() {
  local source_path="$1"
  local target_name="$2"
  install -m 644 "$source_path" "${SYSTEMD_DIR}/${target_name}"
}

enable_service() {
  local service_name="$1"
  echo "    enabling ${service_name}"
  systemctl enable --now "$service_name" >/dev/null 2>&1
}

disable_service() {
  local service_name="$1"
  echo "    disabling ${service_name}"
  systemctl disable --now "$service_name" >/dev/null 2>&1 || true
}

prepare_app_root() {
  install -d -m 755 "$APP_ROOT"

  if [ "$SOURCE_ROOT" != "$APP_ROOT" ]; then
    cp -a "${SOURCE_ROOT}/." "$APP_ROOT/"
  fi

  chown -R "${SERVICE_USER}:${SERVICE_USER}" "$APP_ROOT"
}

prepare_venv() {
  if [ ! -x "${VENV_DIR}/bin/python" ]; then
    sudo -u "$SERVICE_USER" python3 -m venv "$VENV_DIR"
  fi

  sudo -u "$SERVICE_USER" "${VENV_DIR}/bin/pip" install -r "${APP_ROOT}/requirements.txt"
}

prepare_runtime_config() {
  install -d -m 755 "$IPRADIO_DIR"
  install -d -m 755 "${IPRADIO_DIR}/keys"
  install -d -m 755 "${IPRADIO_DIR}/keys/test-default"

  if [ ! -s "$IPRADIO_BASE_CFG" ]; then
    install -m 644 "${APP_ROOT}/config/base.cfg" "$IPRADIO_BASE_CFG"
  fi

  if [ ! -s "$LIVE_WFB_CFG" ]; then
    install -m 644 "$IPRADIO_BASE_CFG" "$LIVE_WFB_CFG"
  fi

  chown -R "${SERVICE_USER}:${SERVICE_USER}" "$IPRADIO_DIR"
  chown "${SERVICE_USER}:${SERVICE_USER}" "$LIVE_WFB_CFG"
}

install_bundled_test_keys() {
  if [ ! -s "${BUNDLED_TEST_KEY_DIR}/gs.key" ] || [ ! -s "${BUNDLED_TEST_KEY_DIR}/drone.key" ]; then
    return
  fi

  install -m 644 "${BUNDLED_TEST_KEY_DIR}/gs.key" "${IPRADIO_DIR}/keys/test-default/gs.key"
  install -m 644 "${BUNDLED_TEST_KEY_DIR}/drone.key" "${IPRADIO_DIR}/keys/test-default/drone.key"
  install -m 600 "${BUNDLED_TEST_KEY_DIR}/gs.key" "$LIVE_GS_KEY"
  install -m 600 "${BUNDLED_TEST_KEY_DIR}/drone.key" "$LIVE_DRONE_KEY"

  cat >"${IPRADIO_CURRENT_KEY_PATH}" <<'EOF'
{
  "bundle_id": "test-default"
}
EOF

  cat >"${IPRADIO_KEY_INDEX_PATH}" <<'EOF'
{
  "bundles": [
    {
      "bundle_id": "test-default",
      "source": "bundled_repo_test_key",
      "generated_here": false
    }
  ]
}
EOF

  chown -R "${SERVICE_USER}:${SERVICE_USER}" "$IPRADIO_DIR"
  chown "${SERVICE_USER}:${SERVICE_USER}" "$LIVE_GS_KEY" "$LIVE_DRONE_KEY"
}

require_root

print_step "Copying app into place"
prepare_app_root

print_step "Preparing Python virtual environment"
prepare_venv

print_step "Preparing runtime config"
prepare_runtime_config

print_step "Installing bundled test key if present"
install_bundled_test_keys

print_step "Setting script permissions"
chmod 755 "${APP_ROOT}/scripts/wfb-camera.sh"
chmod 755 "${APP_ROOT}/scripts/wfb-eth0.sh"
chmod 755 "${APP_ROOT}/scripts/build-radio-host.sh"
chmod 755 "${APP_ROOT}/scripts/bootstrap-radio.sh"
chmod 755 "${APP_ROOT}/scripts/install-visr.sh"

print_step "Installing and enabling VISR services"
install_unit "${APP_ROOT}/systemd/wfb-api.service" "wfb-api.service"
install_unit "${APP_ROOT}/systemd/wfb-collect.service" "wfb-collect.service"
install_unit "${APP_ROOT}/systemd/wfb-camera.service" "wfb-camera.service"
install_unit "${APP_ROOT}/systemd/wfb-eth0.service" "wfb-eth0.service"
install_unit "${APP_ROOT}/systemd/wfb-observability.service" "wfb-observability.service"

systemctl daemon-reload

enable_service "wfb-api.service"
enable_service "wfb-collect.service"
enable_service "wfb-eth0.service"
enable_service "wfb-observability.service"
disable_service "wfb-camera.service"

echo "VISR bootstrap complete. API, collector, eth0, and observability services are enabled. Camera service is installed but disabled."

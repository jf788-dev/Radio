#!/bin/bash
set -eu

SERVICE_USER="${SERVICE_USER:-pi}"
RTL8812AU_REPO="${RTL8812AU_REPO:-https://github.com/svpcom/rtl8812au.git}"
RTL8812AU_BRANCH="${RTL8812AU_BRANCH:-v5.2.20}"
RTL8812AU_DIR="${RTL8812AU_DIR:-/usr/local/src/rtl8812au}"
WFB_KEYRING="/usr/share/keyrings/wfb-ng.gpg"
WFB_LIST="/etc/apt/sources.list.d/wfb-ng.list"
NETWORKMANAGER_CONF="/etc/NetworkManager/NetworkManager.conf"
DHCPCD_CONF="/etc/dhcpcd.conf"
TOTAL_STEPS=8
STEP=0
REBOOT_ON_COMPLETE="${REBOOT_ON_COMPLETE:-1}"

print_step() {
  STEP=$((STEP + 1))
  echo
  echo "[${STEP}/${TOTAL_STEPS}] $1"
}

print_info() {
  echo "    $1"
}

require_root() {
  if [ "$(id -u)" -ne 0 ]; then
    echo "Run this script as root: sudo $0" >&2
    exit 1
  fi
}

install_docker_if_missing() {
  print_step "Installing Docker and Docker Compose"

  if command -v docker >/dev/null 2>&1; then
    print_info "Docker already installed"
  else
    curl -fsSL https://get.docker.com | sh
    usermod -aG docker "$SERVICE_USER" || true
  fi

  if docker compose version >/dev/null 2>&1; then
    print_info "Docker Compose plugin available"
    return
  fi

  apt install -y docker-compose-plugin || true

  if docker compose version >/dev/null 2>&1; then
    print_info "Docker Compose plugin installed"
    return
  fi

  echo "Docker is installed but 'docker compose' is not available." >&2
  exit 1
}

configure_wfb_repo() {
  print_step "Configuring WFB-ng apt repository"

  if [ ! -f "$WFB_KEYRING" ]; then
    curl -s https://apt.wfb-ng.org/public.asc | gpg --dearmor --yes -o "$WFB_KEYRING"
  fi

  cat >"$WFB_LIST" <<EOF
deb [signed-by=$WFB_KEYRING] https://apt.wfb-ng.org/ $(lsb_release -cs) master
EOF
}

install_rtl8812au() {
  print_step "Installing RTL8812AU DKMS driver"

  if [ ! -d "$RTL8812AU_DIR/.git" ]; then
    rm -rf "$RTL8812AU_DIR"
    git clone -b "$RTL8812AU_BRANCH" "$RTL8812AU_REPO" "$RTL8812AU_DIR"
  else
    git -C "$RTL8812AU_DIR" fetch --all --tags
    git -C "$RTL8812AU_DIR" checkout "$RTL8812AU_BRANCH"
    git -C "$RTL8812AU_DIR" pull --ff-only || true
  fi

  (cd "$RTL8812AU_DIR" && ./dkms-install.sh)
}

configure_network_manager() {
  print_step "Configuring NetworkManager for wlan1"
  install -d -m 755 /etc/NetworkManager
  cat >"$NETWORKMANAGER_CONF" <<'EOF'
[main]
plugins=ifupdown,keyfile

[ifupdown]
managed=false

[keyfile]
unmanaged-devices=interface-name:wlan1
EOF
}

configure_dhcpcd() {
  print_step "Configuring dhcpcd for wlan1"
  if [ -f "$DHCPCD_CONF" ]; then
    if ! grep -q '^denyinterfaces wlan1$' "$DHCPCD_CONF"; then
      printf '\ndenyinterfaces wlan1\n' >>"$DHCPCD_CONF"
    fi
  fi
}

restart_network_services() {
  print_step "Restarting network services and unblocking RF"
  systemctl daemon-reload
  systemctl restart NetworkManager 2>/dev/null || true
  systemctl restart dhcpcd 2>/dev/null || true
  rfkill unblock all || true
}

require_root

print_step "Updating host packages"
apt update
apt upgrade -y
apt full-upgrade -y
apt autoremove -y

print_step "Installing host package dependencies"
apt install -y \
  curl \
  dkms \
  ffmpeg \
  git \
  gnupg \
  gstreamer1.0-plugins-bad \
  gstreamer1.0-plugins-base \
  gstreamer1.0-plugins-good \
  gstreamer1.0-tools \
  lsb-release \
  python3 \
  python3-venv \
  rpicam-apps \
  rfkill

install_docker_if_missing
install_rtl8812au
configure_wfb_repo

print_step "Installing WFB-ng"
apt update
apt install -y wfb-ng

configure_network_manager
configure_dhcpcd
restart_network_services

echo
if [ "$REBOOT_ON_COMPLETE" = "1" ]; then
  echo "Radio host build complete. Rebooting now so the Wi-Fi driver and network stack come up cleanly."
  sleep 3
  reboot
else
  echo "Radio host build complete. Reboot skipped because REBOOT_ON_COMPLETE=0."
fi

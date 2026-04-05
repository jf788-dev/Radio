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

require_root() {
  if [ "$(id -u)" -ne 0 ]; then
    echo "Run this script as root: sudo $0" >&2
    exit 1
  fi
}

install_docker_if_missing() {
  if command -v docker >/dev/null 2>&1; then
    return
  fi

  curl -fsSL https://get.docker.com | sh
  usermod -aG docker "$SERVICE_USER" || true
}

configure_wfb_repo() {
  if [ ! -f "$WFB_KEYRING" ]; then
    curl -s https://apt.wfb-ng.org/public.asc | gpg --dearmor --yes -o "$WFB_KEYRING"
  fi

  cat >"$WFB_LIST" <<EOF
deb [signed-by=$WFB_KEYRING] https://apt.wfb-ng.org/ $(lsb_release -cs) master
EOF
}

install_rtl8812au() {
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
  if [ -f "$DHCPCD_CONF" ]; then
    if ! grep -q '^denyinterfaces wlan1$' "$DHCPCD_CONF"; then
      printf '\ndenyinterfaces wlan1\n' >>"$DHCPCD_CONF"
    fi
  fi
}

restart_network_services() {
  systemctl daemon-reload
  systemctl restart NetworkManager 2>/dev/null || true
  systemctl restart dhcpcd 2>/dev/null || true
  rfkill unblock all || true
}

require_root

apt update
apt upgrade -y
apt full-upgrade -y
apt autoremove -y

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

apt update
apt install -y wfb-ng

configure_network_manager
configure_dhcpcd
restart_network_services

echo "Radio host build complete. Reboot is strongly recommended before first radio test."

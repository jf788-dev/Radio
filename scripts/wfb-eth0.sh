#!/bin/bash
set -eu

NODE_FILE="/etc/ipradio/node.json"
ETH_IFACE="eth0"
MGMT_IFACE="eth0mgmt"
LO_IFACE="lo"
ACCESS_PREFIX="172.22"
LOOPBACK_PREFIX="10.5.0"
MANAGEMENT_PREFIX="169.254"
MANAGEMENT_ADDRESS="${MANAGEMENT_ADDRESS:-169.254.100.1/16}"

get_node_config() {
  if [ ! -f "$NODE_FILE" ]; then
    return 1
  fi

  python3 - <<'PY'
import json
import os

node_file = os.environ["NODE_FILE"]

with open(node_file, "r", encoding="utf-8") as file_handle:
    node = json.load(file_handle)

node_id = int(node["node_id"])
eth0_gateway = f"172.22.{node_id}.1/24"
loopback_address = f"10.5.0.{node_id}/32"

print(f"{eth0_gateway} {loopback_address}")
PY
}

delete_prefix_addresses() {
  local iface="$1"
  local prefix="$2"
  /sbin/ip -4 -o addr show dev "$iface" | awk '{print $4}' | while read -r cidr; do
    case "$cidr" in
      ${prefix}.*)
        /usr/bin/sudo /sbin/ip address del "$cidr" dev "$iface" 2>/dev/null || true
        ;;
    esac
  done
}

apply_sysctls() {
  /usr/bin/sudo /usr/sbin/sysctl -w net.ipv4.ip_forward=1 >/dev/null
  /usr/bin/sudo /usr/sbin/sysctl -w net.ipv4.conf.all.send_redirects=0 >/dev/null
  /usr/bin/sudo /usr/sbin/sysctl -w net.ipv4.conf.default.send_redirects=0 >/dev/null
  /usr/bin/sudo /usr/sbin/sysctl -w net.ipv4.conf.all.accept_redirects=0 >/dev/null
  /usr/bin/sudo /usr/sbin/sysctl -w net.ipv4.conf.default.accept_redirects=0 >/dev/null
  /usr/bin/sudo /usr/sbin/sysctl -w net.ipv4.conf.all.rp_filter=0 >/dev/null
  /usr/bin/sudo /usr/sbin/sysctl -w net.ipv4.conf.default.rp_filter=0 >/dev/null
}

ensure_management_interface() {
  if ! /sbin/ip link show dev "$MGMT_IFACE" >/dev/null 2>&1; then
    /usr/bin/sudo /sbin/ip link add "$MGMT_IFACE" link "$ETH_IFACE" type macvlan mode bridge
  fi
}

set_eth0_unmanaged() {
  if [ -x /usr/bin/nmcli ]; then
    /usr/bin/sudo /usr/bin/nmcli device set "$ETH_IFACE" managed no >/dev/null 2>&1 || true
  fi
}

apply_addresses() {
  ensure_management_interface
  /usr/bin/sudo /sbin/ip link set "$ETH_IFACE" up
  /usr/bin/sudo /sbin/ip link set "$MGMT_IFACE" up
  /usr/bin/sudo /sbin/ip link set "$LO_IFACE" up
  delete_prefix_addresses "$ETH_IFACE" "$MANAGEMENT_PREFIX"
  delete_prefix_addresses "$MGMT_IFACE" "$MANAGEMENT_PREFIX"
  /usr/bin/sudo /sbin/ip address replace "$MANAGEMENT_ADDRESS" dev "$MGMT_IFACE"

  delete_prefix_addresses "$ETH_IFACE" "$ACCESS_PREFIX"
  delete_prefix_addresses "$ETH_IFACE" "$LOOPBACK_PREFIX"
  delete_prefix_addresses "$LO_IFACE" "$LOOPBACK_PREFIX"

  if NODE_CONFIG="$(NODE_FILE="$NODE_FILE" get_node_config)"; then
    # On provisioned nodes, keep NetworkManager alive for wlan1 but force it to leave eth0 alone.
    set_eth0_unmanaged
    ETH0_GATEWAY="$(printf '%s' "$NODE_CONFIG" | awk '{print $1}')"
    LOOPBACK_ADDRESS="$(printf '%s' "$NODE_CONFIG" | awk '{print $2}')"
    /usr/bin/sudo /sbin/ip address replace "$ETH0_GATEWAY" dev "$ETH_IFACE"
    /usr/bin/sudo /sbin/ip address replace "$LOOPBACK_ADDRESS" dev "$LO_IFACE"
    apply_sysctls
  fi
}

apply_addresses

/usr/bin/sudo /sbin/ip monitor link address | while read -r _; do
  apply_addresses
done

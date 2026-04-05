#!/bin/bash
set -eu

NODE_FILE="/etc/ipradio/node.json"
ETH_IFACE="eth0"
SUBNET_PREFIX="10.5.0"
MANAGEMENT_ADDRESS="${MANAGEMENT_ADDRESS:-169.254.100.1/24}"

get_node_id() {
  if [ ! -f "$NODE_FILE" ]; then
    return 1
  fi

  python3 - <<'PY'
import json

with open("/etc/ipradio/node.json", "r", encoding="utf-8") as file_handle:
    node = json.load(file_handle)

print(int(node["node_id"]))
PY
}

apply_addresses() {
  /usr/bin/sudo /sbin/ip link set "$ETH_IFACE" up
  /usr/bin/sudo /sbin/ip address replace "$MANAGEMENT_ADDRESS" dev "$ETH_IFACE"

  if NODE_ID="$(get_node_id)"; then
    /usr/bin/sudo /sbin/ip address replace "${SUBNET_PREFIX}.${NODE_ID}/24" dev "$ETH_IFACE"
  fi
}

apply_addresses

/usr/bin/sudo /sbin/ip monitor link address dev "$ETH_IFACE" | while read -r _; do
  apply_addresses
done

#!/bin/bash
set -eu

NODE_FILE="/etc/ipradio/node.json"
ETH_IFACE="eth0"
SUBNET_PREFIX="10.5.0"

if [ ! -f "$NODE_FILE" ]; then
  echo "Missing node file: $NODE_FILE" >&2
  exit 1
fi

NODE_ID="$(python3 - <<'PY'
import json

with open("/etc/ipradio/node.json", "r", encoding="utf-8") as file_handle:
    node = json.load(file_handle)

print(int(node["node_id"]))
PY
)"

/usr/bin/sudo /sbin/ip link set "$ETH_IFACE" up
exec /usr/bin/sudo /sbin/ip address replace "${SUBNET_PREFIX}.${NODE_ID}/24" dev "$ETH_IFACE"

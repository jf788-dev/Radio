#!/bin/bash
set -eu

NODE_FILE="/etc/ipradio/node.json"
CONFIG_PATH="/etc/ipradio/dnsmasq.conf"
LEASE_FILE="/run/wfb-dhcp.leases"
ETH_IFACE="eth0"

if [ ! -f "$NODE_FILE" ]; then
  echo "Missing ${NODE_FILE}; refusing to start DHCP before provisioning." >&2
  exit 1
fi

python3 - <<'PY' >"$CONFIG_PATH"
import json

with open("/etc/ipradio/node.json", "r", encoding="utf-8") as file_handle:
    node = json.load(file_handle)

node_id = int(node["node_id"])
gateway_ip = node.get("eth0_gateway_ip", f"172.22.{node_id}.1")
range_start = node.get("dhcp_range_start", f"172.22.{node_id}.100")
range_end = node.get("dhcp_range_end", f"172.22.{node_id}.199")

print("port=0")
print("interface=eth0")
print(f"listen-address={gateway_ip}")
print("bind-interfaces")
print("except-interface=lo")
print("dhcp-authoritative")
print(f"dhcp-range={range_start},{range_end},255.255.255.0,12h")
print(f"dhcp-option=option:router,{gateway_ip}")
print(f"dhcp-option=option:dns-server,{gateway_ip}")
print("dhcp-option=option:netmask,255.255.255.0")
print("dhcp-option=option:mtu,1500")
print("dhcp-lease-max=64")
print("dhcp-leasefile=/run/wfb-dhcp.leases")
PY

touch "$LEASE_FILE"

exec /usr/sbin/dnsmasq --keep-in-foreground --conf-file="$CONFIG_PATH"

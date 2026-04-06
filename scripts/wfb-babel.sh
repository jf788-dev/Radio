#!/bin/bash
set -eu

NODE_FILE="/etc/ipradio/node.json"
CONFIG_PATH="/etc/ipradio/babeld.conf"
PID_FILE="/run/wfb-babel.pid"
STATE_FILE="/var/lib/babel-state"

get_tunnel_interfaces() {
  python3 - <<'PY'
import json


def tunnel_ifname(node_id: int, peer: int) -> str:
    return f"wfb{node_id:02d}{peer:02d}"


with open("/etc/ipradio/node.json", "r", encoding="utf-8") as file_handle:
    node = json.load(file_handle)

node_id = int(node["node_id"])
peers = sorted({int(peer) for peer in node.get("links", []) if int(peer) != node_id})

for peer in peers:
    print(tunnel_ifname(node_id, peer))
PY
}

enable_ipv6_for_babel() {
  /usr/bin/sudo /usr/sbin/sysctl -w net.ipv6.conf.all.disable_ipv6=0 >/dev/null
  /usr/bin/sudo /usr/sbin/sysctl -w net.ipv6.conf.default.disable_ipv6=0 >/dev/null

  while read -r iface; do
    [ -n "$iface" ] || continue
    /usr/bin/sudo /usr/sbin/sysctl -w "net.ipv6.conf.${iface}.disable_ipv6=0" >/dev/null 2>&1 || true
  done <<EOF
$(get_tunnel_interfaces)
EOF
}

wait_for_link_local() {
  local tries=20

  while [ "$tries" -gt 0 ]; do
    local ready=1

    while read -r iface; do
      [ -n "$iface" ] || continue
      if ! /sbin/ip -6 addr show dev "$iface" scope link | /bin/grep -q 'inet6 fe80:'; then
        ready=0
        break
      fi
    done <<EOF
$(get_tunnel_interfaces)
EOF

    if [ "$ready" -eq 1 ]; then
      return 0
    fi

    sleep 1
    tries=$((tries - 1))
  done
}

if [ ! -f "$NODE_FILE" ]; then
  echo "Missing ${NODE_FILE}; refusing to start Babel before provisioning." >&2
  exit 1
fi

mkdir -p "$(dirname "$STATE_FILE")"

python3 - <<'PY' >"$CONFIG_PATH"
import json


def tunnel_ifname(node_id: int, peer: int) -> str:
    return f"wfb{node_id:02d}{peer:02d}"


with open("/etc/ipradio/node.json", "r", encoding="utf-8") as file_handle:
    node = json.load(file_handle)

node_id = int(node["node_id"])
peers = sorted({int(peer) for peer in node.get("links", []) if int(peer) != node_id})
eth0_subnet = node.get("eth0_subnet", f"172.22.{node_id}.0/24")
loopback_address = node.get("loopback_address", f"10.5.0.{node_id}/32")

print("kernel-priority 100")
print("link-detect true")
print("default type tunnel hello-interval 4 update-interval 16")

for peer in peers:
    print(f"interface {tunnel_ifname(node_id, peer)} type tunnel split-horizon false")

print(f"redistribute ip {eth0_subnet} if eth0 metric 256")
print(f"redistribute local ip {loopback_address} if lo metric 128")
print("redistribute local deny")
PY

if ! grep -q '^interface ' "$CONFIG_PATH"; then
  echo "No peer tunnels configured; Babel is not needed for this node." >&2
  exit 0
fi

enable_ipv6_for_babel
wait_for_link_local

exec /usr/sbin/babeld -d 1 -I "$PID_FILE" -S "$STATE_FILE" -c "$CONFIG_PATH"

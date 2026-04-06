#!/bin/bash
set -eu

NODE_FILE="/etc/ipradio/node.json"
ETH0_SERVICE="wfb-eth0.service"
DHCP_SERVICE="wfb-dhcp.service"
BABEL_SERVICE="wfb-babel.service"

if [ ! -f "$NODE_FILE" ]; then
  exit 0
fi

read_node_config() {
  python3 - <<'PY'
import json

with open("/etc/ipradio/node.json", "r", encoding="utf-8") as file_handle:
    node = json.load(file_handle)

node_id = int(node["node_id"])
peers = [int(peer) for peer in node.get("links", []) if int(peer) != node_id]

print(node_id)
print(len(peers))
PY
}

NODE_INFO="$(read_node_config)"
NODE_ID="$(printf '%s' "$NODE_INFO" | sed -n '1p')"
PEER_COUNT="$(printf '%s' "$NODE_INFO" | sed -n '2p')"
RADIO_SERVICE="$(printf 'wifibroadcast@node%02d' "$NODE_ID")"

/usr/bin/sudo /usr/sbin/rfkill unblock all >/dev/null 2>&1 || true
/usr/bin/sudo /bin/systemctl enable --now "$RADIO_SERVICE" >/dev/null 2>&1 || true
/usr/bin/sudo /bin/systemctl restart "$RADIO_SERVICE" >/dev/null 2>&1 || true

# eth0 is the final refresh step after the radio profile has recreated the tunnel interfaces.
/usr/bin/sudo /bin/systemctl enable --now "$ETH0_SERVICE" >/dev/null 2>&1 || true
/usr/bin/sudo /bin/systemctl restart "$ETH0_SERVICE" >/dev/null 2>&1 || true
/usr/bin/sudo /bin/systemctl enable --now "$DHCP_SERVICE" >/dev/null 2>&1 || true
/usr/bin/sudo /bin/systemctl restart "$DHCP_SERVICE" >/dev/null 2>&1 || true

if [ "$PEER_COUNT" -gt 0 ]; then
  /usr/bin/sudo /bin/systemctl enable --now "$BABEL_SERVICE" >/dev/null 2>&1 || true
  /usr/bin/sudo /bin/systemctl restart "$BABEL_SERVICE" >/dev/null 2>&1 || true
else
  /usr/bin/sudo /bin/systemctl disable --now "$BABEL_SERVICE" >/dev/null 2>&1 || true
fi

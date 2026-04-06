import subprocess
from typing import Any

from app_config import (
    BABEL_SERVICE_NAME,
    CONFIG_PATH,
    DHCP_SERVICE_NAME,
    ETHERNET_SERVICE_NAME,
    IPRADIO_NODE_PATH,
    NODE_ID_MAX,
    NODE_ID_MIN,
    format_service_name,
)


def _run_system_command(*args: str):
    subprocess.run(list(args), check=False)


def get_service_name(node_id: int) -> str:
    return format_service_name(node_id)


def update_base_value(key, value, comment):
    with CONFIG_PATH.open("r") as file_handle:
        lines = file_handle.readlines()

    in_base = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        if stripped == "[base]":
            in_base = True
            continue

        if in_base and stripped.startswith("[") and stripped.endswith("]"):
            break

        if in_base and stripped.startswith(key):
            lines[i] = f"{key} = {value}      # {comment}\n"
            break

    with CONFIG_PATH.open("w") as file_handle:
        file_handle.writelines(lines)


def update_tunnel_value(key1, value1, key2, value2, comment1, comment2):
    with CONFIG_PATH.open("r") as file_handle:
        lines = file_handle.readlines()

    in_tunnel = False
    updated_key1 = False
    updated_key2 = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        if stripped == "[tunnel]":
            in_tunnel = True
            continue

        if in_tunnel and stripped.startswith("[") and stripped.endswith("]"):
            break

        if in_tunnel and stripped.startswith(key1):
            lines[i] = f"{key1} = {value1}      # {comment1}\n"
            updated_key1 = True

        if in_tunnel and stripped.startswith(key2):
            lines[i] = f"{key2} = {value2}      # {comment2}\n"
            updated_key2 = True

        if updated_key1 and updated_key2:
            break

    with CONFIG_PATH.open("w") as file_handle:
        file_handle.writelines(lines)


def restart_radio(node_id: int):
    service_name = get_service_name(node_id)
    _run_system_command("/usr/bin/sudo", "/usr/sbin/rfkill", "unblock", "all")
    _run_system_command("/usr/bin/sudo", "/bin/systemctl", "restart", service_name)


def sync_radio_services(node_id: int):
    target_service = get_service_name(node_id)

    for candidate_id in range(NODE_ID_MIN, NODE_ID_MAX + 1):
        service_name = get_service_name(candidate_id)
        if service_name == target_service:
            continue

        _run_system_command("/usr/bin/sudo", "/bin/systemctl", "disable", "--now", service_name)

    # Disable the legacy ground-station profile if it exists so it doesn't recreate old interfaces at boot.
    _run_system_command("/usr/bin/sudo", "/bin/systemctl", "disable", "--now", "wifibroadcast@gs")
    _run_system_command("/usr/bin/sudo", "/bin/systemctl", "enable", "--now", target_service)


def configure_eth0(node_id: int):
    del node_id
    _run_system_command("/usr/bin/sudo", "/bin/systemctl", "enable", "--now", ETHERNET_SERVICE_NAME)
    _run_system_command("/usr/bin/sudo", "/bin/systemctl", "restart", ETHERNET_SERVICE_NAME)


def _set_eth0_unmanaged():
    # Keep NetworkManager running for wlan1/nmcli, but stop it from rewriting eth0.
    _run_system_command("/usr/bin/sudo", "/usr/bin/nmcli", "device", "set", "eth0", "managed", "no")


def configure_routed_access(node_id: int):
    del node_id

    _set_eth0_unmanaged()
    # eth0 is the final refresh step after provisioning/radio changes.
    _run_system_command("/usr/bin/sudo", "/bin/systemctl", "enable", "--now", ETHERNET_SERVICE_NAME)
    _run_system_command("/usr/bin/sudo", "/bin/systemctl", "restart", ETHERNET_SERVICE_NAME)
    _run_system_command("/usr/bin/sudo", "/bin/systemctl", "enable", "--now", DHCP_SERVICE_NAME)
    _run_system_command("/usr/bin/sudo", "/bin/systemctl", "restart", DHCP_SERVICE_NAME)

    peers: list[int] = []
    if IPRADIO_NODE_PATH.exists():
        try:
            import json

            with IPRADIO_NODE_PATH.open("r", encoding="utf-8") as file_handle:
                node = json.load(file_handle)
            peers = [int(peer) for peer in node.get("links", [])]
        except Exception:
            peers = []

    if peers:
        _run_system_command("/usr/bin/sudo", "/bin/systemctl", "enable", "--now", BABEL_SERVICE_NAME)
        _run_system_command("/usr/bin/sudo", "/bin/systemctl", "restart", BABEL_SERVICE_NAME)
    else:
        _run_system_command("/usr/bin/sudo", "/bin/systemctl", "disable", "--now", BABEL_SERVICE_NAME)


def get_service_state(service_name: str) -> str:
    result = subprocess.run(
        ["/bin/systemctl", "is-active", service_name],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.stdout.strip() else "unknown"


def _read_ini_like_config() -> dict[str, dict[str, str]]:
    sections: dict[str, dict[str, str]] = {}
    current_section: str | None = None

    if not CONFIG_PATH.exists():
        return sections

    with CONFIG_PATH.open("r") as file_handle:
        for raw_line in file_handle:
            line = raw_line.split("#", 1)[0].strip()
            if not line:
                continue

            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1]
                sections.setdefault(current_section, {})
                continue

            if current_section and "=" in line:
                key, value = line.split("=", 1)
                sections[current_section][key.strip()] = value.strip().strip("'\"")

    return sections


def get_current_radio_settings() -> dict[str, Any]:
    sections = _read_ini_like_config()
    base = sections.get("base", {})
    tunnel = sections.get("tunnel", {})
    node_video_rx = sections.get("node_video_rx", {})
    peers: list[int] = []

    if IPRADIO_NODE_PATH.exists():
        try:
            import json

            with IPRADIO_NODE_PATH.open("r", encoding="utf-8") as file_handle:
                node = json.load(file_handle)
            peers = [int(peer) for peer in node.get("links", [])]
        except Exception:
            peers = []

    return {
        "mcs_index": base.get("mcs_index"),
        "bandwidth": base.get("bandwidth"),
        "fec_k": tunnel.get("fec_k"),
        "fec_n": tunnel.get("fec_n"),
        "video_rx_target": node_video_rx.get("peer"),
        "peers": peers,
    }

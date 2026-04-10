import subprocess
from typing import Any

from app_config import (
    CONFIG_PATH,
    IPRADIO_NODE_PATH,
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

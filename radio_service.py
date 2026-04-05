import subprocess

from app_config import CONFIG_PATH, NODE_ID_MAX, NODE_ID_MIN, format_service_name


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
    subprocess.run(["/usr/bin/sudo", "/usr/sbin/rfkill", "unblock", "all"])
    subprocess.run(["/usr/bin/sudo", "/bin/systemctl", "restart", service_name])


def sync_radio_services(node_id: int):
    target_service = get_service_name(node_id)

    for candidate_id in range(NODE_ID_MIN, NODE_ID_MAX + 1):
        service_name = get_service_name(candidate_id)
        if service_name == target_service:
            continue

        subprocess.run(["/usr/bin/sudo", "/bin/systemctl", "disable", "--now", service_name])

    # Disable the legacy ground-station profile if it exists so it doesn't recreate old interfaces at boot.
    subprocess.run(["/usr/bin/sudo", "/bin/systemctl", "disable", "--now", "wifibroadcast@gs"])
    subprocess.run(["/usr/bin/sudo", "/bin/systemctl", "enable", "--now", target_service])


def get_service_state(service_name: str) -> str:
    result = subprocess.run(
        ["/bin/systemctl", "is-active", service_name],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.stdout.strip() else "unknown"

import subprocess
from typing import Any

from app_config import CAMERA_CONFIG_PATH, CAMERA_SERVICE_NAME


def set_camera_values(width, height, framerate, bitrate, lens_position):
    with CAMERA_CONFIG_PATH.open("r") as file_handle:
        lines = file_handle.readlines()

    replacements = {
        "WIDTH": str(width),
        "HEIGHT": str(height),
        "FRAMERATE": str(framerate),
        "BITRATE": str(bitrate),
        "LENS_POSITION": str(lens_position),
    }

    found = {key: False for key in replacements}

    for i, line in enumerate(lines):
        for key, value in replacements.items():
            if line.startswith(key + "="):
                lines[i] = f"{key}={value}\n"
                found[key] = True

    for key, value in replacements.items():
        if not found[key]:
            lines.append(f"{key}={value}\n")

    with CAMERA_CONFIG_PATH.open("w") as file_handle:
        file_handle.writelines(lines)


def restart_camera():
    subprocess.run(["/usr/bin/sudo", "/bin/systemctl", "restart", CAMERA_SERVICE_NAME])


def stop_camera():
    subprocess.run(["/usr/bin/sudo", "/bin/systemctl", "stop", CAMERA_SERVICE_NAME])


def start_camera():
    subprocess.run(["/usr/bin/sudo", "/bin/systemctl", "start", CAMERA_SERVICE_NAME])


def get_camera_values() -> dict[str, Any]:
    values: dict[str, Any] = {
        "width": None,
        "height": None,
        "framerate": None,
        "bitrate": None,
        "lens_position": None,
    }

    if not CAMERA_CONFIG_PATH.exists():
        return values

    key_map = {
        "WIDTH": "width",
        "HEIGHT": "height",
        "FRAMERATE": "framerate",
        "BITRATE": "bitrate",
        "LENS_POSITION": "lens_position",
    }

    with CAMERA_CONFIG_PATH.open("r") as file_handle:
        for raw_line in file_handle:
            line = raw_line.strip()
            if not line or "=" not in line:
                continue

            key, value = line.split("=", 1)
            mapped_key = key_map.get(key)
            if not mapped_key:
                continue

            values[mapped_key] = value.strip()

    return values

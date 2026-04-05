import subprocess

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

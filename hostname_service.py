import subprocess
from pathlib import Path

from app_config import HOSTNAME_PATH, HOSTS_PATH, format_hostname


def set_node_hostname(node_id: int) -> str:
    hostname = format_hostname(node_id)

    subprocess.run(["/usr/bin/sudo", "/bin/hostnamectl", "set-hostname", hostname], check=True)

    subprocess.run(
        [
            "/usr/bin/sudo",
            "/usr/bin/python3",
            "-c",
            """
from pathlib import Path

hostname_path = Path("/etc/hostname")
hosts_path = Path("/etc/hosts")
hostname = %r

hostname_path.write_text(hostname + "\\n")

hosts_lines = []
if hosts_path.exists():
    hosts_lines = hosts_path.read_text().splitlines()

updated = False
new_lines = []
for line in hosts_lines:
    stripped = line.strip()
    if stripped.startswith("127.0.1.1"):
        new_lines.append(f"127.0.1.1\\t{hostname}")
        updated = True
    else:
        new_lines.append(line)

if not updated:
    new_lines.append(f"127.0.1.1\\t{hostname}")

hosts_path.write_text("\\n".join(new_lines) + "\\n")
""" % hostname,
        ],
        check=True,
    )

    return hostname

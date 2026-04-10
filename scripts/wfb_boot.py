#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from node_config import render_wfb_config


CURRENT_NODE_FILE = Path("/etc/ipradio/node.json")
TARGET_NODE_FILE = Path("/etc/ipradio/node_prov.json")
DEFAULT_NODE_FILE = Path("/etc/ipradio/default_node.json")
ROLLBACK_NODE_FILE = Path("/run/wfb-node.rollback.json")
FINAL_CFG_FILE = Path("/etc/wifibroadcast.cfg")

API_SERVICE = "wfb-api.service"
COLLECT_SERVICE = "wfb-collect.service"
OBSERVABILITY_SERVICE = "wfb-observability.service"
ETH0_SERVICE = "wfb-eth0.service"
DHCP_SERVICE = "wfb-dhcp.service"
BABEL_SERVICE = "wfb-babel.service"


def log(message: str) -> None:
    print(f"[wfb-boot] {message}", flush=True)


def wait_for_service(service_name: str, tries: int = 10) -> None:
    for _ in range(tries):
        result = subprocess.run(
            ["/bin/systemctl", "is-active", service_name],
            check=False,
            text=True,
            capture_output=True,
        )
        if result.stdout.strip() == "active":
            return
        time.sleep(1)
    raise RuntimeError(f"{service_name} did not become active")


def choose_config() -> Path:
    if TARGET_NODE_FILE.is_file():
        return TARGET_NODE_FILE
    if CURRENT_NODE_FILE.is_file():
        return CURRENT_NODE_FILE
    if DEFAULT_NODE_FILE.is_file():
        return DEFAULT_NODE_FILE
    raise FileNotFoundError("no boot config found")


def activate_config(source_file: Path) -> dict:
    node = json.loads(source_file.read_text())
    FINAL_CFG_FILE.write_text(render_wfb_config(node))
    return node


def start_stack(node: dict) -> None:
    node_id = int(node["node_id"])
    peers = sorted({int(peer) for peer in node.get("links", []) if int(peer) != node_id})
    radio_service = f"wifibroadcast@node{node_id:02d}"
    tunnels = [f"wfb{node_id:02d}{peer:02d}" for peer in peers]

    log("starting observability")
    subprocess.run(["/bin/systemctl", "enable", "--now", OBSERVABILITY_SERVICE], check=True, text=True)

    log("starting api")
    subprocess.run(["/bin/systemctl", "enable", "--now", API_SERVICE], check=True, text=True)
    wait_for_service(API_SERVICE)

    log(f"selecting node{node_id:02d} radio")
    for candidate_id in range(1, 17):
        service_name = f"wifibroadcast@node{candidate_id:02d}"
        if service_name != radio_service:
            subprocess.run(["/bin/systemctl", "disable", "--now", service_name], check=False, text=True)
    subprocess.run(["/bin/systemctl", "disable", "--now", "wifibroadcast@gs"], check=False, text=True)
    subprocess.run(["/usr/sbin/rfkill", "unblock", "all"], check=False, text=True)
    subprocess.run(["/bin/systemctl", "enable", "--now", radio_service], check=True, text=True)
    subprocess.run(["/bin/systemctl", "restart", radio_service], check=True, text=True)
    wait_for_service(radio_service)

    if tunnels:
        log(f"waiting for {len(tunnels)} tunnel interface(s)")
        for _ in range(20):
            if all(subprocess.run(["/sbin/ip", "link", "show", "dev", tunnel], check=False).returncode == 0 for tunnel in tunnels):
                break
            time.sleep(1)
        else:
            raise RuntimeError("expected tunnel interfaces did not appear")

    log("starting eth0 keeper")
    subprocess.run(["/bin/systemctl", "enable", "--now", ETH0_SERVICE], check=True, text=True)
    subprocess.run(["/bin/systemctl", "restart", ETH0_SERVICE], check=True, text=True)
    wait_for_service(ETH0_SERVICE)

    log("starting dhcp")
    subprocess.run(["/bin/systemctl", "enable", "--now", DHCP_SERVICE], check=True, text=True)
    subprocess.run(["/bin/systemctl", "restart", DHCP_SERVICE], check=True, text=True)
    wait_for_service(DHCP_SERVICE)

    if peers:
        log("starting babel")
        subprocess.run(["/bin/systemctl", "enable", "--now", BABEL_SERVICE], check=True, text=True)
        subprocess.run(["/bin/systemctl", "restart", BABEL_SERVICE], check=True, text=True)
        wait_for_service(BABEL_SERVICE, 25)
    else:
        log("stopping babel for node without peers")
        subprocess.run(["/bin/systemctl", "disable", "--now", BABEL_SERVICE], check=False, text=True)

    log("starting collector")
    subprocess.run(["/bin/systemctl", "enable", "--now", COLLECT_SERVICE], check=True, text=True)


def rollback() -> dict:
    if ROLLBACK_NODE_FILE.is_file():
        source_file = ROLLBACK_NODE_FILE
    elif DEFAULT_NODE_FILE.is_file():
        source_file = DEFAULT_NODE_FILE
    else:
        raise FileNotFoundError("no rollback config available")

    log(f"rolling back to {source_file.name}")
    return activate_config(source_file)


def main() -> int:
    try:
        source_file = choose_config()
    except FileNotFoundError as error:
        log(str(error))
        return 1

    if CURRENT_NODE_FILE.is_file() and source_file != CURRENT_NODE_FILE:
        shutil.copy2(CURRENT_NODE_FILE, ROLLBACK_NODE_FILE)

    log(f"activating {source_file.name}")
    node = activate_config(source_file)

    try:
        start_stack(node)
    except Exception as error:
        log(f"boot failed with {source_file.name}: {error}")
        if source_file != TARGET_NODE_FILE:
            return 1

        try:
            rollback_source = ROLLBACK_NODE_FILE if ROLLBACK_NODE_FILE.is_file() else DEFAULT_NODE_FILE
            start_stack(rollback())
        except Exception as rollback_error:
            log(f"boot failed after rollback: {rollback_error}")
            return 1

        CURRENT_NODE_FILE.parent.mkdir(parents=True, exist_ok=True)
        if rollback_source != CURRENT_NODE_FILE:
            shutil.copy2(rollback_source, CURRENT_NODE_FILE)
        log("boot recovered using fallback config")
        return 0

    CURRENT_NODE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if source_file != CURRENT_NODE_FILE:
        shutil.copy2(source_file, CURRENT_NODE_FILE)

    if source_file == TARGET_NODE_FILE and TARGET_NODE_FILE.exists():
        log("target config accepted; clearing staged target")
        TARGET_NODE_FILE.unlink()

    log("boot complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

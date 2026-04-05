import base64
import hashlib
import json
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from app_config import (
    DEFAULT_TEST_KEY_BUNDLE_ID,
    IPRADIO_CURRENT_KEY_PATH,
    IPRADIO_KEY_DIR,
    IPRADIO_KEY_INDEX_PATH,
    SERVICE_USER,
    WFB_DRONE_KEY_PATH,
    WFB_GS_KEY_PATH,
    WFB_KEYGEN_COMMAND,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _fingerprint_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _ensure_key_store() -> None:
    IPRADIO_KEY_DIR.mkdir(parents=True, exist_ok=True)


def _load_index() -> dict:
    if not IPRADIO_KEY_INDEX_PATH.exists():
        return {"bundles": []}
    return json.loads(IPRADIO_KEY_INDEX_PATH.read_text())


def _save_index(index: dict) -> None:
    _ensure_key_store()
    IPRADIO_KEY_INDEX_PATH.write_text(json.dumps(index, indent=2) + "\n")


def _bundle_path(bundle_id: str) -> Path:
    return IPRADIO_KEY_DIR / bundle_id


def _metadata_path(bundle_id: str) -> Path:
    return _bundle_path(bundle_id) / "metadata.json"


def _bundle_key_paths(bundle_id: str) -> tuple[Path, Path]:
    bundle_dir = _bundle_path(bundle_id)
    return bundle_dir / "gs.key", bundle_dir / "drone.key"


def _read_bundle_bytes(bundle_id: str) -> tuple[bytes, bytes]:
    gs_path, drone_path = _bundle_key_paths(bundle_id)
    if not gs_path.exists() or not drone_path.exists():
        raise FileNotFoundError(f"missing stored key files for bundle {bundle_id}")
    return gs_path.read_bytes(), drone_path.read_bytes()


def key_bundle_exists(bundle_id: str) -> bool:
    gs_path, drone_path = _bundle_key_paths(bundle_id)
    return gs_path.exists() and drone_path.exists()


def _write_bundle(bundle_id: str, gs_key: bytes, drone_key: bytes, source: str, generated_here: bool) -> dict:
    _ensure_key_store()
    bundle_dir = _bundle_path(bundle_id)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    gs_path, drone_path = _bundle_key_paths(bundle_id)
    gs_path.write_bytes(gs_key)
    drone_path.write_bytes(drone_key)

    metadata = {
        "bundle_id": bundle_id,
        "created_at": _utc_now(),
        "source": source,
        "generated_here": generated_here,
        "gs_sha256": _fingerprint_bytes(gs_key),
        "drone_sha256": _fingerprint_bytes(drone_key),
    }
    _metadata_path(bundle_id).write_text(json.dumps(metadata, indent=2) + "\n")

    index = _load_index()
    bundles = [bundle for bundle in index["bundles"] if bundle["bundle_id"] != bundle_id]
    bundles.insert(0, metadata)
    index["bundles"] = bundles
    _save_index(index)
    return metadata


def _generate_bundle(bundle_id: str, source: str, generated_here: bool) -> dict:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        subprocess.run([WFB_KEYGEN_COMMAND], cwd=temp_path, check=True)

        gs_key_path = temp_path / "gs.key"
        drone_key_path = temp_path / "drone.key"
        if not gs_key_path.exists() or not drone_key_path.exists():
            raise FileNotFoundError("wfb_keygen did not produce gs.key and drone.key")

        gs_key = gs_key_path.read_bytes()
        drone_key = drone_key_path.read_bytes()

    metadata = _write_bundle(bundle_id, gs_key, drone_key, source=source, generated_here=generated_here)
    install_key_bundle(bundle_id)
    return metadata


def _set_current_bundle(bundle_id: str) -> None:
    IPRADIO_CURRENT_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    IPRADIO_CURRENT_KEY_PATH.write_text(json.dumps({"bundle_id": bundle_id}, indent=2) + "\n")


def list_key_bundles() -> list[dict]:
    return _load_index()["bundles"]


def get_current_bundle_id() -> str | None:
    if not IPRADIO_CURRENT_KEY_PATH.exists():
        return None
    current = json.loads(IPRADIO_CURRENT_KEY_PATH.read_text())
    return current.get("bundle_id")


def get_key_status() -> dict:
    bundles = list_key_bundles()
    gs_exists = WFB_GS_KEY_PATH.exists()
    drone_exists = WFB_DRONE_KEY_PATH.exists()

    return {
        "has_local_keys": gs_exists and drone_exists,
        "current_bundle_id": get_current_bundle_id(),
        "gs_key_path": str(WFB_GS_KEY_PATH),
        "drone_key_path": str(WFB_DRONE_KEY_PATH),
        "gs_key_sha256": _fingerprint_bytes(WFB_GS_KEY_PATH.read_bytes()) if gs_exists else None,
        "drone_key_sha256": _fingerprint_bytes(WFB_DRONE_KEY_PATH.read_bytes()) if drone_exists else None,
        "stored_bundle_count": len(bundles),
        "stored_bundles": bundles[:10],
    }


def install_key_bundle(bundle_id: str) -> dict:
    gs_key, drone_key = _read_bundle_bytes(bundle_id)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        gs_temp = temp_path / "gs.key"
        drone_temp = temp_path / "drone.key"
        gs_temp.write_bytes(gs_key)
        drone_temp.write_bytes(drone_key)

        subprocess.run(["/usr/bin/sudo", "/bin/cp", str(gs_temp), str(WFB_GS_KEY_PATH)], check=True)
        subprocess.run(["/usr/bin/sudo", "/bin/cp", str(drone_temp), str(WFB_DRONE_KEY_PATH)], check=True)
        subprocess.run(["/usr/bin/sudo", "/bin/chmod", "600", str(WFB_GS_KEY_PATH)], check=True)
        subprocess.run(["/usr/bin/sudo", "/bin/chmod", "600", str(WFB_DRONE_KEY_PATH)], check=True)
        subprocess.run(
            ["/usr/bin/sudo", "/bin/chown", f"{SERVICE_USER}:{SERVICE_USER}", str(WFB_GS_KEY_PATH), str(WFB_DRONE_KEY_PATH)],
            check=True,
        )

    _set_current_bundle(bundle_id)
    return {
        "status": "installed",
        "bundle_id": bundle_id,
        "gs_sha256": _fingerprint_bytes(gs_key),
        "drone_sha256": _fingerprint_bytes(drone_key),
    }


def generate_key_bundle() -> dict:
    bundle_id = f"bundle-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    metadata = _generate_bundle(bundle_id, source="generated_local", generated_here=True)

    return {
        "status": "generated",
        "warning": (
            "Generated a new local key bundle and replaced the active /etc/gs.key and /etc/drone.key files. "
            "Redistribute this bundle to every matching radio before expecting link compatibility."
        ),
        "bundle": metadata,
    }


def ensure_default_test_bundle() -> dict:
    if key_bundle_exists(DEFAULT_TEST_KEY_BUNDLE_ID):
        install = install_key_bundle(DEFAULT_TEST_KEY_BUNDLE_ID)
        metadata = json.loads(_metadata_path(DEFAULT_TEST_KEY_BUNDLE_ID).read_text())
        return {
            "status": "installed_existing_default_test_bundle",
            "warning": (
                "Installed the stored default test key bundle. Radios must share this same bundle to communicate."
            ),
            "bundle": metadata,
            "install": install,
        }

    metadata = _generate_bundle(
        DEFAULT_TEST_KEY_BUNDLE_ID,
        source="generated_default_test",
        generated_here=True,
    )
    return {
        "status": "generated_default_test_bundle",
        "warning": (
            "Generated and installed a local default test key bundle. Export this bundle and reuse it on other radios "
            "if you want them to join the same test network."
        ),
        "bundle": metadata,
    }


def set_default_test_bundle(bundle_id: str) -> dict:
    gs_key, drone_key = _read_bundle_bytes(bundle_id)
    metadata = _write_bundle(
        DEFAULT_TEST_KEY_BUNDLE_ID,
        gs_key,
        drone_key,
        source=f"default_test_alias:{bundle_id}",
        generated_here=False,
    )
    install = install_key_bundle(DEFAULT_TEST_KEY_BUNDLE_ID)
    return {
        "status": "set_default_test_bundle",
        "bundle": metadata,
        "install": install,
    }


def export_key_bundle(bundle_id: str) -> dict:
    gs_key, drone_key = _read_bundle_bytes(bundle_id)
    metadata = json.loads(_metadata_path(bundle_id).read_text())
    return {
        "bundle": metadata,
        "gs_key_b64": base64.b64encode(gs_key).decode("ascii"),
        "drone_key_b64": base64.b64encode(drone_key).decode("ascii"),
    }


def import_key_bundle(bundle_id: str, gs_key_b64: str, drone_key_b64: str, install: bool) -> dict:
    gs_key = base64.b64decode(gs_key_b64)
    drone_key = base64.b64decode(drone_key_b64)

    metadata = _write_bundle(bundle_id, gs_key, drone_key, source="imported_remote", generated_here=False)
    result = {
        "status": "imported",
        "bundle": metadata,
    }

    if install:
        result["install"] = install_key_bundle(bundle_id)

    return result

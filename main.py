from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app_config import (
    BABEL_SERVICE_NAME,
    CAMERA_SERVICE_NAME,
    DEFAULT_BANDWIDTH,
    DEFAULT_CAMERA_BITRATE,
    DEFAULT_CAMERA_FRAMERATE,
    DEFAULT_CAMERA_HEIGHT,
    DEFAULT_CAMERA_LENS_POSITION,
    DEFAULT_CAMERA_WIDTH,
    DEFAULT_FEC_K,
    DEFAULT_FEC_N,
    DEFAULT_MCS_INDEX,
    DEFAULT_TEST_KEY_BUNDLE_ID,
    DEFAULT_VIDEO_RX_TARGET,
    DHCP_SERVICE_NAME,
    NODE_ID_MAX,
    NODE_ID_MIN,
    format_eth0_address,
    format_eth0_subnet,
    format_fallback_eth0_address,
    format_hostname,
    format_loopback_address,
    format_profile_name,
)
from camera_service import get_camera_values, restart_camera, set_camera_values, start_camera, stop_camera
from hostname_service import set_node_hostname
from key_service import (
    ensure_default_test_bundle,
    export_key_bundle,
    generate_key_bundle,
    get_current_bundle_id,
    get_key_status,
    import_key_bundle,
    key_bundle_exists,
    set_default_test_bundle,
)
from provisioning_service import write_ipradio_node
from radio_service import (
    get_current_radio_settings,
    get_service_name,
    get_service_state,
    configure_routed_access,
    configure_eth0,
    restart_radio,
    sync_radio_services,
    update_base_value,
    update_tunnel_value,
)
from ui import UI_HTML

app = FastAPI()


class KeyBundleImportRequest(BaseModel):
    bundle_id: str
    gs_key_b64: str
    drone_key_b64: str
    install: bool = True


class DefaultTestBundleRequest(BaseModel):
    bundle_id: str


def validate_node_id(node_id: int):
    if node_id < NODE_ID_MIN or node_id > NODE_ID_MAX:
        return {"error": f"node_id must be between {NODE_ID_MIN} and {NODE_ID_MAX}"}
    return None


def validate_radio_settings(mcs_index: int, bandwidth: int, fec_k: int, fec_n: int):
    if mcs_index < 0 or mcs_index > 5:
        return {"error": "mcs_index must be between 0 and 5"}

    if bandwidth not in [20, 40]:
        return {"error": "bandwidth must be 20 or 40"}

    if fec_k < 1 or fec_k > 32:
        return {"error": "fec_k must be between 1 and 32"}

    if fec_n < 1 or fec_n > 64:
        return {"error": "fec_n must be between 1 and 64"}

    if fec_n < fec_k:
        return {"error": "fec_n must be greater than or equal to fec_k"}

    return None


def apply_radio_settings(mcs_index: int, bandwidth: int, fec_k: int, fec_n: int):
    update_base_value("mcs_index", mcs_index, "mcs index")
    update_base_value("bandwidth", bandwidth, "bandwidth")
    update_tunnel_value(
        "fec_k",
        fec_k,
        "fec_n",
        fec_n,
        "FEC K value",
        "FEC N value",
    )


@app.get("/")
def root():
    return {"message": "API is working"}


@app.get("/defaults")
def defaults():
    return {
        "radio": {
            "mcs_index": DEFAULT_MCS_INDEX,
            "bandwidth": DEFAULT_BANDWIDTH,
            "fec_k": DEFAULT_FEC_K,
            "fec_n": DEFAULT_FEC_N,
            "video_rx_target": DEFAULT_VIDEO_RX_TARGET,
        },
        "camera": {
            "width": DEFAULT_CAMERA_WIDTH,
            "height": DEFAULT_CAMERA_HEIGHT,
            "framerate": DEFAULT_CAMERA_FRAMERATE,
            "bitrate": DEFAULT_CAMERA_BITRATE,
            "lens_position": DEFAULT_CAMERA_LENS_POSITION,
        },
        "keys": {
            "default_test_bundle_id": DEFAULT_TEST_KEY_BUNDLE_ID,
            "default_test_bundle_present": key_bundle_exists(DEFAULT_TEST_KEY_BUNDLE_ID),
        },
    }


@app.get("/keys/status")
def key_status():
    return get_key_status()


@app.get("/keys/generate")
def key_generate():
    try:
        return generate_key_bundle()
    except FileNotFoundError as error:
        return {"error": f"missing file: {str(error)}"}
    except Exception as error:
        return {"error": str(error)}


@app.get("/keys/export/current")
def key_export_current():
    bundle_id = get_current_bundle_id()
    if not bundle_id:
        return {"error": "no active key bundle installed"}

    try:
        return export_key_bundle(bundle_id)
    except FileNotFoundError as error:
        return {"error": f"missing file: {str(error)}"}
    except Exception as error:
        return {"error": str(error)}


@app.get("/keys/export/{bundle_id}")
def key_export(bundle_id: str):
    try:
        return export_key_bundle(bundle_id)
    except FileNotFoundError as error:
        return {"error": f"missing file: {str(error)}"}
    except Exception as error:
        return {"error": str(error)}


@app.post("/keys/import")
def key_import(payload: KeyBundleImportRequest):
    try:
        return import_key_bundle(
            bundle_id=payload.bundle_id,
            gs_key_b64=payload.gs_key_b64,
            drone_key_b64=payload.drone_key_b64,
            install=payload.install,
        )
    except Exception as error:
        return {"error": str(error)}


@app.get("/keys/default_test/ensure")
def key_default_test_ensure():
    try:
        return ensure_default_test_bundle()
    except FileNotFoundError as error:
        return {"error": f"missing file: {str(error)}"}
    except Exception as error:
        return {"error": str(error)}


@app.post("/keys/default_test/set")
def key_default_test_set(payload: DefaultTestBundleRequest):
    try:
        return set_default_test_bundle(payload.bundle_id)
    except Exception as error:
        return {"error": str(error)}


@app.get("/status/{node_id}")
def status(node_id: int):
    radio_settings = get_current_radio_settings()
    camera_settings = get_camera_values()
    return {
        "node_id": node_id,
        "hostname": format_hostname(node_id),
        "eth0_address": format_eth0_address(node_id),
        "eth0_subnet": format_eth0_subnet(node_id),
        "fallback_address": format_fallback_eth0_address(),
        "loopback_address": format_loopback_address(node_id),
        "radio_service": get_service_state(get_service_name(node_id)),
        "dhcp_service": get_service_state(DHCP_SERVICE_NAME),
        "babel_service": get_service_state(BABEL_SERVICE_NAME),
        "camera_service": get_service_state(CAMERA_SERVICE_NAME),
        "key_bundle_id": get_current_bundle_id(),
        "current_radio": radio_settings,
        "current_camera": camera_settings,
    }


@app.get("/set_mcs/{node_id}/{value}")
def set_mcs(node_id: int, value: int):
    node_error = validate_node_id(node_id)
    if node_error:
        return node_error

    if value < 0 or value > 5:
        return {"error": "mcs_index must be between 0 and 5"}

    update_base_value("mcs_index", value, "mcs index")
    restart_radio(node_id)
    return {"node_id": node_id, "mcs_index": value}


@app.get("/set_bw/{node_id}/{value}")
def set_bw(node_id: int, value: int):
    node_error = validate_node_id(node_id)
    if node_error:
        return node_error

    if value not in [20, 40]:
        return {"error": "bandwidth must be 20 or 40"}

    update_base_value("bandwidth", value, "bandwidth")
    restart_radio(node_id)
    return {"node_id": node_id, "bandwidth": value}


@app.get("/set_fec/{node_id}/{value1}/{value2}")
def set_fec(node_id: int, value1: int, value2: int):
    node_error = validate_node_id(node_id)
    if node_error:
        return node_error

    if value1 < 1 or value1 > 32:
        return {"error": "fec_k must be between 1 and 32"}

    if value2 < 1 or value2 > 64:
        return {"error": "fec_n must be between 1 and 64"}

    if value2 < value1:
        return {"error": "fec_n must be greater than or equal to fec_k"}

    update_tunnel_value(
        "fec_k",
        value1,
        "fec_n",
        value2,
        "FEC K value",
        "FEC N value",
    )
    restart_radio(node_id)
    return {"node_id": node_id, "fec_k": value1, "fec_n": value2}


@app.get("/camera/apply")
def apply_camera(width: int, height: int, framerate: int, bitrate: int, lens_position: float):
    if width < 1 or height < 1:
        return {"error": "width and height must be positive"}

    if framerate < 1 or framerate > 120:
        return {"error": "framerate must be between 1 and 120"}

    if bitrate < 10000:
        return {"error": "bitrate must be at least 10000"}

    if lens_position < 0.0 or lens_position > 32.0:
        return {"error": "lens_position must be between 0.0 and 32.0"}

    set_camera_values(width, height, framerate, bitrate, lens_position)
    restart_camera()

    return {
        "WIDTH": width,
        "HEIGHT": height,
        "FRAMERATE": framerate,
        "BITRATE": bitrate,
        "LENS_POSITION": lens_position,
    }


@app.get("/camera/{command}")
def camera_control(command: str):
    command = command.upper()

    if command not in ["STOP", "START"]:
        return {"error": "invalid command"}

    if command == "STOP":
        stop_camera()
        return {"status": "stopped"}

    if command == "START":
        start_camera()
        return {"status": "started"}


@app.get("/ipradio/provision/{node_id}")
def ipradio_provision(node_id: int, peers: str, video_rx_target: str):
    node_error = validate_node_id(node_id)
    if node_error:
        return node_error

    try:
        peer_list = [int(x) for x in peers.split(",") if x.strip()]
    except ValueError:
        return {"error": "peers must be comma-separated integers"}

    if node_id in peer_list:
        return {"error": "node cannot peer with itself"}

    if len(peer_list) != len(set(peer_list)):
        return {"error": "duplicate peers are not allowed"}

    invalid_peers = [peer for peer in peer_list if peer < NODE_ID_MIN or peer > NODE_ID_MAX]
    if invalid_peers:
        return {"error": f"invalid peer ids: {invalid_peers}"}

    try:
        write_ipradio_node(node_id, peer_list, video_rx_target)
    except FileNotFoundError as error:
        return {"error": f"missing file: {str(error)}"}
    except Exception as error:
        return {"error": str(error)}

    sync_radio_services(node_id)
    set_node_hostname(node_id)
    configure_eth0(node_id)
    restart_radio(node_id)
    configure_routed_access(node_id)

    return {
        "status": "provisioned",
        "profile": format_profile_name(node_id),
        "node_id": node_id,
        "hostname": format_hostname(node_id),
        "eth0_address": format_eth0_address(node_id),
        "eth0_subnet": format_eth0_subnet(node_id),
        "fallback_address": format_fallback_eth0_address(),
        "loopback_address": format_loopback_address(node_id),
        "peers": peer_list,
        "video_rx_target": video_rx_target,
        "service_name": get_service_name(node_id),
    }


@app.get("/node/apply/{node_id}")
def apply_node_config(
    node_id: int,
    peers: str,
    video_rx_target: str,
    mcs_index: int,
    bandwidth: int,
    fec_k: int,
    fec_n: int,
):
    node_error = validate_node_id(node_id)
    if node_error:
        return node_error

    radio_error = validate_radio_settings(mcs_index, bandwidth, fec_k, fec_n)
    if radio_error:
        return radio_error

    try:
        peer_list = [int(x) for x in peers.split(",") if x.strip()]
    except ValueError:
        return {"error": "peers must be comma-separated integers"}

    if node_id in peer_list:
        return {"error": "node cannot peer with itself"}

    if len(peer_list) != len(set(peer_list)):
        return {"error": "duplicate peers are not allowed"}

    invalid_peers = [peer for peer in peer_list if peer < NODE_ID_MIN or peer > NODE_ID_MAX]
    if invalid_peers:
        return {"error": f"invalid peer ids: {invalid_peers}"}

    try:
        write_ipradio_node(node_id, peer_list, video_rx_target)
    except FileNotFoundError as error:
        return {"error": f"missing file: {str(error)}"}
    except Exception as error:
        return {"error": str(error)}

    apply_radio_settings(mcs_index, bandwidth, fec_k, fec_n)
    sync_radio_services(node_id)
    set_node_hostname(node_id)
    configure_eth0(node_id)
    restart_radio(node_id)
    configure_routed_access(node_id)

    return {
        "status": "applied",
        "profile": format_profile_name(node_id),
        "node_id": node_id,
        "hostname": format_hostname(node_id),
        "eth0_address": format_eth0_address(node_id),
        "eth0_subnet": format_eth0_subnet(node_id),
        "fallback_address": format_fallback_eth0_address(),
        "loopback_address": format_loopback_address(node_id),
        "peers": peer_list,
        "video_rx_target": video_rx_target,
        "mcs_index": mcs_index,
        "bandwidth": bandwidth,
        "fec_k": fec_k,
        "fec_n": fec_n,
        "service_name": get_service_name(node_id),
    }


@app.get("/ui", response_class=HTMLResponse)
def ui():
    return UI_HTML

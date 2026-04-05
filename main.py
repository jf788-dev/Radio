from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app_config import CAMERA_SERVICE_NAME, NODE_ID_MAX, NODE_ID_MIN, format_profile_name
from camera_service import restart_camera, set_camera_values, start_camera, stop_camera
from provisioning_service import write_ipradio_node
from radio_service import (
    get_service_name,
    get_service_state,
    restart_radio,
    sync_radio_services,
    update_base_value,
    update_tunnel_value,
)
from ui import UI_HTML

app = FastAPI()


@app.get("/")
def root():
    return {"message": "API is working"}


@app.get("/status/{node_id}")
def status(node_id: int):
    return {
        "node_id": node_id,
        "radio_service": get_service_state(get_service_name(node_id)),
        "camera_service": get_service_state(CAMERA_SERVICE_NAME),
    }


@app.get("/set_mcs/{node_id}/{value}")
def set_mcs(node_id: int, value: int):
    if node_id < NODE_ID_MIN or node_id > NODE_ID_MAX:
        return {"error": f"node_id must be between {NODE_ID_MIN} and {NODE_ID_MAX}"}

    if value < 0 or value > 5:
        return {"error": "mcs_index must be between 0 and 5"}

    update_base_value("mcs_index", value, "mcs index")
    restart_radio(node_id)
    return {"node_id": node_id, "mcs_index": value}


@app.get("/set_bw/{node_id}/{value}")
def set_bw(node_id: int, value: int):
    if node_id < NODE_ID_MIN or node_id > NODE_ID_MAX:
        return {"error": f"node_id must be between {NODE_ID_MIN} and {NODE_ID_MAX}"}

    if value not in [20, 40]:
        return {"error": "bandwidth must be 20 or 40"}

    update_base_value("bandwidth", value, "bandwidth")
    restart_radio(node_id)
    return {"node_id": node_id, "bandwidth": value}


@app.get("/set_fec/{node_id}/{value1}/{value2}")
def set_fec(node_id: int, value1: int, value2: int):
    if node_id < NODE_ID_MIN or node_id > NODE_ID_MAX:
        return {"error": f"node_id must be between {NODE_ID_MIN} and {NODE_ID_MAX}"}

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
    if node_id < NODE_ID_MIN or node_id > NODE_ID_MAX:
        return {"error": f"node_id must be between {NODE_ID_MIN} and {NODE_ID_MAX}"}

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
    restart_radio(node_id)

    return {
        "status": "provisioned",
        "profile": format_profile_name(node_id),
        "node_id": node_id,
        "peers": peer_list,
        "video_rx_target": video_rx_target,
        "service_name": get_service_name(node_id),
    }


@app.get("/ui", response_class=HTMLResponse)
def ui():
    return UI_HTML

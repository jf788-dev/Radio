from pathlib import Path

NODE_ID_MIN = 1
NODE_ID_MAX = 16
GROUND_STATION_NAME = "ground_station"

CONFIG_PATH = Path("/etc/wifibroadcast.cfg")
CAMERA_CONFIG_PATH = Path("/etc/default/wfb-camera")
HOSTNAME_PATH = Path("/etc/hostname")
HOSTS_PATH = Path("/etc/hosts")

IPRADIO_NODE_PATH = Path("/etc/ipradio/node.json")
IPRADIO_BASE_PATH = Path("/etc/ipradio/base.cfg")
IPRADIO_NODE_CFG_PATH = Path("/etc/ipradio/node.cfg")
IPRADIO_FINAL_CFG_PATH = CONFIG_PATH
IPRADIO_KEY_DIR = Path("/etc/ipradio/keys")
IPRADIO_KEY_INDEX_PATH = IPRADIO_KEY_DIR / "index.json"
IPRADIO_CURRENT_KEY_PATH = Path("/etc/ipradio/current_key.json")
WFB_GS_KEY_PATH = Path("/etc/gs.key")
WFB_DRONE_KEY_PATH = Path("/etc/drone.key")
WFB_KEYGEN_COMMAND = "/usr/bin/wfb_keygen"
BUNDLED_TEST_KEY_DIR = Path("config/keys/test-default")

WFB_API_HOST = "127.0.0.1"
WFB_API_PORT = 8102
WFB_STATS_PORT = 8002

MQTT_HOST = "localhost"
MQTT_PORT = 1883

CAMERA_SERVICE_NAME = "wfb-camera"
SERVICE_USER = "pi"
ETHERNET_INTERFACE = "eth0"
ETHERNET_SUBNET_PREFIX = "10.5.0"
ETHERNET_SERVICE_NAME = "wfb-eth0.service"
DEFAULT_MCS_INDEX = 1
DEFAULT_BANDWIDTH = 20
DEFAULT_FEC_K = 8
DEFAULT_FEC_N = 12
DEFAULT_VIDEO_RX_TARGET = "127.0.0.1:5600"
DEFAULT_CAMERA_WIDTH = 1280
DEFAULT_CAMERA_HEIGHT = 720
DEFAULT_CAMERA_FRAMERATE = 30
DEFAULT_CAMERA_BITRATE = 3000000
DEFAULT_CAMERA_LENS_POSITION = 0.0
DEFAULT_TEST_KEY_BUNDLE_ID = "test-default"


def format_node_name(node_id: int) -> str:
    return f"node{node_id:02d}"


def format_profile_name(node_id: int) -> str:
    return format_node_name(node_id)


def format_service_name(node_id: int) -> str:
    return f"wifibroadcast@{format_node_name(node_id)}"


def format_hostname(node_id: int) -> str:
    return format_node_name(node_id)


def format_eth0_address(node_id: int) -> str:
    return f"{ETHERNET_SUBNET_PREFIX}.{node_id}/24"

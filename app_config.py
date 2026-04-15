from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent

NODE_ID_MIN = 1
NODE_ID_MAX = 16
GROUND_STATION_NAME = "ground_station"

CONFIG_PATH = Path("/etc/wifibroadcast.cfg")
CAMERA_CONFIG_PATH = Path("/etc/default/wfb-camera")
HOSTNAME_PATH = Path("/etc/hostname")
HOSTS_PATH = Path("/etc/hosts")

IPRADIO_NODE_PATH = Path("/etc/ipradio/node.json")
IPRADIO_TARGET_PATH = Path("/etc/ipradio/node_prov.json")
IPRADIO_FINAL_CFG_PATH = CONFIG_PATH
IPRADIO_KEY_DIR = Path("/etc/ipradio/keys")
IPRADIO_KEY_INDEX_PATH = IPRADIO_KEY_DIR / "index.json"
IPRADIO_CURRENT_KEY_PATH = Path("/etc/ipradio/current_key.json")
IPRADIO_DHCP_CONFIG_PATH = Path("/etc/ipradio/dnsmasq.conf")
IPRADIO_BABEL_CONFIG_PATH = Path("/etc/ipradio/babeld.conf")
WFB_GS_KEY_PATH = Path("/etc/gs.key")
WFB_DRONE_KEY_PATH = Path("/etc/drone.key")
WFB_KEYGEN_COMMAND = "/usr/bin/wfb_keygen"
BUNDLED_BASE_CONFIG_PATH = APP_ROOT / "config/base.cfg"
BUNDLED_TEST_KEY_DIR = APP_ROOT / "config/keys/test-default"
CAMERA_DEFAULT_CONFIG_TEMPLATE_PATH = APP_ROOT / "config/wfb-camera.env"

WFB_API_HOST = "127.0.0.1"
WFB_API_PORT = 8102
WFB_STATS_PORT = 8002

MQTT_HOST = "localhost"
MQTT_PORT = 1883

CAMERA_SERVICE_NAME = "wfb-camera"
SERVICE_USER = "pi"
ETHERNET_INTERFACE = "eth0"
LOOPBACK_INTERFACE = "lo"
ETHERNET_ACCESS_PREFIX = "172.22"
ETHERNET_ACCESS_PREFIX_LEN = 24
ETHERNET_GATEWAY_HOST = 1
ETHERNET_DHCP_RANGE_START_HOST = 100
ETHERNET_DHCP_RANGE_END_HOST = 199
ETHERNET_FALLBACK_ADDRESS = "169.254.100.1/16"
LOOPBACK_SUBNET_PREFIX = "10.5.0"
ETHERNET_SERVICE_NAME = "wfb-eth0.service"
DHCP_SERVICE_NAME = "wfb-dhcp.service"
BABEL_SERVICE_NAME = "wfb-babel.service"
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
    return format_eth0_gateway(node_id)


def format_eth0_network(node_id: int) -> str:
    return f"{ETHERNET_ACCESS_PREFIX}.{node_id}.0"


def format_eth0_subnet(node_id: int) -> str:
    return f"{format_eth0_network(node_id)}/{ETHERNET_ACCESS_PREFIX_LEN}"


def format_eth0_gateway_ip(node_id: int) -> str:
    return f"{ETHERNET_ACCESS_PREFIX}.{node_id}.{ETHERNET_GATEWAY_HOST}"


def format_eth0_gateway(node_id: int) -> str:
    return f"{format_eth0_gateway_ip(node_id)}/{ETHERNET_ACCESS_PREFIX_LEN}"


def format_fallback_eth0_address() -> str:
    return ETHERNET_FALLBACK_ADDRESS


def format_dhcp_range_start(node_id: int) -> str:
    return f"{ETHERNET_ACCESS_PREFIX}.{node_id}.{ETHERNET_DHCP_RANGE_START_HOST}"


def format_dhcp_range_end(node_id: int) -> str:
    return f"{ETHERNET_ACCESS_PREFIX}.{node_id}.{ETHERNET_DHCP_RANGE_END_HOST}"


def format_loopback_ip(node_id: int) -> str:
    return f"{LOOPBACK_SUBNET_PREFIX}.{node_id}"


def format_loopback_address(node_id: int) -> str:
    return f"{format_loopback_ip(node_id)}/32"
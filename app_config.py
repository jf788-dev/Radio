from pathlib import Path

NODE_ID_MIN = 1
NODE_ID_MAX = 16
GROUND_STATION_NAME = "ground_station"

CONFIG_PATH = Path("/etc/wifibroadcast.cfg")
CAMERA_CONFIG_PATH = Path("/etc/default/wfb-camera")

IPRADIO_NODE_PATH = Path("/etc/ipradio/node.json")
IPRADIO_BASE_PATH = Path("/etc/ipradio/base.cfg")
IPRADIO_NODE_CFG_PATH = Path("/etc/ipradio/node.cfg")
IPRADIO_FINAL_CFG_PATH = CONFIG_PATH

WFB_API_HOST = "127.0.0.1"
WFB_API_PORT = 8102
WFB_STATS_PORT = 8002

MQTT_HOST = "localhost"
MQTT_PORT = 1883

CAMERA_SERVICE_NAME = "wfb-camera"
ETHERNET_INTERFACE = "eth0"
ETHERNET_SUBNET_PREFIX = "10.5.0"
ETHERNET_SERVICE_NAME = "wfb-eth0.service"


def format_node_name(node_id: int) -> str:
    return f"node_{node_id:02d}"


def format_profile_name(node_id: int) -> str:
    return format_node_name(node_id)


def format_service_name(node_id: int) -> str:
    return f"wifibroadcast@{format_node_name(node_id)}"


def format_eth0_address(node_id: int) -> str:
    return f"{ETHERNET_SUBNET_PREFIX}.{node_id}/24"

import json
from pathlib import Path

from app_config import (
    BUNDLED_BASE_CONFIG_PATH,
    IPRADIO_FINAL_CFG_PATH,
    IPRADIO_NODE_PATH,
    IPRADIO_TARGET_PATH,
    WFB_API_PORT,
    WFB_STATS_PORT,
    format_profile_name,
)


def tunnel_ifname(node_id: int, peer: int) -> str:
    return f"wfb{node_id:02d}{peer:02d}"


def tunnel_ifaddr(node_id: int, peer: int) -> str:
    low = min(node_id, peer)
    high = max(node_id, peer)
    host = 1 if node_id == low else 2
    return f"10.5.{low}.{high * 4 + host}/30"


def build_node_config(node_id: int, peers: list[int], video_rx_target: str) -> dict:
    return {
        "node_id": node_id,
        "links": peers,
        "video_rx_target": video_rx_target,
    }


def render_wfb_config(node: dict) -> str:
    node_id = int(node["node_id"])
    peers = [int(x) for x in node.get("links", [])]
    video_rx_target = node["video_rx_target"]

    stream_lines = [
        (
            f"{{'name': 'video{node_id:02d}tx', 'stream_rx': None, "
            f"'stream_tx': 0x{node_id - 1:02x}, 'service_type': 'udp_direct_tx', "
            f"'profiles': ['base', 'side_a', 'video', 'node_video_tx']}}"
        )
    ]

    for peer in peers:
        if peer == node_id:
            continue

        stream_lines.append(
            f"{{'name': 'video{peer:02d}rx', 'stream_rx': 0x{peer - 1:02x}, 'stream_tx': None, "
            f"'service_type': 'udp_direct_rx', 'profiles': ['base', 'side_b', 'video', 'node_video_rx']}}"
        )

        if node_id > peer:
            stream_tx = 0x20 + (node_id - 1)
            stream_rx = 0xA0 + (peer - 1)
            side = "side_a"
        else:
            stream_tx = 0xA0 + (node_id - 1)
            stream_rx = 0x20 + (peer - 1)
            side = "side_b"

        stream_lines.append(
            f"{{'name': 'tunnel{peer:02d}', 'stream_rx': 0x{stream_rx:02x}, 'stream_tx': 0x{stream_tx:02x}, "
            f"'service_type': 'tunnel', 'profiles': ['base', '{side}', 'tunnel', '{format_profile_name(node_id)}tunnel{peer:02d}']}}"
        )

    lines = [
        f"[{format_profile_name(node_id)}]",
        "streams = [",
    ]
    for index, stream in enumerate(stream_lines):
        suffix = "," if index < len(stream_lines) - 1 else ""
        lines.append(f"           {stream}{suffix}")
    lines.extend(
        [
            "           ]",
            "",
            f"stats_port = {WFB_STATS_PORT}",
            f"api_port = {WFB_API_PORT}",
            'link_domain = "default"',
            "",
            "[node_video_tx]",
            "peer = 'listen://0.0.0.0:5602'",
            "",
            "[node_video_rx]",
            f"peer = 'connect://{video_rx_target}'",
            "",
        ]
    )

    for peer in peers:
        if peer == node_id:
            continue
        lines.extend(
            [
                f"[{format_profile_name(node_id)}tunnel{peer:02d}]",
                "fwmark = 30",
                f"ifname = '{tunnel_ifname(node_id, peer)}'",
                f"ifaddr = '{tunnel_ifaddr(node_id, peer)}'",
                "default_route = False",
                "",
            ]
        )

    node_cfg = "\n".join(lines).rstrip() + "\n"
    return BUNDLED_BASE_CONFIG_PATH.read_text().rstrip() + "\n\n" + node_cfg


def load_node_config(path: Path) -> dict:
    return json.loads(path.read_text())


def write_node_json(node: dict, path: Path = IPRADIO_NODE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(node, indent=2) + "\n")


def write_final_wfb_config(node: dict, path: Path = IPRADIO_FINAL_CFG_PATH) -> None:
    path.write_text(render_wfb_config(node))


def write_current_node(node_id: int, peers: list[int], video_rx_target: str) -> dict:
    node = build_node_config(node_id, peers, video_rx_target)
    write_node_json(node)
    write_final_wfb_config(node)
    return node


def write_target_node(node_id: int, peers: list[int], video_rx_target: str) -> dict:
    node = build_node_config(node_id, peers, video_rx_target)
    write_node_json(node, path=IPRADIO_TARGET_PATH)
    return node

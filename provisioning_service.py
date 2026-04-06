import json

from app_config import (
    IPRADIO_BASE_PATH,
    format_dhcp_range_end,
    format_dhcp_range_start,
    format_eth0_gateway,
    format_eth0_gateway_ip,
    format_eth0_network,
    format_eth0_subnet,
    format_fallback_eth0_address,
    IPRADIO_FINAL_CFG_PATH,
    IPRADIO_NODE_CFG_PATH,
    IPRADIO_NODE_PATH,
    WFB_API_PORT,
    WFB_STATS_PORT,
    format_profile_name,
    format_loopback_address,
    format_loopback_ip,
)


def tunnel_ifname(node_id: int, peer: int) -> str:
    return f"wfb{node_id:02d}{peer:02d}"


def tunnel_ifaddr(node_id: int, peer: int) -> str:
    low = min(node_id, peer)
    high = max(node_id, peer)
    host = 1 if node_id == low else 2
    return f"10.5.{low}.{high * 4 + host}/30"


def generate_ipradio_cfg(node: dict) -> str:
    node_id = int(node["node_id"])
    peers = [int(x) for x in node.get("links", [])]
    video_rx_target = node["video_rx_target"]

    stream_lines = []

    stream_lines.append(
        f"{{'name': 'video{node_id:02d}tx', 'stream_rx': None, 'stream_tx': 0x{node_id - 1:02x}, "
        f"'service_type': 'udp_direct_tx', 'profiles': ['base', 'side_a', 'video', 'node_video_tx']}}"
    )

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

    lines = []

    lines.append(f"[{format_profile_name(node_id)}]")
    lines.append("streams = [")
    for i, stream in enumerate(stream_lines):
        suffix = "," if i < len(stream_lines) - 1 else ""
        lines.append(f"           {stream}{suffix}")
    lines.append("           ]")
    lines.append("")
    lines.append(f"stats_port = {WFB_STATS_PORT}")
    lines.append(f"api_port = {WFB_API_PORT}")
    lines.append('link_domain = "default"')
    lines.append("")

    lines.append("[node_video_tx]")
    lines.append("peer = 'listen://0.0.0.0:5602'")
    lines.append("")

    lines.append("[node_video_rx]")
    lines.append(f"peer = 'connect://{video_rx_target}'")
    lines.append("")

    for peer in peers:
        if peer == node_id:
            continue

        lines.append(f"[{format_profile_name(node_id)}tunnel{peer:02d}]")
        lines.append("fwmark = 30")
        lines.append(f"ifname = '{tunnel_ifname(node_id, peer)}'")
        lines.append(f"ifaddr = '{tunnel_ifaddr(node_id, peer)}'")
        lines.append("default_route = False")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_ipradio_node(node_id: int, peers: list[int], video_rx_target: str):
    node = {
        "node_id": node_id,
        "links": peers,
        "video_rx_target": video_rx_target,
        "eth0_gateway": format_eth0_gateway(node_id),
        "eth0_gateway_ip": format_eth0_gateway_ip(node_id),
        "eth0_network": format_eth0_network(node_id),
        "eth0_subnet": format_eth0_subnet(node_id),
        "fallback_address": format_fallback_eth0_address(),
        "dhcp_range_start": format_dhcp_range_start(node_id),
        "dhcp_range_end": format_dhcp_range_end(node_id),
        "loopback_address": format_loopback_address(node_id),
        "loopback_ip": format_loopback_ip(node_id),
    }

    IPRADIO_NODE_PATH.parent.mkdir(parents=True, exist_ok=True)
    IPRADIO_NODE_PATH.write_text(json.dumps(node, indent=2) + "\n")

    node_cfg = generate_ipradio_cfg(node)
    IPRADIO_NODE_CFG_PATH.write_text(node_cfg)
    IPRADIO_FINAL_CFG_PATH.write_text(IPRADIO_BASE_PATH.read_text().rstrip() + "\n\n" + node_cfg)

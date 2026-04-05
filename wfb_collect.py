import json
import socket
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from app_config import MQTT_HOST, MQTT_PORT, WFB_API_HOST, WFB_API_PORT, format_node_name

RADIO_NODE_ID = 3
NODE_NAME = format_node_name(RADIO_NODE_ID)

TOPIC_RF_CONFIG = f"visr/compute/rf_config/{NODE_NAME}"
TOPIC_RF_STREAMS = f"visr/compute/rf_streams/{NODE_NAME}"
TOPIC_RF_RX = f"visr/compute/rf_rx/{NODE_NAME}"
TOPIC_RF_TX = f"visr/compute/rf_tx/{NODE_NAME}"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def publish_json(client: mqtt.Client, topic: str, payload: dict) -> None:
    client.publish(topic, json.dumps(payload, separators=(",", ":")), qos=0, retain=False)


def parse_settings(msg: dict, client: mqtt.Client, node_name: str, node_num: int) -> None:
    settings = msg["settings"]
    profile = msg["profile"]
    interfaces = msg["wlans"]

    common = settings["common"]
    side_cfg = settings[profile]

    config_payload = {
        "ts": now_iso(),
        "node_id": node_name,
        "node_name": node_name,
        "node_num": node_num,
        "profile": profile,
        "interfaces": interfaces,
        "regulatory_region": common.get("wifi_region"),
        "frequency_channel": common.get("wifi_channel"),
        "tx_power": common.get("wifi_txpower"),
        "mtu": common.get("radio_mtu"),
        "stats_port": side_cfg.get("stats_port"),
        "api_port": side_cfg.get("api_port"),
        "link_domain": side_cfg.get("link_domain"),
        "version": common.get("version"),
        "commit": common.get("commit"),
    }

    publish_json(client, TOPIC_RF_CONFIG, config_payload)
    print(config_payload)

    streams = side_cfg["streams"]

    for stream in streams:
        name = stream["name"]
        rx_id = stream.get("stream_rx")
        tx_id = stream.get("stream_tx")
        service_type = stream["service_type"]
        fragment_names = stream.get("profiles", [])

        resolved = {}

        for fragment_name in fragment_names:
            fragment = settings.get(fragment_name, {})
            resolved.update(fragment)

        resolved.update(stream)

        stream_payload = {
            "ts": now_iso(),
            "node_id": node_name,
            "node_name": node_name,
            "node_num": node_num,
            "profile": profile,
            "stream_name": name,
            "rx_id": rx_id,
            "tx_id": tx_id,
            "service_type": service_type,
            "peer": resolved.get("peer"),
            "fwmark": resolved.get("fwmark"),
            "bandwidth": resolved.get("bandwidth"),
            "mcs_index": resolved.get("mcs_index"),
            "stbc": resolved.get("stbc"),
            "ldpc": resolved.get("ldpc"),
            "frame_type": resolved.get("frame_type"),
            "fec_k": resolved.get("fec_k"),
            "fec_n": resolved.get("fec_n"),
            "fec_timeout": resolved.get("fec_timeout"),
            "fec_delay": resolved.get("fec_delay"),
            "injection_retries": resolved.get("injection_retries"),
            "injection_retry_delay": resolved.get("injection_retry_delay"),
            "ifname": resolved.get("ifname"),
            "ifaddr": resolved.get("ifaddr"),
            "keypair": resolved.get("keypair"),
        }

        publish_json(client, TOPIC_RF_STREAMS, stream_payload)
        print(stream_payload)


def parse_rx(msg: dict, client: mqtt.Client, node_name: str, node_num: int) -> None:
    stream_id = msg["id"]
    packets = msg["packets"]

    packets_received_current = packets["all"][0]
    packets_received_total = packets["all"][1]
    packets_recovered_current = packets["fec_rec"][0]
    packets_recovered_total = packets["fec_rec"][1]
    packets_lost_current = packets["lost"][0]
    packets_lost_total = packets["lost"][1]

    ants = msg.get("rx_ant_stats", [])

    rf_by_chain = {}
    for a in ants:
        chain = a["ant"]
        rf_by_chain[chain] = {
            "snr_min": a["snr_min"],
            "snr_avg": a["snr_avg"],
            "snr_max": a["snr_max"],
            "rssi_min": a["rssi_min"],
            "rssi_avg": a["rssi_avg"],
            "rssi_max": a["rssi_max"],
            "freq": a.get("freq"),
            "mcs": a.get("mcs"),
            "bw": a.get("bw"),
            "pkt_recv": a.get("pkt_recv"),
        }

    if packets_received_total > 0:
        loss_pct = (packets_lost_total / packets_received_total) * 100
    else:
        loss_pct = 0.0

    rx_payload = {
        "ts": now_iso(),
        "node_id": node_name,
        "node_name": node_name,
        "node_num": node_num,
        "stream_id": stream_id,
        "packets_received_current": packets_received_current,
        "packets_received_total": packets_received_total,
        "packets_recovered_current": packets_recovered_current,
        "packets_recovered_total": packets_recovered_total,
        "packets_lost_current": packets_lost_current,
        "packets_lost_total": packets_lost_total,
        "loss_pct": round(loss_pct, 6),
        "snr_min_chain_0": rf_by_chain.get(0, {}).get("snr_min"),
        "snr_avg_chain_0": rf_by_chain.get(0, {}).get("snr_avg"),
        "snr_max_chain_0": rf_by_chain.get(0, {}).get("snr_max"),
        "rssi_min_chain_0": rf_by_chain.get(0, {}).get("rssi_min"),
        "rssi_avg_chain_0": rf_by_chain.get(0, {}).get("rssi_avg"),
        "rssi_max_chain_0": rf_by_chain.get(0, {}).get("rssi_max"),
        "snr_min_chain_1": rf_by_chain.get(1, {}).get("snr_min"),
        "snr_avg_chain_1": rf_by_chain.get(1, {}).get("snr_avg"),
        "snr_max_chain_1": rf_by_chain.get(1, {}).get("snr_max"),
        "rssi_min_chain_1": rf_by_chain.get(1, {}).get("rssi_min"),
        "rssi_avg_chain_1": rf_by_chain.get(1, {}).get("rssi_avg"),
        "rssi_max_chain_1": rf_by_chain.get(1, {}).get("rssi_max"),
        "freq_chain_0": rf_by_chain.get(0, {}).get("freq"),
        "freq_chain_1": rf_by_chain.get(1, {}).get("freq"),
        "mcs_chain_0": rf_by_chain.get(0, {}).get("mcs"),
        "mcs_chain_1": rf_by_chain.get(1, {}).get("mcs"),
        "bw_chain_0": rf_by_chain.get(0, {}).get("bw"),
        "bw_chain_1": rf_by_chain.get(1, {}).get("bw"),
        "pkt_recv_chain_0": rf_by_chain.get(0, {}).get("pkt_recv"),
        "pkt_recv_chain_1": rf_by_chain.get(1, {}).get("pkt_recv"),
    }

    publish_json(client, TOPIC_RF_RX, rx_payload)
    print(rx_payload)


def parse_tx(msg: dict, client: mqtt.Client, node_name: str, node_num: int) -> None:
    stream_id = msg["id"]
    packets = msg["packets"]

    packets_incoming = packets["incoming"][0]
    packets_incoming_total = packets["incoming"][1]
    bytes_incoming = packets["incoming_bytes"][0]
    bytes_incoming_total = packets["incoming_bytes"][1]

    packets_injected = packets["injected"][0]
    packets_injected_total = packets["injected"][1]
    bytes_injected = packets["injected_bytes"][0]
    bytes_injected_total = packets["injected_bytes"][1]

    packets_dropped = packets["dropped"][0]
    packets_dropped_total = packets["dropped"][1]
    packets_truncated = packets["truncated"][0]
    packets_truncated_total = packets["truncated"][1]
    fec_timeouts = packets["fec_timeouts"][0]
    fec_timeouts_total = packets["fec_timeouts"][1]

    tx_paths = msg.get("tx_ant_stats", [])
    tx_rf = {}

    for path in tx_paths:
        chain = path["ant"]
        tx_rf[chain] = {
            "pkt_sent": path["pkt_sent"],
            "pkt_drop": path["pkt_drop"],
            "lat_min": path["lat_min"],
            "lat_avg": path["lat_avg"],
            "lat_max": path["lat_max"],
        }

    if tx_paths:
        tx_latency_avg = sum(path["lat_avg"] for path in tx_paths) / len(tx_paths)
    else:
        tx_latency_avg = None

    if packets_injected_total > 0:
        tx_drop_pct = (packets_dropped_total / packets_injected_total) * 100
    else:
        tx_drop_pct = 0.0

    tx_payload = {
        "ts": now_iso(),
        "node_id": node_name,
        "node_name": node_name,
        "node_num": node_num,
        "stream_id": stream_id,
        "packets_incoming": packets_incoming,
        "packets_incoming_total": packets_incoming_total,
        "bytes_incoming": bytes_incoming,
        "bytes_incoming_total": bytes_incoming_total,
        "packets_injected": packets_injected,
        "packets_injected_total": packets_injected_total,
        "bytes_injected": bytes_injected,
        "bytes_injected_total": bytes_injected_total,
        "packets_dropped": packets_dropped,
        "packets_dropped_total": packets_dropped_total,
        "packets_truncated": packets_truncated,
        "packets_truncated_total": packets_truncated_total,
        "fec_timeouts": fec_timeouts,
        "fec_timeouts_total": fec_timeouts_total,
        "tx_drop_pct": round(tx_drop_pct, 6),
        "tx_latency_avg": tx_latency_avg,
        "tx_pkt_sent_chain_255": tx_rf.get(255, {}).get("pkt_sent"),
        "tx_pkt_drop_chain_255": tx_rf.get(255, {}).get("pkt_drop"),
        "tx_lat_min_chain_255": tx_rf.get(255, {}).get("lat_min"),
        "tx_lat_avg_chain_255": tx_rf.get(255, {}).get("lat_avg"),
        "tx_lat_max_chain_255": tx_rf.get(255, {}).get("lat_max"),
    }

    publish_json(client, TOPIC_RF_TX, tx_payload)
    print(tx_payload)


def main() -> None:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()

    with socket.create_connection((WFB_API_HOST, WFB_API_PORT)) as sock:
        print("Connected to WFB API")
        with sock.makefile("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    msg = json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    continue

                msg_type = msg.get("type")
                print(msg_type)

                if msg_type == "settings":
                    parse_settings(msg, client, NODE_NAME, RADIO_NODE_ID)
                elif msg_type == "rx":
                    parse_rx(msg, client, NODE_NAME, RADIO_NODE_ID)
                elif msg_type == "tx":
                    parse_tx(msg, client, NODE_NAME, RADIO_NODE_ID)


if __name__ == "__main__":
    main()

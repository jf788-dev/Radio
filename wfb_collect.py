import socket
import json
import paho.mqtt.client as mqtt
from datetime import datetime, timezone

HOST = "127.0.0.1"
PORT = 8103
node_id = "ground_station"

MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883
TOPIC = f"visr/compute/rf/{node_id}"


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="wfb-mvp-writer")
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=30)
    client.loop_start()

    sock = socket.create_connection((HOST, PORT))
    f = sock.makefile("r")

    print("Connected to WFB API")
    print(f"Publishing to MQTT topic: {TOPIC}")

    try:
        for line in f:
            msg = json.loads(line)

            if msg.get("type") != "rx":
                continue

            stream_id = msg["id"]
            lost = msg["packets"]["lost"][0]
            total = msg["packets"]["all"][0]
            out = msg["packets"]["out_bytes"][0]

            ants = msg["rx_ant_stats"]

            if ants:
                snr = sum(a["snr_avg"] for a in ants) / len(ants)
                rssi = sum(a["rssi_avg"] for a in ants) / len(ants)
            else:
                snr = 0
                rssi = 0

            if total > 0:
                loss_pct = (lost / total) * 100
            else:
                loss_pct = 0

            payload = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "node_id": node_id,
                "stream_id": stream_id,
                "loss": lost,
                "loss_pct": loss_pct,
                "out_bytes": out,
                "snr": snr,
                "rssi": rssi,
            }

            client.publish(TOPIC, json.dumps(payload, separators=(",", ":")), qos=0, retain=False)
            print(payload)

    except KeyboardInterrupt:
        print("\nStopped.")

    finally:
        try:
            f.close()
            sock.close()
        except Exception:
            pass
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
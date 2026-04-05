import json
import time
from datetime import datetime, timezone

import serial
from pynmeagps import NMEAReader
import paho.mqtt.client as mqtt

from app_config import GROUND_STATION_NAME, MQTT_HOST, MQTT_PORT


def iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_str(x):
    return None if x is None or x == "" else str(x)


def main():
    # ---------- CONFIG ----------
    SERIAL_PORT = "/dev/ttyUSB0"
    BAUD = 38400
    node_name = GROUND_STATION_NAME
    TOPIC = f"visr/sensors/gps/{node_name}"

    PUBLISH_HZ = 1.0            # publish cadence to MQTT
    CLIENT_ID = "telegraf-visr-gps"
    # ---------------------------

    # MQTT setup
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID)
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=30)
    client.loop_start()

    # Serial setup
    ser = serial.Serial(SERIAL_PORT, BAUD, timeout=1)
    nmr = NMEAReader(ser)

    # Unified state (gets filled in as sentences arrive)
    state = {
        # meta
        "talker_last": None,
        "sentence_last": None,

        # time (from RMC preferably)
        "rmc_date": None,       # "YYYY-MM-DD"
        "rmc_time": None,       # "HH:MM:SS[.sss]"
        "rmc_status": None,     # "A" valid, "V" void
        "pos_mode": None,       # often "A"/"D"/etc depending on receiver

        # position
        "lat": None,
        "lon": None,
        "alt_m": None,

        # motion
        "speed_kn": None,
        "speed_mps": None,
        "course_deg": None,

        # quality (from GGA)
        "fix_quality": None,    # 0 invalid, 1 gps, 2 dgps, 4 rtk fixed, 5 rtk float...
        "sats_used": None,
        "hdop": None,
    }

    last_pub = 0.0
    period = 1.0 / PUBLISH_HZ

    try:
        while True:
            raw, msg = nmr.read()
            if not msg:
                # even if no new sentences, still publish at 1 Hz so consumers see "alive"
                pass
            else:
                # These attributes exist in pynmeagps message objects
                state["talker_last"] = getattr(msg, "talker", state["talker_last"])
                state["sentence_last"] = getattr(msg, "msgID", state["sentence_last"])

                # ---- RMC: time/date/validity + lat/lon + speed/course ----
                if msg.msgID == "RMC":
                    state["rmc_status"] = getattr(msg, "status", None)  # A/V
                    state["pos_mode"] = getattr(msg, "posMode", None)   # often A/D/E etc

                    # RMC date/time objects -> stringify safely
                    state["rmc_date"] = safe_str(getattr(msg, "date", None))
                    state["rmc_time"] = safe_str(getattr(msg, "time", None))

                    # lat/lon (may still appear even when status=V depending on device;
                    # we keep them but you can gate downstream using rmc_status)
                    state["lat"] = getattr(msg, "lat", state["lat"])
                    state["lon"] = getattr(msg, "lon", state["lon"])

                    spd = getattr(msg, "spd", None)  # knots
                    crs = getattr(msg, "cog", None)  # degrees (may be empty)
                    state["speed_kn"] = spd
                    state["speed_mps"] = (spd * 0.514444) if isinstance(spd, (int, float)) else None
                    state["course_deg"] = crs if crs not in ("", None) else None

                # ---- GGA: fix quality + altitude + sats + hdop (+ lat/lon) ----
                elif msg.msgID == "GGA":
                    state["lat"] = getattr(msg, "lat", state["lat"])
                    state["lon"] = getattr(msg, "lon", state["lon"])
                    state["alt_m"] = getattr(msg, "alt", state["alt_m"])

                    state["fix_quality"] = getattr(msg, "quality", state["fix_quality"])
                    state["sats_used"] = getattr(msg, "numSV", state["sats_used"])
                    state["hdop"] = getattr(msg, "HDOP", state["hdop"])

            # ---- Publish at fixed rate (always) ----
            now = time.monotonic()
            if now - last_pub >= period:
                last_pub = now

                payload = {
                    "ts": iso_utc_now(),
                    "node_id": node_name,
                    "node_name": node_name,
                    "sensor_id": 1,          # ingest timestamp
                    **state,

                    # Helpful derived flags for consumers:
                    "has_fix_gga": (state["fix_quality"] is not None and state["fix_quality"] > 0),
                    "has_fix_rmc": (state["rmc_status"] == "A"),
                }

                client.publish(TOPIC, json.dumps(payload, separators=(",", ":")), qos=0, retain=False)

    finally:
        try:
            ser.close()
        except Exception:
            pass
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()

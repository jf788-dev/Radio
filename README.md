# Radio

Repo for monitoring, control, and provisioning around a WFB-ng radio link for testing and visualisation workflows.

## Repo Readiness

This repo is intended to hold:

- application code
- Docker-based observability config
- checked-in deployment artifacts such as systemd unit files

Host-specific runtime files such as `/etc/wifibroadcast.cfg`, `/etc/default/wfb-camera`, and generated `/etc/ipradio/*` files are not stored in the repo.

## Current Layout

### `app_config.py`
Central place for shared configuration.

- Defines node ID bounds.
- Defines shared node naming helpers such as `node03` and `wifibroadcast@node03`.
- Defines file paths for the live WFB config, camera config, and IPRadio provisioning files.
- Defines shared port values for the WFB API, WFB stats, and MQTT.
- Defines the recommended default radio and camera settings used by the UI and API.
- Keeps the collector and provisioning code aligned on the same port values.

### `radio_service.py`
Radio control and radio config mutation helpers.

- Builds the `wifibroadcast@nodeXX` service name for a node.
- Updates values in the `[base]` section of `/etc/wifibroadcast.cfg`.
- Updates FEC values in the `[tunnel]` section of `/etc/wifibroadcast.cfg`.
- Restarts the radio service after config changes.
- Reads the current `systemctl is-active` state for a service.

This file owns the direct interaction with radio-related systemd services and the live WFB config file.

### `camera_service.py`
Camera configuration and service control helpers.

- Updates `/etc/default/wfb-camera`.
- Writes `WIDTH`, `HEIGHT`, `FRAMERATE`, `BITRATE`, and `LENS_POSITION`.
- Starts, stops, and restarts the `wfb-camera` service.

This keeps the camera-specific logic separate from the radio and provisioning code.

### `provisioning_service.py`
Provisioning logic for node-specific IPRadio / WFB configuration.

- Generates tunnel interface names and addresses.
- Builds a node-specific config block based on node ID, peers, and video target.
- Uses the shared `nodeXX` naming convention for generated profiles and tunnel sections.
- Injects shared `api_port` and `stats_port` values from `app_config.py`.
- Writes:
  - `/etc/ipradio/node.json`
  - `/etc/ipradio/node.cfg`
  - `/etc/wifibroadcast.cfg` from `base.cfg + node.cfg`

This file owns config generation for test provisioning workflows.

### `key_service.py`
Key bundle lifecycle helpers for WFB encryption material.

- Runs `wfb_keygen` in a temporary directory so bundle generation does not clobber live `/etc/*.key` files during creation
- Stores generated or imported bundles under `/etc/ipradio/keys/<bundle_id>/`
- Installs active keys to `/etc/gs.key` and `/etc/drone.key`
- Tracks the active bundle in `/etc/ipradio/current_key.json`
- Returns SHA-256 fingerprints for normal status calls and only returns plaintext key material from explicit export endpoints

### `ui.py`
Holds the browser UI as a static HTML string.

- Contains the current control page for radio, camera, and provisioning actions.
- Keeps the large inline HTML/JS payload out of the API logic.

If the UI grows, this is the natural place to replace with templates or separate static files later.

### `wfb_collect.py`
Telemetry collector that listens to the WFB API and republishes structured data over MQTT.

- Connects to the WFB API using `WFB_API_HOST` and `WFB_API_PORT` from `app_config.py`.
- Connects to MQTT using `MQTT_HOST` and `MQTT_PORT`.
- Parses `settings`, `rx`, and `tx` messages from WFB.
- Publishes structured RF config, stream, RX, and TX telemetry topics for downstream ingestion using a canonical `node_name`.

This is the bridge between the radio runtime and the observability stack.

### `docker-compose.yaml`
Local monitoring and data services used around the radio stack.

- Mosquitto for MQTT.
- Telegraf for ingest/forwarding.
- Grafana for dashboards.
- Postgres / Timescale for storage.
- PostgREST, Adminer, and MinIO for supporting access and storage workflows.

### `systemd/wfb-api.service`
Systemd unit for running the FastAPI control service on the Pi.

- Runs `uvicorn main:app`
- Binds the HTTP API on port `8000`
- Assumes the app is deployed at `/opt/visr`
- Assumes a virtual environment exists at `/opt/visr/venv`

### `systemd/wfb-collect.service`
Systemd unit for running the WFB telemetry collector on the Pi.

- Runs `wfb_collect.py`
- Assumes the app is deployed at `/opt/visr`
- Assumes a virtual environment exists at `/opt/visr/venv`
- Waits briefly before startup so dependent services can settle

### `systemd/wfb-observability.service`
Systemd unit for bringing up the Docker Compose observability stack on boot.

- Runs `docker compose up -d` for `/opt/visr/docker-compose.yaml`
- Starts after Docker and network are available
- Keeps the MQTT, database, and dashboard stack aligned with the radio app boot flow

### `systemd/wfb-camera.service`
Systemd unit for running the camera RTP feed on the drone node.

- Runs `scripts/wfb-camera.sh`
- Restarts automatically if the camera feed exits
- Assumes the app is deployed at `/opt/visr`
- Assumes `/etc/default/wfb-camera` exists on the host

### `systemd/wfb-eth0.service`
Systemd unit for maintaining the management addresses on `eth0`.

- Runs `scripts/wfb-eth0.sh`
- Reads `/etc/ipradio/node.json`
- Applies `10.5.0.<node_id>/24` to `eth0`
- Applies the fixed fallback management address `169.254.100.1/24` to `eth0`
- Uses `ip address replace` so both managed addresses stay present without flushing unrelated `eth0` addresses
- Starts on boot and restarts automatically if the keeper exits

### `scripts/wfb-camera.sh`
Repo-managed camera launch script used by `wfb-camera.service`.

- Sources `/etc/default/wfb-camera`
- Launches `rpicam-vid`
- Streams H.264 video to `udp://127.0.0.1:5602`

### `scripts/wfb-eth0.sh`
Repo-managed helper script used by `wfb-eth0.service`.

- Reads the provisioned node ID from `/etc/ipradio/node.json`
- Adds the deterministic `10.5.0.<node_id>/24` address to `eth0`
- Adds the fixed fallback management address `169.254.100.1/24` to `eth0`
- Monitors `eth0` and reapplies both addresses if the interface changes

## Provisioning Process

Provisioning starts through the FastAPI route in `main.py`:

- `GET /ipradio/provision/{node_id}?peers=...&video_rx_target=...`

That route:

- validates the numeric `node_id`
- parses and validates peer node IDs
- calls `write_ipradio_node()` in `provisioning_service.py`
- restarts the matching radio service after the files are written

`write_ipradio_node()` produces three outputs:

- `/etc/ipradio/node.json`
  Persisted input data for the selected node, peers, and video target.
- `/etc/ipradio/node.cfg`
  Generated node-specific config derived from the selected topology.
- `/etc/wifibroadcast.cfg`
  Final live config built from `base.cfg + node.cfg`.

The generated config includes:

- the profile name such as `node03`
- video TX and RX stream definitions
- tunnel stream definitions for each peer
- tunnel interface names and `/30` addresses
- shared `stats_port` and `api_port` values from `app_config.py`

After provisioning, the app:

- enables the selected radio systemd instance such as `wifibroadcast@node03`
- disables other `wifibroadcast@nodeXX` instances
- disables the legacy `wifibroadcast@gs` instance
- enables and restarts `wfb-eth0.service` so the deterministic `eth0` address is applied persistently
- restarts the selected radio service

## Key Workflow

- Generate a new key bundle on a Pi through `/keys/generate`
- Ensure a named reusable local test bundle through `/keys/default_test/ensure`
- The Pi runs `wfb_keygen` locally in a temporary directory
- The generated `gs.key` and `drone.key` files are stored under `/etc/ipradio/keys/<bundle_id>/`
- The active bundle is installed to:
  - `/etc/gs.key`
  - `/etc/drone.key`
- The normal status route `/keys/status` reports fingerprints and metadata, not plaintext key contents
- The export routes `/keys/export/current` and `/keys/export/{bundle_id}` return base64-encoded key material for EUD pickup and redistribution
- The import route `/keys/import` accepts a stored bundle from an EUD and can install it immediately

This keeps key generation on the radio/Pi while still allowing an external EUD to collect and redistribute the active bundle to other radios.

## Recommended Defaults

The shared defaults exposed by `/defaults` and loaded by the UI are:

- bandwidth: `20`
- mcs_index: `1`
- fec_k / fec_n: `8 / 12`
- video_rx_target: `127.0.0.1:5600`
- camera profile: `1280x720 @ 30 fps` with `3000000` bitrate and `0.0` lens position

The named default test key bundle is `test-default`. If it does not exist on a Pi yet, `/keys/default_test/ensure` generates it locally and installs it.

## Base Config

The app provisioning flow uses a repo-managed baseline WFB config template at `config/base.cfg`.

- bootstrap installs it to `/etc/ipradio/base.cfg` if that file is missing
- bootstrap seeds `/etc/wifibroadcast.cfg` from `/etc/ipradio/base.cfg` if the live file is missing
- provisioning then writes the final live config as:
  - `/etc/wifibroadcast.cfg = /etc/ipradio/base.cfg + /etc/ipradio/node.cfg`

This keeps the baseline config internal to the install flow so a fresh Pi does not require manual creation of `/etc/ipradio/base.cfg`.

## Data Flows

### 1. Control Flow

- The browser UI in `ui.py` calls FastAPI routes in `main.py`.
- `main.py` validates input and delegates work to:
  - `radio_service.py`
  - `camera_service.py`
  - `provisioning_service.py`
- Those service modules update config files and restart the relevant systemd units.

### 2. RF Telemetry Flow

- `wfb_collect.py` connects to the WFB API socket using `WFB_API_HOST` and `WFB_API_PORT`.
- It reads `settings`, `rx`, and `tx` messages from WFB.
- It publishes JSON telemetry to MQTT topics shaped like:
  - `visr/compute/rf_config/<node_name>`
  - `visr/compute/rf_streams/<node_name>`
  - `visr/compute/rf_rx/<node_name>`
  - `visr/compute/rf_tx/<node_name>`

### 3. GPS Telemetry Flow

- `gps_collect.py` reads NMEA data from `/dev/ttyUSB0`.
- It maintains a rolling GPS state from incoming `RMC` and `GGA` sentences.
- It publishes JSON telemetry to:
  - `visr/sensors/gps/ground_station`

### 4. MQTT to Storage Flow

- Mosquitto receives MQTT messages from the collectors.
- Telegraf subscribes to:
  - `visr/sensors/+/+`
  - `visr/compute/+/+`
- Telegraf parses topic segments into:
  - measurement name
  - `node_id` tag
- Telegraf writes the resulting metrics into PostgreSQL.
- Grafana reads from PostgreSQL for dashboards and visualisation.

### 5. Naming Through the Stack

- Control and provisioning use numeric `node_id`, for example `3`.
- Telemetry topics use canonical `node_name`, for example `node03`.
- Provisioned WFB profiles also use `node_name`.
- Radio systemd services derive from `node_name`, for example `wifibroadcast@node03`.

## Intended Split

The current codebase is moving toward this separation of concerns:

- API layer: thin FastAPI routes that validate input and call services.
- service layer: radio, camera, and provisioning logic in small Python modules.
- UI layer: browser-facing control page kept separate from backend logic.
- telemetry layer: `wfb_collect.py` for publishing radio state into MQTT.

This split is about keeping the Python code easier to test and change. It does not imply separate systemd services for each Python module.

## Naming Convention

The repo now uses two related identifiers:

- `node_id`: numeric control/provisioning ID used by the API and radio provisioning.
- `node_name`: canonical string identity used in MQTT topics and telemetry payloads.

Examples:

- `node_id = 3`
- `node_name = "node03"`
- `profile = "node03"`
- `service_name = "wifibroadcast@node03"`

For non-radio publishers such as GPS, the canonical telemetry identity is a descriptive `node_name`, currently `ground_station`.

## Local Setup

Create a virtual environment and install Python dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run the FastAPI app locally:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Bring up the observability stack:

```bash
docker compose up -d
```

## Raspberry Pi Deployment

Expected deployment layout after bootstrap:

- app installed at `/opt/visr`
- virtual environment at `/opt/visr/venv`
- FastAPI served by systemd using `systemd/wfb-api.service`
- WFB collector served by systemd using `systemd/wfb-collect.service`
- Camera feed available through `systemd/wfb-camera.service`
- Deterministic `eth0` address managed by `systemd/wfb-eth0.service`

Full Pi bootstrap from a staged checkout:

```bash
sudo apt update
sudo apt install -y git
git clone <your-private-repo-url> ~/wfb_collect
cd ~/wfb_collect
sudo ./scripts/bootstrap-radio.sh
```

This full bootstrap script:

- updates the host packages
- installs Docker if missing
- verifies `docker compose` is available
- installs the RTL8812AU DKMS driver from `svpcom/rtl8812au`
- adds the `wfb-ng` apt repository and installs `wfb-ng`
- installs camera and media packages
- configures `NetworkManager` and `dhcpcd` so `wlan1` is unmanaged
- installs the VISR app and systemd units
- reboots once at the very end so the Wi-Fi driver, Docker stack, and services start cleanly

Docker and Docker Compose are needed for the observability stack in `docker-compose.yaml`.
The core radio control app can run without that stack, but Grafana, Mosquitto, Postgres, and related services will not come up without Docker and `docker compose`.

App-only bootstrap:

```bash
sudo ./scripts/install-visr.sh
```

The bootstrap script:

- copies the staged checkout into `/opt/visr`
- creates `/opt/visr/venv` if it does not exist yet
- installs Python dependencies from `requirements.txt`
- creates `/etc/ipradio` and `/etc/ipradio/keys`
- installs `/etc/ipradio/base.cfg` from `config/base.cfg` if it is missing
- seeds `/etc/wifibroadcast.cfg` from that base template if the live config is missing
- installs the systemd unit files
- enables and starts:
  - `wfb-api.service`
  - `wfb-collect.service`
  - `wfb-eth0.service`
  - `wfb-observability.service`
- installs but does not enable `wfb-camera.service`

Host-only bootstrap:

```bash
sudo ./scripts/build-radio-host.sh
```

Check service status:

```bash
sudo systemctl status wfb-api.service
sudo systemctl status wfb-collect.service
sudo systemctl status wfb-camera.service
sudo systemctl status wfb-eth0.service
```

View logs:

```bash
journalctl -u wfb-api.service -f
journalctl -u wfb-collect.service -f
journalctl -u wfb-camera.service -f
journalctl -u wfb-eth0.service -f
```

## What Lives Where

Repo-managed:

- Python application code
- Docker Compose file
- Telegraf, Mosquitto, and Grafana config under `config/`
- systemd service definitions under `systemd/`
- dependency list in `requirements.txt`

Host-managed:

- `/etc/wifibroadcast.cfg`
- `/etc/default/wfb-camera`
- `/etc/ipradio/base.cfg`
- `/etc/ipradio/node.json`
- `/etc/ipradio/node.cfg`
- `/etc/default/wfb-camera`
- any installed systemd units under `/etc/systemd/system/`

## Node Cleanup Before Deploy

If you want to replace the old deployment entirely, remove the old units before enabling the new ones:

```bash
sudo systemctl disable --now wfb-api.service wfb-collect.service wfb-camera.service
sudo rm -f /etc/systemd/system/wfb-api.service
sudo rm -f /etc/systemd/system/wfb-collect.service
sudo rm -f /etc/systemd/system/wfb-camera.service
sudo systemctl daemon-reload
```

Back up the live runtime config before first use of the new app:

```bash
sudo cp /etc/wifibroadcast.cfg /etc/wifibroadcast.cfg.bak
sudo cp /etc/default/wfb-camera /etc/default/wfb-camera.bak
sudo cp /etc/ipradio/base.cfg /etc/ipradio/base.cfg.bak
sudo cp /etc/ipradio/node.json /etc/ipradio/node.json.bak 2>/dev/null || true
sudo cp /etc/ipradio/node.cfg /etc/ipradio/node.cfg.bak 2>/dev/null || true
```

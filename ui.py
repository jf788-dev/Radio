UI_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>WFB Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        :root {
            --bg: #091017;
            --bg-panel: rgba(10, 19, 29, 0.92);
            --bg-panel-strong: rgba(14, 26, 39, 0.98);
            --line: rgba(120, 160, 190, 0.22);
            --line-strong: rgba(151, 198, 231, 0.4);
            --text: #e7f2fb;
            --muted: #90a8bb;
            --accent: #73d6ff;
            --accent-strong: #2af5c9;
            --danger: #ff8577;
            --shadow: 0 18px 40px rgba(0, 0, 0, 0.35);
        }
        body {
            font-family: "Segoe UI", "Arial Narrow", Arial, sans-serif;
            max-width: 1120px;
            margin: 0 auto;
            padding: 28px 20px 40px;
            background:
                radial-gradient(circle at top, rgba(42, 245, 201, 0.08), transparent 28%),
                linear-gradient(180deg, #0b121a 0%, #070d13 100%);
            color: var(--text);
            min-height: 100vh;
        }
        h1 {
            margin: 0 0 8px;
            font-size: 40px;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            text-align: center;
        }
        .intro {
            color: var(--muted);
            margin: 0 auto 28px;
            max-width: 760px;
            text-align: center;
            line-height: 1.5;
        }
        .card {
            background: var(--bg-panel);
            padding: 20px;
            margin-bottom: 16px;
            border-radius: 18px;
            box-shadow: var(--shadow);
            border: 1px solid var(--line);
            backdrop-filter: blur(12px);
            text-align: center;
        }
        h2 {
            margin: 0 0 10px;
            font-size: 24px;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }
        label {
            display: block;
            margin-top: 14px;
            margin-bottom: 6px;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            font-size: 12px;
            color: var(--muted);
        }
        input, select, button {
            padding: 12px 14px;
            margin: 4px 0 8px 0;
            font-size: 14px;
            border-radius: 12px;
            border: 1px solid var(--line);
        }
        input, select {
            background: rgba(4, 10, 16, 0.92);
            color: var(--text);
            width: min(100%, 340px);
            box-sizing: border-box;
            text-align: center;
        }
        button {
            cursor: pointer;
            margin-right: 8px;
            background: linear-gradient(180deg, rgba(49, 81, 110, 0.95), rgba(18, 36, 53, 0.95));
            color: var(--text);
            border-color: rgba(115, 214, 255, 0.2);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-weight: 700;
        }
        button:hover {
            border-color: var(--line-strong);
            transform: translateY(-1px);
        }
        button:active {
            transform: translateY(0);
        }
        .row {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            align-items: center;
            justify-content: center;
        }
        .stack {
            display: grid;
            gap: 18px;
        }
        .split {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 18px;
            margin-bottom: 18px;
        }
        .section-title {
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.16em;
            color: var(--accent);
            margin-bottom: 10px;
        }
        .help {
            color: var(--muted);
            font-size: 13px;
            margin: 0 auto 8px;
            max-width: 640px;
            line-height: 1.5;
        }
        .action-row button {
            min-width: 190px;
        }
        pre {
            background: #031018;
            color: var(--accent-strong);
            padding: 16px;
            border-radius: 14px;
            overflow-x: auto;
            min-height: 140px;
            border: 1px solid rgba(42, 245, 201, 0.2);
            text-align: left;
        }
        .status {
            font-size: 14px;
            color: var(--text);
            margin: 0;
            display: grid;
            gap: 10px;
            align-content: center;
        }
        .status strong {
            color: var(--muted);
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.08em;
            margin-right: 8px;
        }
        .status-chip {
            display: inline-flex;
            justify-content: center;
            align-items: center;
            min-width: 120px;
            padding: 8px 12px;
            border-radius: 999px;
            border: 1px solid var(--line);
            background: rgba(3, 16, 24, 0.88);
        }
        .peer-list {
            margin: 10px auto 0;
            padding: 12px;
            background: rgba(3, 16, 24, 0.88);
            border: 1px solid var(--line);
            border-radius: 14px;
            min-height: 40px;
            max-width: 720px;
        }
        .peer-item {
            display: inline-block;
            background: rgba(30, 54, 73, 0.88);
            border: 1px solid rgba(115, 214, 255, 0.18);
            border-radius: 999px;
            padding: 8px 12px;
            margin: 4px;
        }
        .peer-item button {
            margin-left: 6px;
            padding: 2px 6px;
            font-size: 12px;
            min-width: 0;
        }
        .hero {
            margin-bottom: 18px;
        }
        .hero .card {
            background: linear-gradient(180deg, var(--bg-panel-strong), rgba(11, 20, 30, 0.98));
        }
        .provision-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 12px 18px;
            align-items: start;
            margin-top: 18px;
        }
        .provision-grid .field {
            text-align: center;
        }
        .provision-grid .field input,
        .provision-grid .field select {
            width: 100%;
        }
        .wide {
            grid-column: 1 / -1;
        }
        .big-button {
            min-width: 260px;
            min-height: 52px;
            background: linear-gradient(180deg, rgba(53, 101, 129, 0.98), rgba(15, 48, 69, 0.98));
            border-color: rgba(42, 245, 201, 0.35);
        }
        .secondary {
            background: linear-gradient(180deg, rgba(54, 65, 76, 0.95), rgba(21, 30, 38, 0.95));
        }
        @media (max-width: 720px) {
            body {
                padding: 18px 14px 30px;
            }
            h1 {
                font-size: 30px;
            }
            .card {
                padding: 16px;
            }
        }
    </style>
</head>
<body>
    <div class="hero">
        <div class="card">
            <div class="section-title">Operational Console</div>
            <h1>WFB Radio Control</h1>
            <div class="intro">Provision the node, apply link tuning as one operation, then move to camera control and diagnostics. This layout is optimized for fast field-side reconfiguration.</div>
        </div>
    </div>

    <div class="stack">
        <div class="card">
            <div class="section-title">Overview</div>
            <h2>Node Context</h2>
            <div class="help">Pick the node you are working on and confirm the current radio and camera service state before making changes.</div>
            <div class="split">
                <div>
                    <label>Current Node ID</label>
                    <input type="number" id="node_id" value="1" min="1" max="16">
                </div>
                <div class="status">
                    <div><strong>Node ID</strong><span id="status_node_id" class="status-chip">1</span></div>
                    <div><strong>Hostname</strong><span id="hostname" class="status-chip">node01</span></div>
                    <div><strong>ETH0 Gateway</strong><span id="eth0_address" class="status-chip">172.22.1.1/24</span></div>
                    <div><strong>ETH0 Subnet</strong><span id="eth0_subnet" class="status-chip">172.22.1.0/24</span></div>
                    <div><strong>Fallback Address</strong><span id="fallback_address" class="status-chip">169.254.100.1/24</span></div>
                    <div><strong>Loopback</strong><span id="loopback_address" class="status-chip">10.5.0.1/32</span></div>
                    <div><strong>Radio Service</strong><span id="radio_state" class="status-chip">...</span></div>
                    <div><strong>DHCP Service</strong><span id="dhcp_state" class="status-chip">...</span></div>
                    <div><strong>Babel Service</strong><span id="babel_state" class="status-chip">...</span></div>
                    <div><strong>Camera Service</strong><span id="camera_state" class="status-chip">...</span></div>
                    <div><strong>Key Bundle</strong><span id="key_bundle" class="status-chip">none</span></div>
                </div>
            </div>
            <div class="split">
                <div class="status">
                    <div><strong>Current MCS</strong><span id="current_mcs" class="status-chip">...</span></div>
                    <div><strong>Current Bandwidth</strong><span id="current_bw" class="status-chip">...</span></div>
                    <div><strong>Current FEC</strong><span id="current_fec" class="status-chip">...</span></div>
                    <div><strong>Video RX Target</strong><span id="current_video_target" class="status-chip">...</span></div>
                    <div><strong>Peers</strong><span id="current_peers" class="status-chip">...</span></div>
                </div>
                <div class="status">
                    <div><strong>Camera Width</strong><span id="current_cam_width" class="status-chip">...</span></div>
                    <div><strong>Camera Height</strong><span id="current_cam_height" class="status-chip">...</span></div>
                    <div><strong>Camera FPS</strong><span id="current_cam_framerate" class="status-chip">...</span></div>
                    <div><strong>Camera Bitrate</strong><span id="current_cam_bitrate" class="status-chip">...</span></div>
                    <div><strong>Lens Position</strong><span id="current_cam_lens" class="status-chip">...</span></div>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="section-title">Crypto</div>
            <h2>Key Bundle</h2>
            <div class="help">Generate WFB keys on this Pi only when you intentionally want a new network bundle. The normal status view shows fingerprints and bundle metadata, not plaintext keys.</div>
            <div class="row action-row">
                <button class="secondary" onclick="refreshKeys()">Refresh Key Status</button>
                <button onclick="generateKeys()">Generate New Key Bundle</button>
                <button class="secondary" onclick="installDefaultTestKey()">Create Or Install Test Key</button>
                <button class="secondary" onclick="exportCurrentKeys()">Export Current Bundle</button>
            </div>
            <pre id="key_output">No key status loaded yet.</pre>
        </div>

        <div class="card">
            <div class="section-title">Provisioning</div>
            <h2>Provision And Tune Radio</h2>
            <div class="help">Define topology and apply radio tuning in one step. This writes the active node config, updates bandwidth and FEC, selects the boot-persistent radio service, and restarts the link once.</div>
            <div class="row action-row">
                <button class="secondary" onclick="loadDefaults()">Set Recommended Defaults</button>
            </div>

            <label>Add Peer</label>
            <div class="row">
                <select id="peer_select">
                    <option value="1">1</option>
                    <option value="2">2</option>
                    <option value="3">3</option>
                    <option value="4">4</option>
                    <option value="5">5</option>
                    <option value="6">6</option>
                    <option value="7">7</option>
                    <option value="8">8</option>
                    <option value="9">9</option>
                    <option value="10">10</option>
                    <option value="11">11</option>
                    <option value="12">12</option>
                    <option value="13">13</option>
                    <option value="14">14</option>
                    <option value="15">15</option>
                    <option value="16">16</option>
                </select>
                <button onclick="addPeer()">Add Peer</button>
            </div>

            <label>Selected Peers</label>
            <div id="peer_list" class="peer-list"></div>

            <label>Video RX Target</label>
            <input type="text" id="video_rx_target" value="127.0.0.1:5600">

            <div class="provision-grid">
                <div class="field">
                    <label>MCS Index</label>
                    <input type="number" id="mcs" value="1" min="0" max="5">
                </div>
                <div class="field">
                    <label>Bandwidth</label>
                    <select id="bw">
                        <option value="20">20 MHz</option>
                        <option value="40">40 MHz</option>
                    </select>
                </div>
                <div class="field">
                    <label>FEC K</label>
                    <input type="number" id="fec_k" value="8" min="1" max="32" placeholder="fec_k">
                </div>
                <div class="field">
                    <label>FEC N</label>
                    <input type="number" id="fec_n" value="12" min="1" max="64" placeholder="fec_n">
                </div>
                <div class="field wide">
                    <div class="help">Allowed radio range: MCS 0-5, bandwidth 20 or 40, fec_k 1-32, fec_n 1-64, and fec_n must be at least fec_k.</div>
                </div>
                <div class="field wide row action-row">
                    <button class="big-button" onclick="applyNodeConfig()">Provision And Apply Radio</button>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="section-title">Camera</div>
            <h2>Camera Controls</h2>
            <div class="help">Use start and stop for quick checks. Adjust the camera parameters below, then apply them once.</div>
            <div class="row action-row">
                <button class="secondary" onclick="cameraStart()">Start Camera</button>
                <button class="secondary" onclick="cameraStop()">Stop Camera</button>
            </div>

            <div class="provision-grid">
                <div class="field">
                    <label>Width</label>
                    <input type="number" id="cam_width" value="1280" min="1">
                </div>
                <div class="field">
                    <label>Height</label>
                    <input type="number" id="cam_height" value="720" min="1">
                </div>
                <div class="field">
                    <label>Framerate</label>
                    <input type="number" id="cam_framerate" value="30" min="1" max="120">
                </div>
                <div class="field">
                    <label>Bitrate</label>
                    <input type="number" id="cam_bitrate" value="3000000" min="10000">
                </div>
                <div class="field wide">
                    <label>Lens Position</label>
                    <input type="number" id="cam_lens_position" value="0.0" min="0" max="32" step="0.1">
                </div>
                <div class="field wide row action-row">
                    <button onclick="applyCamera()">Apply Camera Settings</button>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="section-title">Diagnostics</div>
            <h2>API Output</h2>
            <div class="help">Every action posts its response here so you can quickly confirm what the backend accepted or rejected.</div>
            <pre id="output">Ready.</pre>
        </div>
    </div>

    <script>
        let selectedPeers = [];
        let defaultConfig = null;

        function currentNodeId() {
            return parseInt(document.getElementById("node_id").value);
        }

        async function apiCall(url) {
            const output = document.getElementById("output");
            output.textContent = "Calling " + url + " ...";

            try {
                const response = await fetch(url);
                const data = await response.json();
                output.textContent = JSON.stringify(data, null, 2);
                refreshStatus();
            } catch (err) {
                output.textContent = "Error: " + err;
            }
        }

        async function loadDefaults() {
            const output = document.getElementById("output");
            output.textContent = "Loading defaults...";

            try {
                const response = await fetch("/defaults");
                const data = await response.json();
                defaultConfig = data;

                document.getElementById("mcs").value = data.radio.mcs_index;
                document.getElementById("bw").value = data.radio.bandwidth;
                document.getElementById("fec_k").value = data.radio.fec_k;
                document.getElementById("fec_n").value = data.radio.fec_n;
                document.getElementById("video_rx_target").value = data.radio.video_rx_target;

                document.getElementById("cam_width").value = data.camera.width;
                document.getElementById("cam_height").value = data.camera.height;
                document.getElementById("cam_framerate").value = data.camera.framerate;
                document.getElementById("cam_bitrate").value = data.camera.bitrate;
                document.getElementById("cam_lens_position").value = data.camera.lens_position;

                output.textContent = JSON.stringify({
                    status: "defaults_loaded",
                    defaults: data,
                }, null, 2);
            } catch (err) {
                output.textContent = "Error: " + err;
            }
        }

        async function refreshStatus() {
            const nodeId = currentNodeId();
            document.getElementById("status_node_id").textContent = nodeId;

            try {
                const response = await fetch("/status/" + nodeId);
                const data = await response.json();
                document.getElementById("hostname").textContent = data.hostname || "unknown";
                document.getElementById("eth0_address").textContent = data.eth0_address;
                document.getElementById("eth0_subnet").textContent = data.eth0_subnet;
                document.getElementById("fallback_address").textContent = data.fallback_address;
                document.getElementById("loopback_address").textContent = data.loopback_address;
                document.getElementById("radio_state").textContent = data.radio_service;
                document.getElementById("dhcp_state").textContent = data.dhcp_service;
                document.getElementById("babel_state").textContent = data.babel_service;
                document.getElementById("camera_state").textContent = data.camera_service;
                document.getElementById("key_bundle").textContent = data.key_bundle_id || "none";
                document.getElementById("current_mcs").textContent = data.current_radio.mcs_index || "unknown";
                document.getElementById("current_bw").textContent = data.current_radio.bandwidth || "unknown";
                document.getElementById("current_fec").textContent = (data.current_radio.fec_k && data.current_radio.fec_n)
                    ? data.current_radio.fec_k + "/" + data.current_radio.fec_n
                    : "unknown";
                document.getElementById("current_video_target").textContent = data.current_radio.video_rx_target || "unknown";
                document.getElementById("current_peers").textContent = data.current_radio.peers && data.current_radio.peers.length
                    ? data.current_radio.peers.join(",")
                    : "none";
                document.getElementById("current_cam_width").textContent = data.current_camera.width || "unknown";
                document.getElementById("current_cam_height").textContent = data.current_camera.height || "unknown";
                document.getElementById("current_cam_framerate").textContent = data.current_camera.framerate || "unknown";
                document.getElementById("current_cam_bitrate").textContent = data.current_camera.bitrate || "unknown";
                document.getElementById("current_cam_lens").textContent = data.current_camera.lens_position || "unknown";
            } catch (err) {
                document.getElementById("hostname").textContent = "error";
                document.getElementById("eth0_address").textContent = "error";
                document.getElementById("eth0_subnet").textContent = "error";
                document.getElementById("fallback_address").textContent = "error";
                document.getElementById("loopback_address").textContent = "error";
                document.getElementById("radio_state").textContent = "error";
                document.getElementById("dhcp_state").textContent = "error";
                document.getElementById("babel_state").textContent = "error";
                document.getElementById("camera_state").textContent = "error";
                document.getElementById("key_bundle").textContent = "error";
                document.getElementById("current_mcs").textContent = "error";
                document.getElementById("current_bw").textContent = "error";
                document.getElementById("current_fec").textContent = "error";
                document.getElementById("current_video_target").textContent = "error";
                document.getElementById("current_peers").textContent = "error";
                document.getElementById("current_cam_width").textContent = "error";
                document.getElementById("current_cam_height").textContent = "error";
                document.getElementById("current_cam_framerate").textContent = "error";
                document.getElementById("current_cam_bitrate").textContent = "error";
                document.getElementById("current_cam_lens").textContent = "error";
            }
        }

        async function refreshKeys() {
            const output = document.getElementById("key_output");
            output.textContent = "Loading key status...";

            try {
                const response = await fetch("/keys/status");
                const data = await response.json();
                output.textContent = JSON.stringify(data, null, 2);
                refreshStatus();
            } catch (err) {
                output.textContent = "Error: " + err;
            }
        }

        function generateKeys() {
            const confirmed = window.confirm(
                "Generate a new WFB key bundle on this Pi? This replaces the active /etc/gs.key and /etc/drone.key files and can break connectivity until other radios receive the same bundle."
            );

            if (!confirmed) {
                return;
            }

            apiCall("/keys/generate");
            setTimeout(refreshKeys, 300);
        }

        function exportCurrentKeys() {
            apiCall("/keys/export/current");
        }

        function installDefaultTestKey() {
            const confirmed = window.confirm(
                "Create or install the local test key bundle on this Pi? If the named test bundle does not exist yet, this Pi will generate it locally. If it already exists here, it will be reinstalled as the active key bundle."
            );

            if (!confirmed) {
                return;
            }

            apiCall("/keys/default_test/ensure");
            setTimeout(refreshKeys, 300);
        }

        function setMcs() {
            const nodeId = currentNodeId();
            const value = document.getElementById("mcs").value;
            apiCall("/set_mcs/" + nodeId + "/" + value);
        }

        function setBw() {
            const nodeId = currentNodeId();
            const value = document.getElementById("bw").value;
            apiCall("/set_bw/" + nodeId + "/" + value);
        }

        function setFec() {
            const nodeId = currentNodeId();
            const k = document.getElementById("fec_k").value;
            const n = document.getElementById("fec_n").value;
            apiCall("/set_fec/" + nodeId + "/" + k + "/" + n);
        }

        function applyNodeConfig() {
            const nodeId = currentNodeId();
            const target = encodeURIComponent(document.getElementById("video_rx_target").value);
            const peers = encodeURIComponent(selectedPeers.join(","));
            const mcs = encodeURIComponent(document.getElementById("mcs").value);
            const bw = encodeURIComponent(document.getElementById("bw").value);
            const fecK = encodeURIComponent(document.getElementById("fec_k").value);
            const fecN = encodeURIComponent(document.getElementById("fec_n").value);

            const url = "/node/apply/" + nodeId
                + "?peers=" + peers
                + "&video_rx_target=" + target
                + "&mcs_index=" + mcs
                + "&bandwidth=" + bw
                + "&fec_k=" + fecK
                + "&fec_n=" + fecN;

            apiCall(url);
        }

        function applyCamera() {
            const width = document.getElementById("cam_width").value;
            const height = document.getElementById("cam_height").value;
            const framerate = document.getElementById("cam_framerate").value;
            const bitrate = document.getElementById("cam_bitrate").value;
            const lens = document.getElementById("cam_lens_position").value;

            const url = "/camera/apply"
                + "?width=" + encodeURIComponent(width)
                + "&height=" + encodeURIComponent(height)
                + "&framerate=" + encodeURIComponent(framerate)
                + "&bitrate=" + encodeURIComponent(bitrate)
                + "&lens_position=" + encodeURIComponent(lens);

            apiCall(url);
        }

        function cameraStart() {
            apiCall("/camera/START");
        }

        function cameraStop() {
            apiCall("/camera/STOP");
        }

        function addPeer() {
            const nodeId = currentNodeId();
            const peer = parseInt(document.getElementById("peer_select").value);

            if (peer === nodeId) {
                document.getElementById("output").textContent = "Cannot add node as its own peer.";
                return;
            }

            if (!selectedPeers.includes(peer)) {
                selectedPeers.push(peer);
                selectedPeers.sort((a, b) => a - b);
                renderPeers();
            }
        }

        function removePeer(peer) {
            selectedPeers = selectedPeers.filter(p => p !== peer);
            renderPeers();
        }

        function renderPeers() {
            const container = document.getElementById("peer_list");

            if (selectedPeers.length === 0) {
                container.innerHTML = "<em>No peers selected</em>";
                return;
            }

            container.innerHTML = selectedPeers.map(function(peer) {
                return '<span class="peer-item">'
                    + 'Peer ' + peer
                    + ' <button onclick="removePeer(' + peer + ')">x</button>'
                    + '</span>';
            }).join("");
        }

        document.getElementById("node_id").addEventListener("change", function() {
            const nodeId = parseInt(this.value);
            selectedPeers = selectedPeers.filter(p => p !== nodeId);
            renderPeers();
            refreshStatus();
        });

        renderPeers();
        loadDefaults();
        refreshStatus();
        refreshKeys();
        setInterval(refreshStatus, 3000);
    </script>
</body>
</html>
"""

UI_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>WFB Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 950px;
            margin: 20px auto;
            padding: 0 16px;
            background: #f5f5f5;
        }
        h1 {
            margin-bottom: 8px;
        }
        .card {
            background: white;
            padding: 16px;
            margin-bottom: 16px;
            border-radius: 8px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.1);
        }
        label {
            display: block;
            margin-top: 10px;
            margin-bottom: 4px;
            font-weight: bold;
        }
        input, select, button {
            padding: 8px;
            margin: 4px 0 8px 0;
            font-size: 14px;
        }
        button {
            cursor: pointer;
            margin-right: 8px;
        }
        .row {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            align-items: center;
        }
        pre {
            background: #111;
            color: #0f0;
            padding: 12px;
            border-radius: 6px;
            overflow-x: auto;
            min-height: 140px;
        }
        .status {
            font-size: 14px;
            color: #333;
            margin-bottom: 16px;
        }
        .peer-list {
            margin-top: 8px;
            padding: 8px;
            background: #fafafa;
            border: 1px solid #ddd;
            border-radius: 6px;
            min-height: 40px;
        }
        .peer-item {
            display: inline-block;
            background: #e9e9e9;
            border-radius: 14px;
            padding: 6px 10px;
            margin: 4px;
        }
        .peer-item button {
            margin-left: 6px;
            padding: 2px 6px;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <h1>WFB Control UI</h1>

    <div class="status">
        <div><strong>Node ID:</strong> <span id="status_node_id">1</span></div>
        <div><strong>Radio service:</strong> <span id="radio_state">...</span></div>
        <div><strong>Camera service:</strong> <span id="camera_state">...</span></div>
    </div>

    <div class="card">
        <h2>Node</h2>
        <label>Current Node ID</label>
        <input type="number" id="node_id" value="1" min="1" max="16">
    </div>

    <div class="card">
        <h2>Radio</h2>

        <label>MCS Index (0 to 5)</label>
        <div class="row">
            <input type="number" id="mcs" value="1" min="0" max="5">
            <button onclick="setMcs()">Set MCS</button>
        </div>

        <label>Bandwidth</label>
        <div class="row">
            <select id="bw">
                <option value="20">20</option>
                <option value="40">40</option>
            </select>
            <button onclick="setBw()">Set BW</button>
        </div>

        <label>FEC</label>
        <div class="row">
            <input type="number" id="fec_k" value="8" min="1" max="32" placeholder="fec_k">
            <input type="number" id="fec_n" value="12" min="1" max="64" placeholder="fec_n">
            <button onclick="setFec()">Set FEC</button>
        </div>
        <div>Allowed range: fec_k 1-32, fec_n 1-64, and fec_n must be at least fec_k.</div>
    </div>

    <div class="card">
        <h2>Camera</h2>

        <label>Width</label>
        <input type="number" id="cam_width" value="1280" min="1">

        <label>Height</label>
        <input type="number" id="cam_height" value="720" min="1">

        <label>Framerate</label>
        <input type="number" id="cam_framerate" value="30" min="1" max="120">

        <label>Bitrate</label>
        <input type="number" id="cam_bitrate" value="2000000" min="10000">

        <label>Lens Position</label>
        <input type="number" id="cam_lens_position" value="0.0" min="0" max="32" step="0.1">

        <div class="row">
            <button onclick="applyCamera()">Apply Camera Config</button>
            <button onclick="cameraStart()">Start Camera</button>
            <button onclick="cameraStop()">Stop Camera</button>
        </div>
    </div>

    <div class="card">
        <h2>IPRadio</h2>

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

        <div class="row">
            <button onclick="provision()">Provision</button>
        </div>
    </div>

    <div class="card">
        <h2>Output</h2>
        <pre id="output">Ready.</pre>
    </div>

    <script>
        let selectedPeers = [];

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

        async function refreshStatus() {
            const nodeId = currentNodeId();
            document.getElementById("status_node_id").textContent = nodeId;

            try {
                const response = await fetch("/status/" + nodeId);
                const data = await response.json();
                document.getElementById("radio_state").textContent = data.radio_service;
                document.getElementById("camera_state").textContent = data.camera_service;
            } catch (err) {
                document.getElementById("radio_state").textContent = "error";
                document.getElementById("camera_state").textContent = "error";
            }
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

        function provision() {
            const nodeId = currentNodeId();
            const target = encodeURIComponent(document.getElementById("video_rx_target").value);
            const peers = encodeURIComponent(selectedPeers.join(","));

            apiCall("/ipradio/provision/" + nodeId + "?peers=" + peers + "&video_rx_target=" + target);
        }

        document.getElementById("node_id").addEventListener("change", function() {
            const nodeId = parseInt(this.value);
            selectedPeers = selectedPeers.filter(p => p !== nodeId);
            renderPeers();
            refreshStatus();
        });

        renderPeers();
        refreshStatus();
        setInterval(refreshStatus, 3000);
    </script>
</body>
</html>
"""

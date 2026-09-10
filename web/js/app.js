import { TelemetryState } from "./telemetry-state.js";
import { WsClient } from "./ws-client.js";
import { initMap, updateBoatPosition, setStaleStyle, resetTrail } from "./map-view.js";
import { updateStatusPanel } from "./status-panel.js";

const DEFAULT_WS_URL = "ws://localhost:8765";
const DEFAULT_CENTER = { lat: 42.1396, lon: -71.0964 };
const STALE_CHECK_INTERVAL_MS = 500;

function getWsUrl() {
    const params = new URLSearchParams(window.location.search);
    return params.get("ws") || DEFAULT_WS_URL;
}

function getStatusElements() {
    return {
        connection: document.getElementById("connection-status"),
        stale: document.getElementById("stale-indicator"),
        lat: document.getElementById("value-lat"),
        lon: document.getElementById("value-lon"),
        accuracy: document.getElementById("value-accuracy"),
        satellites: document.getElementById("value-satellites"),
        fixQuality: document.getElementById("value-fix-quality"),
        linkQuality: document.getElementById("value-link-quality"),
        age: document.getElementById("value-age"),
        rejected: document.getElementById("count-rejected"),
        duplicate: document.getElementById("count-duplicate"),
        outOfOrder: document.getElementById("count-out-of-order"),
        delayed: document.getElementById("count-delayed"),
    };
}

function main() {
    const state = new TelemetryState();
    const elements = getStatusElements();
    const mapState = initMap("map", DEFAULT_CENTER);

    const wsClient = new WsClient(getWsUrl(), {
        onMessage: (rawMessageText, receivedAtMs) => {
            const result = state.ingest(rawMessageText, receivedAtMs);
            if (result.sessionChanged) {
                resetTrail(mapState);
            }
            if (result.status === "accepted" || result.status === "delayed") {
                updateBoatPosition(mapState, result.record.lat, result.record.lon);
            }
        },
    });

    setInterval(() => {
        const nowMs = Date.now();
        const stale = state.isStale(nowMs);
        setStaleStyle(mapState, stale);
        updateStatusPanel(elements, state, wsClient.connected, nowMs);
    }, STALE_CHECK_INTERVAL_MS);
}

main();

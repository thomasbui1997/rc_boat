function formatAgeSeconds(receivedAtMs, nowMs) {
    return `${((nowMs - receivedAtMs) / 1000).toFixed(1)}s ago`;
}

function fixQualityLabel(fixQuality) {
    if (fixQuality === 2) return "DGPS";
    if (fixQuality === 1) return "GPS";
    return "no fix";
}

export function updateStatusPanel(elements, state, connected, nowMs) {
    const record = state.latest;
    const stale = state.isStale(nowMs);

    elements.connection.textContent = connected ? "connected" : "disconnected";
    elements.stale.textContent = stale ? "STALE" : "live";
    elements.stale.classList.toggle("status-stale", stale);
    elements.stale.classList.toggle("status-live", !stale);

    if (record) {
        elements.lat.textContent = record.lat !== null ? record.lat.toFixed(6) : "--";
        elements.lon.textContent = record.lon !== null ? record.lon.toFixed(6) : "--";
        elements.accuracy.textContent =
            record.position_accuracy_m !== null ? `${record.position_accuracy_m.toFixed(1)} m` : "--";
        elements.satellites.textContent = record.satellites_used;
        elements.fixQuality.textContent = fixQualityLabel(record.fix_quality);
        elements.linkQuality.textContent =
            record.link_quality_pct !== null ? `${record.link_quality_pct}%` : "unknown";
        elements.age.textContent = formatAgeSeconds(state.lastAcceptedReceivedAtMs, nowMs);
    } else {
        elements.lat.textContent = "--";
        elements.lon.textContent = "--";
        elements.accuracy.textContent = "--";
        elements.satellites.textContent = "--";
        elements.fixQuality.textContent = "--";
        elements.linkQuality.textContent = "--";
        elements.age.textContent = "never";
    }

    elements.rejected.textContent = state.counts.rejected;
    elements.duplicate.textContent = state.counts.duplicate;
    elements.outOfOrder.textContent = state.counts.outOfOrder;
    elements.delayed.textContent = state.counts.delayed;
}

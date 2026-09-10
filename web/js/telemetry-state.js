// Must match SCHEMA_VERSION in src/telemetry/schema.py.
const SCHEMA_VERSION = 2;

const REQUIRED_NUMBER_FIELDS = ["sequence", "satellites_used", "fix_quality"];

// lat/lon/position_accuracy_m are null on a no-fix message (fix_quality 0);
// link_quality_pct is null when the boat couldn't read its own Wi-Fi signal.
// Both are distinct from a real 0 value, so they stay nullable rather than
// defaulting to a number.
const NULLABLE_NUMBER_FIELDS = ["lat", "lon", "position_accuracy_m", "link_quality_pct"];

function isNumber(value) {
    return typeof value === "number" && !Number.isNaN(value);
}

function validateShape(message) {
    if (message === null || typeof message !== "object") {
        return "not_an_object";
    }
    if (message.schema_version !== SCHEMA_VERSION) {
        return "schema_version_mismatch";
    }
    if (typeof message.session_id !== "string" || message.session_id === "") {
        return "invalid_session_id";
    }
    if (typeof message.source !== "string" || message.source === "") {
        return "invalid_source";
    }
    if (typeof message.timestamp_utc !== "string" || Number.isNaN(Date.parse(message.timestamp_utc))) {
        return "invalid_timestamp";
    }
    for (const field of REQUIRED_NUMBER_FIELDS) {
        if (!isNumber(message[field])) {
            return `invalid_${field}`;
        }
    }
    for (const field of NULLABLE_NUMBER_FIELDS) {
        if (message[field] !== null && !isNumber(message[field])) {
            return `invalid_${field}`;
        }
    }

    const hasFix = message.fix_quality !== 0;
    if (hasFix) {
        if (message.lat === null || message.lon === null || message.position_accuracy_m === null) {
            return "missing_position_for_fix";
        }
        if (message.lat < -90 || message.lat > 90) {
            return "lat_out_of_range";
        }
        if (message.lon < -180 || message.lon > 180) {
            return "lon_out_of_range";
        }
    } else if (message.lat !== null || message.lon !== null) {
        return "unexpected_position_without_fix";
    }
    return null;
}

export class TelemetryState {
    constructor({ staleAfterMs = 5000, delayThresholdMs = 2000, seenWindowSize = 50 } = {}) {
        this.staleAfterMs = staleAfterMs;
        this.delayThresholdMs = delayThresholdMs;
        this.seenWindowSize = seenWindowSize;

        this.latest = null;
        this.sessionId = null;
        this.maxSequenceSeen = -Infinity;
        this.seenSequences = [];
        this.lastAcceptedReceivedAtMs = null;
        this.counts = { rejected: 0, duplicate: 0, outOfOrder: 0, delayed: 0 };
    }

    ingest(rawMessageText, receivedAtMs) {
        let message;
        try {
            message = JSON.parse(rawMessageText);
        } catch {
            this.counts.rejected++;
            return { status: "rejected", reason: "invalid_json" };
        }

        const validationError = validateShape(message);
        if (validationError) {
            this.counts.rejected++;
            return { status: "rejected", reason: validationError };
        }

        // A changed session_id means the boat process restarted (its
        // sequence counter reset to 1), not that messages arrived out of
        // order — start fresh instead of discarding everything as stale
        // duplicates/out-of-order.
        const sessionChanged = this.sessionId !== null && message.session_id !== this.sessionId;
        if (sessionChanged) {
            this.maxSequenceSeen = -Infinity;
            this.seenSequences = [];
        }
        this.sessionId = message.session_id;

        if (this._hasSeen(message.sequence)) {
            this.counts.duplicate++;
            return { status: "duplicate", sessionChanged };
        }

        if (message.sequence < this.maxSequenceSeen) {
            this._remember(message.sequence);
            this.counts.outOfOrder++;
            return { status: "out_of_order", sessionChanged };
        }

        this._remember(message.sequence);
        this.maxSequenceSeen = message.sequence;
        this.latest = message;
        this.lastAcceptedReceivedAtMs = receivedAtMs;

        if (message.fix_quality === 0) {
            // Well-formed, arriving on schedule, just no position yet — the
            // link is up, so this must not be treated as stale/link-lost.
            return { status: "no_fix", record: message, sessionChanged };
        }

        const messageAgeMs = receivedAtMs - Date.parse(message.timestamp_utc);
        if (messageAgeMs > this.delayThresholdMs) {
            this.counts.delayed++;
            return { status: "delayed", record: message, sessionChanged };
        }
        return { status: "accepted", record: message, sessionChanged };
    }

    isStale(nowMs) {
        if (this.lastAcceptedReceivedAtMs === null) {
            return true;
        }
        return nowMs - this.lastAcceptedReceivedAtMs > this.staleAfterMs;
    }

    _hasSeen(sequence) {
        return this.seenSequences.includes(sequence);
    }

    _remember(sequence) {
        this.seenSequences.push(sequence);
        if (this.seenSequences.length > this.seenWindowSize) {
            this.seenSequences.shift();
        }
    }
}

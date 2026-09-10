import { test } from "node:test";
import assert from "node:assert/strict";

import { TelemetryState } from "../js/telemetry-state.js";

function validMessage(overrides = {}) {
    return JSON.stringify({
        schema_version: 2,
        session_id: "session-a",
        source: "gps",
        sequence: 1,
        timestamp_utc: "2026-09-01T21:54:40.000Z",
        lat: 42.1396,
        lon: -71.0964,
        position_accuracy_m: 8.85,
        satellites_used: 8,
        fix_quality: 1,
        link_quality_pct: 72,
        battery_status: null,
        ...overrides,
    });
}

function noFixMessage(overrides = {}) {
    return validMessage({
        lat: null,
        lon: null,
        position_accuracy_m: null,
        fix_quality: 0,
        ...overrides,
    });
}

test("accepts an in-order message and updates latest", () => {
    const state = new TelemetryState();
    const now = Date.parse("2026-09-01T21:54:40.500Z");
    const result = state.ingest(validMessage(), now);

    assert.equal(result.status, "accepted");
    assert.equal(state.latest.sequence, 1);
    assert.equal(state.lastAcceptedReceivedAtMs, now);
});

test("rejects invalid JSON without touching latest", () => {
    const state = new TelemetryState();
    const result = state.ingest("not json", Date.now());

    assert.equal(result.status, "rejected");
    assert.equal(state.latest, null);
    assert.equal(state.counts.rejected, 1);
});

test("rejects a schema_version mismatch", () => {
    const state = new TelemetryState();
    const result = state.ingest(validMessage({ schema_version: 99 }), Date.now());

    assert.equal(result.status, "rejected");
    assert.equal(state.counts.rejected, 1);
});

test("rejects out-of-range latitude", () => {
    const state = new TelemetryState();
    const result = state.ingest(validMessage({ lat: 200 }), Date.now());

    assert.equal(result.status, "rejected");
});

test("rejects a message missing a required field", () => {
    const state = new TelemetryState();
    const message = JSON.parse(validMessage());
    delete message.satellites_used;
    const result = state.ingest(JSON.stringify(message), Date.now());

    assert.equal(result.status, "rejected");
});

test("accepts a well-formed no-fix message and marks it no_fix, not rejected", () => {
    const state = new TelemetryState();
    const now = Date.parse("2026-09-01T21:54:40.500Z");
    const result = state.ingest(noFixMessage(), now);

    assert.equal(result.status, "no_fix");
    assert.equal(state.latest.fix_quality, 0);
    assert.equal(state.lastAcceptedReceivedAtMs, now);
});

test("rejects a fix-quality message with a missing position", () => {
    const state = new TelemetryState();
    const result = state.ingest(validMessage({ lat: null }), Date.now());

    assert.equal(result.status, "rejected");
});

test("rejects a no-fix message that still carries a position", () => {
    const state = new TelemetryState();
    const result = state.ingest(noFixMessage({ lat: 42.1396 }), Date.now());

    assert.equal(result.status, "rejected");
});

test("resets sequence tracking when session_id changes (boat reboot)", () => {
    const state = new TelemetryState();
    const now = Date.parse("2026-09-01T21:54:40.500Z");
    state.ingest(validMessage({ session_id: "session-a", sequence: 50 }), now);

    const result = state.ingest(
        validMessage({ session_id: "session-b", sequence: 1 }),
        now + 1000,
    );

    assert.equal(result.status, "accepted");
    assert.equal(result.sessionChanged, true);
    assert.equal(state.latest.sequence, 1);
});

test("labels a repeated sequence as duplicate without changing latest", () => {
    const state = new TelemetryState();
    const now = Date.parse("2026-09-01T21:54:40.500Z");
    state.ingest(validMessage({ sequence: 5 }), now);

    const result = state.ingest(validMessage({ sequence: 5 }), now + 1000);

    assert.equal(result.status, "duplicate");
    assert.equal(state.latest.sequence, 5);
    assert.equal(state.lastAcceptedReceivedAtMs, now);
});

test("labels a lower sequence as out of order and never moves latest backward", () => {
    const state = new TelemetryState();
    const now = Date.parse("2026-09-01T21:54:40.500Z");
    state.ingest(validMessage({ sequence: 10, timestamp_utc: "2026-09-01T21:54:40.000Z" }), now);

    const result = state.ingest(
        validMessage({ sequence: 3, timestamp_utc: "2026-09-01T21:54:35.000Z" }),
        now + 1000,
    );

    assert.equal(result.status, "out_of_order");
    assert.equal(state.latest.sequence, 10);
});

test("accepts the newest sequence but labels it delayed if timestamp is old", () => {
    const state = new TelemetryState({ delayThresholdMs: 2000 });
    const timestamp = "2026-09-01T21:54:40.000Z";
    const receivedAt = Date.parse(timestamp) + 5000;

    const result = state.ingest(validMessage({ sequence: 1, timestamp_utc: timestamp }), receivedAt);

    assert.equal(result.status, "delayed");
    assert.equal(state.latest.sequence, 1);
    assert.equal(state.counts.delayed, 1);
});

test("is stale before any message has ever been accepted", () => {
    const state = new TelemetryState();
    assert.equal(state.isStale(Date.now()), true);
});

test("flips stale after staleAfterMs of no accepted update, then back on a fresh update", () => {
    const state = new TelemetryState({ staleAfterMs: 5000 });
    const now = Date.parse("2026-09-01T21:54:40.000Z");
    state.ingest(validMessage({ sequence: 1, timestamp_utc: "2026-09-01T21:54:40.000Z" }), now);

    assert.equal(state.isStale(now + 4000), false);
    assert.equal(state.isStale(now + 5001), true);

    state.ingest(validMessage({ sequence: 2, timestamp_utc: "2026-09-01T21:54:49.000Z" }), now + 9000);
    assert.equal(state.isStale(now + 9000), false);
});

# Telemetry message schema

Reviewed 2026-09-02. This is the formal contract for the JSON message the
onboard Pi sends to the shore application once per second, the identical
shape used for the local NDJSON record, and the validation rules the shore
application applies on receipt. It closes the "message schema, units,
sending interval, clock behavior, validation rules, local-record format"
open item in [DECISIONS.md](DECISIONS.md).

## Message fields

One JSON object per message, sent once per second (matching the GPS
receiver's native 1 Hz refresh — sending faster would just repeat the same
fix).

| Field | Type | Units / format | Notes |
|---|---|---|---|
| `schema_version` | int | — | Bump on any breaking format change. A mismatch is treated as malformed (reject) by the shore app. |
| `session_id` | string | — | Generated once when the sender process starts; unchanged for the life of that run. A change in value tells the shore app the boat rebooted, so it should reset its sequence tracking and start a new trail segment instead of rejecting every message as a duplicate or out-of-order (see "Reboot behavior" below). |
| `source` | string | `gps`, `simulate`, or `replay` | Which location source produced this message, so simulated/replayed sessions are distinguishable from a real one on the wire. |
| `sequence` | int | — | Increments by 1 each message; resets to 1 on boat reboot (a new `session_id`). Used to detect duplicates and out-of-order delivery. |
| `timestamp_utc` | string | ISO 8601 | Sourced from the GPS receiver's own NMEA time, not the Pi's system clock (see "Clock source" below). |
| `lat`, `lon` | float or null | decimal degrees, signed | Position. `null` on a no-fix message (`fix_quality` 0) — see "No-fix behavior". |
| `position_accuracy_m` | float or null | meters | Estimated error radius, derived as `HDOP × 5` — an approximation, not a rigorous bound. `null` alongside `lat`/`lon` on a no-fix message. |
| `satellites_used` | int | count | From the GPS receiver. |
| `fix_quality` | int | NMEA code | `0` = no fix, `1` = GPS fix, `2` = DGPS fix. |
| `link_quality_pct` | int or null | 0–100 | Wi-Fi link quality between the Pi and the shore router. `null` means the measurement itself failed (e.g. the `iw` command is missing, times out, or the interface reports no link) — a different situation from a measured `0` (link readable but very weak). |
| `battery_status` | string or null | — | Ships as `null`/unresolved. Reading the power bank's remaining charge needs an additional sensor (e.g. an INA219-class current-sense chip) that hasn't been purchased — see the open item in `DECISIONS.md`. |

## No-fix behavior

The onboard sender emits a message once per second regardless of whether the
GPS currently has a fix. Before the first fix, or if the GPS temporarily
loses one, `fix_quality` is `0` and `lat`/`lon`/`position_accuracy_m` are
explicitly `null` — never a fabricated position. This matters because the
GPS parsing library reports `lat`/`lon` as `0.0, 0.0` (a real point in the
Gulf of Guinea) for "no fix" rather than "unknown" internally; the sender
converts that into an explicit null instead of forwarding it as if it were
real.

Sending a message every second even without a fix — rather than staying
silent — lets the shore app tell two different failures apart, which
otherwise both look like "messages stopped, then stale after five seconds":
the boat has Wi-Fi but has lost sky visibility (wait, or steer back into
open water), versus the boat has a fix but has lost the Wi-Fi link (drive
back toward shore before it gets worse). It also keeps `link_quality_pct`
observable while there is no fix, which is exactly when it is most useful.

## Reboot behavior

`sequence` resets to 1 on every boat reboot, but `session_id` changes at the
same time. The shore app uses that pairing to distinguish "the boat
restarted" from "packets arrived duplicated or out of order": on a new
`session_id` it resets its sequence-tracking state and starts a fresh trail
segment, rather than discarding the reset counter as duplicates/out-of-order
and freezing the display at the last pre-reboot position.

## Clock source

`timestamp_utc` always comes from the GPS receiver's own time signal, read
out of the NMEA sentence stream, never from the Pi's system clock. The Pi
has no battery-backed real-time clock, and the test site's Wi-Fi has no
internet uplink to sync against — so the system clock cannot be trusted at
boot. GPS satellites broadcast a precise UTC time as part of their normal
signal, and the receiver already parses it out, which sidesteps the whole
networked-clock problem. The one caveat: a `$GPGGA` sentence carries only a
time-of-day, not a date, so the sender combines it with the date most
recently seen on a valid `$GPRMC`/`$GNRMC` sentence. Before any such date
has been seen (the first second or so after boot), the sender falls back to
the Pi's own system time.

## Validation rules (shore-side)

| Case | Rule | Effect |
|---|---|---|
| Malformed | Bad JSON, a required field missing or the wrong type, `lat`/`lon` outside ±90/±180, a fix-quality message missing its position, a no-fix message carrying a position, or a `schema_version` mismatch | Rejected — never shown as current |
| Duplicate | `sequence` already seen in the current `session_id` | Labeled, no state change |
| Out of order | `sequence` lower than the highest seen so far in the current `session_id` | Labeled, no state change — the displayed position never moves backward |
| Reboot | `session_id` differs from the previously seen one | Sequence tracking resets and the trail starts a new segment; the message itself is still validated normally (accepted/delayed/no-fix) against the fresh state |
| No fix | `fix_quality` is `0` | Accepted as the latest message (updates link/satellite readouts and counts as "boat is still there" for staleness), but does not move the displayed position, since it carries none |
| Delayed | `sequence` is the newest seen, but `timestamp_utc` is more than ~2 seconds behind the shore computer's clock at arrival | Still becomes the current position (it's the best data available), but flagged as degraded |
| Stale | No message accepted as current in the last 5 seconds | The boat state is marked stale, independent of any single message — checked on a repeating timer, not just on arrival |

This rule table is the shared contract between the boat-side sender
(`src/telemetry/message_builder.py`) and the shore-side validator
(`web/js/telemetry-state.js`). The logic is necessarily duplicated across
the two languages — a standalone JSON Schema plus a validation library was
deliberately skipped as unneeded weight for one message type at this scale.
If the two ever drift, this document is the source of truth for which one
is wrong.

## Local record format

The Pi retains every message it sends in a local file, in addition to
broadcasting it — this is the "local telemetry record" required by
`MVP-DESIGN.md`. One newline-delimited JSON (NDJSON) file per run, in the
gitignored `data/` directory, one line per message, in the exact same
shape as the wire message:

```
data/session_<UTC-start-timestamp>.ndjson
```

## Worked example

```json
{
  "schema_version": 2,
  "session_id": "6641a03b9a624ad3ac61e19565c78df9",
  "source": "gps",
  "sequence": 42,
  "timestamp_utc": "2026-09-01T21:54:40+00:00",
  "lat": 42.139617,
  "lon": -71.096421,
  "position_accuracy_m": 8.85,
  "satellites_used": 8,
  "fix_quality": 1,
  "link_quality_pct": 72,
  "battery_status": null
}
```

A no-fix message from the same run looks like this instead:

```json
{
  "schema_version": 2,
  "session_id": "6641a03b9a624ad3ac61e19565c78df9",
  "source": "gps",
  "sequence": 43,
  "timestamp_utc": "2026-09-01T21:54:41+00:00",
  "lat": null,
  "lon": null,
  "position_accuracy_m": null,
  "satellites_used": 3,
  "fix_quality": 0,
  "link_quality_pct": 72,
  "battery_status": null
}
```

## Link-quality conversion

Wi-Fi signal strength is read via `iw dev <interface> link`, which reports
raw signal strength in dBm (decibels relative to a milliwatt — more
negative is weaker). That's converted to a 0–100% scale by linearly
clamping between -90 dBm (0%) and -30 dBm (100%), a common convention (used
by tools like NetworkManager) rather than a precise physical measure.

# Current decisions

Reviewed 2026-09-02. Statements labeled **accepted** define the current project
boundary. Statements labeled **candidate** remain open until supported by the
design or bench-test evidence named below.

## Accepted scope

The project is limited to one-way, boat-to-shore location telemetry and a shore
display application. The system makes no safety-performance claim, accepts no
shore commands, and does not control the boat.

## Accepted chassis and control boundary

Use the Carp Angler bait boat as the test chassis. Stock propulsion, receiver,
and RC transmitter remain unchanged. The RC transmitter is the only propulsion
control path; loss or failure of onboard compute, GPS, Wi-Fi, or the shore
application must not reduce the operator's ability to recover the boat.

## Accepted telemetry constraints

Use a removable, independently powered onboard unit with GPS, local storage,
fused power, and Wi-Fi. The shore computer connects to a dedicated portable
router/access point. The boat retains valid GPS records locally while sending a
compact, versioned message containing timestamped location and necessary
health/link fields.

## Current candidates

- A Raspberry Pi 3 **Model A+** (not the B/B+ discussed earlier — corrected
  2026-08-27) has been purchased as the onboard-computer candidate to
  integrate GPS, storage, and telemetry software. It is not yet an accepted
  part. Notable differences from the B/B+ figures previously recorded here:
  the A+ has no Ethernet port and only **one USB 2.0 port** (enough for the
  GPS receiver alone; no spare port for another USB device without adding a
  hub) and **512 MB RAM** (vs. 1 GB on the B/B+; still expected to be plenty
  for a headless Lite OS plus a small telemetry script). Because the A+ omits
  the Ethernet/USB-hub chip present on the B/B+, it is expected to draw less
  power and run cooler, but this has not been bench-tested and no verified
  wattage/temperature figures for the A+ specifically are recorded yet. Because
  the onboard enclosure must be sealed for waterproofing (no convective
  airflow), thermal and power bench-testing in the actual sealed enclosure is
  still required before this candidate is promoted to accepted. See "Open
  decisions" below.
- WebSocket may provide the persistent local telemetry stream. Select the
  transport only after defining the interface and demonstrating reconnect,
  delayed-message, and out-of-order-message behavior on the bench.
- A microSD card (16-32 GB class) has been purchased to serve as both the Pi's
  boot media and its local telemetry-record storage. Candidate, not yet
  bench-tested for write endurance under continuous logging.
- A USB "G-mouse"-style GPS receiver (magnetic-base, marine-navigation
  branded) has been purchased as the position-source candidate. Plugs into the
  Pi over USB; no wiring required. It carries a u-blox 7 chipset and enumerates
  as `/dev/ttyACM0` on Raspberry Pi OS (not `/dev/ttyUSB0`), streaming standard
  NMEA sentences at 9600 baud. First bench check (2026-09-01, indoors at a
  desk near a window) got a valid `$GPGGA` fix (quality 1) on 5 satellites,
  HDOP 1.77, with the reported lat/lon matching Google Maps for the same spot.
  Satellite count climbed to 8 after a few minutes settled at the same desk,
  confirming decent sky visibility indoors near a window. Time-to-first-fix
  from a cold start (unplug/replug) was confirmed to occur (0→1 fix flip
  observed) but not precisely timed. Still not bench-tested for outdoor/
  on-water accuracy or fix consistency over time — remains a candidate, not
  yet accepted.
- A GL.iNet GL-SFT1200 ("Opal") travel router has been purchased as the
  router/access-point candidate. It stays on shore, not on the boat: the shore
  laptop connects to it directly (Ethernet preferred, since it has gigabit
  ports), and only the boat's Pi joins its Wi-Fi wirelessly across the water.
  Not yet bench-tested for boat-to-shore range at an actual test site.
- An INIU 10000mAh USB-C power bank, plus a USB-C-to-micro-USB cable, has been
  purchased as the onboard (boat-side) power source for the Pi. Only the Pi
  needs boat-mounted power now that the router is confirmed shore-side; the
  GPS receiver draws from the Pi's own USB port. Not yet bench-tested for
  sustained-load runtime or for the "smart" auto-shutoff behavior some power
  banks exhibit under a continuous, non-phone-like load.

## Accepted message schema and protocol

WebSocket carries a one-way, boat-to-shore JSON telemetry stream at 1 Hz:
the Pi runs the WebSocket server, and the shore browser connects to it
directly as a client over the shared Wi-Fi (no separate shore-side backend
process). The full field-by-field message schema, the GPS-sourced clock
rationale, the malformed/duplicate/out-of-order/delayed/stale validation
rules, and the local NDJSON record format are defined in
[SCHEMA.md](SCHEMA.md).

Evidence (2026-09-01): implemented in `src/telemetry/` (boat side) and
`web/js/telemetry-state.js` (shore side), with 18 passing Python tests
(`pytest`) and 10 passing JavaScript tests (`node --test web/tests`). A
live end-to-end smoke test (simulated GPS source → WebSocket → a real
client) confirmed delivered messages match the documented schema exactly,
including the local NDJSON log. The shore client auto-reconnects on
disconnect. Validated so far only against simulated data on a laptop, per
the test boundary in `MVP-DESIGN.md` — not yet against the real GPS/Pi
pairing or over the actual boat-to-shore Wi-Fi link.

Updated (2026-09-02): the schema moved to version 2, adding `session_id`
(reboot detection) and `source` (simulated/replayed/real), and making
`lat`/`lon`/`position_accuracy_m`/`link_quality_pct` explicitly nullable so
a no-fix message can be sent every second instead of the sender going
silent — closing the two most misleading gaps recorded in
[CONCERNS.md](CONCERNS.md) (the reboot freeze, and "no fix" being
indistinguishable from "link lost"). The boat-side code (`src/telemetry/`)
had already moved to this shape; this update brings the shore-side
validator (`web/js/telemetry-state.js`) and this document in line with it,
after a live smoke test confirmed the two had drifted — v2 messages were
being rejected outright as a `schema_version` mismatch. Re-verified with 22
Python tests, 14 JavaScript tests (4 new, covering no-fix acceptance and
the reboot/session reset), and a fresh end-to-end smoke test of real v2
WebSocket messages against the updated validator.

## Open decisions

- Whether the power bank's internal protection satisfies the accepted "fused
  power" constraint above, or whether a separate inline fuse must still be
  added between the power bank and the Pi.
- Enclosure and mounting hardware (deferred until after bench testing, per the
  test boundary in MVP-DESIGN.md).
- Local-record retention period: how long to keep old NDJSON session files
  on the Pi's 32 GB microSD before rotating or deleting them.
- The shore GUI's map (MapLibre GL JS) loads its default basemap tiles from
  a remote CDN, which needs internet access. The shore Wi-Fi network at the
  eventual test site has no internet uplink, so the basemap won't load
  there — needs a self-hosted tile set or a tile-less lat/lon-only fallback
  before water testing.

Record each selection here with the evidence that closed it; do not promote a
candidate to an accepted decision based on a planning estimate alone.

## Accepted operating safeguards

Test only at an authorized, recoverable site. Retain a documented manual
recovery method, inspect after water ingress or abnormal battery behavior, and
stop testing for control faults or worsening conditions. The shore application
must label data stale after five seconds without an update rather than showing
it as current.

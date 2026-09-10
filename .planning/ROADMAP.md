# Current focus

The boat has been accepted by the project owner as functional. The sole active
objective is a manual-control-safe, one-way telemetry system: the boat reports
its location to a shore application over a local network, and no command path
runs from shore to boat.

No work is planned beyond this objective. When it is complete, use the test
results to decide the next direction.

## Status

Reviewed 2026-09-01. Step 1 is done (see `SCHEMA.md` and `DECISIONS.md`).
Step 2 is partially underway: the GPS receiver has a first bench-test result
(see `DECISIONS.md`), but the onboard computer, power, storage, and router
are still untested. Step 3's simulated-data path and step 4's shore
application are implemented and passing their test suites, validated
end-to-end on a laptop against a simulated GPS source — not yet run against
the real GPS/Pi pairing or deployed to `boat-pi` itself. Update this section
only when the corresponding decision, code, or test evidence is added.

## Scope

The onboard unit is removable and independently powered. It obtains GPS fixes,
stores them locally, and sends versioned telemetry to a computer on shore via a
dedicated portable router or access point. The shore application shows the
current position, trail, update age, link/health state, and an explicit stale
state after five seconds without a received update.

The stock RC transmitter remains the only propulsion-control path. The onboard
unit must not connect to propulsion wiring or the RC receiver. The system is
boat-to-shore only: it receives no commands and must not move the boat.

## Work sequence

1. **Done:** Define the location/health message, a sending interval compatible
   with the five-second stale timeout, local-record format, clock source, and
   validation rules. See `SCHEMA.md`.
2. **Partially started:** Select and bench-test the removable onboard computer,
   GPS, independent fused power, local storage, and shore-router connection.
   The GPS receiver has a first indoor bench-test result (see DECISIONS.md).
   A Raspberry Pi 3 has been purchased for the onboard-computer role;
   bench-test its power draw and thermal behavior inside the actual sealed
   enclosure (see DECISIONS.md) before treating it as the accepted part.
   Local storage and the shore router remain untested.
3. **Mostly done, not yet on the boat:** Implement and test the boat-side
   sender and shore receiver using simulated and replayed locations. The
   simulated-data path is implemented and passing tests end to end
   (`src/telemetry/`); the replay path is implemented and unit-tested but not
   yet exercised against a real captured session. Remaining: deploy to
   `boat-pi` and run the real `GpsSerialSource` against the actual GPS
   receiver and the boat-to-shore Wi-Fi link.
4. **Implemented, pending a manual check:** Implement the shore application
   with a map, current position and trail, timestamp/update age, link health,
   and obvious stale-data treatment. Built in `web/` (MapLibre GL JS, dark
   Lattice-style layout) with its validation/staleness logic unit-tested
   (`web/js/telemetry-state.js`). Not yet visually confirmed in an actual
   browser — no browser-automation tool was available in the session that
   built it.
5. **Not started:** Run controlled manual-only, near-shore trials. Measure GPS
   accuracy, end-to-end latency, message loss, useful range, runtime, restart
   recovery, and water resistance.

## Completion conditions

- The boat transmits timestamped location telemetry at the selected interval.
- The shore application accurately distinguishes current, delayed, malformed,
  and stale data.
- A Wi-Fi/router/onboard-computer failure does not affect manual control or
  recovery, and local boat records remain available after a link loss.
- Trial measurements and the operating envelope are documented.

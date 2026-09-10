# Telemetry prototype design boundary

## Purpose

The prototype demonstrates one capability: a manually operated boat sends its
own GPS location and basic telemetry to an application running on a shore
computer. The shore application displays the received data without controlling
the boat.

## System boundary

```text
Stock RC transmitter ──> stock receiver ──> motors

GPS ──> removable onboard computer ──> local telemetry record
                           │
                           └── local Wi-Fi ──> portable router ──> shore app
```

The telemetry equipment is removable, independently powered, and electrically
separate from propulsion and the stock RC receiver. Manual RC control remains
available if the GPS, computer, router, or application fails.

## Architecture constraints and candidates

- **Accepted constraint — onboard unit:** use removable compute subject to
  power, mass, thermal, and enclosure testing. A Raspberry Pi-class computer is
  the current candidate, not a selected part.
- **Accepted constraint — position source:** use a separate GPS receiver; do
  not rely on an unknown stock GPS interface.
- **Accepted constraint — network:** use a dedicated portable router/access
  point with a local Wi-Fi connection between the boat and shore computer.
- **Open decision — protocol:** use versioned, one-way boat-to-shore telemetry.
  WebSocket is the current candidate for a persistent local stream; select the
  protocol only after interface design and bench testing.
- **Accepted constraint — records:** retain valid GPS fixes locally on the boat
  as well as sending them to shore.

## Required telemetry behavior

Each message must include a schema version, unique or monotonic sequence value,
UTC timestamp, latitude, longitude, position-accuracy estimate, and essential
health/link fields. The exact fields, units, sending interval, clock source,
and validation rules are defined in [SCHEMA.md](SCHEMA.md).

The application must show current location and trail, last received time,
telemetry age, and link/health state. After five seconds without a valid update,
it must visibly mark the boat state as stale. It must label or reject malformed,
duplicated, delayed, and out-of-order data rather than presenting it as current.

## Test boundary

First validate sender, receiver, and GUI using simulated or replayed location
data. Then conduct controlled, manual-only near-shore tests with a documented
recovery method. Measure GPS accuracy, end-to-end latency, message loss, useful
range, runtime, restart recovery, water resistance, and local-record integrity.

Stop testing after water ingress, control faults, abnormal battery behavior, or
worsening conditions. A telemetry failure requires normal manual recovery; it
must never change the stock RC path.

## Completion decision

The current effort is complete when timestamped telemetry is reliable over the
documented test envelope, the shore application accurately handles live and
stale state, local records survive a link loss, and manual recovery is
unaffected. The project direction after that point is intentionally undecided.

# Boat telemetry prototype

## Project status

Documentation reviewed 2026-09-01. The boat chassis is functional, and the
candidate telemetry hardware is purchased with an initial GPS bench-test
result recorded (see [DECISIONS.md](DECISIONS.md)) — but the onboard
computer, storage, and router remain untested. The message schema and a
first working implementation (boat-side sender, shore-side web application)
now exist and pass their automated tests against simulated GPS data; see
"Running the code" below. Neither has yet been run against the real GPS/Pi
pairing or on the water. See [ROADMAP.md](ROADMAP.md) for the active work.

## Current objective

Build a manually operated boat that reports its GPS location to a shore
application over a local Wi-Fi network. The boat records telemetry locally;
the shore application shows live location, trail, link health, and stale data.

No future capability is committed until this objective has been tested and
reviewed.

## System overview

```text
Stock RC transmitter ──> stock receiver and motors

GPS + removable onboard computer ──> local records
             │
             └── Wi-Fi / portable router ──> shore application
```

The onboard unit is independently powered and must not modify stock propulsion
wiring or the RC receiver. It sends data only; the shore application does not
control the boat.

## Safety rules

- Retain manual RC control and a documented recovery method for every test.
- Keep the powered boat away from people, wildlife, fishing lines, docks, and
  other vessels.
- Test only at authorized, controlled, recoverable sites.
- Stop and inspect after water ingress, control faults, unusual battery
  behavior, or worsening conditions.
- Treat stale or missing telemetry as unavailable data, never as current boat
  location.

See [ROADMAP.md](ROADMAP.md) for the active work, [MVP-DESIGN.md](MVP-DESIGN.md)
for the current system boundary, [SCHEMA.md](SCHEMA.md) for the telemetry
message format, [DECISIONS.md](DECISIONS.md) for selected architecture
decisions, [CONCERNS.md](CONCERNS.md) for open concerns with the shore
application, and [COSTS.md](COSTS.md) for the working budget.

## Running the code

Set up once:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the automated tests:

```
python -m pytest
node --test web/tests
```

Try the full pipeline against simulated GPS data (no hardware needed) — in
one terminal:

```
python -m src.telemetry_sender --source simulate
```

and in another:

```
python -m http.server 8000 --directory web
```

then open `http://localhost:8000/?ws=ws://localhost:8765` in a browser.

To run against the real GPS receiver instead (on `boat-pi`, over SSH):

```
python -m src.telemetry_sender --source gps
```

The Pi user must be in the `dialout` group to read `/dev/ttyACM0`. On
Raspberry Pi OS Bookworm, `pip install` at the system level is blocked
(PEP 668) — use the venv setup above there too.

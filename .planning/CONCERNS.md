# Open concerns with the first milestone GUI

Reviewed 2026-09-02. This document records unresolved problems found by
reviewing the shore application in `web/` against the requirements in
[MVP-DESIGN.md](MVP-DESIGN.md), the contract in [SCHEMA.md](SCHEMA.md), and
the safety rules in [README.md](README.md). Nothing here is a decision; each
item is a concern awaiting either a fix, evidence that it does not matter, or
a deliberate choice to accept it.

At the time of review the automated suites pass (`python -m pytest`: 22
tests; `node --test web/tests`: 14 tests). Every remaining concern below
survives a green test run — the gaps are in behavior the tests do not cover.

Items are grouped by whether they would produce *misleading* results during a
water trial, merely inconvenient ones, or neither.

## Resolved

### A boat reboot froze the display until the browser was reloaded — fixed 2026-09-02

Schema bumped to version 2 with a `session_id` field: a value generated once
when the sender process starts, sent unchanged on every message. On a
changed `session_id`, `web/js/telemetry-state.js` now resets its
sequence-tracking state and `web/js/app.js` clears the map trail via the new
`resetTrail`, instead of discarding every post-reboot message as a duplicate
or out-of-order. See `SCHEMA.md`'s "Reboot behavior" and `DECISIONS.md`.

### "No GPS fix" and "link lost" looked identical on screen — fixed 2026-09-02

The sender now emits a message every second even without a fix, with
`fix_quality: 0` and `lat`/`lon`/`position_accuracy_m` explicitly `null`
rather than staying silent. `web/js/telemetry-state.js` treats this as a
distinct `no_fix` status: accepted (so `link_quality_pct`,
`satellites_used`, and staleness tracking stay live), but the displayed
position does not move, since none was sent. This makes "link up, no fix"
distinguishable from "link lost, nothing arriving" — the latter still goes
`STALE` after five seconds with no messages at all. See `SCHEMA.md`'s
"No-fix behavior".

Note: the status panel (`web/js/status-panel.js`) shows "no fix" in the Fix
field via the existing `fixQualityLabel`, and no longer crashes on the now
possible `null` lat/lon/accuracy/link-quality values — but it does not yet
give the "no fix" state its own prominent treatment the way the stale state
does. That refinement is folded into the still-open "stale treatment is easy
to miss" item below, since both are about the panel not making a degraded
state visually obvious enough.

## Concerns that could mislead an operator during a trial

### Delayed data is drawn as the current position without being labeled

`MVP-DESIGN.md` requires the application to label delayed data "rather than
presenting it as current", and `SCHEMA.md` says a delayed message is "still
becomes the current position ... but flagged as degraded". The flag exists in
the code — `TelemetryState.ingest` returns `{ status: "delayed" }` — but
nothing carries it to the screen. In `web/js/app.js`, the `"delayed"` and
`"accepted"` cases are handled identically: the marker moves, the trail
extends, and the status panel shows the reading as live. The only visible
trace is the "Delayed" counter in the Diagnostics section quietly ticking up,
which does not tell the operator that *the position they are looking at right
now* is the degraded one.

Possible resolution: carry the per-message status into the status panel, so
the state line can read something like `LIVE (DELAYED 4.2 s)` while the
delayed reading is the newest one.

### The stale treatment is easy to miss

When data goes stale the marker's opacity drops to 40 % and one 13 px word
turns red, while latitude, longitude, and accuracy continue to render as
crisp six-decimal numbers. A position that is two seconds old and one that is
twenty minutes old are typographically identical.

The project's own safety rule is to "treat stale or missing telemetry as
unavailable data, never as current boat location", and `ROADMAP.md` step 4
calls for "obvious stale-data treatment". The current treatment is
detectable, but it is not obvious — particularly on a laptop screen outdoors,
which is where it will be read.

Possible resolution: change the whole panel's state on going stale, replace
the position values with an explicit "last known — 4 min 12 s old" framing
rather than leaving them looking live, and change the marker's shape rather
than only its opacity.

### Simulated and replayed data are indistinguishable from the real boat

`python -m src.telemetry_sender` accepts `--source simulate` and
`--source replay`, and the resulting messages render exactly like live GPS.
The project's test boundary deliberately calls for validating with simulated
and replayed data first, which makes it likely that a simulated session and a
real one will be open at the same time at some point.

Possible resolution: add the source mode to the message and show a
persistent, hard-to-ignore banner whenever it is not `gps`.

### The trail draws a straight line across gaps in the data

`web/js/map-view.js` accumulates every accepted position into a single
unbroken line. A two-minute link loss is therefore drawn as a straight
segment between the last position before the loss and the first one after —
a path the boat may never have taken, rendered with the same confidence as
directly observed positions. This is the same principle as the stale rule:
missing data should not be presented as fact.

Possible resolution: break the line into separate segments whenever the gap
between consecutive accepted positions exceeds the five-second stale
threshold, and draw gap-spanning segments differently or not at all.

### The "delayed" rule depends on the shore laptop's clock, which is unsynced

`SCHEMA.md` resolves the boat's clock question well: `timestamp_utc` comes
from the GPS receiver's own time signal rather than the Pi's system clock,
which has no battery to keep time while unplugged. But the delayed rule
compares that GPS time against "the shore computer's clock at arrival", and
the shore laptop is on the same isolated network with no internet uplink to
synchronize against. Its clock is therefore the unverified half of the
comparison. If it drifts by more than the two-second threshold, either every
message is flagged delayed or none ever is, and the operator has no way to
tell which.

Possible resolution: measure and display the boat-versus-shore clock offset
on connection, and either suppress the delayed rule when the offset is
implausible or subtract the observed offset before applying it. Deriving
delay from the spacing between arrivals, rather than from absolute clocks,
is another option worth considering.

## Concerns that would make a trial harder but not misleading

### The map recenters on every message

`updateBoatPosition` calls `map.panTo` on every accepted position, so at the
specified one-message-per-second rate the map yanks back to center once a
second. The operator cannot pan away to check a landmark, a hazard, or the
far bank without fighting the map.

Possible resolution: a follow-the-boat toggle that switches itself off when
the user drags the map, and a control to re-enable it.

### The panel may be hard to read outdoors

The status panel uses 11–13 px text with dimmed labels (`#7c8794` on
`#12161e`) in a fixed 260 px overlay. That is a comfortable indoor reading
size on a desk; it is a difficult one on a laptop screen in daylight at the
water's edge, which is the only place it actually matters. The stale
indicator does carry a text label as well as a color change, which is the
right instinct and worth keeping.

The layout is also fixed-width with no responsive behavior. If a phone is
ever the shore display — plausible, since it only needs to join the router's
Wi-Fi — the panel will not adapt.

### Accuracy is displayed with more precision than it has

The panel renders `position_accuracy_m` as, for example, `8.9 m`. `SCHEMA.md`
is candid that this is `HDOP × 5`, "an approximation, not a rigorous bound",
but the display conveys none of that hedging — it reads like a measured
figure, to a tenth of a meter. This is the number an operator would use to
decide whether to trust a position near a hazard.

Possible resolution: round to whole meters, prefix with an approximation
sign, or show the raw HDOP value until the conversion has been checked
against known points during bench testing.

### Battery health is invisible rather than explicitly unknown

`SCHEMA.md` carries `battery_status` as always `null`, with a clear
explanation that reading the power bank's remaining charge needs a sensor
that has not been purchased. The status panel does not render the field at
all, so from shore there is simply no battery information and no indication
that any was expected.

There is a zero-cost partial answer worth considering: the Raspberry Pi can
report when its own incoming 5-volt supply sags below what it needs — a
condition it already detects and exposes (`vcgencmd get_throttled`). That is
not a charge percentage, but it is the earliest warning that the power bank
is failing to hold up under load, which is precisely the open question about
this power bank. It needs no extra hardware.

At minimum the panel should show "Battery: not reported" so the absence is
visible rather than silent.

### Link quality reports 0 % for "cannot read" and for "very weak"

`read_link_quality_pct` returns `0` when the `iw` command is missing, times
out, or reports no link, and `SCHEMA.md` documents this as deliberate
(the field is not nullable). The consequence is that a `0%` reading on the
panel could mean the radio link is nearly dead, or it could mean the
measurement itself failed on a boat with a perfectly good link. Those are
different situations.

## Smaller notes

- **The map library itself also comes from a CDN.** `DECISIONS.md` already
  tracks the missing-basemap problem for map *tiles*. Worth noting that
  `web/index.html` also loads the MapLibre library and stylesheet from
  `cdn.jsdelivr.net`, so at a site with no internet the page does not merely
  lose its basemap — nothing renders at all. The convention in `CLAUDE.md`
  that `web/` loads "libraries loaded via CDN, no build step" is a reasonable
  development-time choice that conflicts with field use; resolving the
  basemap item should cover the library too.
- **The trail is unbounded and cannot be cleared.** Positions accumulate for
  the life of the page with no cap and no reset control. At one message per
  second this is not a performance problem for a session of realistic
  length, but there is no way to clear a trail between runs without a page
  reload.
- **"Last received time" is not shown.** `MVP-DESIGN.md` asks for last
  received time *and* telemetry age; the panel shows only the age. After a
  long gap, "1247.3s ago" is harder to reason about than a clock time. The
  age of the GPS fix itself, as distinct from when the message arrived, is
  also never displayed.
- **A specific real-world coordinate is committed in two places.** The same
  latitude and longitude appear in `web/js/app.js` as the default map center
  and in `src/telemetry/simulated_source.py` as the simulation center. The
  repository conventions bar committing location-sensitive test data; a
  neutral default in `config/` would satisfy both.
- **The connection indicator has no "connecting" state.** `WsClient` reports
  only connected or disconnected, and retries on a fixed two-second interval
  forever, so a reconnect in progress is indistinguishable from a link that
  is simply down.
## Testing gaps behind these concerns

`web/js/telemetry-state.js` is well covered — its fourteen tests exercise
the malformed, duplicate, out-of-order, delayed, stale, no-fix, and
reboot/session-reset cases the requirements name. The untested parts are
`status-panel.js`, `map-view.js`, and `ws-client.js`, all of which need a
browser DOM, and `ROADMAP.md` step 4 records that the application has never
been visually confirmed in a browser at all.

That is where most of the concerns above live: the validation logic decides
correctly and then the display fails to communicate the decision.

One refactor would make several of them testable at once: extract a pure
function that turns the current state into a display model — the state to
show, the ages, whether the position should be presented as trustworthy —
leaving the DOM code as a simple renderer. The delayed labeling, the stale
treatment, and the missing last-received time would then all be decided in
one tested place, in the same style as `telemetry-state.js`.

A browser check of the assembled page remains necessary regardless, since no
amount of unit testing confirms that the stale state is *visually* obvious.

## Suggested order

The reboot freeze and the no-fix/link-lost ambiguity — the two schema-level
items — are resolved as of 2026-09-02 (see "Resolved" above). Of what
remains, the two that would still make a trial produce misleading results
rather than merely inconvenient ones are, in order:

1. Labeling delayed data on screen, and strengthening the stale treatment.
2. Marking simulated and replayed sessions unmistakably — the wire-level
   `source` field already exists (added alongside `session_id` in the
   2026-09-02 schema update) and just needs a shore-side banner; this is now
   a UI-only task, no schema change required.

The basemap and library CDN dependency is already tracked as an open decision
in `DECISIONS.md` and blocks water testing independently of this list.

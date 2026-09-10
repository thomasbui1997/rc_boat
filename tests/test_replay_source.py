import json
from pathlib import Path

import pytest

from src.telemetry.replay_source import ReplaySource


def _write_ndjson(path: Path, records: list) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record))
            handle.write("\n")


async def test_replays_records_in_order(tmp_path):
    records = [
        {
            "lat": 42.1,
            "lon": -71.1,
            "timestamp_utc": "2026-09-01T21:54:40+00:00",
            "position_accuracy_m": 8.85,
            "satellites_used": 5,
            "fix_quality": 1,
        },
        {
            "lat": 42.2,
            "lon": -71.2,
            "timestamp_utc": "2026-09-01T21:54:41+00:00",
            "position_accuracy_m": 5.5,
            "satellites_used": 8,
            "fix_quality": 1,
        },
    ]
    ndjson_path = tmp_path / "session.ndjson"
    _write_ndjson(ndjson_path, records)

    source = ReplaySource(ndjson_path, realtime=False)
    collected = [fix async for fix in source]

    assert len(collected) == 2
    assert collected[0].lat == 42.1
    assert collected[1].lat == 42.2
    assert collected[0].hdop == pytest.approx(1.77)


async def test_replays_a_no_fix_record_without_crashing(tmp_path):
    records = [
        {
            "lat": None,
            "lon": None,
            "timestamp_utc": "2026-09-01T21:54:40+00:00",
            "position_accuracy_m": None,
            "satellites_used": 0,
            "fix_quality": 0,
        },
    ]
    ndjson_path = tmp_path / "session.ndjson"
    _write_ndjson(ndjson_path, records)

    source = ReplaySource(ndjson_path, realtime=False)
    collected = [fix async for fix in source]

    assert len(collected) == 1
    assert collected[0].lat is None
    assert collected[0].hdop is None
    assert collected[0].fix_quality == 0

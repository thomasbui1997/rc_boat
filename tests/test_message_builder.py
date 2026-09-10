import pytest

from src.telemetry.fix import Fix
from src.telemetry.message_builder import build_message
from src.telemetry.schema import SCHEMA_VERSION


def _sample_fix() -> Fix:
    return Fix(
        lat=42.139617,
        lon=-71.096421,
        timestamp_utc="2026-09-01T21:54:40+00:00",
        hdop=1.77,
        satellites_used=8,
        fix_quality=1,
    )


def _no_fix() -> Fix:
    return Fix(
        lat=None,
        lon=None,
        timestamp_utc="2026-09-01T21:54:41+00:00",
        hdop=None,
        satellites_used=0,
        fix_quality=0,
    )


def test_build_message_shape():
    message = build_message(
        _sample_fix(), sequence=42, link_quality_pct=72, session_id="abc123", source="gps"
    )
    assert message == {
        "schema_version": SCHEMA_VERSION,
        "session_id": "abc123",
        "source": "gps",
        "sequence": 42,
        "timestamp_utc": "2026-09-01T21:54:40+00:00",
        "lat": 42.139617,
        "lon": -71.096421,
        "position_accuracy_m": pytest.approx(8.85),
        "satellites_used": 8,
        "fix_quality": 1,
        "link_quality_pct": 72,
        "battery_status": None,
    }


def test_build_message_defaults_source_to_gps():
    message = build_message(_sample_fix(), sequence=1, link_quality_pct=72, session_id="abc123")
    assert message["source"] == "gps"


def test_build_message_no_fix_has_null_position_fields():
    message = build_message(
        _no_fix(), sequence=1, link_quality_pct=None, session_id="abc123", source="gps"
    )
    assert message["lat"] is None
    assert message["lon"] is None
    assert message["position_accuracy_m"] is None
    assert message["fix_quality"] == 0
    assert message["link_quality_pct"] is None

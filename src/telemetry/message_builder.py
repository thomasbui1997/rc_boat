from typing import Optional

from src.telemetry.fix import Fix
from src.telemetry.schema import SCHEMA_VERSION, accuracy_from_hdop


def build_message(
    fix: Fix,
    sequence: int,
    link_quality_pct: Optional[int],
    session_id: str,
    source: str = "gps",
) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "session_id": session_id,
        "source": source,
        "sequence": sequence,
        "timestamp_utc": fix.timestamp_utc,
        "lat": fix.lat,
        "lon": fix.lon,
        "position_accuracy_m": accuracy_from_hdop(fix.hdop) if fix.hdop is not None else None,
        "satellites_used": fix.satellites_used,
        "fix_quality": fix.fix_quality,
        "link_quality_pct": link_quality_pct,
        "battery_status": None,
    }

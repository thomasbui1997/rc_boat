import re
import subprocess
from typing import Optional

_SIGNAL_PATTERN = re.compile(r"signal:\s*(-?\d+)\s*dBm")
_MIN_DBM = -90
_MAX_DBM = -30


def parse_signal_dbm(iw_link_output: str) -> Optional[int]:
    match = _SIGNAL_PATTERN.search(iw_link_output)
    if match is None:
        return None
    return int(match.group(1))


def dbm_to_percent(signal_dbm: int) -> int:
    clamped = max(_MIN_DBM, min(_MAX_DBM, signal_dbm))
    return round((clamped - _MIN_DBM) / (_MAX_DBM - _MIN_DBM) * 100)


def read_link_quality_pct(interface: str = "wlan0") -> Optional[int]:
    # link_quality_pct is nullable: None means the measurement itself
    # failed (missing `iw`, timeout, no parseable signal line), which is a
    # different situation from a measured-but-very-weak 0%.
    try:
        result = subprocess.run(
            ["iw", "dev", interface, "link"],
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    signal_dbm = parse_signal_dbm(result.stdout)
    if signal_dbm is None:
        return None
    return dbm_to_percent(signal_dbm)

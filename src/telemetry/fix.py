from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Fix:
    lat: Optional[float]
    lon: Optional[float]
    timestamp_utc: str
    hdop: Optional[float]
    satellites_used: int
    fix_quality: int

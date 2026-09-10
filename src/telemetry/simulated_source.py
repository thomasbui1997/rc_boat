import asyncio
import math
from datetime import datetime, timezone
from typing import AsyncIterator

from src.telemetry.fix import Fix
from src.telemetry.source import LocationSource

_LOOP_RADIUS_DEG = 0.0015
_LOOP_PERIOD_S = 60.0


class SimulatedSource(LocationSource):
    def __init__(
        self,
        center_lat: float = 42.1396,
        center_lon: float = -71.0964,
        interval_s: float = 1.0,
    ):
        self._center_lat = center_lat
        self._center_lon = center_lon
        self._interval_s = interval_s

    async def __aiter__(self) -> AsyncIterator[Fix]:
        elapsed_s = 0.0
        while True:
            angle = 2 * math.pi * (elapsed_s % _LOOP_PERIOD_S) / _LOOP_PERIOD_S
            yield Fix(
                lat=self._center_lat + _LOOP_RADIUS_DEG * math.sin(angle),
                lon=self._center_lon + _LOOP_RADIUS_DEG * math.cos(angle),
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
                hdop=1.5,
                satellites_used=8,
                fix_quality=1,
            )
            elapsed_s += self._interval_s
            await asyncio.sleep(self._interval_s)

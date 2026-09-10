import asyncio
from datetime import datetime, timezone
from typing import AsyncIterator, Callable, Optional

import pynmea2
import serial

from src.telemetry.fix import Fix
from src.telemetry.source import LocationSource

_ClockFn = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class NmeaStreamParser:
    def __init__(self, clock: _ClockFn = _utc_now):
        self._clock = clock
        self._latest_date = None

    def parse_line(self, line: str) -> Optional[Fix]:
        try:
            msg = pynmea2.parse(line)
        except pynmea2.ParseError:
            return None

        if msg.sentence_type == "RMC" and getattr(msg, "status", None) == "A":
            self._latest_date = msg.datestamp

        if msg.sentence_type != "GGA":
            return None

        fix_quality = int(msg.gps_qual) if msg.gps_qual is not None else 0
        if not msg.timestamp:
            # Without even a time-of-day we can't build a timestamp at all.
            return None

        if self._latest_date is not None:
            timestamp_utc = datetime.combine(
                self._latest_date, msg.timestamp, tzinfo=timezone.utc
            ).isoformat()
        else:
            timestamp_utc = self._clock().isoformat()

        if fix_quality == 0:
            # No fix yet: pynmea2 defaults empty lat/lon to 0.0, which would
            # otherwise look like a real position (Gulf of Guinea) instead
            # of "no data". Still emit a message so the shore app can tell
            # "no fix" apart from "link lost" instead of the sender going
            # silent.
            return Fix(
                lat=None,
                lon=None,
                timestamp_utc=timestamp_utc,
                hdop=None,
                satellites_used=int(msg.num_sats) if msg.num_sats else 0,
                fix_quality=0,
            )

        return Fix(
            lat=msg.latitude,
            lon=msg.longitude,
            timestamp_utc=timestamp_utc,
            hdop=float(msg.horizontal_dil) if msg.horizontal_dil else 0.0,
            satellites_used=int(msg.num_sats) if msg.num_sats else 0,
            fix_quality=fix_quality,
        )


class GpsSerialSource(LocationSource):
    def __init__(self, port: str, baud_rate: int = 9600):
        self._port = port
        self._baud_rate = baud_rate
        self._parser = NmeaStreamParser()

    async def __aiter__(self) -> AsyncIterator[Fix]:
        connection = serial.Serial(self._port, self._baud_rate, timeout=2)
        try:
            while True:
                raw_line = await asyncio.to_thread(connection.readline)
                line = raw_line.decode("ascii", errors="ignore").strip()
                if not line:
                    continue
                fix = self._parser.parse_line(line)
                if fix is not None:
                    yield fix
        finally:
            connection.close()

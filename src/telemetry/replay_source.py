import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator

from src.telemetry.fix import Fix
from src.telemetry.schema import hdop_from_accuracy
from src.telemetry.source import LocationSource


class ReplaySource(LocationSource):
    def __init__(self, path: Path, realtime: bool = True):
        self._path = path
        self._realtime = realtime

    async def __aiter__(self) -> AsyncIterator[Fix]:
        previous_timestamp = None
        with open(self._path, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                accuracy_m = record.get("position_accuracy_m")
                fix = Fix(
                    lat=record.get("lat"),
                    lon=record.get("lon"),
                    timestamp_utc=record["timestamp_utc"],
                    hdop=hdop_from_accuracy(accuracy_m) if accuracy_m is not None else None,
                    satellites_used=record["satellites_used"],
                    fix_quality=record["fix_quality"],
                )
                current_timestamp = datetime.fromisoformat(fix.timestamp_utc)
                if self._realtime and previous_timestamp is not None:
                    gap_s = (current_timestamp - previous_timestamp).total_seconds()
                    if gap_s > 0:
                        await asyncio.sleep(gap_s)
                previous_timestamp = current_timestamp
                yield fix

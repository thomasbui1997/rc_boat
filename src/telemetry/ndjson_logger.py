import json
from datetime import datetime, timezone
from pathlib import Path


class NdjsonLogger:
    def __init__(self, data_dir: Path):
        data_dir.mkdir(parents=True, exist_ok=True)
        session_start = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.path = data_dir / f"session_{session_start}.ndjson"
        self._file = open(self.path, "a", encoding="utf-8")

    def write(self, message: dict) -> None:
        self._file.write(json.dumps(message))
        self._file.write("\n")
        self._file.flush()

    def close(self) -> None:
        self._file.close()

    def __enter__(self) -> "NdjsonLogger":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

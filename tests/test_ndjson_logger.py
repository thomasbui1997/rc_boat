import json

from src.telemetry.ndjson_logger import NdjsonLogger


def test_writes_are_valid_json_lines(tmp_path):
    with NdjsonLogger(tmp_path) as logger:
        logger.write({"a": 1})
        logger.write({"a": 2})

    written_lines = logger.path.read_text().splitlines()
    assert [json.loads(line) for line in written_lines] == [{"a": 1}, {"a": 2}]


def test_filename_lives_inside_data_dir(tmp_path):
    with NdjsonLogger(tmp_path) as logger:
        assert logger.path.parent == tmp_path
        assert logger.path.name.startswith("session_")
        assert logger.path.suffix == ".ndjson"

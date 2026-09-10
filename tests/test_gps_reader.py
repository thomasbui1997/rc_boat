from datetime import datetime, timezone
from pathlib import Path

from src.telemetry.gps_reader import NmeaStreamParser

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_nmea.txt"


def _fixture_lines():
    return FIXTURE_PATH.read_text().splitlines()


def test_rmc_sets_date_and_gga_uses_it():
    parser = NmeaStreamParser()
    lines = _fixture_lines()

    rmc_result = parser.parse_line(lines[0])
    assert rmc_result is None

    gga_result = parser.parse_line(lines[1])
    assert gga_result is not None
    assert gga_result.timestamp_utc == "2026-09-01T21:54:40+00:00"
    assert gga_result.satellites_used == 5
    assert gga_result.fix_quality == 1


def test_handles_gngga_talker_prefix():
    parser = NmeaStreamParser()
    lines = _fixture_lines()
    parser.parse_line(lines[0])
    parser.parse_line(lines[1])
    gngga_result = parser.parse_line(lines[2])
    assert gngga_result is not None
    assert gngga_result.satellites_used == 8


def test_no_fix_line_yields_a_positionless_fix():
    parser = NmeaStreamParser()
    lines = _fixture_lines()
    for line in lines[:3]:
        parser.parse_line(line)
    no_fix_result = parser.parse_line(lines[3])
    assert no_fix_result is not None
    assert no_fix_result.fix_quality == 0
    assert no_fix_result.lat is None
    assert no_fix_result.lon is None
    assert no_fix_result.hdop is None
    assert no_fix_result.timestamp_utc == "2026-09-01T21:54:30+00:00"


def test_garbled_line_yields_none():
    parser = NmeaStreamParser()
    assert parser.parse_line("THIS IS NOT A VALID NMEA SENTENCE") is None


def test_falls_back_to_injected_clock_before_any_rmc_seen():
    fixed_now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    parser = NmeaStreamParser(clock=lambda: fixed_now)
    gga_line = "$GPGGA,215440.00,4208.37701,N,07105.78527,W,1,05,1.77,98.8,M,-33.3,M,,*5B"
    fix = parser.parse_line(gga_line)
    assert fix.timestamp_utc == fixed_now.isoformat()

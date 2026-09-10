from unittest.mock import MagicMock, patch

from src.telemetry.link_quality import (
    dbm_to_percent,
    parse_signal_dbm,
    read_link_quality_pct,
)

SAMPLE_IW_OUTPUT = """Connected to aa:bb:cc:dd:ee:ff (on wlan0)
        SSID: OpalTravelRouter
        freq: 2437
        signal: -58 dBm
        tx bitrate: 72.2 MBit/s
"""


def test_parse_signal_dbm_extracts_value():
    assert parse_signal_dbm(SAMPLE_IW_OUTPUT) == -58


def test_parse_signal_dbm_missing_returns_none():
    assert parse_signal_dbm("no signal info here") is None


def test_dbm_to_percent_clamps_and_scales():
    assert dbm_to_percent(-30) == 100
    assert dbm_to_percent(-90) == 0
    assert dbm_to_percent(-20) == 100
    assert dbm_to_percent(-100) == 0
    assert dbm_to_percent(-60) == 50


def test_read_link_quality_pct_uses_subprocess_output():
    fake_result = MagicMock(stdout=SAMPLE_IW_OUTPUT)
    with patch("src.telemetry.link_quality.subprocess.run", return_value=fake_result):
        assert read_link_quality_pct("wlan0") == dbm_to_percent(-58)


def test_read_link_quality_pct_returns_none_when_iw_unavailable():
    with patch("src.telemetry.link_quality.subprocess.run", side_effect=OSError):
        assert read_link_quality_pct("wlan0") is None


def test_read_link_quality_pct_returns_none_when_signal_unparseable():
    fake_result = MagicMock(stdout="no signal info here")
    with patch("src.telemetry.link_quality.subprocess.run", return_value=fake_result):
        assert read_link_quality_pct("wlan0") is None

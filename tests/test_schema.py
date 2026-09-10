import pytest

from src.telemetry.schema import accuracy_from_hdop, hdop_from_accuracy


def test_accuracy_from_hdop_typical():
    assert accuracy_from_hdop(1.77) == pytest.approx(8.85)


def test_accuracy_from_hdop_zero():
    assert accuracy_from_hdop(0.0) == 0.0


def test_hdop_from_accuracy_is_inverse():
    assert hdop_from_accuracy(accuracy_from_hdop(2.3)) == pytest.approx(2.3)

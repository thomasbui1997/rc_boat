SCHEMA_VERSION = 2

_HDOP_TO_METERS_FACTOR = 5.0


def accuracy_from_hdop(hdop: float) -> float:
    return hdop * _HDOP_TO_METERS_FACTOR


def hdop_from_accuracy(accuracy_m: float) -> float:
    return accuracy_m / _HDOP_TO_METERS_FACTOR

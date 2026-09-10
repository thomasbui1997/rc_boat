from src.telemetry.simulated_source import SimulatedSource


async def test_yields_fixes_within_expected_bounds():
    source = SimulatedSource(center_lat=42.0, center_lon=-71.0, interval_s=0.0)
    collected = []
    async for fix in source:
        collected.append(fix)
        if len(collected) == 5:
            break

    assert len(collected) == 5
    for fix in collected:
        assert 41.99 < fix.lat < 42.01
        assert -71.01 < fix.lon < -70.99
        assert fix.fix_quality == 1
        assert fix.satellites_used > 0

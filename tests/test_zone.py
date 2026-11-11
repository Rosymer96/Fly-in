import pytest

from models import Zone, ZoneType


def make_zone(max_drones: int = 2, unlimited: bool = False) -> Zone:
    """Build a normal zone for the tests."""
    return Zone(
        name="z",
        x=0,
        y=0,
        zone_type=ZoneType.NORMAL,
        color=None,
        max_drones=max_drones,
        unlimited_capacity=unlimited,
    )


def test_new_zone_is_empty() -> None:
    zone = make_zone()
    assert zone.occupancy == 0
    assert zone.capacity == 2
    assert zone.has_capacity()


def test_enter_increases_occupancy() -> None:
    zone = make_zone()
    zone.enter(1)
    assert zone.occupancy == 1
    assert zone.has_capacity()


def test_enter_rejects_when_full() -> None:
    zone = make_zone(max_drones=1)
    zone.enter(1)
    assert not zone.has_capacity()
    with pytest.raises(ValueError):
        zone.enter(2)
    assert zone.occupancy == 1


def test_leave_frees_capacity() -> None:
    zone = make_zone(max_drones=1)
    zone.enter(1)
    zone.leave(1)
    assert zone.occupancy == 0
    assert zone.has_capacity()


def test_leave_unknown_drone_is_ignored() -> None:
    zone = make_zone()
    zone.leave(99)
    assert zone.occupancy == 0


def test_unlimited_zone_has_no_capacity_limit() -> None:
    zone = make_zone(max_drones=1, unlimited=True)
    assert zone.capacity is None
    for drone_id in range(50):
        zone.enter(drone_id)
    assert zone.occupancy == 50
    assert zone.has_capacity()

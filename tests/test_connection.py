import pytest

from models import CapacityResource, Connection, Zone, ZoneType


def make_zone(name: str) -> Zone:
    """Build a normal zone for the tests."""
    return Zone(
        name=name,
        x=0,
        y=0,
        zone_type=ZoneType.NORMAL,
        color=None,
        max_drones=1,
    )


def make_connection(capacity: int = 2) -> Connection:
    """Build a connection between zones 'a' and 'b'."""
    return Connection(
        zone_a=make_zone("a"),
        zone_b=make_zone("b"),
        max_link_capacity=capacity,
    )


def test_zone_and_connection_share_base_class() -> None:
    assert isinstance(make_zone("a"), CapacityResource)
    assert isinstance(make_connection(), CapacityResource)


def test_new_connection_is_empty() -> None:
    connection = make_connection()
    assert connection.occupancy == 0
    assert connection.capacity == 2
    assert connection.has_capacity()


def test_enter_rejects_when_full() -> None:
    connection = make_connection(capacity=1)
    connection.enter(1)
    assert not connection.has_capacity()
    with pytest.raises(ValueError, match="connection a-b is full"):
        connection.enter(2)
    assert connection.occupancy == 1


def test_leave_frees_capacity() -> None:
    connection = make_connection(capacity=1)
    connection.enter(1)
    connection.leave(1)
    assert connection.occupancy == 0
    assert connection.has_capacity()


def test_other_returns_opposite_endpoint() -> None:
    connection = make_connection()
    assert connection.other(connection.zone_a) is connection.zone_b
    assert connection.other(connection.zone_b) is connection.zone_a


def test_other_rejects_foreign_zone() -> None:
    connection = make_connection()
    with pytest.raises(ValueError):
        connection.other(make_zone("c"))

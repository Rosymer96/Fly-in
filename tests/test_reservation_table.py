import pytest

from models import Connection, Zone, ZoneType
from pathfinding import Move, Path, ReservationTable


def make_zone(
    name: str,
    zone_type: ZoneType = ZoneType.NORMAL,
    max_drones: int = 1,
    unlimited: bool = False,
) -> Zone:
    return Zone(name, 0, 0, zone_type, None, max_drones, unlimited)


def make_link(a: Zone, b: Zone, capacity: int = 1) -> Connection:
    return Connection(a, b, capacity)


def test_unreserved_usage_is_zero() -> None:
    a, b = make_zone("a"), make_zone("b")
    table = ReservationTable()
    assert table.zone_usage(a, 5) == 0
    assert table.link_usage(make_link(a, b), 5) == 0


def test_link_counts_both_directions_together() -> None:
    a, b = make_zone("a"), make_zone("b")
    table = ReservationTable()
    table.reserve_link(make_link(a, b), 1)
    assert table.link_usage(make_link(b, a), 1) == 1
    assert not table.is_link_free(make_link(b, a), 1)


def test_opposite_directions_fit_with_capacity_two() -> None:
    a, b = make_zone("a"), make_zone("b")
    table = ReservationTable()
    table.reserve_link(make_link(a, b, 2), 1)
    table.reserve_link(make_link(b, a, 2), 1)
    assert table.link_usage(make_link(a, b, 2), 1) == 2


def test_unlimited_zone_never_fills() -> None:
    start = make_zone("s", unlimited=True)
    table = ReservationTable()
    for _ in range(50):
        table.reserve_zone(start, 0)
    assert table.is_zone_free(start, 0)
    assert table.zone_usage(start, 0) == 50


def test_zone_over_capacity_raises() -> None:
    a = make_zone("a", max_drones=2)
    table = ReservationTable()
    table.reserve_zone(a, 3)
    table.reserve_zone(a, 3)
    with pytest.raises(ValueError):
        table.reserve_zone(a, 3)


def test_link_over_capacity_raises() -> None:
    link = make_link(make_zone("a"), make_zone("b"))
    table = ReservationTable()
    table.reserve_link(link, 2)
    with pytest.raises(ValueError):
        table.reserve_link(link, 2)


def test_turns_are_independent() -> None:
    a = make_zone("a")
    table = ReservationTable()
    table.reserve_zone(a, 1)
    assert table.is_zone_free(a, 2)


def test_leaving_frees_the_zone_for_the_next_turn() -> None:
    # D1 stays in m at turns 1 and 2 and leaves in turn 3: D2 may be
    # in m at the end of turn 3.
    m = make_zone("m")
    table = ReservationTable()
    table.reserve_zone(m, 1)
    table.reserve_zone(m, 2)
    assert table.is_zone_free(m, 3)


def test_normal_move_reserves_one_turn() -> None:
    a, b = make_zone("a", unlimited=True), make_zone("b")
    link = make_link(a, b)
    table = ReservationTable()
    table.reserve_move(Move(link, b, 4))
    assert table.link_usage(link, 4) == 1
    assert table.link_usage(link, 5) == 0
    assert table.zone_usage(b, 4) == 1


def test_restricted_move_reserves_link_two_turns_zone_once() -> None:
    a = make_zone("a", unlimited=True)
    b = make_zone("b", ZoneType.RESTRICTED)
    link = make_link(a, b)
    table = ReservationTable()
    table.reserve_move(Move(link, b, 1))
    assert [table.link_usage(link, t) for t in range(0, 4)] == [0, 1, 1, 0]
    assert [table.zone_usage(b, t) for t in range(0, 4)] == [0, 0, 1, 0]


def test_restricted_link_stays_busy_during_transit() -> None:
    a = make_zone("a", unlimited=True)
    b = make_zone("b", ZoneType.RESTRICTED, max_drones=2)
    link = make_link(a, b)
    table = ReservationTable()
    table.reserve_move(Move(link, b, 1))
    assert not table.is_move_free(Move(link, b, 2))
    assert table.is_move_free(Move(link, b, 3))


def test_failed_move_changes_nothing() -> None:
    a = make_zone("a", unlimited=True)
    b = make_zone("b", ZoneType.RESTRICTED)
    link = make_link(a, b)
    table = ReservationTable()
    table.reserve_move(Move(link, b, 1))
    with pytest.raises(ValueError):
        table.reserve_move(Move(link, b, 2))
    assert [table.link_usage(link, t) for t in range(0, 4)] == [0, 1, 1, 0]


def test_blocked_destination_is_rejected() -> None:
    a = make_zone("a")
    wall = make_zone("w", ZoneType.BLOCKED)
    with pytest.raises(ValueError):
        Move(make_link(a, wall), wall, 1)


def test_move_must_end_in_an_endpoint() -> None:
    a, b, c = make_zone("a"), make_zone("b"), make_zone("c")
    with pytest.raises(ValueError):
        Move(make_link(a, b), c, 1)


def test_move_cannot_start_at_turn_zero() -> None:
    a, b = make_zone("a"), make_zone("b")
    with pytest.raises(ValueError):
        Move(make_link(a, b), b, 0)


def test_path_waits_are_deduced_from_gaps() -> None:
    s = make_zone("s", unlimited=True)
    m = make_zone("m")
    e = make_zone("e", unlimited=True)
    path = Path([
        Move(make_link(s, m), m, 2),
        Move(make_link(m, e), e, 5),
    ])
    assert [(z.name, t) for z, t in path.waits] == [
        ("s", 0), ("s", 1), ("m", 3), ("m", 4),
    ]
    assert path.arrival_turn == 5


def test_path_rejects_a_broken_chain() -> None:
    a, b, c, d = (make_zone(n) for n in "abcd")
    with pytest.raises(ValueError):
        Path([Move(make_link(a, b), b, 1), Move(make_link(c, d), d, 2)])


def test_path_rejects_overlapping_moves() -> None:
    a = make_zone("a", unlimited=True)
    b = make_zone("b", ZoneType.RESTRICTED)
    c = make_zone("c")
    with pytest.raises(ValueError):
        Path([Move(make_link(a, b), b, 1), Move(make_link(b, c), c, 2)])


def test_empty_path_is_rejected() -> None:
    with pytest.raises(ValueError):
        Path([])


def test_reserve_path_reserves_moves_and_waits() -> None:
    s = make_zone("s", unlimited=True)
    m = make_zone("m")
    e = make_zone("e", unlimited=True)
    table = ReservationTable()
    table.reserve_path(Path([
        Move(make_link(s, m), m, 1),
        Move(make_link(m, e), e, 4),
    ]))
    assert [table.zone_usage(m, t) for t in range(0, 5)] == [0, 1, 1, 1, 0]
    assert table.zone_usage(e, 4) == 1


def test_failed_reserve_path_changes_nothing() -> None:
    s = make_zone("s", unlimited=True)
    m = make_zone("m")
    e = make_zone("e", unlimited=True)
    link_sm, link_me = make_link(s, m), make_link(m, e)
    table = ReservationTable()
    table.reserve_link(link_me, 4)  # blocks the last move of the path
    with pytest.raises(ValueError):
        table.reserve_path(Path([Move(link_sm, m, 1), Move(link_me, e, 4)]))
    assert table.link_usage(link_sm, 1) == 0
    assert table.zone_usage(m, 1) == 0
    assert table.zone_usage(s, 0) == 0


def test_two_drones_share_a_corridor_one_turn_apart() -> None:
    s = make_zone("s", unlimited=True)
    m = make_zone("m")
    e = make_zone("e", unlimited=True)
    link_sm, link_me = make_link(s, m), make_link(m, e)
    table = ReservationTable()
    table.reserve_path(Path([Move(link_sm, m, 1), Move(link_me, e, 2)]))
    table.reserve_path(Path([Move(link_sm, m, 2), Move(link_me, e, 3)]))
    assert table.zone_usage(m, 1) == 1
    assert table.zone_usage(m, 2) == 1
    with pytest.raises(ValueError):
        table.reserve_path(Path([Move(link_sm, m, 2), Move(link_me, e, 4)]))

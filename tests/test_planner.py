from pathlib import Path as FilePath

import pytest

from models import Graph
from parser import MapParser
from pathfinding import Path, Planner, PlanningError


def build(tmp_path: FilePath, nb_drones: int, body: str) -> Graph:
    """Write a map with the given drones and body, and parse it."""
    map_file = tmp_path / "map.txt"
    map_file.write_text(f"nb_drones: {nb_drones}\n" + body)
    graph, _ = MapParser().parse(str(map_file))
    return graph


def arrivals(paths: list[Path]) -> list[int]:
    return [path.arrival_turn for path in paths]


LINE = (
    "start_hub: s 0 0\n"
    "hub: m 1 0\n"
    "end_hub: e 2 0\n"
    "connection: s-m\n"
    "connection: m-e\n"
)


def test_single_drone_on_a_line(tmp_path: FilePath) -> None:
    paths = Planner(build(tmp_path, 1, LINE), 1).plan_all()
    assert arrivals(paths) == [2]
    assert [m.destination.name for m in paths[0].moves] == ["m", "e"]


def test_corridor_with_capacity_one_pipelines_drones(
    tmp_path: FilePath,
) -> None:
    paths = Planner(build(tmp_path, 3, LINE), 3).plan_all()
    assert arrivals(paths) == [2, 3, 4]


def test_long_corridor_many_drones(tmp_path: FilePath) -> None:
    body = (
        "start_hub: s 0 0\n"
        "hub: a 1 0\n"
        "hub: b 2 0\n"
        "end_hub: e 3 0\n"
        "connection: s-a\n"
        "connection: a-b\n"
        "connection: b-e\n"
    )
    paths = Planner(build(tmp_path, 10, body), 10).plan_all()
    assert max(arrivals(paths)) == 12


def test_drones_spread_over_parallel_routes(tmp_path: FilePath) -> None:
    body = (
        "start_hub: s 0 0\n"
        "hub: a 1 0\n"
        "hub: b 1 1\n"
        "end_hub: e 2 0\n"
        "connection: s-a\n"
        "connection: s-b\n"
        "connection: a-e\n"
        "connection: b-e\n"
    )
    paths = Planner(build(tmp_path, 2, body), 2).plan_all()
    assert arrivals(paths) == [2, 2]
    assert {p.moves[0].destination.name for p in paths} == {"a", "b"}


def test_restricted_zone_takes_two_turns(tmp_path: FilePath) -> None:
    body = (
        "start_hub: s 0 0\n"
        "hub: r 1 0 [zone=restricted]\n"
        "end_hub: e 2 0\n"
        "connection: s-r\n"
        "connection: r-e\n"
    )
    paths = Planner(build(tmp_path, 1, body), 1).plan_all()
    assert arrivals(paths) == [3]


def test_detour_beats_restricted_shortcut(tmp_path: FilePath) -> None:
    body = (
        "start_hub: s 0 0\n"
        "hub: r 1 0 [zone=restricted]\n"
        "hub: a 1 1\n"
        "end_hub: e 2 0\n"
        "connection: s-r\n"
        "connection: r-e\n"
        "connection: s-a\n"
        "connection: a-e\n"
    )
    paths = Planner(build(tmp_path, 1, body), 1).plan_all()
    assert arrivals(paths) == [2]
    assert paths[0].moves[0].destination.name == "a"


def test_priority_zone_is_preferred_on_a_tie(tmp_path: FilePath) -> None:
    body = (
        "start_hub: s 0 0\n"
        "hub: n 1 0\n"
        "hub: p 1 1 [zone=priority]\n"
        "end_hub: e 2 0\n"
        "connection: s-n\n"
        "connection: s-p\n"
        "connection: n-e\n"
        "connection: p-e\n"
    )
    paths = Planner(build(tmp_path, 1, body), 1).plan_all()
    assert paths[0].moves[0].destination.name == "p"


def test_zone_capacity_is_respected(tmp_path: FilePath) -> None:
    body = (
        "start_hub: s 0 0\n"
        "hub: m 1 0 [max_drones=2]\n"
        "end_hub: e 2 0\n"
        "connection: s-m [max_link_capacity=2]\n"
        "connection: m-e [max_link_capacity=2]\n"
    )
    paths = Planner(build(tmp_path, 4, body), 4).plan_all()
    assert arrivals(paths) == [2, 2, 3, 3]


def test_blocked_zone_is_never_used(tmp_path: FilePath) -> None:
    body = (
        "start_hub: s 0 0\n"
        "hub: w 1 0 [zone=blocked]\n"
        "hub: a 1 1\n"
        "end_hub: e 2 0\n"
        "connection: s-w\n"
        "connection: w-e\n"
        "connection: s-a\n"
        "connection: a-e\n"
    )
    paths = Planner(build(tmp_path, 2, body), 2).plan_all()
    for path in paths:
        assert all(m.destination.name != "w" for m in path.moves)


def test_disconnected_graph_gives_a_clear_error(tmp_path: FilePath) -> None:
    body = (
        "start_hub: s 0 0\n"
        "hub: m 1 0\n"
        "end_hub: e 5 0\n"
        "connection: s-m\n"
    )
    with pytest.raises(PlanningError, match="no route"):
        Planner(build(tmp_path, 1, body), 1).plan_all()


def test_only_route_blocked_gives_a_clear_error(tmp_path: FilePath) -> None:
    body = (
        "start_hub: s 0 0\n"
        "hub: w 1 0 [zone=blocked]\n"
        "end_hub: e 2 0\n"
        "connection: s-w\n"
        "connection: w-e\n"
    )
    with pytest.raises(PlanningError, match="no route"):
        Planner(build(tmp_path, 1, body), 1).plan_all()


def test_plan_drone_reserves_nothing(tmp_path: FilePath) -> None:
    graph = build(tmp_path, 1, LINE)
    planner = Planner(graph, 1)
    path = planner.plan_drone()
    assert path is not None
    assert planner.table.zone_usage(graph.zones["m"], 1) == 0


def test_plan_all_can_be_repeated(tmp_path: FilePath) -> None:
    planner = Planner(build(tmp_path, 3, LINE), 3)
    assert arrivals(planner.plan_all()) == arrivals(planner.plan_all())


def test_table_shows_the_plan(tmp_path: FilePath) -> None:
    graph = build(tmp_path, 2, LINE)
    planner = Planner(graph, 2)
    planner.plan_all()
    mid = graph.zones["m"]
    assert planner.table.zone_usage(mid, 1) == 1
    assert planner.table.zone_usage(mid, 2) == 1
    assert planner.table.zone_usage(mid, 3) == 0

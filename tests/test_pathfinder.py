from pathlib import Path

from models import Graph
from parser import MapParser
from pathfinding.pathfinder import Pathfinder


def build_graph(tmp_path: Path, body: str) -> Graph:
    """Write a map with 1 drone and the given body, and parse it."""
    map_file = tmp_path / "map.txt"
    map_file.write_text("nb_drones: 1\n" + body)
    graph, _ = MapParser().parse(str(map_file))
    return graph


def test_hops_on_a_line(tmp_path: Path) -> None:
    graph = build_graph(tmp_path, (
        "start_hub: a 0 0\n"
        "hub: b 1 0\n"
        "end_hub: c 2 0\n"
        "connection: a-b\n"
        "connection: b-c\n"
    ))
    hops = Pathfinder(graph).hops_from(graph.start)
    assert hops == {"a": 0, "b": 1, "c": 2}


def test_shortest_route_is_chosen(tmp_path: Path) -> None:
    graph = build_graph(tmp_path, (
        "start_hub: a 0 0\n"
        "hub: b 1 0\n"
        "hub: c 2 0\n"
        "end_hub: d 3 0\n"
        "connection: a-b\n"
        "connection: b-c\n"
        "connection: c-d\n"
        "connection: a-d\n"
    ))
    assert Pathfinder(graph).hops_from(graph.start)["d"] == 1


def test_cycle_terminates(tmp_path: Path) -> None:
    graph = build_graph(tmp_path, (
        "start_hub: a 0 0\n"
        "hub: b 1 0\n"
        "end_hub: c 2 0\n"
        "connection: a-b\n"
        "connection: b-c\n"
        "connection: c-a\n"
    ))
    assert Pathfinder(graph).hops_from(graph.start) == {
        "a": 0, "b": 1, "c": 1,
    }


def test_blocked_zone_is_not_crossed(tmp_path: Path) -> None:
    graph = build_graph(tmp_path, (
        "start_hub: a 0 0\n"
        "hub: b 1 0 [zone=blocked]\n"
        "end_hub: c 2 0\n"
        "connection: a-b\n"
        "connection: b-c\n"
    ))
    hops = Pathfinder(graph).hops_from(graph.start)
    assert graph.end.name not in hops
    assert "b" not in hops


def test_disconnected_zone_is_missing(tmp_path: Path) -> None:
    graph = build_graph(tmp_path, (
        "start_hub: a 0 0\n"
        "hub: b 1 0\n"
        "end_hub: c 2 0\n"
        "connection: a-b\n"
    ))
    hops = Pathfinder(graph).hops_from(graph.end)
    assert hops == {"c": 0}
    assert graph.start.name not in hops

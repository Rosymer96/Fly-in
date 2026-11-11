from pathlib import Path

import pytest

from models import ZoneType
from parser import MapError, MapFileError, MapParser, ParserError


@pytest.fixture
def parser() -> MapParser:
    """A parser that already read the mandatory nb_drones first line."""
    p = MapParser()
    p._parse_line(1, "nb_drones: 1")
    return p


@pytest.fixture
def parser_with_zones() -> MapParser:
    """A parser that already has two zones defined, for connection tests."""
    p = MapParser()
    p._parse_line(1, "nb_drones: 1")
    p._parse_line(1, "hub: a 0 0")
    p._parse_line(2, "hub: b 1 0")
    return p


def test_parse_metadata_empty() -> None:
    parser = MapParser()
    assert parser._parse_metadata(1, "") == {}


def test_parse_metadata_multiple_keys() -> None:
    parser = MapParser()
    result = parser._parse_metadata(
        1,
        "zone=priority color=green max_drones=2"
    )
    assert result == {"zone": "priority", "color": "green", "max_drones": "2"}


def test_parse_metadata_malformed_token_raises() -> None:
    parser = MapParser()
    with pytest.raises(ParserError):
        parser._parse_metadata(1, "zone")  # falta el '='


# Valid cases


def test_parse_zone_hub_minimal(parser: MapParser) -> None:
    parser._parse_line(1, "hub: roof1 3 4")
    zone = parser._zones["roof1"]
    assert zone.x == 3
    assert zone.y == 4
    assert zone.zone_type is ZoneType.NORMAL      # default
    assert zone.max_drones == 1                    # default
    assert zone.unlimited_capacity is False


def test_parse_zone_with_metadata(parser: MapParser) -> None:
    parser._parse_line(
        1, "hub: corridorA 4 3 [zone=priority color=green max_drones=2]"
    )
    zone = parser._zones["corridorA"]
    assert zone.zone_type is ZoneType.PRIORITY
    assert zone.color == "green"
    assert zone.max_drones == 2


def test_parse_start_hub_sets_unlimited_capacity(parser: MapParser) -> None:
    parser._parse_line(1, "start_hub: base 0 0")
    assert parser._start is not None
    assert parser._start.name == "base"
    assert parser._start.unlimited_capacity is True


def test_start_hub_max_drones_is_ignored_not_an_error(
    parser: MapParser
) -> None:
    # Per the subject: max_drones present on start_hub is ignored,
    # not a validation error.
    parser._parse_line(1, "start_hub: base 0 0 [max_drones=5]")
    assert parser._start is not None
    assert parser._start.unlimited_capacity is True


# Invalid cases
def test_duplicate_zone_name_raises(parser: MapParser) -> None:
    parser._parse_line(1, "hub: roof1 3 4")
    with pytest.raises(ParserError):
        parser._parse_line(2, "hub: roof1 5 5")


def test_duplicate_start_hub_raises(parser: MapParser) -> None:
    parser._parse_line(1, "start_hub: base 0 0")
    with pytest.raises(ParserError):
        parser._parse_line(2, "start_hub: other 1 1")


def test_duplicate_end_hub_raises(parser: MapParser) -> None:
    parser._parse_line(1, "end_hub: goal 10 10")
    with pytest.raises(ParserError):
        parser._parse_line(2, "end_hub: other 9 9")


def test_invalid_zone_type_raises(parser: MapParser) -> None:
    with pytest.raises(ParserError):
        parser._parse_line(1, "hub: roof1 3 4 [zone=nonexistent]")


@pytest.mark.parametrize("bad_value", ["0", "-1", "abc", "1.5"])
def test_non_positive_max_drones_raises(
    parser: MapParser, bad_value: str
) -> None:
    with pytest.raises(ParserError):
        parser._parse_line(1, f"hub: roof1 3 4 [max_drones={bad_value}]")


def test_zone_name_with_dash_raises(parser: MapParser) -> None:
    with pytest.raises(ParserError):
        parser._parse_line(1, "hub: roof-1 3 4")


def test_non_integer_coordinates_raises(parser: MapParser) -> None:
    with pytest.raises(ParserError):
        parser._parse_line(1, "hub: roof1 3.5 4")


def test_wrong_token_count_raises(parser: MapParser) -> None:
    with pytest.raises(ParserError):
        parser._parse_line(1, "hub: roof1 3")


@pytest.mark.parametrize("keyword", ["start_hub", "end_hub"])
def test_blocked_start_or_end_raises(
    parser: MapParser, keyword: str
) -> None:
    with pytest.raises(ParserError, match="cannot be a blocked zone"):
        parser._parse_line(2, f"{keyword}: base 0 0 [zone=blocked]")


VALID_MAP = (
    "nb_drones: 2\n"
    "start_hub: s 0 0\n"
    "end_hub: e 1 0\n"
    "connection: s-e\n"
)


def test_parser_can_be_reused(tmp_path: Path) -> None:
    first = tmp_path / "first.txt"
    first.write_text(VALID_MAP, encoding="utf-8")
    second = tmp_path / "second.txt"
    second.write_text(VALID_MAP.replace("2", "5", 1), encoding="utf-8")
    reused = MapParser()
    reused.parse(str(first))
    graph, nb_drones = reused.parse(str(second))
    assert nb_drones == 5
    assert len(graph.zones) == 2
    assert len(graph.connections) == 1


def test_missing_file_raises_map_file_error(tmp_path: Path) -> None:
    with pytest.raises(MapFileError, match="No such file"):
        MapParser().parse(str(tmp_path / "missing.txt"))


def test_directory_instead_of_file_raises_map_file_error(
    tmp_path: Path
) -> None:
    with pytest.raises(MapFileError, match="directory"):
        MapParser().parse(str(tmp_path))


def test_non_utf8_file_raises_map_file_error(tmp_path: Path) -> None:
    bad = tmp_path / "bad.txt"
    bad.write_bytes(b"nb_drones: 1\n\xff\xfe\n")
    with pytest.raises(MapFileError, match="UTF-8"):
        MapParser().parse(str(bad))


def test_both_errors_share_map_error_base(tmp_path: Path) -> None:
    with pytest.raises(MapError):
        MapParser().parse(str(tmp_path / "missing.txt"))
    with pytest.raises(MapError):
        MapParser()._parse_line(1, "hub: a 0 0")

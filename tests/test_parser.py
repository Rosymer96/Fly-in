# tests/test_parser.py
import pytest
from parser import MapParser, ParserError

# tests/test_parser.py
import pytest
from models import Zone, ZoneType


@pytest.fixture
def parser() -> MapParser:
    return MapParser()


@pytest.fixture
def parser_with_zones() -> MapParser:
    """A parser that already has two zones defined, for connection tests."""
    p = MapParser()
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

#Test validos

def test_parse_zone_hub_minimal(parser: MapParser) -> None:
    parser._parse_line(1, "hub: roof1 3 4")
    zone = parser._zones["roof1"]
    assert zone.x == 3
    assert zone.y == 4
    assert zone.zone_type is ZoneType.NORMAL      # default
    assert zone.max_drones == 1                    # default
    assert zone.unlimited_capacity is False


def test_parse_zone_with_metadata(parser: MapParser) -> None:
    parser._parse_line(1, "hub: corridorA 4 3 [zone=priority color=green max_drones=2]")
    zone = parser._zones["corridorA"]
    assert zone.zone_type is ZoneType.PRIORITY
    assert zone.color == "green"
    assert zone.max_drones == 2


def test_parse_start_hub_sets_unlimited_capacity(parser: MapParser) -> None:
    parser._parse_line(1, "start_hub: base 0 0")
    assert parser._start is not None
    assert parser._start.name == "base"
    assert parser._start.unlimited_capacity is True


def test_start_hub_max_drones_is_ignored_not_an_error(parser: MapParser) -> None:
    # Per the subject: max_drones present on start_hub is ignored,
    # not a validation error.
    parser._parse_line(1, "start_hub: base 0 0 [max_drones=5]")
    assert parser._start.unlimited_capacity is True

#Test invalidos
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
def test_non_positive_max_drones_raises(parser: MapParser, bad_value: str) -> None:
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
        parser._parse_line(1, "hub: roof1 3")  # falta la coordenada y
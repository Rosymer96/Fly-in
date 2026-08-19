class ParserError(Exception):
    """Base class for parser errors."""


def __init__(self, line_number: int, message: str) -> None:
    self.line_number = line_number
    self.message = message
    super().__init__(f"Line {line_number}: {message}")


class MapParser:
    """Parser for map files."""

    def __init__(self) -> None:
        self._zones: dict[str, Zone] = {}
        
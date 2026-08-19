from models import Zone, Connection


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
        self._connections: list[Connection] = []
        self._start: Zone | None = None
        self._end: Zone | None = None
        self._nb_drones: int | None = None
        self._seen_connections: set[frozenset[str]] = set()

    def _parse_metadata(
            self,
            line_number: int,
            raw_metadata: str
    ) -> dict[str, str]:

        """Parse a bracketed metadata block into a key-value dict.

        Args:
            line_number: current line, used only for error reporting.
            raw_metadata: the content between '[' and ']', e.g.
                "zone=priority color=green max_drones=2". Empty string
                if the line had no metadata block at all.

        Returns:
            A dict mapping each key to its raw string value. Values are
            NOT converted to int/enum here — that's the caller's job,
            since only the caller (zone vs connection handler) knows
            which keys are expected and what type each should be.

        Raises:
            ParseError: if any token isn't a well-formed key=value pair.
        """
        metadata: dict[str, str] = {}
        if not raw_metadata.strip():
            return metadata
        for token in raw_metadata.split():
            if '=' not in token:
                raise ParserError(
                    line_number,
                    f"metadata token {token!r} is not a key=value pair"
                )
            key, _, value = token.partition('=')
            if not key or not value:
                raise ParserError(
                    line_number,
                    f"malformed metadata token {token!r} (empty key or value)",
                )
            if key in metadata:
                raise ParserError(
                    line_number,
                    f"duplicate metadata key {key!r} in token {token!r}",
                )
            metadata[key] = value
        return metadata

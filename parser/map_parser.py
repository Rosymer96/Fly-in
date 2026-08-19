from collections.abc import Callable
from functools import partial
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

    def _strip_comments(self, line: str) -> str:
        """Remove comments from a line.

        Args:
            line: the raw line from the file.

        Returns:
            The line with comments removed.
        """
        line = line.split('#', 1)[0].strip()
        return line if line else None

    def _split_metadata(self, line_number: int, line: str) -> tuple[str, str]:
        if "[" in line:
            return line.strip(), ""

        body, _, remainder = line.partition("[")
        if "]" not in remainder:
            raise ParserError(
                line_number,
                "metadata block is missing closing ']'",
            )

        raw_metadata, _, extra = remainder.partition("]")
        if extra.strip():
            raise ParserError(
                line_number,
                "metadata block has extra content after closing ']'",
            )
        return body.strip(), raw_metadata.strip()

    def _split_prefix(
            self,
            line_number: int,
            body: str,
    ) -> tuple[str, str]:
        """Split off the leading `keyword:` prefix from the rest of the line.

        Returns (prefix, rest) e.g. ("hub", "corridorA 4 3").

        Raises:
            ParseError: if the line has no recognizable "keyword:" prefix.
        """
        if ":" not in body:
            raise ParserError(
                line_number,
                "line is missing a prefix (e.g. 'hub:')",
            )
        prefix, _, rest = body.partition(":")
        return prefix.strip(), rest.strip()

    def _handlers(
        self
    ) -> dict[str, Callable[[int, str, dict[str, str]], None]]:
        """Map each recognized line prefix to the method that handles it.

        Built as a method (not a class-level constant) because the
        start_hub/end_hub/hub variants are bound via functools.partial
        to the same underlying _parse_zone, which needs `self`.
        """
        return {
            "nb_drones": self._parse_nb_drones,
            "start_hub": partial(self._parse_zone, kind="start_hub"),
            "end_hub": partial(self._parse_zone, kind="end_hub"),
            "hub": partial(self._parse_zone, kind="hub"),
            "connection": self._parse_connection,
        }

    def _parse_line(
            self,
            line_number: int,
            raw_line: str
    ) -> None:
        """Parse a single line of the map file and update internal state.

        Dispatches to the right handler based on the line's prefix
        keyword. Blank lines and comments are silently skipped.
        """
        cleaned = self._strip_comments(raw_line)
        if cleaned is None:
            return
        body, raw_metadata = self._split_metadata(line_number, cleaned)
        prefix, rest = self._split_prefix(line_number, body)
        metadata = self._parse_metadata(line_number, raw_metadata)

        handler = self._handlers().get(prefix)
        if handler is None:
            raise ParserError(
                line_number,
                f"unrecognized line prefix {prefix!r}",
            )
        handler(self, line_number, rest, metadata)

    def _parse_zone(
        self,
        line_number: int,
        rest: str,
        metadata: dict[str, str],
        kind: str
    ) -> None:
        """Parse a zone definition line (start_hub, end_hub, or hub).

        Args:
            rest: everything after 'keyword:', e.g. "roof1 3 4".
            kind: which keyword introduced this zone — "start_hub",
                "end_hub", or "hub". Determines whether unlimited_capacity
                is set and whether this zone is tracked as start/end.

        Raises:
            ParseError: on malformed coordinates, unknown zone name reuse,
            an invalid zone type, a non-positive max_drones, or a second
            start_hub/end_hub appearing in the file.
        """
        tokens = rest.split()
        if len(tokens) != 3:
            raise ParserError(
                line_number,
                f"expected '<name> <x> <y>', got {rest!r}",
            )
        name, x_str, y_str = tokens
        


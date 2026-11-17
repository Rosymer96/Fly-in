import re
from collections.abc import Callable
from functools import partial

from models import Zone, Connection, ZoneType, Graph


class MapError(Exception):
    """Base class for every error raised while loading a map."""


class MapFileError(MapError):
    """The map file could not be opened or read."""

    def __init__(self, file_path: str, message: str) -> None:
        """Store the file path and cause, and build the message.

        Args:
            file_path: path of the map file that failed to load.
            message: human-readable description of the cause.
        """
        self.file_path = file_path
        self.message = message
        super().__init__(f"Cannot read map file {file_path!r}: {message}")


class ParserError(MapError):
    """The map file content is invalid."""

    def __init__(self, line_number: int, message: str) -> None:
        """Store the failing line and cause, and build the message.

        Args:
            line_number: line of the map file where the error occurred.
            message: readable description of the cause.
        """
        self.line_number = line_number
        self.message = message
        super().__init__(f"Line {line_number}: {message}")


class MapParser:
    """Parser for map files."""

    def __init__(self) -> None:
        """Create a parser with empty state, ready to read one map file."""
        self._reset()

    def _reset(self) -> None:
        """Clear all parsed data so the parser can read a new map."""
        self._zones: dict[str, Zone] = {}
        self._connections: list[Connection] = []
        self._start: Zone | None = None
        self._end: Zone | None = None
        self._nb_drones: int | None = None
        self._seen_connections: set[frozenset[str]] = set()

    @staticmethod
    def _parse_metadata(
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
            ParserError: if any token isn't a well-formed key=value pair.
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

    @staticmethod
    def _strip_comments(line: str) -> str | None:
        """Remove the '#' comment and surrounding whitespace from a line.

        Args:
            line: the raw line from the file.

        Returns:
            The line without its comment and stripped of whitespace, or
            None if nothing is left (blank line or comment-only line).
        """
        line = line.split('#', 1)[0].strip()
        return line if line else None

    @staticmethod
    def _split_metadata(line_number: int, line: str) -> tuple[str, str]:
        """Separate a line into its body and its bracketed metadata.

        Args:
            line_number: current line, used only for error reporting.
            line: the line with comments already removed.

        Returns:
            A tuple (body, raw_metadata). raw_metadata is an empty string
            when the line has no metadata block.

        Raises:
            ParserError: if the closing ']' is missing or there is extra
            content after it.
        """
        if "[" not in line:
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

    @staticmethod
    def _split_prefix(
            line_number: int,
            body: str,
    ) -> tuple[str, str]:
        """Split off the leading `keyword:` prefix from the rest of the line.

        Args:
            line_number: current line, used only for error reporting.
            body: the line without comment or metadata block, e.g.
                "hub: corridorA 4 3".

        Returns:
            A tuple (prefix, rest), both stripped, e.g.
            ("hub", "corridorA 4 3"). Only the first ':' is used to split.

        Raises:
            ParserError: if the line contains no ':' at all.
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

        Returns:
            A dict from line prefix to a handler taking (line_number,
            rest, metadata) and returning None.
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

        Args:
            line_number: current line (1-based), used for error reporting.
            raw_line: the line exactly as read from the file.

        Raises:
            ParserError: on malformed syntax or metadata, if the first
            meaningful line is not nb_drones, or on an unknown prefix.
            Errors from the specific handler also propagate.
        """
        cleaned = self._strip_comments(raw_line)
        if cleaned is None:
            return
        body, raw_metadata = self._split_metadata(line_number, cleaned)
        prefix, rest = self._split_prefix(line_number, body)
        metadata = self._parse_metadata(line_number, raw_metadata)

        if self._nb_drones is None and prefix != "nb_drones":
            raise ParserError(
                line_number,
                "first line must define nb_drones",
            )

        handler = self._handlers().get(prefix)
        if handler is None:
            raise ParserError(
                line_number,
                f"unrecognized line prefix {prefix!r}",
            )
        handler(line_number, rest, metadata)

    @staticmethod
    def _check_known_keys(
        line_number: int,
        metadata: dict[str, str],
        allowed: set[str],
    ) -> None:
        """Reject metadata keys that this kind of line does not support.

        Args:
            line_number: current line, used only for error reporting.
            metadata: the parsed key-value pairs of the line.
            allowed: the keys this kind of line accepts.

        Raises:
            ParserError: if metadata contains a key not in `allowed`.
        """
        for key in metadata:
            if key not in allowed:
                raise ParserError(
                    line_number,
                    f"unknown metadata key {key!r}, allowed: "
                    f"{', '.join(sorted(allowed)) or 'none'}",
                )

    @staticmethod
    def _parse_positive_int(
        line_number: int,
        raw_value: str,
        field_name: str
    ) -> int:
        """Parse a string that must be a positive integer (>= 1).

        Only plain digits are accepted: signs, decimals and spaces are
        rejected.

        Args:
            line_number: current line, used only for error reporting.
            raw_value: the text to convert, e.g. "3".
            field_name: name of the field, used in the error message.

        Returns:
            The value as an int.

        Raises:
            ParserError: if the text is not a positive integer.
        """
        if not re.fullmatch(r"[0-9]+", raw_value) or int(raw_value) < 1:
            raise ParserError(
                line_number,
                f"{field_name} must be a positive integer, got {raw_value!r}",
            )
        return int(raw_value)

    def _parse_zone(
        self,
        line_number: int,
        rest: str,
        metadata: dict[str, str],
        kind: str
    ) -> None:
        """Parse a zone definition line (start_hub, end_hub, or hub).

        Args:
            line_number: current line, used only for error reporting.
            rest: everything after 'keyword:', e.g. "roof1 3 4".
            metadata: the parsed key-value pairs of the line.
            kind: which keyword introduced this zone — "start_hub",
                "end_hub", or "hub". Determines whether unlimited_capacity
                is set and whether this zone is tracked as start/end.

        Raises:
            ParserError: on malformed coordinates, unknown zone name reuse,
            an invalid zone type, a non-positive max_drones, or a second
            start_hub/end_hub appearing in the file.
        """
        self._check_known_keys(
            line_number, metadata, {"zone", "color", "max_drones"}
        )
        tokens = rest.split()
        if len(tokens) != 3:
            raise ParserError(
                line_number,
                f"expected '<name> <x> <y>', got {rest!r}",
            )
        name, x_str, y_str = tokens

        if "-" in name or " " in name:
            raise ParserError(
                line_number,
                f"zone name {name!r} cannot contain '-' or spaces"
            )

        if name in self._zones:
            raise ParserError(line_number, f"duplicate zone name {name!r}")

        if not (re.fullmatch(r"-?[0-9]+", x_str)
                and re.fullmatch(r"-?[0-9]+", y_str)):
            raise ParserError(
                line_number,
                f"coordinates must be integers, got {x_str!r} {y_str!r}"
            )

        zone_type_str = metadata.get("zone", "normal")
        try:
            zone_type = ZoneType(zone_type_str)
        except ValueError:
            raise ParserError(
                line_number,
                f"invalid zone type {zone_type_str!r}, must be one of "
                f"{', '.join(z.value for z in ZoneType)}",
            )

        is_hub_boundary = kind in ("start_hub", "end_hub")
        if is_hub_boundary and zone_type.is_blocked():
            raise ParserError(
                line_number,
                f"{kind} cannot be a blocked zone",
            )
        if is_hub_boundary:
            max_drones = 1
        else:
            max_drones = self._parse_positive_int(
                line_number,
                metadata.get("max_drones", "1"),
                "max_drones"
            )

        zone = Zone(
            name=name,
            x=int(x_str),
            y=int(y_str),
            zone_type=zone_type,
            color=metadata.get("color"),
            max_drones=max_drones,
            unlimited_capacity=is_hub_boundary,
        )

        self._zones[name] = zone

        if kind == "start_hub":
            if self._start is not None:
                raise ParserError(
                    line_number,
                    "multiple start_hub definitions"
                )
            self._start = zone
        elif kind == "end_hub":
            if self._end is not None:
                raise ParserError(line_number, "multiple end_hub definitions")
            self._end = zone

    def _parse_connection(
        self,
        line_number: int,
        rest: str,
        metadata: dict[str, str]
    ) -> None:
        """Parse a 'connection: name1-name2 [metadata]' line.

        Args:
            line_number: current line, used only for error reporting.
            rest: everything after 'connection:', e.g. "roof1-roof2".
            metadata: the parsed key-value pairs of the line.

        Raises:
            ParserError: on malformed syntax, a reference to an undefined
            zone, or a duplicate connection (a-b same as b-a).
        """
        self._check_known_keys(line_number, metadata, {"max_link_capacity"})
        if "-" not in rest:
            raise ParserError(
                line_number,
                f"connection must be in the form 'zoneA-zoneB', got {rest!r}",
            )
        name1, _, name2 = rest.partition("-")
        name1, name2 = name1.strip(), name2.strip()

        if not name1 or not name2:
            raise ParserError(
                line_number,
                f"connection must have two zone names, got {rest!r}",
            )
        if name1 not in self._zones:
            raise ParserError(
                line_number,
                f"connection references undefined zone {name1!r}",
            )
        if name2 not in self._zones:
            raise ParserError(
                line_number,
                f"connection references undefined zone {name2!r}",
            )
        if name1 == name2:
            raise ParserError(
                line_number,
                f"connection cannot link zone {name1!r} to itself",
            )
        pair_key = frozenset({name1, name2})
        if pair_key in self._seen_connections:
            raise ParserError(
                line_number,
                f"duplicate connection between {name1!r} and {name2!r}",
            )
        self._seen_connections.add(pair_key)

        max_link_capacity = self._parse_positive_int(
            line_number,
            metadata.get("max_link_capacity", "1"),
            "max_link_capacity"
        )

        connection = Connection(
            zone_a=self._zones[name1],
            zone_b=self._zones[name2],
            max_link_capacity=max_link_capacity,
        )
        self._connections.append(connection)

    def _parse_nb_drones(
        self, line_number: int, rest: str, metadata: dict[str, str]
    ) -> None:
        """Parse the 'nb_drones: <positive_integer>' line.

        Args:
            line_number: current line, used only for error reporting.
            rest: everything after 'nb_drones:', e.g. "5".
            metadata: the parsed key-value pairs of the line.

        Raises:
            ParserError: if not a positive integer, if this line
            appears more than once in the file, or if it carries any
            metadata (this line supports none).
        """
        self._check_known_keys(line_number, metadata, set())
        if self._nb_drones is not None:
            raise ParserError(line_number, "nb_drones defined more than once")
        self._nb_drones = self._parse_positive_int(
            line_number, rest, "nb_drones"
        )

    def finalize(
        self,
        line_number: int
    ) -> tuple[Graph, int]:
        """Run whole-file validations and build the final Graph.

        These checks can't run line-by-line because they depend on
        having seen the entire file first (e.g. "exactly one start_hub").

        Args:
            line_number: last line read, reported if a check fails.

        Returns:
            A tuple (graph, nb_drones) with the validated network and the
            number of drones.

        Raises:
            ParserError: if nb_drones, start_hub or end_hub is missing.
        """
        if self._nb_drones is None:
            raise ParserError(line_number, "missing nb_drones line")
        if self._start is None:
            raise ParserError(line_number, "no start_hub defined")
        if self._end is None:
            raise ParserError(line_number, "no end_hub defined")
        graph = Graph(
            zones=self._zones,
            connections=self._connections,
            start=self._start,
            end=self._end,
        )
        return graph, self._nb_drones

    def parse(
        self,
        file_path: str
    ) -> tuple[Graph, int]:
        """Parse a map file and return (graph, nb_drones).

        Any state left by a previous call is discarded first.

        Args:
            file_path: path of the map file to read (UTF-8 text).

        Returns:
            A tuple (graph, nb_drones) with the validated network and the
            number of drones.

        Raises:
            ParserError: on any structural or semantic violation.
            MapFileError: if the file cannot be opened or decoded.
        """
        self._reset()
        line_number = 0
        try:
            with open(file_path, "r", encoding="utf-8") as handle:
                for line_number, raw_line in enumerate(handle, start=1):
                    self._parse_line(line_number, raw_line)
        except OSError as error:
            raise MapFileError(
                file_path, error.strerror or str(error)
            ) from error
        except UnicodeDecodeError as error:
            raise MapFileError(
                file_path, "file is not valid UTF-8 text"
            ) from error
        return self.finalize(line_number)

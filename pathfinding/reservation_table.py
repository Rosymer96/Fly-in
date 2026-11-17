from models import Connection, Zone

from .move import Move
from .path import Path


class ReservationTable:
    """Future occupancy of zones and connections, turn by turn."""

    def __init__(self) -> None:
        """Create an empty table: nothing is reserved yet."""
        self._zone_usage: dict[tuple[str, int], int] = {}
        self._link_usage: dict[tuple[frozenset[str], int], int] = {}

    @staticmethod
    def _link_key(connection: Connection) -> frozenset[str]:
        """Return a key equal for a-b and b-a."""

        return frozenset({connection.zone_a.name, connection.zone_b.name})

    def zone_usage(self, zone: Zone, turn: int) -> int:
        """Return how many drones are in the zone at the end of a turn.

        Args:
            zone: the zone to look up.
            turn: the turn number (0 is the initial state).

        Returns:
            The number of reserved drones, or 0 if nothing is reserved.
        """
        return self._zone_usage.get((zone.name, turn), 0)

    def link_usage(self, connection: Connection, turn: int) -> int:
        """Return how many drones use the connection during a turn.

        Args:
            connection: the connection to look up (a-b equals b-a).
            turn: the turn number.

        Returns:
            The number of reserved drones, or 0 if nothing is reserved.
        """
        return self._link_usage.get((self._link_key(connection), turn), 0)

    def is_zone_free(self, zone: Zone, turn: int) -> bool:
        """Return whether one more drone fits in the zone at that turn.

        Args:
            zone: the zone to check.
            turn: the turn number.

        Returns:
            True if the zone is unlimited (start or end) or has a free
            slot at the end of that turn, False if it is full.
        """
        if zone.capacity is None:
            return True
        return self.zone_usage(zone, turn) < zone.capacity

    def is_link_free(self, connection: Connection, turn: int) -> bool:
        """Return whether one more drone fits on the link at that turn.

        Args:
            connection: the connection to check (a-b equals b-a).
            turn: the turn number.

        Returns:
            True if the link has a free slot during that turn, False if
            it is full.
        """
        return self.link_usage(connection, turn) < connection.capacity

    def reserve_zone(self, zone: Zone, turn: int) -> None:
        """Count one more drone in the zone at the end of a turn.

        Args:
            zone: the zone to reserve.
            turn: the turn number.

        Raises:
            ValueError: if the zone is already full at that turn.
        """
        if not self.is_zone_free(zone, turn):
            raise ValueError(f"{zone.label} is full at turn {turn}")
        self._zone_usage[(zone.name, turn)] = self.zone_usage(zone, turn) + 1

    def reserve_link(self, connection: Connection, turn: int) -> None:
        """Count one more drone on the connection during a turn.

        Args:
            connection: the connection to reserve (a-b equals b-a).
            turn: the turn number.

        Raises:
            ValueError: if the connection is already full at that turn.
        """
        if not self.is_link_free(connection, turn):
            raise ValueError(f"{connection.label} is full at turn {turn}")
        key = (self._link_key(connection), turn)
        self._link_usage[key] = self.link_usage(connection, turn) + 1

    def is_move_free(self, move: Move) -> bool:
        """Return whether a whole move fits, without reserving anything.

        Args:
            move: the move to check.

        Returns:
            True if the connection is free in every turn of the transit
            and the destination zone is free when the drone arrives.
        """
        links_free = all(
            self.is_link_free(move.connection, turn)
            for turn in move.link_turns
        )
        return links_free and self.is_zone_free(
            move.destination, move.arrival_turn
        )

    def reserve_move(self, move: Move) -> None:
        """Reserve one drone making a move: the link and the arrival.

        A move costing c turns keeps the connection busy for c turns,
        and the drone is in the destination at the end of the last one.
        Either everything is reserved or nothing is.

        Args:
            move: the move to reserve.

        Raises:
            ValueError: if the connection or the destination zone has no
                free capacity in any of the turns needed.
        """
        if not self.is_move_free(move):
            raise ValueError(
                f"cannot move into {move.destination.label} through "
                f"{move.connection.label} starting at turn "
                f"{move.start_turn}"
            )
        for turn in move.link_turns:
            self.reserve_link(move.connection, turn)
        self.reserve_zone(move.destination, move.arrival_turn)

    def reserve_path(self, path: Path) -> None:
        """Reserve a whole route: every move and every waiting turn.

        Everything is checked first, so a failure leaves the table as it
        was. This is sound because a valid Path never claims the same
        zone or link at the same turn twice.

        Args:
            path: the route to reserve.

        Raises:
            ValueError: if any move or waiting turn does not fit.
        """
        moves_free = all(self.is_move_free(move) for move in path.moves)
        waits_free = all(
            self.is_zone_free(zone, turn) for zone, turn in path.waits
        )
        if not (moves_free and waits_free):
            raise ValueError(
                f"cannot reserve the path from {path.origin.label} "
                f"to {path.destination.label}"
            )
        for move in path.moves:
            self.reserve_move(move)
        for zone, turn in path.waits:
            self.reserve_zone(zone, turn)

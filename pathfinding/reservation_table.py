from models import Connection, Zone


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

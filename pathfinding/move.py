from dataclasses import dataclass

from models import Connection, Zone


@dataclass(frozen=True)
class Move:
    """One drone crossing one connection into the next zone.

    Attributes:
        connection: the connection the drone travels along.
        destination: the zone at the other end of the connection.
        start_turn: the turn in which the drone leaves its zone
            (turn 0 is the initial state, so the first move is turn 1).
    """

    connection: Connection
    destination: Zone
    start_turn: int

    def __post_init__(self) -> None:
        """Reject moves that can never be valid.

        Raises:
            ValueError: if start_turn is below 1, if the destination is
                not an endpoint of the connection, or if it is blocked.
        """
        if self.start_turn < 1:
            raise ValueError(
                f"a move cannot start before turn 1, got {self.start_turn}"
            )
        if (self.destination is not self.connection.zone_a
                and self.destination is not self.connection.zone_b):
            raise ValueError(
                f"{self.destination.label} is not an endpoint of "
                f"{self.connection.label}"
            )
        if self.destination.zone_type.is_blocked():
            raise ValueError(f"{self.destination.label} is blocked")

    @property
    def origin(self) -> Zone:
        """Return the zone the drone leaves."""
        return self.connection.other(self.destination)

    @property
    def cost(self) -> int:
        """Return how many turns the move takes (set by the destination)."""
        return self.destination.zone_type.movement_cost()

    @property
    def arrival_turn(self) -> int:
        """Return the turn at whose end the drone is in the destination."""
        return self.start_turn + self.cost - 1

    @property
    def link_turns(self) -> range:
        """Return the turns in which the drone occupies the connection."""
        return range(self.start_turn, self.start_turn + self.cost)

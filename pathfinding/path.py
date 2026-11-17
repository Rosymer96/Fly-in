from collections.abc import Iterable

from models import Zone

from .move import Move


class Path:
    """The full route of one drone: a chain of moves, plus its waits.

    Waiting is not stored: it is deduced from the gaps between moves
    (and before the first one).
    """

    def __init__(self, moves: Iterable[Move]) -> None:
        """Validate the chain of moves and work out where the drone waits.

        Args:
            moves: the moves in the order they happen.

        Raises:
            ValueError: if there are no moves, if a move does not start
                in the zone where the previous one ended, or if a move
                starts before the previous one has arrived.
        """
        ordered = tuple(moves)
        if not ordered:
            raise ValueError("a path needs at least one move")

        waits: list[tuple[Zone, int]] = []
        first = ordered[0]
        for turn in range(0, first.start_turn):
            waits.append((first.origin, turn))
        for previous, current in zip(ordered, ordered[1:]):
            if current.origin is not previous.destination:
                raise ValueError(
                    f"move into {current.destination.label} does not start "
                    f"in {previous.destination.label}"
                )
            if current.start_turn <= previous.arrival_turn:
                raise ValueError(
                    f"move into {current.destination.label} starts at turn "
                    f"{current.start_turn}, before the drone has arrived "
                    f"(turn {previous.arrival_turn})"
                )
            for turn in range(previous.arrival_turn + 1, current.start_turn):
                waits.append((previous.destination, turn))

        self._moves: tuple[Move, ...] = ordered
        self._waits: tuple[tuple[Zone, int], ...] = tuple(waits)

    @property
    def moves(self) -> tuple[Move, ...]:
        """Return the moves of the path, in order."""
        return self._moves

    @property
    def waits(self) -> tuple[tuple[Zone, int], ...]:
        """Return every (zone, turn) where the drone stays without moving.

        The first entries are the turns spent in the origin zone,
        starting at turn 0.
        """
        return self._waits

    @property
    def origin(self) -> Zone:
        """Return the zone where the drone starts."""
        return self._moves[0].origin

    @property
    def destination(self) -> Zone:
        """Return the zone where the drone ends."""
        return self._moves[-1].destination

    @property
    def arrival_turn(self) -> int:
        """Return the turn at whose end the drone reaches the destination."""
        return self._moves[-1].arrival_turn

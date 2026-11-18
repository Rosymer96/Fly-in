import heapq
from itertools import count

from models import Graph, Zone, ZoneType

from .move import Move
from .path import Path
from .pathfinder import Pathfinder
from .reservation_table import ReservationTable

# A search state: (zone name, turn at whose end the drone is there).
State = tuple[str, int]
# A heap entry: (turn, -priority zones crossed, tie-breaker, zone,
# previous state, move that led here or None if the drone waited).
Entry = tuple[int, int, int, Zone, State | None, Move | None]


class PlanningError(Exception):
    """The drones cannot be routed from the start zone to the end zone."""


class Planner:
    """Plans one path per drone, reserving each before the next.

    Every drone is searched over (zone, turn) states using the
    reservation table, so a path is only accepted if every step fits.
    """

    def __init__(self, graph: Graph, nb_drones: int) -> None:
        """Create a planner with an empty reservation table.

        Args:
            graph: the network the drones fly through.
            nb_drones: how many drones have to be routed.
        """
        self._graph: Graph = graph
        self._nb_drones: int = nb_drones
        self._table: ReservationTable = ReservationTable()
        self._latest_arrival: int = 0

    @property
    def table(self) -> ReservationTable:
        """Return the reservation table (read by the simulator).

        Returns:
            The table holding every reservation made so far.
        """
        return self._table

    def plan_drone(self) -> Path | None:
        """Find the fastest path for one more drone, reserving nothing.

        The search is a Dijkstra over (zone, turn) states. A drone may
        wait in its zone or move along a connection; both are accepted
        only if the reservation table says they fit. Among paths with
        the same arrival turn, the one crossing more priority zones
        wins. The search is cut at ``latest arrival + 2 * zones``: once
        every planned drone has arrived the network is empty, and a
        lone drone needs at most 2 turns per zone, so a reachable end
        is always found inside that limit.

        Returns:
            The path, or None if the end cannot be reached in time.
        """
        limit = self._latest_arrival + 2 * len(self._graph.zones)
        end = self._graph.end
        tie = count()
        heap: list[Entry] = [
            (0, 0, next(tie), self._graph.start, None, None)
        ]
        visited: dict[State, tuple[State | None, Move | None]] = {}

        while heap:
            turn, neg_priority, _, zone, previous, move = heapq.heappop(heap)
            state: State = (zone.name, turn)
            if state in visited:
                continue
            visited[state] = (previous, move)
            if zone is end:
                return self._rebuild(visited, state)

            if turn + 1 <= limit and self._table.is_zone_free(zone, turn + 1):
                heapq.heappush(
                    heap,
                    (turn + 1, neg_priority, next(tie), zone, state, None),
                )
            for connection in self._graph.neighbors(zone):
                destination = connection.other(zone)
                if destination.zone_type.is_blocked():
                    continue
                candidate = Move(connection, destination, turn + 1)
                if candidate.arrival_turn > limit:
                    continue
                if not self._table.is_move_free(candidate):
                    continue
                bonus = 1 if destination.zone_type is ZoneType.PRIORITY else 0
                heapq.heappush(heap, (
                    candidate.arrival_turn,
                    neg_priority - bonus,
                    next(tie),
                    destination,
                    state,
                    candidate,
                ))
        return None

    @staticmethod
    def _rebuild(
        visited: dict[State, tuple[State | None, Move | None]],
        last: State,
    ) -> Path:
        """Walk back from the last state and build the Path.

        Args:
            visited: for each closed state, the state it came from and
                the move used (None if the drone waited).
            last: the final state, where the drone is in the end zone.

        Returns:
            The path made of the moves found, in travel order.
        """
        moves: list[Move] = []
        current: State | None = last
        while current is not None:
            previous, move = visited[current]
            if move is not None:
                moves.append(move)
            current = previous
        moves.reverse()
        return Path(moves)

    def plan_all(self) -> list[Path]:
        """Plan and reserve a path for every drone, one after another.

        Any earlier plan is discarded, so the call can be repeated.

        Returns:
            One path per drone, in the order they were planned.

        Raises:
            PlanningError: if the end zone cannot be reached from the
                start zone (disconnected graph or blocked zones).
        """
        self._table = ReservationTable()
        self._latest_arrival = 0
        start, end = self._graph.start, self._graph.end
        if start.name not in Pathfinder(self._graph).hops_from(end):
            raise PlanningError(
                f"no route from {start.name!r} to {end.name!r}"
            )

        paths: list[Path] = []
        for drone in range(1, self._nb_drones + 1):
            path = self.plan_drone()
            if path is None:
                raise PlanningError(f"could not plan a path for drone {drone}")
            self._table.reserve_path(path)
            self._latest_arrival = max(self._latest_arrival, path.arrival_turn)
            paths.append(path)
        return paths

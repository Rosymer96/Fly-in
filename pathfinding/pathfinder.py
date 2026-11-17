from collections import deque
from models import Graph, Zone


class Pathfinder:
    """Answers reachability and distance questions about a Graph."""

    def __init__(self, graph: Graph) -> None:
        """Store the graph to search.

        Args:
            graph: the network to explore.
        """
        self._graph: Graph = graph

    def hops_from(self, origin: Zone) -> dict[str, int]:
        """Count the connections from origin to every reachable zone.

        Blocked zones are never entered.

        Args:
            origin: the zone where the search starts.

        Returns:
            A dict from zone name to number of connections. Zones that
            cannot be reached are missing from the dict.
        """
        hops: dict[str, int] = {origin.name: 0}
        queue: deque[Zone] = deque([origin])
        while queue:
            current = queue.popleft()
            for connection in self._graph.neighbors(current):
                neighbor = connection.other(current)
                if neighbor.zone_type.is_blocked():
                    continue
                if neighbor.name in hops:
                    continue
                hops[neighbor.name] = hops[current.name] + 1
                queue.append(neighbor)
        return hops

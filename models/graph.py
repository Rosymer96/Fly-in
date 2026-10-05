from .zone import Zone
from .connection import Connection


class Graph:
    """The network of zones and the connections between them."""

    def __init__(
            self, zones: dict[str, Zone],
            connections: list[Connection],
            start: Zone,
            end: Zone
    ) -> None:
        """Store the network and build the adjacency index.

        Args:
            zones: all zones, indexed by name.
            connections: all links between zones.
            start: the start zone.
            end: the end zone.
        """
        self.zones = zones
        self.connections = connections
        self.start = start
        self.end = end

        self._adjacency: dict[str, list[Connection]] = self._build_adjacency()

    def _build_adjacency(self) -> dict[str, list[Connection]]:
        """Map each zone name to the connections touching that zone."""
        index: dict[str, list[Connection]] = {name: [] for name in self.zones}
        for connection in self.connections:
            index[connection.zone_a.name].append(connection)
            index[connection.zone_b.name].append(connection)
        return index

    def neighbors(self, zone: Zone) -> list[Connection]:
        """Return the connections that start or end at the given zone."""
        return self._adjacency[zone.name]

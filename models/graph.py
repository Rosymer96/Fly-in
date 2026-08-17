from models.zone import Zone
from models.connection import Connection


class Graph:
    def __init__(
            self, zones: dict[str, Zone],
            connections: list[Connection],
            start: Zone,
            end: Zone
    ) -> None:
        self.zones = zones
        self.connections = connections
        self.start = start
        self.end = end

        self._adjacency: dict[str, list[Connection]] = self._build_adjacency()

    def _build_adjacency(self) -> dict[str, list[Connection]]:
        index: dict[str, list[Connection]] = {name: [] for name in self.zones}
        for connection in self.connections:
            index[connection.zone_a.name].append(connection)
            index[connection.zone_b.name].append(connection)
        return index

    def neighbors(self, zone: Zone) -> list[Connection]:
        return self._adjacency[zone.name]

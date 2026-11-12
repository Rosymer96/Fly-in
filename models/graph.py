from types import MappingProxyType
from typing import Mapping

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
        """Store a private copy of the network and build the adjacency index.

        The graph is immutable after construction: the inputs are copied
        and exposed only through read-only properties.

        Args:
            zones: all zones, indexed by name.
            connections: all links between zones.
            start: the start zone.
            end: the end zone.

        Raises:
            KeyError: if a connection uses a zone missing from ``zones``.
        """
        self._zones: dict[str, Zone] = dict(zones)
        self._connections: tuple[Connection, ...] = tuple(connections)
        self._start: Zone = start
        self._end: Zone = end

        self._adjacency: dict[str, tuple[Connection, ...]] = (
            self._build_adjacency()
        )

    @property
    def zones(self) -> Mapping[str, Zone]:
        """Return a read-only view of the zones, indexed by name.

        Returns:
            A mapping from zone name to zone that cannot be modified.
        """
        return MappingProxyType(self._zones)

    @property
    def connections(self) -> tuple[Connection, ...]:
        """Return all links between zones.

        Returns:
            An immutable tuple with every connection of the network.
        """
        return self._connections

    @property
    def start(self) -> Zone:
        """Return the start zone.

        Returns:
            The zone where all drones begin.
        """
        return self._start

    @property
    def end(self) -> Zone:
        """Return the end zone.

        Returns:
            The zone every drone must reach.
        """
        return self._end

    def _build_adjacency(self) -> dict[str, tuple[Connection, ...]]:
        """Map each zone name to the connections touching that zone.

        Returns:
            A dict from zone name to an immutable tuple of its connections.
            Zones without connections map to an empty tuple.

        Raises:
            KeyError: if a connection uses a zone missing from the zones.
        """
        index: dict[str, list[Connection]] = {
            name: [] for name in self._zones
        }
        for connection in self._connections:
            index[connection.zone_a.name].append(connection)
            index[connection.zone_b.name].append(connection)
        return {name: tuple(links) for name, links in index.items()}

    def neighbors(self, zone: Zone) -> tuple[Connection, ...]:
        """Return the connections that start or end at the given zone.

        The tuple is precomputed, so the call costs O(1) and exposes no
        internal state.

        Args:
            zone: the zone whose connections are requested.

        Returns:
            An immutable tuple with the connections touching ``zone``.

        Raises:
            KeyError: if ``zone`` does not belong to this graph.
        """
        return self._adjacency[zone.name]

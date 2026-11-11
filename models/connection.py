from dataclasses import dataclass

from .capacity_resource import CapacityResource
from .zone import Zone


@dataclass
class Connection(CapacityResource):
    """A bidirectional link between two zones.

    Attributes:
        zone_a: one endpoint of the link.
        zone_b: the other endpoint of the link.
        max_link_capacity: maximum drones that can traverse it at once.
    """

    zone_a: Zone
    zone_b: Zone
    max_link_capacity: int

    @property
    def capacity(self) -> int:
        """Return the maximum drones allowed on the link at once."""
        return self.max_link_capacity

    @property
    def label(self) -> str:
        """Return the link name, used in error messages."""
        return f"connection {self.zone_a.name}-{self.zone_b.name}"

    def other(self, zone: Zone) -> Zone:
        """Given one endpoint, return the opposite one.

        Raises:
            ValueError: if `zone` is not an endpoint of this connection.
        """
        if zone is self.zone_a:
            return self.zone_b
        if zone is self.zone_b:
            return self.zone_a
        raise ValueError(
            f"zone {zone.name!r} is not an endpoint of connection "
            f"{self.zone_a.name}-{self.zone_b.name}"
        )

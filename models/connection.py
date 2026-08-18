from dataclasses import dataclass, field
from models.zone import Zone


@dataclass
class Connection:
    zone_a: Zone
    zone_b: Zone
    max_link_capacity: int
    current_traversals: int = field(default_factory=set)

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

    def has_capacity(self) -> bool:
        """Return whether one more drone can traverse
        this connection right now."""
        return len(self.current_traversals) < self.max_link_capacity

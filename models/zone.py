from dataclasses import dataclass
from enum import Enum

from .capacity_resource import CapacityResource


class ZoneType(Enum):
    """Zone type enumeration."""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"

    def movement_cost(self) -> int:
        """Return the number of turns needed to enter this zone type.

        Raises:
            ValueError: if the zone type is blocked.
        """
        if self is ZoneType.BLOCKED:
            raise ValueError("blocked zones have no movement cost")
        return _MOVEMENT_COSTS[self]

    def is_blocked(self) -> bool:
        """Return whether drones are forbidden from entering this type."""
        return self is ZoneType.BLOCKED


_MOVEMENT_COSTS: dict[ZoneType, int] = {
    ZoneType.NORMAL: 1,
    ZoneType.RESTRICTED: 2,
    ZoneType.PRIORITY: 1,
}


@dataclass
class Zone(CapacityResource):
    """A node of the network, with its position, type and capacity.

    Attributes:
        name: unique zone name.
        x: integer x coordinate.
        y: integer y coordinate.
        zone_type: kind of zone (normal, blocked, restricted, priority).
        color: optional color used for visual output.
        max_drones: maximum drones allowed at once.
        unlimited_capacity: True for start and end zones, which ignore
            max_drones.
    """

    name: str
    x: int
    y: int
    zone_type: ZoneType
    color: str | None
    max_drones: int
    unlimited_capacity: bool = False

    @property
    def capacity(self) -> int | None:
        """Return the drone limit, or None if the zone is unlimited."""
        return None if self.unlimited_capacity else self.max_drones

    @property
    def label(self) -> str:
        """Return the zone name, used in error messages."""
        return f"zone {self.name!r}"

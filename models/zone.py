from dataclasses import dataclass, field
from enum import Enum


class ZoneType(Enum):
    """Zone type enumeration."""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"

    def movement_cost(self) -> int:
        if self is ZoneType.BLOCKED:
            raise ValueError("blocked zones have no movement cost")
        return _MOVEMENT_COSTS[self]

    def is_blocked(self) -> bool:
        return self is ZoneType.BLOCKED


_MOVEMENT_COSTS: dict[ZoneType, int] = {
    ZoneType.NORMAL: 1,
    ZoneType.RESTRICTED: 2,
    ZoneType.PRIORITY: 1,
}


@dataclass
class Zone:
    name: str
    x: int
    y: int
    zone_type: ZoneType
    color: str | None
    max_drones: int
    current_occupants: set[int] = field(default_factory=set)
    unlimited_capacity: bool = False

    def has_capacity(self) -> bool:
        """Return whether the zone can accept another drone right now."""
        if self.unlimited_capacity:
            return True
        return len(self.current_occupants) < self.max_drones

class ZoneType:
    """Zone type enumeration."""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"

    def movement_cost(self) -> int:
        """Turns required to move into a zone of this type.

        Blocked zones have no valid cost — callers must check
        is_blocked() before calling this.
        """
        costs = {
            ZoneType.NORMAL: 1,
            ZoneType.RESTRICTED: 2,
            ZoneType.PRIORITY: 1,
        }
        return costs[self]

    def is_blocked(self) -> bool:
        """Return True if this zone type is blocked."""
        return self is ZoneType.BLOCKED


class Zone:
    name: str
    x: int
    y: int
    zone_type: ZoneType
    color: str | None
    max_drones: int
    current_occupants: set[int]
    unlimited_capacity: bool = False

    def has_capacity(self, extra: int = 1) -> bool:
        """Return True if the zone has capacity for `extra` more drones."""
        if self.unlimited_capacity:
            return True
        return len(self.current_occupants) + extra <= self.max_drones

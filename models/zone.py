class ZoneType:
    """Zone type enumeration."""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class Zone:
    name: str
    x: int
    y: int
    zone_type: ZoneType
    color: str | None
    max_drones: int
    current_occupants: set[int]

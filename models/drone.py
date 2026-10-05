from dataclasses import dataclass
from .zone import Zone


@dataclass
class Drone:
    """A drone travelling along a planned path of zones.

    Attributes:
        id: unique drone identifier.
        current_zone: zone where the drone currently is.
        path: ordered zones the drone must visit.
        next_index: index in path of the next zone to reach.
        in_transit_to: destination while crossing a restricted link.
        turns_remaining: turns left to finish the current movement.
        delivered: True once the drone has reached the end zone.
    """

    id: int
    current_zone: Zone
    path: list[Zone]
    next_index: int = 1
    in_transit_to: Zone | None = None
    turns_remaining: int = 0
    delivered: bool = False

    def next_target(self) -> Zone | None:
        """Return the next zone in the path, or None if at the end."""
        if self.next_index >= len(self.path):
            return None
        return self.path[self.next_index]

from models.zone import Zone


class Drone:
    id: int
    current_zone: Zone
    path: list[Zone]
    next_index: int = 1
    in_transit_to: Zone | None
    turns_remaining: int
    delivered: bool = False

    def next_target(self) -> Zone | None:
        """Return the next zone in the path, or None if at the end."""
        if self.next_index >= len(self.path):
            return None
        return self.path[self.next_index]

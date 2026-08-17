from models.zone import Zone


class Drone:
    id: int
    current_zone: Zone
    path: list[Zone]
    in_transit_to: Zone | None
    turns_remaining: int
    delivered: bool

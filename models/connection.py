from models.zone import Zone


class Connection:
    zone_a: Zone
    zone_b: Zone
    max_link_capacity: int
    current_traversals: int

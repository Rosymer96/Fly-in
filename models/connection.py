from models.zone import Zone


class Connection:
    zone_a: Zone
    zone_b: Zone
    max_link_capacity: int
    current_traversals: int

    def other(self, zone: Zone) -> Zone:
        """Given one endpoint, return the opposite one.

        Lets callers write `connection.other(current_zone)` instead
        of re-checking which side is zone_a vs zone_b every time.
        """
        return self.zone_b if zone is self.zone_a else self.zone_a

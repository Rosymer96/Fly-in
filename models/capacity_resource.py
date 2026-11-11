from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class CapacityResource(ABC):
    """Base class for anything that can hold a limited number of drones.

    The occupant set is private: it can only change through `enter` and
    `leave`, and it can only be read through `occupancy`.
    """

    _occupants: set[int] = field(
        default_factory=set, init=False, repr=False
    )

    @property
    @abstractmethod
    def capacity(self) -> int | None:
        """Return the drone limit, or None if there is no limit."""

    @property
    @abstractmethod
    def label(self) -> str:
        """Return a short human-readable name, used in error messages."""

    @property
    def occupancy(self) -> int:
        """Return how many drones are using the resource right now."""
        return len(self._occupants)

    def has_capacity(self) -> bool:
        """Return whether one more drone can use the resource right now."""
        return self.capacity is None or self.occupancy < self.capacity

    def enter(self, drone_id: int) -> None:
        """Register a drone in the resource.

        Args:
            drone_id: id of the drone entering.

        Raises:
            ValueError: if the resource has no free capacity.
        """
        if not self.has_capacity():
            raise ValueError(f"{self.label} is full")
        self._occupants.add(drone_id)

    def leave(self, drone_id: int) -> None:
        """Remove a drone from the resource (no error if it was not there).

        Args:
            drone_id: id of the drone leaving.
        """
        self._occupants.discard(drone_id)

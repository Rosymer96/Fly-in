from models.zone import Zone
from models.connection import Connection


class Graph:
    zones: dict[str, Zone]
    connections: list[Connection]
    start: Zone
    end: Zone

    

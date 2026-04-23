from dataclasses import dataclass, field


@dataclass(frozen=True)
class Node:
    id: int
    label: str
    y: float  # CRS.Simple pixel y-coordinate (Leaflet lat, origin bottom-left)
    x: float  # CRS.Simple pixel x-coordinate (Leaflet lng)


@dataclass(frozen=True)
class Edge:
    from_id: int
    to_id: int


@dataclass
class CampusGraph:
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)

    def get_node(self, id: int) -> Node | None:
        return next((n for n in self.nodes if n.id == id), None)

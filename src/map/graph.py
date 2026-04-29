from dataclasses import dataclass, field, replace


@dataclass(frozen=True)
class Node:
    id: int
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
    # Internal index for O(1) node lookup; kept in sync by add_node
    _node_index: dict[int, Node] = field(
        default_factory=dict, init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        self._node_index = {n.id: n for n in self.nodes}

    def add_node(self, node: Node) -> None:
        """Add a node, raising ValueError if its id already exists."""
        if node.id in self._node_index:
            raise ValueError(f"Node with id {node.id} already exists")
        self.nodes.append(node)
        self._node_index[node.id] = node

    def add_edge(self, edge: Edge) -> None:
        """Append an edge to the graph."""
        self.edges.append(edge)

    def get_node(self, node_id: int) -> Node | None:
        return self._node_index.get(node_id)

    def move_node(self, node_id: int, y: float, x: float) -> None:
        """Replace a node's position, raising KeyError if node_id is unknown."""
        existing = self._node_index[node_id]
        updated = replace(existing, y=y, x=x)
        self.nodes[self.nodes.index(existing)] = updated
        self._node_index[node_id] = updated

    def next_node_id(self) -> int:
        """Return the next sequential node ID (max existing ID + 1, or 0 if empty)."""
        return max((n.id for n in self.nodes), default=-1) + 1

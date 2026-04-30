import json
from dataclasses import dataclass, field, replace
from pathlib import Path


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
        """Append an edge to the graph, ignoring duplicates.

        Edges are semantically undirected walking routes, so an Edge(a, b) is
        rejected if an edge already exists between a and b in *either*
        direction — adding a second one would render as a parallel line on
        top of the first and would not represent a distinct route.
        """
        for existing in self.edges:
            same_direction = existing.from_id == edge.from_id and existing.to_id == edge.to_id
            reverse_direction = existing.from_id == edge.to_id and existing.to_id == edge.from_id
            if same_direction or reverse_direction:
                return
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
        """Return the next sequential node id (max existing id + 1, or 0 if empty)."""
        return max((n.id for n in self.nodes), default=-1) + 1

    def degree(self, node_id: int) -> int:
        """Return the number of edges incident to node_id (undirected count)."""
        return sum(1 for e in self.edges if e.from_id == node_id or e.to_id == node_id)

    def remove_node(self, node_id: int) -> None:
        """Remove a node and all its incident edges, raising KeyError if node_id is unknown."""
        node = self._node_index.pop(node_id)
        self.nodes.remove(node)
        self.edges[:] = [e for e in self.edges if e.from_id != node_id and e.to_id != node_id]

    def to_dict(self) -> dict:
        return {
            "nodes": [{"id": n.id, "y": n.y, "x": n.x} for n in self.nodes],
            "edges": [{"from_id": e.from_id, "to_id": e.to_id} for e in self.edges],
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "CampusGraph":
        if not isinstance(payload, dict):
            raise ValueError("Graph payload must be a dictionary")

        nodes_payload = payload.get("nodes")
        edges_payload = payload.get("edges")
        if not isinstance(nodes_payload, list) or not isinstance(edges_payload, list):
            raise ValueError("Graph payload must include list fields 'nodes' and 'edges'")

        graph = cls()

        for node_payload in nodes_payload:
            if not isinstance(node_payload, dict):
                raise ValueError("Each node must be a dictionary")
            if not all(key in node_payload for key in ("id", "y", "x")):
                raise ValueError("Each node must include 'id', 'y', and 'x'")
            graph.add_node(
                Node(
                    id=int(node_payload["id"]),
                    y=float(node_payload["y"]),
                    x=float(node_payload["x"]),
                )
            )

        for edge_payload in edges_payload:
            if not isinstance(edge_payload, dict):
                raise ValueError("Each edge must be a dictionary")
            if not all(key in edge_payload for key in ("from_id", "to_id")):
                raise ValueError("Each edge must include 'from_id' and 'to_id'")
            graph.add_edge(
                Edge(
                    from_id=int(edge_payload["from_id"]),
                    to_id=int(edge_payload["to_id"]),
                )
            )

        return graph

    def save_to_file(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load_from_file(cls, path: Path) -> "CampusGraph":
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(payload)

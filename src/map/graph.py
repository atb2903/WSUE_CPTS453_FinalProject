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
    nodes: list[Node] = field(default_factory = list)
    edges: list[Edge] = field(default_factory = list)
    # Internal index for O(1) node lookup; kept in sync by add_node
    _node_index: dict[int, Node] = field(
        default_factory = dict, init = False, repr = False, compare = False
    )

    def __post_init__(self) -> None:
        self._node_index = {n.id: n for n in self.nodes}

    def add_node(self, node: Node) -> None:
        """Add a node, raising ValueError if its id or (y, x) is already taken."""
        if node.id in self._node_index:
            raise ValueError(f"Node with id {node.id} already exists")
        if self._coordinate_in_use(node.y, node.x):
            raise ValueError(f"Node at coordinates ({node.y}, {node.x}) already exists")
        self.nodes.append(node)
        self._node_index[node.id] = node

    def add_edge(self, edge: Edge) -> None:
        """Append an edge to the graph, ignoring duplicates and self-loops.

        Edges are semantically undirected walking routes, so an Edge(a, b) is
        rejected if an edge already exists between a and b in *either*
        direction — adding a second one would render as a parallel line on
        top of the first and would not represent a distinct route. Self-loops
        (Edge(a, a)) are not meaningful walking routes and are silently dropped.
        """
        if edge.from_id == edge.to_id:
            return
        for existing in self.edges:
            same_direction = existing.from_id == edge.from_id and existing.to_id == edge.to_id
            reverse_direction = existing.from_id == edge.to_id and existing.to_id == edge.from_id
            if same_direction or reverse_direction:
                return
        self.edges.append(edge)

    def get_node(self, node_id: int) -> Node | None:
        return self._node_index.get(node_id)

    def move_node(self, node_id: int, y: float, x: float) -> None:
        """Replace a node's position; raise KeyError if node_id is unknown,
        ValueError if (y, x) is already taken by a different node.
        """
        existing = self._node_index[node_id]
        if self._coordinate_in_use(y, x, except_id = node_id):
            raise ValueError(f"Node at coordinates ({y}, {x}) already exists")
        updated = replace(existing, y = y, x = x)
        self.nodes[self.nodes.index(existing)] = updated
        self._node_index[node_id] = updated

    def _coordinate_in_use(
        self, y: float, x: float, *, except_id: int | None = None
    ) -> bool:
        """Return True if any node other than except_id occupies (y, x)."""
        return any(n.y == y and n.x == x and n.id != except_id for n in self.nodes)

    def next_node_id(self) -> int:
        """Return the next sequential node id (max existing id + 1, or 0 if empty)."""
        # TODO: this is simple and safe, but is too slow for something used this frequently. Optimize with memoization
        return max((n.id for n in self.nodes), default = -1) + 1

    def degree(self, node_id: int) -> int:
        """Return the number of edges incident to node_id (undirected count)."""
        return sum(1 for e in self.edges if e.from_id == node_id or e.to_id == node_id)

    def remove_node(self, node_id: int) -> None:
        """Remove a node and all its incident edges, raising KeyError if node_id is unknown."""
        # TODO: streamlit's aggressive reruns sometimes prevent this from finishing on high-degree nodes. 
        # User can work around by just doing it multiple times, but it's annoying. Find a way to detect and handle this.
        node = self._node_index.pop(node_id)
        self.nodes.remove(node)
        self.edges[:] = [e for e in self.edges if e.from_id != node_id and e.to_id != node_id]

    def remove_edge(self, from_id: int, to_id: int) -> bool:
        """Remove one edge for the undirected pair; return True if removed, else False."""
        for index, edge in enumerate(self.edges):
            same_direction = edge.from_id == from_id and edge.to_id == to_id
            reverse_direction = edge.from_id == to_id and edge.to_id == from_id
            if same_direction or reverse_direction:
                del self.edges[index]
                return True
        return False

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

        normalized_nodes, normalized_edges = cls._normalize_duplicate_locations(
            nodes_payload = nodes_payload,
            edges_payload = edges_payload,
        )

        graph = cls()

        for node_payload in normalized_nodes:
            graph.add_node(
                Node(
                    id = int(node_payload["id"]),
                    y = float(node_payload["y"]),
                    x = float(node_payload["x"]),
                )
            )

        for edge_payload in normalized_edges:
            graph.add_edge(
                Edge(
                    from_id = int(edge_payload["from_id"]),
                    to_id = int(edge_payload["to_id"]),
                )
            )

        return graph

    def save_to_file(self, path: Path) -> None:
        path.parent.mkdir(parents = True, exist_ok = True)
        path.write_text(json.dumps(self.to_dict(), indent = 2), encoding = "utf-8")

    @classmethod
    def load_from_file(cls, path: Path) -> "CampusGraph":
        payload = json.loads(path.read_text(encoding = "utf-8"))
        return cls.from_dict(payload)

    @staticmethod
    def _normalize_duplicate_locations(
        # Node placement detects and prevents this on new nodes, but not on existing nodes.
        # This method protects against it on loaded graphs, as the protection on node placement was added partway through development.
        nodes_payload: list[dict],
        edges_payload: list[dict],
    ) -> tuple[list[dict[str, float | int]], list[dict[str, int]]]:
        """Collapse duplicate node coordinates and remap edges to canonical ids."""
        deduplicated_nodes: list[dict[str, float | int]] = []
        remapped_edges: list[dict[str, int]] = []
        id_remap: dict[int, int] = {}
        coordinate_to_canonical_id: dict[tuple[float, float], int] = {}
        seen_ids: set[int] = set()

        for node_payload in nodes_payload:
            if not isinstance(node_payload, dict):
                raise ValueError("Each node must be a dictionary")
            if not all(key in node_payload for key in ("id", "y", "x")):
                raise ValueError("Each node must include 'id', 'y', and 'x'")

            node_id = int(node_payload["id"])
            node_y = float(node_payload["y"])
            node_x = float(node_payload["x"])
            if node_id in seen_ids:
                raise ValueError(f"Node with id {node_id} already exists")
            seen_ids.add(node_id)

            coordinate_key = (node_y, node_x)
            canonical_id = coordinate_to_canonical_id.get(coordinate_key)
            if canonical_id is None:
                coordinate_to_canonical_id[coordinate_key] = node_id
                deduplicated_nodes.append({"id": node_id, "y": node_y, "x": node_x})
                id_remap[node_id] = node_id
                continue

            id_remap[node_id] = canonical_id

        for edge_payload in edges_payload:
            if not isinstance(edge_payload, dict):
                raise ValueError("Each edge must be a dictionary")
            if not all(key in edge_payload for key in ("from_id", "to_id")):
                raise ValueError("Each edge must include 'from_id' and 'to_id'")

            from_id = int(edge_payload["from_id"])
            to_id = int(edge_payload["to_id"])
            remapped_edges.append(
                {
                    "from_id": id_remap.get(from_id, from_id),
                    "to_id": id_remap.get(to_id, to_id),
                }
            )

        return deduplicated_nodes, remapped_edges

# Graph Overlay Design

**Date:** 2026-04-22
**Status:** Approved

## Goal

Overlay a graph (nodes + edges) on the CRS.Simple campus map, starting with a two-node dummy graph. Establish reusable data and rendering architecture that graph algorithms and route visualization can build on later.

## Architecture

Approach B: separate `GraphOverlayRenderer` class, leaving `CampusMapRenderer` untouched.

```
src/map/graph.py           # Data model: Node, Edge, CampusGraph
src/map/graph_renderer.py  # GraphOverlayRenderer — renders a CampusGraph onto a folium.Map
src/app.py                 # Coordinator: builds base map, builds graph, renders overlay
```

## Data Model (`src/map/graph.py`)

Three dataclasses:

```python
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

    def get_node(self, id: int) -> Node | None: ...
```

`Node` and `Edge` are frozen (immutable); `CampusGraph` is mutable so nodes and edges can be added incrementally.

`id` is an `int` — purely internal, no need for string keys.

## Rendering (`src/map/graph_renderer.py`)

```python
class GraphOverlayRenderer:
    def __init__(self, graph: CampusGraph) -> None: ...
    def render_onto(self, campus_map: folium.Map) -> None: ...
```

- Draws **edges first** (`folium.PolyLine`), then **nodes on top** (`folium.CircleMarker`)
- Edges referencing unknown node IDs are silently skipped (no crash during incremental graph builds)
- Default color: `#717c7d` (WSU gray) for both nodes and edges
- `#981e32` (WSU crimson) is reserved for selected/highlighted nodes and edges (algorithm visualization, future work)
- Node `label` is exposed as the Leaflet tooltip

## Wiring (`src/app.py`)

`app.py` reads image dimensions directly via `PIL.Image.open` (one extra line), then:

1. Builds base map via `CampusMapRenderer`
2. Constructs a `CampusGraph` with two dummy nodes at opposite pixel corners:
   - Node 0 `"Node A"`: `y = height * 0.9, x = width * 0.1` (near top-left)
   - Node 1 `"Node B"`: `y = height * 0.1, x = width * 0.9` (near bottom-right)
   - Edge from 0 → 1
3. Calls `GraphOverlayRenderer(graph).render_onto(campus_map)`

## Testing

| File | Coverage |
|------|----------|
| `tests/test_graph.py` | `Node`, `Edge`, `CampusGraph` construction; `get_node` hit and miss |
| `tests/test_graph_renderer.py` | Correct number of `PolyLine` and `CircleMarker` children added to map; unknown-node-id edge is skipped without error |

All tests under `src/map/` must reach 100% coverage after every change (per project rules).

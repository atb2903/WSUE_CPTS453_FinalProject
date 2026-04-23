# Graph Overlay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Overlay a graph of nodes and edges on the campus map using a reusable data model and a dedicated renderer, starting with a two-node dummy graph.

**Architecture:** Approach B — `CampusMapRenderer` is untouched. A new `CampusGraph` data model lives in `src/map/graph.py`. A new `GraphOverlayRenderer` in `src/map/graph_renderer.py` draws nodes and edges onto any `folium.Map`. `app.py` coordinates them.

**Tech Stack:** Python 3.12, folium (`PolyLine`, `CircleMarker`), dataclasses, pytest, pytest-cov

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `src/map/graph.py` | `Node`, `Edge`, `CampusGraph` dataclasses |
| Create | `src/map/graph_renderer.py` | `GraphOverlayRenderer` — renders a `CampusGraph` onto a `folium.Map` |
| Create | `tests/test_graph.py` | Unit tests for the data model |
| Create | `tests/test_graph_renderer.py` | Unit tests for `GraphOverlayRenderer` |
| Modify | `src/app.py` | Wire up dummy graph and render the overlay |

---

## Task 1: Data model (`src/map/graph.py`)

**Files:**
- Create: `tests/test_graph.py`
- Create: `src/map/graph.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_graph.py`:

```python
import pytest
from dataclasses import FrozenInstanceError

from map.graph import Node, Edge, CampusGraph


def test_node_stores_attributes():
    node = Node(id=0, label="Test Node", y=100.0, x=200.0)
    assert node.id == 0
    assert node.label == "Test Node"
    assert node.y == 100.0
    assert node.x == 200.0


def test_node_is_immutable():
    node = Node(id=0, label="Test", y=0.0, x=0.0)
    with pytest.raises(FrozenInstanceError):
        node.id = 1  # type: ignore[misc]


def test_edge_stores_from_and_to():
    edge = Edge(from_id=0, to_id=1)
    assert edge.from_id == 0
    assert edge.to_id == 1


def test_edge_is_immutable():
    edge = Edge(from_id=0, to_id=1)
    with pytest.raises(FrozenInstanceError):
        edge.from_id = 2  # type: ignore[misc]


def test_campus_graph_starts_empty():
    graph = CampusGraph()
    assert graph.nodes == []
    assert graph.edges == []


def test_campus_graph_get_node_returns_matching_node():
    node = Node(id=42, label="A", y=1.0, x=2.0)
    graph = CampusGraph(nodes=[node])
    assert graph.get_node(42) is node


def test_campus_graph_get_node_returns_none_for_unknown_id():
    graph = CampusGraph()
    assert graph.get_node(99) is None
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
pytest tests/test_graph.py -v
```

Expected: `ERROR` — `ModuleNotFoundError: No module named 'map.graph'`

- [ ] **Step 3: Implement `src/map/graph.py`**

```python
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
```

- [ ] **Step 4: Run tests and confirm all pass with 100% coverage**

```bash
pytest tests/test_graph.py -v
```

Expected: 7 tests PASSED. Then run the full suite:

```bash
pytest
```

Expected: all tests PASSED, 100% coverage on `src/map`.

- [ ] **Step 5: Commit**

```bash
git add src/map/graph.py tests/test_graph.py
git commit -m "feat: add Node, Edge, CampusGraph data model"
```

---

## Task 2: Graph overlay renderer (`src/map/graph_renderer.py`)

**Files:**
- Create: `tests/test_graph_renderer.py`
- Create: `src/map/graph_renderer.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_graph_renderer.py`:

```python
import folium
from folium.vector_layers import CircleMarker, PolyLine

from map.graph import CampusGraph, Edge, Node
from map.graph_renderer import GraphOverlayRenderer


def _children_of_type(campus_map: folium.Map, kind: type) -> list:
    return [c for c in campus_map._children.values() if isinstance(c, kind)]


def _make_base_map() -> folium.Map:
    return folium.Map(crs="Simple")


def _make_two_node_graph() -> CampusGraph:
    return CampusGraph(
        nodes=[
            Node(id=0, label="Node A", y=900.0, x=100.0),
            Node(id=1, label="Node B", y=100.0, x=900.0),
        ],
        edges=[Edge(from_id=0, to_id=1)],
    )


def test_render_onto_adds_one_circle_marker_per_node():
    campus_map = _make_base_map()
    GraphOverlayRenderer(_make_two_node_graph()).render_onto(campus_map)
    assert len(_children_of_type(campus_map, CircleMarker)) == 2


def test_render_onto_adds_one_polyline_per_edge():
    campus_map = _make_base_map()
    GraphOverlayRenderer(_make_two_node_graph()).render_onto(campus_map)
    assert len(_children_of_type(campus_map, PolyLine)) == 1


def test_render_onto_skips_edge_with_unknown_from_id():
    campus_map = _make_base_map()
    graph = CampusGraph(
        nodes=[Node(id=1, label="B", y=100.0, x=900.0)],
        edges=[Edge(from_id=99, to_id=1)],
    )
    GraphOverlayRenderer(graph).render_onto(campus_map)
    assert len(_children_of_type(campus_map, PolyLine)) == 0


def test_render_onto_skips_edge_with_unknown_to_id():
    campus_map = _make_base_map()
    graph = CampusGraph(
        nodes=[Node(id=0, label="A", y=900.0, x=100.0)],
        edges=[Edge(from_id=0, to_id=99)],
    )
    GraphOverlayRenderer(graph).render_onto(campus_map)
    assert len(_children_of_type(campus_map, PolyLine)) == 0


def test_render_onto_empty_graph_adds_nothing():
    campus_map = _make_base_map()
    before = set(campus_map._children.keys())
    GraphOverlayRenderer(CampusGraph()).render_onto(campus_map)
    after = set(campus_map._children.keys())
    assert before == after
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
pytest tests/test_graph_renderer.py -v
```

Expected: `ERROR` — `ModuleNotFoundError: No module named 'map.graph_renderer'`

- [ ] **Step 3: Implement `src/map/graph_renderer.py`**

```python
import folium

from map.graph import CampusGraph

_COLOR = "#717c7d"  # WSU gray; crimson (#981e32) reserved for selected elements
_NODE_RADIUS = 8
_EDGE_WEIGHT = 3


class GraphOverlayRenderer:
    """
    Renders a CampusGraph onto a folium.Map using CRS.Simple pixel coordinates.

    Edges are drawn before nodes so nodes sit on top visually.
    Edges referencing unknown node IDs are silently skipped.
    """

    def __init__(self, graph: CampusGraph) -> None:
        self._graph = graph

    def render_onto(self, campus_map: folium.Map) -> None:
        """Draw the graph overlay onto campus_map in-place."""
        self._draw_edges(campus_map)
        self._draw_nodes(campus_map)

    def _draw_edges(self, campus_map: folium.Map) -> None:
        for edge in self._graph.edges:
            from_node = self._graph.get_node(edge.from_id)
            to_node = self._graph.get_node(edge.to_id)
            if from_node is None or to_node is None:
                continue
            folium.PolyLine(
                locations=[[from_node.y, from_node.x], [to_node.y, to_node.x]],
                color=_COLOR,
                weight=_EDGE_WEIGHT,
            ).add_to(campus_map)

    def _draw_nodes(self, campus_map: folium.Map) -> None:
        for node in self._graph.nodes:
            folium.CircleMarker(
                location=[node.y, node.x],
                radius=_NODE_RADIUS,
                color=_COLOR,
                fill=True,
                fill_opacity=1.0,
                tooltip=node.label,
            ).add_to(campus_map)
```

- [ ] **Step 4: Run tests and confirm all pass with 100% coverage**

```bash
pytest tests/test_graph_renderer.py -v
```

Expected: 5 tests PASSED. Then run the full suite:

```bash
pytest
```

Expected: all tests PASSED, 100% coverage on `src/map`.

- [ ] **Step 5: Commit**

```bash
git add src/map/graph_renderer.py tests/test_graph_renderer.py
git commit -m "feat: add GraphOverlayRenderer for drawing nodes and edges on the campus map"
```

---

## Task 3: Wire dummy graph into `app.py`

**Files:**
- Modify: `src/app.py`

The campus map image is 13200 × 10200 px. In CRS.Simple, origin is bottom-left, so:
- Node 0 "Node A" (near top-left): `y = 9180, x = 1320`
- Node 1 "Node B" (near bottom-right): `y = 1020, x = 11880`

- [ ] **Step 1: Update `src/app.py`**

Replace the contents of `src/app.py` with:

```python
from pathlib import Path

import streamlit as st
from PIL import Image
from streamlit_folium import st_folium

from map.graph import CampusGraph, Edge, Node
from map.graph_renderer import GraphOverlayRenderer
from map.renderer import CampusMapRenderer

# Path to the campus map image asset, relative to the project root
_IMAGE_PATH = Path("assets/map.png")

# Wide layout maximises the available map viewport area
st.set_page_config(page_title="WSU Map Viewer", layout="wide")
st.title("WSU Map Viewer")
st.caption("Pan by dragging and zoom with mouse wheel or +/- controls.")

# Stop early with a clear error rather than letting folium fail silently
if not _IMAGE_PATH.exists():
    st.error(f"Map image not found at: {_IMAGE_PATH}")
    st.stop()

# PIL returns (width, height); CRS.Simple uses [y, x] = [lat, lng]
Image.MAX_IMAGE_PIXELS = 200_000_000
with Image.open(_IMAGE_PATH) as img:
    image_width, image_height = img.size

campus_map = CampusMapRenderer(_IMAGE_PATH).build()

# Dummy graph: two nodes at opposite corners, one connecting edge
dummy_graph = CampusGraph(
    nodes=[
        Node(id=0, label="Node A", y=image_height * 0.9, x=image_width * 0.1),
        Node(id=1, label="Node B", y=image_height * 0.1, x=image_width * 0.9),
    ],
    edges=[Edge(from_id=0, to_id=1)],
)
GraphOverlayRenderer(dummy_graph).render_onto(campus_map)

# returned_objects=[] prevents Streamlit from re-running the script on every
# pan or zoom interaction, which would otherwise reset the map viewport state
st_folium(campus_map, width=None, height=760, returned_objects=[])
```

- [ ] **Step 2: Run the full test suite to confirm nothing broke**

```bash
pytest
```

Expected: all tests PASSED, 100% coverage on `src/map`.

- [ ] **Step 3: Smoke-test the app visually**

```bash
streamlit run src/app.py
```

Open the browser. Confirm: two gray circle markers visible at opposite corners, connected by a gray line. Hover a marker to confirm the tooltip shows "Node A" or "Node B".

- [ ] **Step 4: Commit**

```bash
git add src/app.py
git commit -m "feat: render dummy two-node graph overlay on campus map"
```

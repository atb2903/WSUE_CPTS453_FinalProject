# Edit / Navigation Modes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Navigation and Edit modes to the Streamlit app; Edit mode lets users click a node to select it (highlighted in WSU crimson), then click the map to move it there.

**Architecture:** Graph state moves into `st.session_state` so node positions persist across Streamlit reruns. `CampusGraph` gains a `move_node` mutation method. `GraphOverlayRenderer.render_onto` accepts an optional `selected_node_id` to highlight the active node. `app.py` gains a `st.segmented_control` mode toggle and an edit-mode event-handling block that reads drag positions from `st_folium`'s return dict.

**Tech Stack:** Python 3.12, Streamlit 1.56, folium, streamlit-folium, pytest, pytest-cov

---

## File Map

| File | Change |
|---|---|
| `src/map/graph.py` | Add `move_node` method; add `replace` to dataclasses import |
| `src/map/graph_renderer.py` | Rename `_COLOR` → `_WSU_GRAY`; add `_WSU_CRIMSON`; add `selected_node_id` param to `render_onto` and `_draw_nodes` |
| `src/app.py` | Session state init; `st.segmented_control` toggle; navigation/edit render branches; click-event handler |
| `tests/test_graph.py` | Add three `move_node` tests |
| `tests/test_graph_renderer.py` | Add three selection-color tests |

---

## Task 1: Add `CampusGraph.move_node`

**Files:**
- Modify: `src/map/graph.py`
- Test: `tests/test_graph.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_graph.py`:

```python
def test_move_node_updates_position_in_index_and_list():
    node = Node(id=0, label="A", y=0.0, x=0.0)
    graph = CampusGraph(nodes=[node])
    graph.move_node(0, y=500.0, x=300.0)
    updated = graph.get_node(0)
    assert updated.y == 500.0
    assert updated.x == 300.0
    assert graph.nodes[0].y == 500.0
    assert graph.nodes[0].x == 300.0


def test_move_node_preserves_id_and_label():
    node = Node(id=7, label="Campus Loc", y=0.0, x=0.0)
    graph = CampusGraph(nodes=[node])
    graph.move_node(7, y=100.0, x=200.0)
    updated = graph.get_node(7)
    assert updated.id == 7
    assert updated.label == "Campus Loc"


def test_move_node_raises_key_error_for_unknown_id():
    graph = CampusGraph()
    with pytest.raises(KeyError):
        graph.move_node(99, y=1.0, x=1.0)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_graph.py::test_move_node_updates_position_in_index_and_list tests/test_graph.py::test_move_node_preserves_id_and_label tests/test_graph.py::test_move_node_raises_key_error_for_unknown_id -v
```

Expected: 3 failures with `AttributeError: 'CampusGraph' object has no attribute 'move_node'`

- [ ] **Step 3: Update the import line in `src/map/graph.py`**

Replace:
```python
from dataclasses import dataclass, field
```
With:
```python
from dataclasses import dataclass, field, replace
```

- [ ] **Step 4: Add `move_node` to `CampusGraph` in `src/map/graph.py`**

Add after `get_node`:
```python
    def move_node(self, node_id: int, y: float, x: float) -> None:
        """Replace a node's position, raising KeyError if node_id is unknown."""
        existing = self._node_index[node_id]
        updated = replace(existing, y=y, x=x)
        self.nodes[self.nodes.index(existing)] = updated
        self._node_index[node_id] = updated
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_graph.py -v
```

Expected: all tests PASS

- [ ] **Step 6: Check coverage is still 100% on `src/map`**

```bash
pytest --cov=src/map --cov-report=term-missing
```

Expected: 100% coverage, all tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/map/graph.py tests/test_graph.py
git commit -m "feat: add CampusGraph.move_node for node repositioning"
```

---

## Task 2: Refactor color constants and add selection highlight to `GraphOverlayRenderer`

**Files:**
- Modify: `src/map/graph_renderer.py`
- Test: `tests/test_graph_renderer.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_graph_renderer.py`:

```python
def test_selected_node_renders_in_wsu_crimson():
    campus_map = _make_base_map()
    GraphOverlayRenderer(_make_two_node_graph()).render_onto(campus_map, selected_node_id=0)
    markers = _children_of_type(campus_map, CircleMarker)
    crimson = [m for m in markers if m.options["color"] == "#981e32"]
    assert len(crimson) == 1


def test_unselected_nodes_render_in_wsu_gray():
    campus_map = _make_base_map()
    GraphOverlayRenderer(_make_two_node_graph()).render_onto(campus_map, selected_node_id=0)
    markers = _children_of_type(campus_map, CircleMarker)
    gray = [m for m in markers if m.options["color"] == "#717c7d"]
    assert len(gray) == 1


def test_no_selection_all_nodes_render_in_wsu_gray():
    campus_map = _make_base_map()
    GraphOverlayRenderer(_make_two_node_graph()).render_onto(campus_map)
    markers = _children_of_type(campus_map, CircleMarker)
    assert all(m.options["color"] == "#717c7d" for m in markers)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_graph_renderer.py::test_selected_node_renders_in_wsu_crimson tests/test_graph_renderer.py::test_unselected_nodes_render_in_wsu_gray tests/test_graph_renderer.py::test_no_selection_all_nodes_render_in_wsu_gray -v
```

Expected: first two FAIL (signature mismatch / wrong color), third FAIL (color value `#3388ff` or `#717c7d` key not yet tested but `_COLOR` still exists)

- [ ] **Step 3: Replace `src/map/graph_renderer.py` with the updated version**

Full file content:

```python
import folium

from map.graph import CampusGraph

_WSU_GRAY = "#717c7d"
_WSU_CRIMSON = "#981e32"
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

    def render_onto(
        self, campus_map: folium.Map, selected_node_id: int | None = None
    ) -> None:
        """Draw the graph overlay onto campus_map in-place."""
        self._draw_edges(campus_map)
        self._draw_nodes(campus_map, selected_node_id)

    def _draw_edges(self, campus_map: folium.Map) -> None:
        for edge in self._graph.edges:
            from_node = self._graph.get_node(edge.from_id)
            to_node = self._graph.get_node(edge.to_id)
            if from_node is None or to_node is None:
                continue
            folium.PolyLine(
                locations=[[from_node.y, from_node.x], [to_node.y, to_node.x]],
                color=_WSU_GRAY,
                weight=_EDGE_WEIGHT,
            ).add_to(campus_map)

    def _draw_nodes(
        self, campus_map: folium.Map, selected_node_id: int | None
    ) -> None:
        for node in self._graph.nodes:
            color = _WSU_CRIMSON if node.id == selected_node_id else _WSU_GRAY
            folium.CircleMarker(
                location=[node.y, node.x],
                radius=_NODE_RADIUS,
                color=color,
                fill=True,
                fill_opacity=1.0,
                tooltip=node.label,
            ).add_to(campus_map)
```

- [ ] **Step 4: Run the full renderer test suite**

```bash
pytest tests/test_graph_renderer.py -v
```

Expected: all 8 tests PASS

- [ ] **Step 5: Check coverage is still 100% on `src/map`**

```bash
pytest --cov=src/map --cov-report=term-missing
```

Expected: 100% coverage, all tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/map/graph_renderer.py tests/test_graph_renderer.py
git commit -m "refactor: rename _COLOR to _WSU_GRAY/CRIMSON, add selected_node_id highlight"
```

---

## Task 3: Add mode toggle and edit mode to `app.py`

**Files:**
- Modify: `src/app.py`

No unit tests — `src/app.py` is outside the `src/map` coverage target. Verify manually by running the app.

- [ ] **Step 1: Replace `src/app.py` with the updated version**

Full file content:

```python
from pathlib import Path

import streamlit as st
from PIL import Image
from streamlit_folium import st_folium

from map.graph import CampusGraph, Edge, Node
from map.graph_renderer import GraphOverlayRenderer
from map.renderer import CampusMapRenderer

_IMAGE_PATH = Path("assets/map.png")

st.set_page_config(page_title="WSU Map Viewer", layout="wide")
st.title("WSU Map Viewer")

if not _IMAGE_PATH.exists():
    st.error(f"Map image not found at: {_IMAGE_PATH}")
    st.stop()

Image.MAX_IMAGE_PIXELS = 200_000_000
with Image.open(_IMAGE_PATH) as img:
    image_width, image_height = img.size

# --- Session state ---
if "graph" not in st.session_state:
    st.session_state.graph = CampusGraph(
        nodes=[
            Node(id=0, label="Node A", y=image_height * 0.9, x=image_width * 0.1),
            Node(id=1, label="Node B", y=image_height * 0.1, x=image_width * 0.9),
        ],
        edges=[Edge(from_id=0, to_id=1)],
    )
if "selected_node_id" not in st.session_state:
    st.session_state.selected_node_id = None
if "last_object_clicked" not in st.session_state:
    st.session_state.last_object_clicked = None
if "last_map_click" not in st.session_state:
    st.session_state.last_map_click = None

mode = st.segmented_control("Mode", ["Navigation", "Edit"], default="Navigation")

graph: CampusGraph = st.session_state.graph
campus_map = CampusMapRenderer(_IMAGE_PATH).build()

if mode == "Navigation":
    st.caption("Pan by dragging and zoom with mouse wheel or +/- controls.")
    GraphOverlayRenderer(graph).render_onto(campus_map)
    st_folium(campus_map, width=None, height=760, returned_objects=[])

else:  # Edit
    selected_id: int | None = st.session_state.selected_node_id
    selected_node = graph.get_node(selected_id) if selected_id is not None else None
    if selected_node is not None:
        st.caption(f"'{selected_node.label}' selected — click the map to move it.")
    else:
        st.caption("Click a node to select it, then click the map to move it.")

    GraphOverlayRenderer(graph).render_onto(campus_map, selected_node_id=selected_id)
    map_data = st_folium(
        campus_map,
        width=None,
        height=760,
        returned_objects=["last_object_clicked", "last_object_clicked_tooltip", "last_clicked"],
    )

    obj_clicked = map_data.get("last_object_clicked")
    tooltip = map_data.get("last_object_clicked_tooltip")
    map_click = map_data.get("last_clicked")

    new_node_click = obj_clicked != st.session_state.last_object_clicked
    new_map_click = map_click != st.session_state.last_map_click

    # Node click takes priority over map click if both changed in the same rerun
    if new_node_click and tooltip:
        matching = next((n for n in graph.nodes if n.label == tooltip), None)
        if matching is not None:
            st.session_state.last_object_clicked = obj_clicked
            st.session_state.selected_node_id = matching.id
            st.rerun()
    elif new_map_click and selected_id is not None and map_click:
        graph.move_node(selected_id, y=map_click["lat"], x=map_click["lng"])
        st.session_state.last_map_click = map_click
        st.session_state.selected_node_id = None
        st.rerun()
```

- [ ] **Step 2: Run the full test suite to confirm nothing regressed**

```bash
pytest --cov=src/map --cov-report=term-missing
```

Expected: all tests PASS, 100% coverage on `src/map`

- [ ] **Step 3: Start the app and manually verify navigation mode**

```bash
streamlit run src/app.py
```

Check:
- Segmented control shows "Navigation" selected by default
- Map renders with two nodes and one edge in WSU gray
- Pan and zoom work; no rerun flash on pan/zoom

- [ ] **Step 4: Manually verify edit mode**

In the running app:
- Switch to "Edit" mode
- Caption reads "Click a node to select it..."
- Click Node A — it turns crimson, caption updates to "'Node A' selected — click the map to move it."
- Click somewhere else on the map — Node A moves there, edge redraws, selection clears
- Switch back to Navigation — nodes render in gray, pan/zoom remain smooth

- [ ] **Step 5: Commit**

```bash
git add src/app.py
git commit -m "feat: add Navigation/Edit mode toggle with click-to-reposition nodes"
```

# Node Creation in Edit Mode — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add node creation to Edit mode via a typed `EditController` state machine, migrating all existing Edit-mode logic into it.

**Architecture:** `EditState` (frozen dataclass) holds the current state enum, active node ID, and last-seen click values; `EditController` (stateless service) takes a graph and state, handles a `st_folium` map-data dict, mutates the graph in-place, and returns a new `EditState`. `app.py`'s Edit block is reduced to: render → call `st_folium` → call `controller.handle_click()` → rerun if state changed.

**Tech Stack:** Python 3.12, Streamlit, folium/streamlit-folium, pytest, dataclasses, enum

> **Git note:** Do NOT make any git commits during execution. The user commits manually on request.

---

### Task 1: Remove `label` from `Node` and update all call sites

**Files:**
- Modify: `src/map/graph.py`
- Modify: `tests/test_graph.py`

- [ ] **Step 1: Replace `tests/test_graph.py` with the updated version (label removed everywhere)**

```python
import pytest
from dataclasses import FrozenInstanceError

from map.graph import Node, Edge, CampusGraph


def test_node_stores_attributes():
    node = Node(id=0, y=100.0, x=200.0)
    assert node.id == 0
    assert node.y == 100.0
    assert node.x == 200.0


def test_node_is_immutable():
    node = Node(id=0, y=0.0, x=0.0)
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
    node = Node(id=42, y=1.0, x=2.0)
    graph = CampusGraph(nodes=[node])
    assert graph.get_node(42) is node


def test_campus_graph_get_node_returns_none_for_unknown_id():
    graph = CampusGraph()
    assert graph.get_node(99) is None


def test_campus_graph_get_node_finds_correct_node_among_multiple():
    node_a = Node(id=0, y=0.0, x=0.0)
    node_b = Node(id=1, y=1.0, x=1.0)
    node_c = Node(id=2, y=2.0, x=2.0)
    graph = CampusGraph(nodes=[node_a, node_b, node_c])
    assert graph.get_node(1) is node_b


def test_add_node_appends_and_indexes_node():
    graph = CampusGraph()
    node = Node(id=0, y=0.0, x=0.0)
    graph.add_node(node)
    assert node in graph.nodes
    assert graph.get_node(0) is node


def test_add_node_raises_on_duplicate_id():
    graph = CampusGraph()
    node = Node(id=0, y=0.0, x=0.0)
    graph.add_node(node)
    with pytest.raises(ValueError, match="already exists"):
        graph.add_node(Node(id=0, y=1.0, x=1.0))


def test_add_edge_appends_edge():
    graph = CampusGraph()
    edge = Edge(from_id=0, to_id=1)
    graph.add_edge(edge)
    assert edge in graph.edges


def test_move_node_updates_position_in_index_and_list():
    node = Node(id=0, y=0.0, x=0.0)
    graph = CampusGraph(nodes=[node])
    graph.move_node(0, y=500.0, x=300.0)
    updated = graph.get_node(0)
    assert updated.y == 500.0
    assert updated.x == 300.0
    assert graph.nodes[0].y == 500.0
    assert graph.nodes[0].x == 300.0


def test_move_node_preserves_id():
    node = Node(id=7, y=0.0, x=0.0)
    graph = CampusGraph(nodes=[node])
    graph.move_node(7, y=100.0, x=200.0)
    updated = graph.get_node(7)
    assert updated.id == 7


def test_move_node_raises_key_error_for_unknown_id():
    graph = CampusGraph()
    with pytest.raises(KeyError):
        graph.move_node(99, y=1.0, x=1.0)
```

- [ ] **Step 2: Update `Node` in `src/map/graph.py` — remove the `label` field**

Replace the `Node` dataclass with:

```python
@dataclass(frozen=True)
class Node:
    id: int
    y: float  # CRS.Simple pixel y-coordinate (Leaflet lat, origin bottom-left)
    x: float  # CRS.Simple pixel x-coordinate (Leaflet lng)
```

- [ ] **Step 3: Run tests to confirm everything passes**

```
pytest
```

Expected: all tests pass, 100% coverage.

---

### Task 2: Add `CampusGraph.next_node_id()`

**Files:**
- Modify: `src/map/graph.py`
- Modify: `tests/test_graph.py`

- [ ] **Step 1: Add failing tests to `tests/test_graph.py`**

Append to the end of the file:

```python
def test_next_node_id_returns_zero_for_empty_graph():
    assert CampusGraph().next_node_id() == 0


def test_next_node_id_returns_max_id_plus_one():
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0), Node(id=3, y=0.0, x=0.0)])
    assert graph.next_node_id() == 4


def test_next_node_id_reflects_added_nodes():
    graph = CampusGraph()
    graph.add_node(Node(id=5, y=0.0, x=0.0))
    assert graph.next_node_id() == 6
```

- [ ] **Step 2: Run tests to confirm they fail**

```
pytest tests/test_graph.py -v -k "next_node_id"
```

Expected: `AttributeError: 'CampusGraph' object has no attribute 'next_node_id'`

- [ ] **Step 3: Implement `next_node_id()` in `src/map/graph.py`**

Add after `move_node`:

```python
def next_node_id(self) -> int:
    """Return the smallest unused node ID (max existing ID + 1, or 0 if empty)."""
    return max((n.id for n in self.nodes), default=-1) + 1
```

- [ ] **Step 4: Run tests to confirm they pass**

```
pytest
```

Expected: all tests pass, 100% coverage.

---

### Task 3: Update `GraphOverlayRenderer` — rename param, use ID as tooltip

**Files:**
- Modify: `src/map/graph_renderer.py`
- Modify: `tests/test_graph_renderer.py`

- [ ] **Step 1: Replace `tests/test_graph_renderer.py` with the updated version**

```python
import folium
from folium.vector_layers import CircleMarker, PolyLine

from map.graph import CampusGraph, Edge, Node
from map.graph_renderer import GraphOverlayRenderer


def _children_of_type(parent, kind: type) -> list:
    return [c for c in parent._children.values() if isinstance(c, kind)]


def _make_base_map() -> folium.Map:
    return folium.Map(crs="Simple")


def _make_two_node_graph() -> CampusGraph:
    return CampusGraph(
        nodes=[
            Node(id=0, y=900.0, x=100.0),
            Node(id=1, y=100.0, x=900.0),
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
        nodes=[Node(id=1, y=100.0, x=900.0)],
        edges=[Edge(from_id=99, to_id=1)],
    )
    GraphOverlayRenderer(graph).render_onto(campus_map)
    assert len(_children_of_type(campus_map, PolyLine)) == 0


def test_render_onto_skips_edge_with_unknown_to_id():
    campus_map = _make_base_map()
    graph = CampusGraph(
        nodes=[Node(id=0, y=900.0, x=100.0)],
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


def test_highlighted_node_renders_in_wsu_crimson():
    campus_map = _make_base_map()
    GraphOverlayRenderer(_make_two_node_graph()).render_onto(campus_map, highlighted_node_id=0)
    markers = _children_of_type(campus_map, CircleMarker)
    assert len([m for m in markers if m.options["color"] == "#981e32"]) == 1


def test_unhighlighted_nodes_render_in_wsu_gray():
    campus_map = _make_base_map()
    GraphOverlayRenderer(_make_two_node_graph()).render_onto(campus_map, highlighted_node_id=0)
    markers = _children_of_type(campus_map, CircleMarker)
    assert len([m for m in markers if m.options["color"] == "#717c7d"]) == 1


def test_no_highlight_all_nodes_render_in_wsu_gray():
    campus_map = _make_base_map()
    GraphOverlayRenderer(_make_two_node_graph()).render_onto(campus_map)
    markers = _children_of_type(campus_map, CircleMarker)
    assert all(m.options["color"] == "#717c7d" for m in markers)


def test_node_tooltip_is_string_id():
    fg = folium.FeatureGroup()
    graph = CampusGraph(nodes=[Node(id=7, y=0.0, x=0.0)])
    GraphOverlayRenderer(graph).render_onto(fg)
    markers = _children_of_type(fg, CircleMarker)
    assert len(markers) == 1
    tooltips = [c for c in markers[0]._children.values() if isinstance(c, folium.Tooltip)]
    assert len(tooltips) == 1
    assert tooltips[0].text == "7"
```

- [ ] **Step 2: Run tests to confirm they fail**

```
pytest tests/test_graph_renderer.py -v
```

Expected: failures due to `selected_node_id` keyword argument and missing `highlighted_node_id`.

- [ ] **Step 3: Update `src/map/graph_renderer.py`**

Replace the file with:

```python
import folium

from map.graph import CampusGraph

_WSU_GRAY = "#717c7d"
_WSU_CRIMSON = "#981e32"
_NODE_RADIUS = 8
_EDGE_WEIGHT = 3


class GraphOverlayRenderer:
    """
    Renders a CampusGraph onto a folium.Map or folium.FeatureGroup using
    CRS.Simple pixel coordinates.

    Edges are drawn before nodes so nodes sit on top visually.
    Edges referencing unknown node IDs are silently skipped.
    """

    def __init__(self, graph: CampusGraph) -> None:
        self._graph = graph

    def render_onto(
        self,
        parent: folium.Map | folium.FeatureGroup,
        highlighted_node_id: int | None = None,
    ) -> None:
        """Draw the graph overlay onto parent in-place."""
        self._draw_edges(parent)
        self._draw_nodes(parent, highlighted_node_id)

    def _draw_edges(self, parent: folium.Map | folium.FeatureGroup) -> None:
        for edge in self._graph.edges:
            from_node = self._graph.get_node(edge.from_id)
            to_node = self._graph.get_node(edge.to_id)
            if from_node is None or to_node is None:
                continue
            folium.PolyLine(
                locations=[[from_node.y, from_node.x], [to_node.y, to_node.x]],
                color=_WSU_GRAY,
                weight=_EDGE_WEIGHT,
            ).add_to(parent)

    def _draw_nodes(
        self, parent: folium.Map | folium.FeatureGroup, highlighted_node_id: int | None
    ) -> None:
        for node in self._graph.nodes:
            color = _WSU_CRIMSON if node.id == highlighted_node_id else _WSU_GRAY
            folium.CircleMarker(
                location=[node.y, node.x],
                radius=_NODE_RADIUS,
                color=color,
                fill=True,
                fill_opacity=1.0,
                tooltip=str(node.id),
            ).add_to(parent)
```

- [ ] **Step 4: Run tests to confirm they pass**

```
pytest
```

Expected: all tests pass, 100% coverage.

---

### Task 4: Create `EditState` with state enum and caption property

**Files:**
- Create: `src/map/edit_controller.py`
- Create: `tests/test_edit_controller.py`

- [ ] **Step 1: Write failing tests for `EditState` in `tests/test_edit_controller.py`**

```python
import pytest
from dataclasses import FrozenInstanceError

from map.edit_controller import EditState, State


def test_edit_state_defaults_to_idle():
    state = EditState()
    assert state.state == State.IDLE
    assert state.active_node_id is None
    assert state.last_object_clicked is None
    assert state.last_map_click is None


def test_edit_state_is_immutable():
    state = EditState()
    with pytest.raises(FrozenInstanceError):
        state.state = State.NODE_SELECTED  # type: ignore[misc]


def test_edit_state_caption_idle():
    assert EditState().caption == (
        "Click a node to select it and move it, or click empty space to add a new node."
    )


def test_edit_state_caption_node_selected():
    state = EditState(state=State.NODE_SELECTED, active_node_id=3)
    assert state.caption == "Node 3 selected — click the map to move it."


def test_edit_state_caption_pending_node():
    state = EditState(state=State.PENDING_NODE, active_node_id=0)
    assert state.caption == (
        "Node placed — click an existing node to connect it, "
        "or click empty space to add a connected node."
    )
```

- [ ] **Step 2: Run tests to confirm they fail**

```
pytest tests/test_edit_controller.py -v
```

Expected: `ModuleNotFoundError: No module named 'map.edit_controller'`

- [ ] **Step 3: Create `src/map/edit_controller.py` with `State` enum and `EditState`**

```python
from dataclasses import dataclass
from enum import Enum, auto

from map.graph import CampusGraph, Edge, Node


class State(Enum):
    IDLE = auto()
    NODE_SELECTED = auto()
    PENDING_NODE = auto()


@dataclass(frozen=True)
class EditState:
    state: State = State.IDLE
    active_node_id: int | None = None
    last_object_clicked: dict | None = None
    last_map_click: dict | None = None

    @property
    def caption(self) -> str:
        if self.state == State.NODE_SELECTED:
            return f"Node {self.active_node_id} selected — click the map to move it."
        if self.state == State.PENDING_NODE:
            return (
                "Node placed — click an existing node to connect it, "
                "or click empty space to add a connected node."
            )
        return "Click a node to select it and move it, or click empty space to add a new node."
```

- [ ] **Step 4: Run tests to confirm they pass**

```
pytest
```

Expected: all tests pass, 100% coverage.

---

### Task 5: `EditController` — no-op and IDLE node-click

**Files:**
- Modify: `src/map/edit_controller.py`
- Modify: `tests/test_edit_controller.py`

- [ ] **Step 1: Add failing tests to `tests/test_edit_controller.py`**

```python
from map.graph import CampusGraph, Node
from map.edit_controller import EditController, EditState, State


def test_handle_click_no_change_returns_same_state():
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0)])
    state = EditState(
        last_object_clicked={"lat": 0.0, "lng": 0.0},
        last_map_click={"lat": 0.0, "lng": 0.0},
    )
    map_data = {
        "last_object_clicked": {"lat": 0.0, "lng": 0.0},
        "last_object_clicked_tooltip": None,
        "last_clicked": {"lat": 0.0, "lng": 0.0},
    }
    assert EditController(graph, state).handle_click(map_data) is state


def test_idle_node_click_transitions_to_node_selected():
    graph = CampusGraph(nodes=[Node(id=5, y=100.0, x=200.0)])
    state = EditState()  # IDLE, last_object_clicked=None
    map_data = {
        "last_object_clicked": {"lat": 100.0, "lng": 200.0},
        "last_object_clicked_tooltip": "5",
        "last_clicked": {"lat": 100.0, "lng": 200.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.NODE_SELECTED
    assert new_state.active_node_id == 5


def test_idle_node_click_ignores_unknown_tooltip():
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0)])
    state = EditState()
    map_data = {
        "last_object_clicked": {"lat": 0.0, "lng": 0.0},
        "last_object_clicked_tooltip": "999",
        "last_clicked": {"lat": 0.0, "lng": 0.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.IDLE
```

- [ ] **Step 2: Run tests to confirm they fail**

```
pytest tests/test_edit_controller.py -v -k "handle_click or node_click"
```

Expected: `AttributeError: type object 'EditController' not found` or similar.

- [ ] **Step 3: Add `EditController` to `src/map/edit_controller.py`**

Add after the `EditState` class:

```python
class EditController:
    """
    Stateless service that applies Edit-mode interaction logic.

    Inspects raw st_folium map_data, mutates the graph in-place for structural
    changes (add/move nodes and edges), and returns a new EditState.
    """

    def __init__(self, graph: CampusGraph, edit_state: EditState) -> None:
        self._graph = graph
        self._edit_state = edit_state

    def handle_click(self, map_data: dict) -> EditState:
        """Apply one interaction event; return unchanged state if nothing new."""
        obj_clicked = map_data.get("last_object_clicked")
        tooltip = map_data.get("last_object_clicked_tooltip")
        map_click = map_data.get("last_clicked")

        new_node_click = obj_clicked != self._edit_state.last_object_clicked
        new_map_click = map_click != self._edit_state.last_map_click

        # Node click takes priority when both change in the same rerun
        if new_node_click and tooltip:
            node = self._node_from_tooltip(tooltip)
            if node is not None:
                return self._handle_node_click(node, obj_clicked, map_click)

        if new_map_click and map_click:
            return self._handle_map_click(map_click)

        return self._edit_state

    def _node_from_tooltip(self, tooltip: str) -> Node | None:
        try:
            return self._graph.get_node(int(tooltip))
        except (ValueError, TypeError):
            return None

    def _handle_node_click(
        self, node: Node, obj_clicked: dict, map_click: dict | None
    ) -> EditState:
        # Consume any concurrent map-click by storing its value,
        # preventing the next rerun from misreading it as a new event.
        consumed_map_click = map_click
        if self._edit_state.state == State.PENDING_NODE:
            return self._connect_pending_to(node, obj_clicked, consumed_map_click)
        return EditState(
            state=State.NODE_SELECTED,
            active_node_id=node.id,
            last_object_clicked=obj_clicked,
            last_map_click=consumed_map_click,
        )

    def _connect_pending_to(
        self, node: Node, obj_clicked: dict, map_click: dict | None
    ) -> EditState:
        if node.id == self._edit_state.active_node_id:
            # Clicking the pending node itself: stay pending, consume clicks
            return EditState(
                state=State.PENDING_NODE,
                active_node_id=self._edit_state.active_node_id,
                last_object_clicked=obj_clicked,
                last_map_click=map_click,
            )
        self._graph.add_edge(Edge(from_id=self._edit_state.active_node_id, to_id=node.id))
        return EditState(
            state=State.IDLE,
            last_object_clicked=obj_clicked,
            last_map_click=map_click,
        )

    def _handle_map_click(self, map_click: dict) -> EditState:
        state = self._edit_state.state
        if state == State.NODE_SELECTED:
            self._graph.move_node(
                self._edit_state.active_node_id,
                y=map_click["lat"],
                x=map_click["lng"],
            )
            return EditState(state=State.IDLE, last_map_click=map_click)
        if state == State.PENDING_NODE:
            return self._create_connected_node(map_click)
        # IDLE: create new node, enter pending
        return self._create_pending_node(map_click)

    def _create_pending_node(self, map_click: dict) -> EditState:
        new_id = self._graph.next_node_id()
        self._graph.add_node(Node(id=new_id, y=map_click["lat"], x=map_click["lng"]))
        return EditState(
            state=State.PENDING_NODE,
            active_node_id=new_id,
            last_map_click=map_click,
        )

    def _create_connected_node(self, map_click: dict) -> EditState:
        new_id = self._graph.next_node_id()
        self._graph.add_node(Node(id=new_id, y=map_click["lat"], x=map_click["lng"]))
        self._graph.add_edge(Edge(from_id=self._edit_state.active_node_id, to_id=new_id))
        return EditState(state=State.IDLE, last_map_click=map_click)
```

- [ ] **Step 4: Run tests to confirm they pass**

```
pytest
```

Expected: all tests pass, 100% coverage.

---

### Task 6: `EditController` — IDLE map-click creates a pending node

**Files:**
- Modify: `tests/test_edit_controller.py`

- [ ] **Step 1: Add failing tests**

```python
def test_idle_map_click_creates_node_and_enters_pending():
    graph = CampusGraph()
    state = EditState()
    map_data = {
        "last_object_clicked": None,
        "last_object_clicked_tooltip": None,
        "last_clicked": {"lat": 300.0, "lng": 400.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.PENDING_NODE
    assert len(graph.nodes) == 1
    created = graph.nodes[0]
    assert created.y == 300.0
    assert created.x == 400.0
    assert new_state.active_node_id == created.id


def test_idle_map_click_assigns_next_available_id():
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=1.0, x=1.0)])
    state = EditState()
    map_data = {
        "last_object_clicked": None,
        "last_object_clicked_tooltip": None,
        "last_clicked": {"lat": 50.0, "lng": 60.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.active_node_id == 2
```

- [ ] **Step 2: Run tests to confirm they fail**

```
pytest tests/test_edit_controller.py -v -k "idle_map_click"
```

Expected: FAIL — the IDLE map-click path is not yet implemented (Task 5 added the shell but the `_create_pending_node` helper call path may not be wired). If they unexpectedly pass, continue to Step 4.

- [ ] **Step 3: Verify `_handle_map_click` in `edit_controller.py` reaches `_create_pending_node` for IDLE state**

The implementation from Task 5 already includes this path:

```python
def _handle_map_click(self, map_click: dict) -> EditState:
    state = self._edit_state.state
    if state == State.NODE_SELECTED:
        ...
    if state == State.PENDING_NODE:
        return self._create_connected_node(map_click)
    # IDLE: create new node, enter pending
    return self._create_pending_node(map_click)
```

If these tests fail for a different reason (e.g., import error), fix it now before proceeding.

- [ ] **Step 4: Run tests to confirm they pass**

```
pytest
```

Expected: all tests pass, 100% coverage.

---

### Task 7: `EditController` — `NODE_SELECTED` transitions

**Files:**
- Modify: `tests/test_edit_controller.py`

- [ ] **Step 1: Add failing tests**

```python
def test_node_selected_map_click_moves_node_and_returns_idle():
    node = Node(id=0, y=0.0, x=0.0)
    graph = CampusGraph(nodes=[node])
    state = EditState(state=State.NODE_SELECTED, active_node_id=0)
    map_data = {
        "last_object_clicked": None,
        "last_object_clicked_tooltip": None,
        "last_clicked": {"lat": 500.0, "lng": 300.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.IDLE
    moved = graph.get_node(0)
    assert moved.y == 500.0
    assert moved.x == 300.0


def test_node_selected_node_click_changes_selection():
    node_a = Node(id=0, y=0.0, x=0.0)
    node_b = Node(id=1, y=100.0, x=100.0)
    graph = CampusGraph(nodes=[node_a, node_b])
    state = EditState(state=State.NODE_SELECTED, active_node_id=0)
    map_data = {
        "last_object_clicked": {"lat": 100.0, "lng": 100.0},
        "last_object_clicked_tooltip": "1",
        "last_clicked": {"lat": 100.0, "lng": 100.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.NODE_SELECTED
    assert new_state.active_node_id == 1
```

- [ ] **Step 2: Run tests to confirm they fail**

```
pytest tests/test_edit_controller.py -v -k "node_selected"
```

Expected: FAIL — `NODE_SELECTED` paths in `_handle_node_click` and `_handle_map_click` are not yet exercised by passing tests. If they pass, proceed directly to Step 4.

- [ ] **Step 3: Verify the `NODE_SELECTED` paths in `edit_controller.py`**

`_handle_node_click` for `NODE_SELECTED` falls through to the `else` branch (same as IDLE) and returns `NODE_SELECTED` with the new node ID — this is already in the Task 5 implementation. `_handle_map_click` for `NODE_SELECTED` calls `move_node` then returns `IDLE` — also already there. If tests still fail, debug accordingly.

- [ ] **Step 4: Run tests to confirm they pass**

```
pytest
```

Expected: all tests pass, 100% coverage.

---

### Task 8: `EditController` — `PENDING_NODE` transitions and priority ordering

**Files:**
- Modify: `tests/test_edit_controller.py`

- [ ] **Step 1: Add failing tests**

```python
def test_pending_node_existing_node_click_adds_edge_and_returns_idle():
    existing = Node(id=0, y=0.0, x=0.0)
    pending = Node(id=1, y=50.0, x=50.0)
    graph = CampusGraph(nodes=[existing, pending])
    state = EditState(state=State.PENDING_NODE, active_node_id=1)
    map_data = {
        "last_object_clicked": {"lat": 0.0, "lng": 0.0},
        "last_object_clicked_tooltip": "0",
        "last_clicked": {"lat": 0.0, "lng": 0.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.IDLE
    assert len(graph.edges) == 1
    edge = graph.edges[0]
    assert edge.from_id == 1
    assert edge.to_id == 0


def test_pending_node_map_click_creates_connected_second_node_and_returns_idle():
    pending = Node(id=0, y=10.0, x=10.0)
    graph = CampusGraph(nodes=[pending])
    state = EditState(state=State.PENDING_NODE, active_node_id=0)
    map_data = {
        "last_object_clicked": None,
        "last_object_clicked_tooltip": None,
        "last_clicked": {"lat": 200.0, "lng": 300.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.IDLE
    assert len(graph.nodes) == 2
    second_node = graph.get_node(1)
    assert second_node.y == 200.0
    assert second_node.x == 300.0
    assert len(graph.edges) == 1
    assert graph.edges[0].from_id == 0
    assert graph.edges[0].to_id == 1


def test_pending_node_self_click_stays_pending():
    pending = Node(id=2, y=50.0, x=50.0)
    graph = CampusGraph(nodes=[pending])
    state = EditState(state=State.PENDING_NODE, active_node_id=2)
    map_data = {
        "last_object_clicked": {"lat": 50.0, "lng": 50.0},
        "last_object_clicked_tooltip": "2",
        "last_clicked": {"lat": 50.0, "lng": 50.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.PENDING_NODE
    assert new_state.active_node_id == 2
    assert len(graph.edges) == 0


def test_node_click_takes_priority_over_concurrent_map_click():
    # When a node click fires, streamlit-folium also updates last_clicked.
    # The controller must handle the node click and consume the map click.
    node = Node(id=0, y=100.0, x=200.0)
    graph = CampusGraph(nodes=[node])
    state = EditState()  # IDLE, both lasts = None
    map_data = {
        "last_object_clicked": {"lat": 100.0, "lng": 200.0},
        "last_object_clicked_tooltip": "0",
        "last_clicked": {"lat": 100.0, "lng": 200.0},  # concurrent — must be consumed
    }
    new_state = EditController(graph, state).handle_click(map_data)
    # Should select node, not also create a new one
    assert new_state.state == State.NODE_SELECTED
    assert new_state.active_node_id == 0
    assert len(graph.nodes) == 1  # no new node created
    # Concurrent map click consumed: next rerun with same last_clicked won't re-fire
    assert new_state.last_map_click == {"lat": 100.0, "lng": 200.0}
```

- [ ] **Step 2: Run tests to confirm they fail**

```
pytest tests/test_edit_controller.py -v -k "pending_node or priority"
```

Expected: FAIL — `PENDING_NODE` paths exist in the implementation but have not been fully exercised yet (or may have a bug). Fix any failures before proceeding.

- [ ] **Step 3: Verify `PENDING_NODE` paths in `edit_controller.py`**

`_connect_pending_to` and `_create_connected_node` were added in Task 5. Walk through each test case manually against the code:
- `pending + existing node click` → `_handle_node_click` → `_connect_pending_to` (node.id ≠ active_node_id) → `add_edge`, return IDLE ✓
- `pending + map click` → `_handle_map_click` → `state == PENDING_NODE` → `_create_connected_node` → `add_node` + `add_edge`, return IDLE ✓
- `pending + self click` → `_connect_pending_to` (node.id == active_node_id) → stay PENDING ✓
- Priority test → `new_node_click` branch fires first, map click consumed via `last_map_click=map_click` ✓

Fix any discrepancies found.

- [ ] **Step 4: Run full test suite**

```
pytest
```

Expected: all tests pass, 100% coverage on `src/map/`.

---

### Task 9: Update `app.py` to use `EditController`

**Files:**
- Modify: `src/app.py`

`app.py` is not covered by the automated test suite. After making changes, manually start the app and verify all three Edit-mode interactions work: select+move, create+connect-to-existing, create+connect-to-new.

- [ ] **Step 1: Replace `src/app.py` with the updated version**

```python
from pathlib import Path

import folium
import streamlit as st
from PIL import Image
from streamlit_folium import st_folium

from map.edit_controller import EditController, EditState
from map.graph import CampusGraph, Edge, Node
from map.graph_renderer import GraphOverlayRenderer
from map.renderer import CampusMapRenderer

_IMAGE_PATH = Path("assets/map.png")

st.set_page_config(page_title="WSU Map Viewer", layout="wide")
st.title("WSU Map Viewer")

if not _IMAGE_PATH.exists():
    st.error(f"Map image not found at: {_IMAGE_PATH}")
    st.stop()


@st.cache_data
def _image_size(path: Path) -> tuple[int, int]:
    Image.MAX_IMAGE_PIXELS = 200_000_000
    with Image.open(path) as img:
        return img.size


image_width, image_height = _image_size(_IMAGE_PATH)

# --- Session state ---
if "graph" not in st.session_state:
    st.session_state.graph = CampusGraph(
        nodes=[
            Node(id=0, y=image_height * 0.9, x=image_width * 0.1),
            Node(id=1, y=image_height * 0.1, x=image_width * 0.9),
        ],
        edges=[Edge(from_id=0, to_id=1)],
    )
if "edit_state" not in st.session_state:
    st.session_state.edit_state = EditState()

mode = st.segmented_control("Mode", ["Navigation", "Edit"], default="Navigation")

graph: CampusGraph = st.session_state.graph
campus_map = CampusMapRenderer(_IMAGE_PATH).build()

if mode == "Navigation":
    # Reset edit state so re-entering Edit mode starts clean
    st.session_state.edit_state = EditState()
    st.caption("Pan by dragging and zoom with mouse wheel or +/- controls.")
    fg = folium.FeatureGroup()
    GraphOverlayRenderer(graph).render_onto(fg)
    st_folium(campus_map, width=None, height=760, returned_objects=[], feature_group_to_add=fg)

else:  # Edit
    edit_state: EditState = st.session_state.edit_state
    st.caption(edit_state.caption)

    fg = folium.FeatureGroup()
    GraphOverlayRenderer(graph).render_onto(fg, highlighted_node_id=edit_state.active_node_id)
    map_data = st_folium(
        campus_map,
        width=None,
        height=760,
        returned_objects=["last_object_clicked", "last_object_clicked_tooltip", "last_clicked"],
        feature_group_to_add=fg,
        key="campus_map_edit",
    )

    new_edit_state = EditController(graph, edit_state).handle_click(map_data)
    if new_edit_state != edit_state:
        st.session_state.edit_state = new_edit_state
        st.rerun()
```

- [ ] **Step 2: Run the full test suite one final time**

```
pytest
```

Expected: all tests pass, 100% coverage on `src/map/`.

- [ ] **Step 3: Start the app and verify manually**

```
streamlit run src/app.py
```

Verify these scenarios in the browser:
1. **Select + move:** Edit mode → click a node (turns crimson) → click elsewhere → node moves
2. **Create + connect to existing:** Edit mode → click empty space (new node appears crimson) → click the other existing node → edge appears between them
3. **Create + connect to new:** Edit mode → click empty space (first new node, crimson) → click another empty space → two new nodes appear connected by an edge
4. **Mode reset:** Switch to Navigation → switch back to Edit → state is IDLE (no node highlighted)
5. **Caption updates:** Confirm the caption string changes correctly for each state

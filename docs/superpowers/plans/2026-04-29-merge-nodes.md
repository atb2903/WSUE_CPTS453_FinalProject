# Merge Nodes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** When a leaf node is selected for moving, clicking any existing node merges the selected node into it — redirecting the source's single edge to the target (or dropping it if doing so creates a self-loop) and removing the source node.

**Architecture:** `CampusGraph` gains a `merge_node` method that owns all graph mutation (edge redirect/drop + node removal). `EditController` gains a `_merge_selected_into` handler called from a new branch in `_handle_node_click` when the current state is `NODE_SELECTED`. The `non_selectable` guard is narrowed so non-leaf nodes are only blocked in `IDLE`, not in `NODE_SELECTED`.

**Tech Stack:** Python 3.12, dataclasses, pytest

---

## File Structure

| Action | Path | Change |
|---|---|---|
| Modify | `src/map/graph.py` | Add `merge_node` method |
| Modify | `src/map/edit_controller.py` | Update caption, narrow `non_selectable`, add `_merge_selected_into`, new branch in `_handle_node_click` |
| Modify | `tests/map/test_graph.py` | Add 7 `merge_node` unit tests |
| Modify | `tests/map/edit_controller/test_node_selected.py` | Replace switch-selection test, add 6 merge tests |
| Modify | `tests/map/edit_controller/test_sequential.py` | Add merge workflow integration test |

---

### Task 1: `CampusGraph.merge_node` — graph layer (TDD)

**Files:**
- Modify: `tests/map/test_graph.py`
- Modify: `src/map/graph.py`

- [ ] **Step 1: Write 8 failing tests for `merge_node`**

Append to `tests/map/test_graph.py`:

```python
def test_merge_node_removes_source_node():
    """Degree-0 source: node is removed, graph otherwise unchanged."""
    graph = CampusGraph(
        nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=1.0, x=1.0)],
    )
    graph.merge_node(0, 1)
    assert graph.get_node(0) is None
    assert graph.get_node(1) is not None
    assert len(graph.nodes) == 1
    assert len(graph.edges) == 0


def test_merge_node_redirects_outgoing_edge():
    """Edge A→C with merge A into B becomes B→C."""
    graph = CampusGraph(
        nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=1.0, x=1.0), Node(id=2, y=2.0, x=2.0)],
        edges=[Edge(from_id=0, to_id=2)],
    )
    graph.merge_node(0, 1)
    assert len(graph.edges) == 1
    assert graph.edges[0].from_id == 1
    assert graph.edges[0].to_id == 2


def test_merge_node_redirects_incoming_edge():
    """Edge C→A with merge A into B becomes C→B."""
    graph = CampusGraph(
        nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=1.0, x=1.0), Node(id=2, y=2.0, x=2.0)],
        edges=[Edge(from_id=2, to_id=0)],
    )
    graph.merge_node(0, 1)
    assert len(graph.edges) == 1
    assert graph.edges[0].from_id == 2
    assert graph.edges[0].to_id == 1


def test_merge_node_drops_edge_when_it_would_create_self_loop_outgoing():
    """Edge A→B with merge A into B would create B→B; edge must be dropped."""
    graph = CampusGraph(
        nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=1.0, x=1.0)],
        edges=[Edge(from_id=0, to_id=1)],
    )
    graph.merge_node(0, 1)
    assert graph.get_node(0) is None
    assert len(graph.edges) == 0


def test_merge_node_drops_edge_when_it_would_create_self_loop_incoming():
    """Edge B→A with merge A into B would create B→B; edge must be dropped."""
    graph = CampusGraph(
        nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=1.0, x=1.0)],
        edges=[Edge(from_id=1, to_id=0)],
    )
    graph.merge_node(0, 1)
    assert graph.get_node(0) is None
    assert len(graph.edges) == 0


def test_merge_node_raises_for_same_ids():
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0)])
    with pytest.raises(ValueError, match="itself"):
        graph.merge_node(0, 0)


def test_merge_node_raises_for_unknown_source():
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0)])
    with pytest.raises(ValueError, match="Source node 99"):
        graph.merge_node(99, 0)


def test_merge_node_raises_for_unknown_target():
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0)])
    with pytest.raises(ValueError, match="Target node 99"):
        graph.merge_node(0, 99)
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/map/test_graph.py -v -k "merge" 2>&1 | tail -20
```

Expected: 8 failures with `AttributeError: 'CampusGraph' object has no attribute 'merge_node'`

- [ ] **Step 3: Implement `merge_node` in `src/map/graph.py`**

Add after the `degree` method at the end of `CampusGraph`:

```python
    def merge_node(self, source_id: int, target_id: int) -> None:
        """Merge source into target: redirect source's edge to target (drop if self-loop), then remove source."""
        if source_id == target_id:
            raise ValueError(f"Cannot merge node {source_id} into itself")
        if source_id not in self._node_index:
            raise ValueError(f"Source node {source_id} does not exist")
        if target_id not in self._node_index:
            raise ValueError(f"Target node {target_id} does not exist")
        new_edges = []
        for edge in self.edges:
            if edge.from_id == source_id:
                if edge.to_id != target_id:
                    new_edges.append(Edge(from_id=target_id, to_id=edge.to_id))
            elif edge.to_id == source_id:
                if edge.from_id != target_id:
                    new_edges.append(Edge(from_id=edge.from_id, to_id=target_id))
            else:
                new_edges.append(edge)
        self.edges[:] = new_edges
        source_node = self._node_index.pop(source_id)
        self.nodes.remove(source_node)
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/map/test_graph.py -v 2>&1 | tail -30
```

Expected: all tests PASS, including the 8 new merge tests. Coverage must remain 100%.

```bash
pytest tests/map/test_graph.py --cov=src/map/graph --cov-branch --cov-report=term-missing 2>&1 | tail -10
```

Expected: `100%` coverage on `src/map/graph.py`.

- [ ] **Step 5: Commit**

```bash
git add src/map/graph.py tests/map/test_graph.py
git commit -m "feat: add CampusGraph.merge_node — redirect/drop edge and remove source node"
```

---

### Task 2: `EditController` merge detection (TDD)

**Files:**
- Modify: `tests/map/edit_controller/test_node_selected.py`
- Modify: `src/map/edit_controller.py`

- [ ] **Step 1: Update `test_node_selected.py` — replace outdated tests and add merge tests**

Replace the entire content of `tests/map/edit_controller/test_node_selected.py` with:

```python
from map.graph import CampusGraph, Edge, Node
from map.edit_controller import EditController, EditState, State


def test_map_click_moves_node_and_returns_idle():
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0)])
    state = EditState(state=State.NODE_SELECTED, active_node_id=0)
    map_data = {
        "last_object_clicked": None,
        "last_object_clicked_tooltip": None,
        "last_clicked": {"lat": 10.0, "lng": 20.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.IDLE
    assert new_state.active_node_id is None
    assert graph.get_node(0).y == 10.0
    assert graph.get_node(0).x == 20.0


def test_node_click_in_node_selected_merges_and_returns_idle():
    """Clicking a leaf node while another is selected merges instead of switching selection."""
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=100.0, x=100.0)])
    state = EditState(state=State.NODE_SELECTED, active_node_id=0)
    map_data = {
        "last_object_clicked": {"lat": 100.0, "lng": 100.0},
        "last_object_clicked_tooltip": "1",
        "last_clicked": {"lat": 100.0, "lng": 100.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.IDLE
    assert new_state.active_node_id is None


def test_merge_removes_source_node_from_graph():
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=100.0, x=100.0)])
    state = EditState(state=State.NODE_SELECTED, active_node_id=0)
    map_data = {
        "last_object_clicked": {"lat": 100.0, "lng": 100.0},
        "last_object_clicked_tooltip": "1",
        "last_clicked": {"lat": 100.0, "lng": 100.0},
    }
    EditController(graph, state).handle_click(map_data)
    assert graph.get_node(0) is None
    assert graph.get_node(1) is not None


def test_merge_redirects_source_edge_to_target():
    """Source node 0 has edge 0→2; merging into node 1 produces edge 1→2."""
    graph = CampusGraph(
        nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=1.0, x=1.0), Node(id=2, y=2.0, x=2.0)],
        edges=[Edge(from_id=0, to_id=2)],
    )
    state = EditState(state=State.NODE_SELECTED, active_node_id=0)
    map_data = {
        "last_object_clicked": {"lat": 1.0, "lng": 1.0},
        "last_object_clicked_tooltip": "1",
        "last_clicked": {"lat": 1.0, "lng": 1.0},
    }
    EditController(graph, state).handle_click(map_data)
    assert len(graph.edges) == 1
    assert graph.edges[0].from_id == 1
    assert graph.edges[0].to_id == 2


def test_merge_into_neighbor_drops_self_loop_edge():
    """Source 0 has edge 0→1; merging into 1 would create 1→1, so edge is dropped."""
    graph = CampusGraph(
        nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=100.0, x=100.0)],
        edges=[Edge(from_id=0, to_id=1)],
    )
    state = EditState(state=State.NODE_SELECTED, active_node_id=0)
    map_data = {
        "last_object_clicked": {"lat": 100.0, "lng": 100.0},
        "last_object_clicked_tooltip": "1",
        "last_clicked": {"lat": 100.0, "lng": 100.0},
    }
    EditController(graph, state).handle_click(map_data)
    assert len(graph.edges) == 0
    assert graph.get_node(0) is None


def test_merge_into_non_leaf_target_is_allowed():
    """A leaf can be merged into a non-leaf target (degree > 1)."""
    # node 1 has degree 2: edges 0→1 and 2→1
    graph = CampusGraph(
        nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=1.0, x=1.0), Node(id=2, y=2.0, x=2.0)],
        edges=[Edge(from_id=0, to_id=1), Edge(from_id=2, to_id=1)],
    )
    # Select node 2 (leaf, degree 1) and merge into node 1 (non-leaf, degree 2)
    state = EditState(state=State.NODE_SELECTED, active_node_id=2)
    map_data = {
        "last_object_clicked": {"lat": 1.0, "lng": 1.0},
        "last_object_clicked_tooltip": "1",
        "last_clicked": {"lat": 1.0, "lng": 1.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.IDLE
    assert graph.get_node(2) is None


def test_clicking_active_node_itself_stays_selected():
    """Clicking the already-selected node while in NODE_SELECTED stays selected."""
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0)])
    state = EditState(state=State.NODE_SELECTED, active_node_id=0)
    obj_clicked = {"lat": 0.0, "lng": 0.0}
    map_data = {
        "last_object_clicked": obj_clicked,
        "last_object_clicked_tooltip": "0",
        "last_clicked": {"lat": 0.0, "lng": 0.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.NODE_SELECTED
    assert new_state.active_node_id == 0
    assert len(graph.nodes) == 1


def test_merge_is_idempotent_on_second_rerun():
    """After a merge, a second rerun with identical map_data must not re-fire."""
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=100.0, x=100.0)])
    state = EditState(state=State.NODE_SELECTED, active_node_id=0)
    obj_clicked = {"lat": 100.0, "lng": 100.0}
    map_data = {
        "last_object_clicked": obj_clicked,
        "last_object_clicked_tooltip": "1",
        "last_clicked": {"lat": 100.0, "lng": 100.0},
    }
    # Rerun 1: merge fires
    state = EditController(graph, state).handle_click(map_data)
    assert state.state == State.IDLE
    assert len(graph.nodes) == 1
    # Rerun 2: same map_data — click is not new, must be idempotent
    state2 = EditController(graph, state).handle_click(map_data)
    assert state2 is state
    assert len(graph.nodes) == 1


def test_map_click_preserves_last_object_clicked_to_prevent_reselection():
    """After moving a node, last_object_clicked must be preserved so the next
    rerun does not see a new object-click event and immediately re-select."""
    original_obj = {"lat": 0.0, "lng": 0.0}
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0)])
    state = EditState(
        state=State.NODE_SELECTED,
        active_node_id=0,
        last_object_clicked=original_obj,
    )
    map_data = {
        "last_object_clicked": original_obj,
        "last_object_clicked_tooltip": None,
        "last_clicked": {"lat": 10.0, "lng": 20.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.IDLE
    assert new_state.last_object_clicked == original_obj
```

- [ ] **Step 2: Run tests to confirm the new tests fail**

```bash
pytest tests/map/edit_controller/test_node_selected.py -v 2>&1 | tail -30
```

Expected: 7 of the new tests FAIL (merge-related ones). `test_map_click_moves_node_and_returns_idle` and `test_map_click_preserves_last_object_clicked_to_prevent_reselection` should still PASS. The removed `test_node_click_changes_selection` and `test_click_on_non_leaf_node_does_not_change_selection` no longer exist.

- [ ] **Step 3: Update `src/map/edit_controller.py`**

Make the following four changes. The full updated file content is:

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
            return (
                f"Node {self.active_node_id} selected — click the map to move it, "
                "or click another node to merge into it."
            )
        if self.state == State.PENDING_NODE:
            return (
                "Node placed — click an existing node to connect it, "
                "or click empty space to add a connected node."
            )
        return "Click a node to select it and move it, or click empty space to add a new node."


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

        # Node click takes priority when both change in the same rerun.
        # If a tooltip is present but refers to an unknown node, ignore the
        # entire event so the concurrent map-click is not misread as intentional.
        if new_node_click and tooltip:
            node = self._node_from_tooltip(tooltip)
            if node is not None:
                # Non-leaf nodes (degree > 1) may only be clicked in IDLE as a
                # selection target — they are blocked there to prevent accidental
                # selection of junction nodes. In NODE_SELECTED they are valid
                # merge targets; in PENDING_NODE they are valid connection targets.
                non_selectable = (
                    self._edit_state.state == State.IDLE
                    and self._graph.degree(node.id) > 1
                )
                if non_selectable:
                    return EditState(
                        state=self._edit_state.state,
                        active_node_id=self._edit_state.active_node_id,
                        last_object_clicked=obj_clicked,
                        last_map_click=map_click,
                    )
                return self._handle_node_click(node, obj_clicked, map_click)
            # Unknown tooltip: consume both clicks to prevent a ghost map-click on the next rerun
            return EditState(
                state=self._edit_state.state,
                active_node_id=self._edit_state.active_node_id,
                last_object_clicked=obj_clicked,
                last_map_click=map_click,
            )

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
        if self._edit_state.state == State.NODE_SELECTED:
            return self._merge_selected_into(node, obj_clicked, consumed_map_click)
        return EditState(
            state=State.NODE_SELECTED,
            active_node_id=node.id,
            last_object_clicked=obj_clicked,
            last_map_click=consumed_map_click,
        )

    def _merge_selected_into(
        self, target: Node, obj_clicked: dict, map_click: dict | None
    ) -> EditState:
        if target.id == self._edit_state.active_node_id:
            # Clicking the selected node itself: stay selected, consume clicks
            return EditState(
                state=State.NODE_SELECTED,
                active_node_id=self._edit_state.active_node_id,
                last_object_clicked=obj_clicked,
                last_map_click=map_click,
            )
        self._graph.merge_node(self._edit_state.active_node_id, target.id)
        return EditState(
            state=State.IDLE,
            last_object_clicked=obj_clicked,
            last_map_click=map_click,
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

    def _from_map_click(self, **fields) -> EditState:
        # streamlit-folium only updates last_object_clicked when a Folium object is
        # clicked, never on empty-space clicks. Centralising here ensures every map-click
        # handler carries the value forward automatically; forgetting to do so causes ghost
        # node-click events on the next Streamlit rerun.
        return EditState(last_object_clicked=self._edit_state.last_object_clicked, **fields)

    def _handle_map_click(self, map_click: dict) -> EditState:
        state = self._edit_state.state
        if state == State.NODE_SELECTED:
            self._graph.move_node(
                self._edit_state.active_node_id,
                y=map_click["lat"],
                x=map_click["lng"],
            )
            return self._from_map_click(state=State.IDLE, last_map_click=map_click)
        if state == State.PENDING_NODE:
            return self._create_connected_node(map_click)
        # IDLE: create new node, enter pending
        return self._create_pending_node(map_click)

    def _create_pending_node(self, map_click: dict) -> EditState:
        new_id = self._graph.next_node_id()
        self._graph.add_node(Node(id=new_id, y=map_click["lat"], x=map_click["lng"]))
        return self._from_map_click(
            state=State.PENDING_NODE,
            active_node_id=new_id,
            last_map_click=map_click,
        )

    def _create_connected_node(self, map_click: dict) -> EditState:
        new_id = self._graph.next_node_id()
        self._graph.add_node(Node(id=new_id, y=map_click["lat"], x=map_click["lng"]))
        self._graph.add_edge(Edge(from_id=self._edit_state.active_node_id, to_id=new_id))
        return self._from_map_click(state=State.IDLE, last_map_click=map_click)
```

- [ ] **Step 4: Run all edit-controller tests to confirm they pass**

```bash
pytest tests/map/edit_controller/ -v 2>&1 | tail -40
```

Expected: all tests PASS.

```bash
pytest tests/map/edit_controller/ --cov=src/map/edit_controller --cov-branch --cov-report=term-missing 2>&1 | tail -10
```

Expected: `100%` coverage on `src/map/edit_controller.py`.

- [ ] **Step 5: Commit**

```bash
git add src/map/edit_controller.py tests/map/edit_controller/test_node_selected.py
git commit -m "feat: merge node on click in NODE_SELECTED — replace switch-selection with merge"
```

---

### Task 3: Sequential workflow integration test

**Files:**
- Modify: `tests/map/edit_controller/test_sequential.py`

- [ ] **Step 1: Add the merge workflow test to `test_sequential.py`**

Append to `tests/map/edit_controller/test_sequential.py`:

```python
def test_merge_does_not_ghost_refire_on_next_rerun():
    """
    Bug scenario: node 0 is selected and user clicks node 1 to merge.
    On the very next rerun Streamlit rerenders with identical map_data.
    The controller must not fire a second merge (node 0 no longer exists after the first).
    """
    node_0_obj = {"lat": 0.0, "lng": 0.0}
    node_1_obj = {"lat": 100.0, "lng": 100.0}
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=100.0, x=100.0)])
    state = EditState(
        state=State.NODE_SELECTED,
        active_node_id=0,
        last_object_clicked=node_0_obj,
        last_map_click={"lat": 0.0, "lng": 0.0},
    )

    map_data = {
        "last_object_clicked": node_1_obj,
        "last_object_clicked_tooltip": "1",
        "last_clicked": {"lat": 100.0, "lng": 100.0},
    }

    # Rerun 1: merge fires — node 0 removed, state returns to IDLE
    state = EditController(graph, state).handle_click(map_data)
    assert state.state == State.IDLE
    assert graph.get_node(0) is None
    assert len(graph.nodes) == 1

    # Rerun 2: same map_data — the node-click has not changed, must be idempotent
    state2 = EditController(graph, state).handle_click(map_data)
    assert state2 is state
    assert len(graph.nodes) == 1


def test_full_node_creation_and_merge_sequence():
    """
    Integration: simulate a complete sequence including a merge.

    Steps:
      1. Click empty space → node 0 created (PENDING)
      2. Click empty space → node 1 created and connected to 0 (IDLE)
      3. Click empty space → node 2 created (PENDING)
      4. Click node 0 to connect → edge 2→0 added (IDLE)
      5. Click node 2 to select it (NODE_SELECTED, node 2 is a leaf)
      6. Click node 1 to merge node 2 into node 1 → edge 1→0 added, node 2 removed (IDLE)

    Each step is followed by a no-op rerun to confirm idempotency.
    """
    graph = CampusGraph()
    state = EditState()

    # Step 1: create node 0 at (10, 10)
    map_data_1 = {
        "last_object_clicked": None,
        "last_object_clicked_tooltip": None,
        "last_clicked": {"lat": 10.0, "lng": 10.0},
    }
    state = EditController(graph, state).handle_click(map_data_1)
    assert state.state == State.PENDING_NODE and state.active_node_id == 0
    assert EditController(graph, state).handle_click(map_data_1) is state

    # Step 2: create node 1 at (20, 20), connected to node 0
    map_data_2 = {**map_data_1, "last_clicked": {"lat": 20.0, "lng": 20.0}}
    state = EditController(graph, state).handle_click(map_data_2)
    assert state.state == State.IDLE
    assert len(graph.nodes) == 2 and len(graph.edges) == 1
    assert EditController(graph, state).handle_click(map_data_2) is state

    # Step 3: create node 2 at (30, 30) — pending
    map_data_3 = {**map_data_1, "last_clicked": {"lat": 30.0, "lng": 30.0}}
    state = EditController(graph, state).handle_click(map_data_3)
    assert state.state == State.PENDING_NODE and state.active_node_id == 2
    assert EditController(graph, state).handle_click(map_data_3) is state

    # Step 4: click node 0 to connect node 2 → node 0
    node_0_obj = {"lat": 10.0, "lng": 10.0}
    map_data_4 = {
        "last_object_clicked": node_0_obj,
        "last_object_clicked_tooltip": "0",
        "last_clicked": {"lat": 10.0, "lng": 10.0},
    }
    state = EditController(graph, state).handle_click(map_data_4)
    assert state.state == State.IDLE
    assert len(graph.nodes) == 3 and len(graph.edges) == 2
    assert EditController(graph, state).handle_click(map_data_4) is state

    # Step 5: click node 2 to select it (node 2 has degree 1 — leaf)
    node_2_obj = {"lat": 30.0, "lng": 30.0}
    map_data_5 = {
        "last_object_clicked": node_2_obj,
        "last_object_clicked_tooltip": "2",
        "last_clicked": {"lat": 30.0, "lng": 30.0},
    }
    state = EditController(graph, state).handle_click(map_data_5)
    assert state.state == State.NODE_SELECTED and state.active_node_id == 2
    assert EditController(graph, state).handle_click(map_data_5) is state

    # Step 6: click node 1 to merge node 2 into node 1
    # node 2 had edge 2→0; merging into node 1 produces edge 1→0
    node_1_obj = {"lat": 20.0, "lng": 20.0}
    map_data_6 = {
        "last_object_clicked": node_1_obj,
        "last_object_clicked_tooltip": "1",
        "last_clicked": {"lat": 20.0, "lng": 20.0},
    }
    state = EditController(graph, state).handle_click(map_data_6)
    assert state.state == State.IDLE
    assert graph.get_node(2) is None
    assert len(graph.nodes) == 2
    # Original edge 0→1 plus redirected edge 1→0 (was 2→0)
    assert len(graph.edges) == 2
    redirected = next((e for e in graph.edges if e.from_id == 1 and e.to_id == 0), None)
    assert redirected is not None
    assert EditController(graph, state).handle_click(map_data_6) is state
```

- [ ] **Step 2: Run the full test suite to confirm everything passes**

```bash
pytest -v 2>&1 | tail -50
```

Expected: all tests PASS.

```bash
pytest --cov=src --cov-branch --cov-report=term-missing 2>&1 | tail -15
```

Expected: `100%` coverage across all `src/` files.

- [ ] **Step 3: Commit**

```bash
git add tests/map/edit_controller/test_sequential.py
git commit -m "test: add merge sequential workflow and ghost-rerun prevention tests"
```

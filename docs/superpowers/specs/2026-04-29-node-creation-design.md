# Node Creation in Edit Mode

**Date:** 2026-04-29  
**Status:** Approved

## Overview

Extend Edit mode with node creation: clicking empty map space creates a new node. A second click either connects it to an existing node (edge added) or to a new node placed at the click location (edge added between the two new nodes). All existing Edit-mode behavior (select node, move node) is preserved and migrated into a dedicated `EditController`.

## State Machine

Three explicit states live in `EditState`:

| State | Meaning |
|---|---|
| `IDLE` | No node selected, no pending node |
| `NODE_SELECTED` | A node is selected for repositioning |
| `PENDING_NODE` | A new node was just placed; awaiting a second click to connect |

Transitions:

- `IDLE` + click existing node → select it → `NODE_SELECTED`
- `IDLE` + click empty space → create node A → `PENDING_NODE`
- `NODE_SELECTED` + click map → move selected node → `IDLE`
- `PENDING_NODE` + click existing node → add edge(A, existing) → `IDLE`
- `PENDING_NODE` + click empty space → create node B, add edge(A, B) → `IDLE`

Node click always takes priority over map click when both change in the same Streamlit rerun (existing behavior preserved).

## Components

### `src/map/edit_controller.py` (new)

`EditState` — frozen dataclass stored in `st.session_state`:
- `state: State` (enum: `IDLE`, `NODE_SELECTED`, `PENDING_NODE`)
- `active_node_id: int | None` — selected node ID (NODE_SELECTED) or pending node ID (PENDING_NODE)
- `last_object_clicked: dict | None` — last seen value, for change detection
- `last_map_click: dict | None` — last seen value, for change detection

`EditController` — stateless service; constructed with `graph: CampusGraph` and `edit_state: EditState`:
- `handle_click(map_data: dict) -> EditState` — inspects raw `st_folium` output, applies the appropriate transition, returns the new `EditState`

`EditState` also exposes:
- `caption: str` (property) — human-readable status string derived from current state and `active_node_id`

### `src/map/graph.py`

- Remove `label: str` from `Node`
- Add `next_node_id() -> int` — returns `max(n.id for n in nodes) + 1`, or `0` if graph is empty

### `src/map/graph_renderer.py`

- Rename `selected_node_id` parameter → `highlighted_node_id` on `render_onto`
- Tooltip on each `CircleMarker` becomes `str(node.id)` (enables click identification; no descriptive label)
- Both `NODE_SELECTED` and `PENDING_NODE` states pass their `active_node_id` as `highlighted_node_id` → crimson highlight

### `src/app.py`

Edit block simplifies to:
1. Read `EditState` from `st.session_state`
2. Build `FeatureGroup`, render graph with `highlighted_node_id=edit_state.active_node_id`
3. Call `st_folium`, get `map_data`
4. Call `controller.handle_click(map_data)` → new state
5. If state changed, write back to `st.session_state` and `st.rerun()`

Initial graph in session state uses `Node(id=0, y=..., x=...)` (no label).

## Node ID & Label

- IDs: `graph.next_node_id()` at creation time
- No labels; tooltip is `str(node.id)` for click detection only

## Visual Feedback

- Highlighted node (selected or pending): crimson (`#981e32`) — existing color
- Normal nodes: WSU gray (`#717c7d`)
- Status captions by state:
  - `IDLE`: "Click a node to select it and move it, or click empty space to add a new node."
  - `NODE_SELECTED`: "Node {id} selected — click the map to move it."
  - `PENDING_NODE`: "Node placed — click an existing node to connect it, or click empty space to add a connected node."

## Testing

- 100% coverage on `src/map/` required (project rule)
- `EditController` unit tests: one test per state transition (5 transitions), plus priority-ordering test (node click beats map click)
- `CampusGraph.next_node_id` unit tests: empty graph, single node, multiple nodes
- `GraphOverlayRenderer` tests: update fixture nodes to drop `label`, verify `highlighted_node_id` renders crimson
- Existing node-move and node-select tests migrated to test `EditController` directly

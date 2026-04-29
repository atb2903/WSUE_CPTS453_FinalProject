# Edit / Navigation Mode Design

**Date:** 2026-04-29
**Status:** Approved

## Overview

Add two user-selectable modes to the WSU-GPS Streamlit app:

- **Navigation mode** — current behaviour, unchanged.
- **Edit mode** — click a node to select it (highlighted in WSU crimson), then click anywhere on the map canvas to move it there. The edge redraws automatically.

## Mode Toggle

`st.segmented_control("Mode", ["Navigation", "Edit"], default="Navigation")` renders at the top of the page. Its return value drives which rendering branch executes; no session state variable is needed for the active mode.

## Session State

| Key | Type | Purpose |
|---|---|---|
| `graph` | `CampusGraph` | Graph with current node positions. Initialized once on first run. |
| `selected_node_id` | `int \| None` | ID of the currently selected node in edit mode. `None` = nothing selected. |
| `last_object_clicked` | `dict \| None` | Last value of `st_folium`'s `last_object_clicked` return key. Used to detect fresh node clicks across reruns. |
| `last_map_click` | `dict \| None` | Last value of `st_folium`'s `last_clicked` return key. Used to detect fresh map clicks across reruns. |

## Edit Mode Interaction

1. User clicks a node → `last_object_clicked_tooltip` matches a node label → `selected_node_id` is set to that node's id. The node re-renders in `_WSU_CRIMSON`.
2. User clicks the map canvas → `last_clicked` returns `[y, x]` → the selected node is moved to that position via `CampusGraph.move_node`, `selected_node_id` is cleared, the map re-renders.
3. If the user clicks a different node while one is already selected, the selection transfers to the newly clicked node.

### Distinguishing fresh events

`st_folium` persists the last event values across reruns. Each rerun compares the returned `last_object_clicked` / `last_clicked` against the stored session-state values. Only a value that has changed is treated as a new user action.

Priority rule: if both values changed in the same rerun (edge case), a node click takes priority over a map click.

## `st_folium` Configuration

| Mode | `returned_objects` |
|---|---|
| Navigation | `[]` — prevents reruns on pan/zoom |
| Edit | `["last_object_clicked_tooltip", "last_clicked"]` |

## Code Changes

### 1. `src/map/graph.py` — `CampusGraph.move_node`

Add one method:

```python
def move_node(self, node_id: int, y: float, x: float) -> None:
    """Replace the node's position, raising KeyError if node_id is unknown."""
    existing = self._node_index[node_id]
    updated = dataclasses.replace(existing, y=y, x=x)
    self._node_index[node_id] = updated
    self.nodes[self.nodes.index(existing)] = updated
```

### 2. `src/map/graph_renderer.py` — colour constants + selection highlight

- Rename `_COLOR` → `_WSU_GRAY = "#717c7d"`.
- Promote the commented crimson value to `_WSU_CRIMSON = "#981e32"`.
- `render_onto(campus_map, selected_node_id=None)` — the node whose `id` matches `selected_node_id` is drawn with `color=_WSU_CRIMSON` instead of `_WSU_GRAY`.

### 3. `src/app.py` — mode toggle + event handling

- Add `st.segmented_control` at the top of the page.
- Initialize session state keys on first run.
- **Navigation branch:** existing rendering code, `returned_objects=[]`.
- **Edit branch:** render graph with `selected_node_id`, `returned_objects=[...]`, then a click-handling block that inspects the `st_folium` return dict, updates session state, and triggers a rerun via `st.rerun()` when state changes.

## Testing

All existing tests must continue to pass. New unit tests cover:

- `CampusGraph.move_node` — happy path, unknown id raises `KeyError`.
- `GraphOverlayRenderer.render_onto` with `selected_node_id` set — selected node rendered in crimson, others in gray.

Coverage target: 100% on `src/map` (unchanged requirement).

## Out of Scope

- Adding or deleting nodes/edges in edit mode.
- Persisting edits beyond the Streamlit session.
- Any navigation-mode routing logic.

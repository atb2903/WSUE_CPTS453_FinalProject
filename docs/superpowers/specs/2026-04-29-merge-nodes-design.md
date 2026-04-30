# Merge Nodes Design

**Date:** 2026-04-29  
**Status:** Approved

## Overview

When a leaf node is selected for moving, clicking an existing node (any degree) merges the selected node into the target instead of moving it. The source node is deleted; its single edge (if any) is redirected to the target unless doing so would create a self-loop, in which case it is dropped.

## Scope

- Extends `CampusGraph` with a `merge_node` method
- Extends `EditController` NODE_SELECTED handling to detect merge intent
- Removes the existing switch-selection behavior (clicking another leaf while one is selected used to re-select; now it merges)

## Graph Mutation (`CampusGraph.merge_node`)

```python
def merge_node(self, source_id: int, target_id: int) -> None
```

**Preconditions:**
- `source_id != target_id` — raises `ValueError` if equal
- Both IDs must exist in the graph — raises `ValueError` otherwise
- `source_id` must be a leaf (degree ≤ 1) — enforced by the controller, not by this method (method is general-purpose)

**Behaviour:**
1. Find the one edge involving `source_id` (if any)
2. If the edge exists and the neighbor is not `target_id`, redirect it: replace `source_id` with `target_id` in the edge (preserving direction — `from_id` or `to_id` as appropriate)
3. If the edge exists and the neighbor IS `target_id`, drop the edge (would be a self-loop)
4. If no edge exists, nothing to redirect
5. Remove `source_id` from `nodes` list and `_node_index`

## State Machine (`EditController`)

No new states. NODE_SELECTED gains a new branch in its click handler:

| Event | Previous behaviour | New behaviour |
|---|---|---|
| Click existing node (any degree) in NODE_SELECTED | Re-select if leaf; ignore if non-leaf | Merge source into clicked node → IDLE |
| Click empty map space in NODE_SELECTED | Move source to clicked position → IDLE | Unchanged |

**Caption update** — while in NODE_SELECTED:
> "Node {id} selected — click the map to move it, or click another node to merge into it."

## Data Flow

```
User clicks existing node while NODE_SELECTED
  → EditController detects tooltip resolves to a known node ID
  → graph.merge_node(active_node_id, target_id)
      → edge redirected or dropped
      → source node removed
  → EditState transitions to IDLE, active_node_id cleared
  → Streamlit rerenders map with updated graph
```

## Error Handling

- `merge_node(source_id, target_id)` raises `ValueError` for: equal IDs, either ID not found in graph
- The controller only calls `merge_node` after confirming both node IDs exist in the graph, so `ValueError` is a programmer error, not a user error

## Testing

**`tests/map/test_graph.py`** — new `merge_node` cases:
- Merge degree-0 source (no edge): source removed, graph otherwise unchanged
- Merge with edge A→neighbor: edge becomes target→neighbor
- Merge with edge neighbor→A: edge becomes neighbor→target
- Merge where neighbor is target: self-loop case, edge dropped and source removed
- `merge_node(id, id)` raises `ValueError`
- `merge_node` with unknown source ID raises `ValueError`
- `merge_node` with unknown target ID raises `ValueError`

**`tests/map/edit_controller/test_node_selected.py`** — new cases:
- Click existing node in NODE_SELECTED triggers merge and returns IDLE
- Merged source node absent from graph after merge
- Edge correctly redirected after merge
- Self-loop edge dropped after merge into neighbor
- Click event consumed (idempotent on second rerun with same map_data)

**`tests/map/edit_controller/test_sequential.py`** — new workflow:
- Full sequence: select leaf → click another node → graph mutated → IDLE → caption reset

## Out of Scope

- Switch-selection (re-selecting a different leaf without merging) — deferred to a later feature
- Merge confirmation / undo — not needed; operation is immediate
- Merging non-leaf nodes — source is always a leaf due to the existing NODE_SELECTED selection constraint

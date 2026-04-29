from map.graph import CampusGraph, Node
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


def test_node_click_changes_selection():
    """Clicking a different leaf node while one is selected updates the selection."""
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=100.0, x=100.0)])
    state = EditState(state=State.NODE_SELECTED, active_node_id=0)
    map_data = {
        "last_object_clicked": {"lat": 100.0, "lng": 100.0},
        "last_object_clicked_tooltip": "1",
        "last_clicked": {"lat": 100.0, "lng": 100.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.NODE_SELECTED
    assert new_state.active_node_id == 1


def test_click_on_non_leaf_node_does_not_change_selection(non_leaf_graph):
    """Clicking a node with degree > 1 must not change the active selection."""
    state = EditState(state=State.NODE_SELECTED, active_node_id=0)
    map_data = {
        "last_object_clicked": {"lat": 1.0, "lng": 1.0},
        "last_object_clicked_tooltip": "1",
        "last_clicked": {"lat": 1.0, "lng": 1.0},
    }
    new_state = EditController(non_leaf_graph, state).handle_click(map_data)
    assert new_state.state == State.NODE_SELECTED
    assert new_state.active_node_id == 0


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

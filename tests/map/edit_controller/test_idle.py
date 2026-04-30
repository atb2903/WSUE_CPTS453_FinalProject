from map.graph import CampusGraph, Node
from map.edit_controller import EditController, EditState, State


def test_node_click_transitions_to_node_selected():
    graph = CampusGraph(nodes=[Node(id=5, y=100.0, x=200.0)])
    state = EditState()
    map_data = {
        "last_object_clicked": {"lat": 100.0, "lng": 200.0},
        "last_object_clicked_tooltip": "5",
        "last_clicked": {"lat": 100.0, "lng": 200.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.NODE_SELECTED
    assert new_state.active_node_id == 5


def test_map_click_creates_pending_node():
    graph = CampusGraph()
    state = EditState()
    map_data = {
        "last_object_clicked": None,
        "last_object_clicked_tooltip": None,
        "last_clicked": {"lat": 50.0, "lng": 75.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.PENDING_NODE
    assert new_state.active_node_id == 0
    assert len(graph.nodes) == 1
    assert graph.nodes[0].y == 50.0
    assert graph.nodes[0].x == 75.0


def test_map_click_assigns_next_available_id():
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=1.0, x=1.0)])
    state = EditState()
    map_data = {
        "last_object_clicked": None,
        "last_object_clicked_tooltip": None,
        "last_clicked": {"lat": 50.0, "lng": 60.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.active_node_id == 2


def test_click_on_non_leaf_node_transitions_to_node_selected(non_leaf_graph):
    """Clicking a node with degree > 1 in IDLE should select it."""
    state = EditState()
    map_data = {
        "last_object_clicked": {"lat": 1.0, "lng": 1.0},
        "last_object_clicked_tooltip": "1",
        "last_clicked": {"lat": 1.0, "lng": 1.0},
    }
    new_state = EditController(non_leaf_graph, state).handle_click(map_data)
    assert new_state.state == State.NODE_SELECTED
    assert new_state.active_node_id == 1
    assert new_state.last_object_clicked == {"lat": 1.0, "lng": 1.0}
    assert new_state.last_map_click == {"lat": 1.0, "lng": 1.0}

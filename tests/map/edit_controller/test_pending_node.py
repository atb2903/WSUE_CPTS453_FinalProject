from map.graph import CampusGraph, Node
from map.edit_controller import EditController, EditState, State


def test_map_click_creates_connected_node_and_returns_idle():
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0)])
    state = EditState(state=State.PENDING_NODE, active_node_id=0)
    map_data = {
        "last_object_clicked": None,
        "last_object_clicked_tooltip": None,
        "last_clicked": {"lat": 30.0, "lng": 40.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.IDLE
    assert new_state.active_node_id is None
    assert len(graph.nodes) == 2
    assert graph.nodes[1].y == 30.0
    assert graph.nodes[1].x == 40.0
    assert len(graph.edges) == 1
    assert graph.edges[0].from_id == 0
    assert graph.edges[0].to_id == 1


def test_node_click_on_different_node_connects_and_goes_idle():
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=5.0, x=5.0)])
    state = EditState(state=State.PENDING_NODE, active_node_id=0)
    map_data = {
        "last_object_clicked": {"lat": 5.0, "lng": 5.0},
        "last_object_clicked_tooltip": "1",
        "last_clicked": {"lat": 5.0, "lng": 5.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.IDLE
    assert len(graph.edges) == 1
    assert graph.edges[0].from_id == 0
    assert graph.edges[0].to_id == 1


def test_node_click_on_self_stays_pending():
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0)])
    state = EditState(state=State.PENDING_NODE, active_node_id=0)
    map_data = {
        "last_object_clicked": {"lat": 0.0, "lng": 0.0},
        "last_object_clicked_tooltip": "0",
        "last_clicked": {"lat": 0.0, "lng": 0.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.PENDING_NODE
    assert new_state.active_node_id == 0
    assert len(graph.edges) == 0


def test_node_click_on_non_leaf_node_connects_and_goes_idle(non_leaf_graph):
    """In PENDING_NODE, non-leaf nodes are valid connection targets."""
    non_leaf_graph.add_node(Node(id=3, y=3.0, x=3.0))
    state = EditState(state=State.PENDING_NODE, active_node_id=3)
    map_data = {
        "last_object_clicked": {"lat": 1.0, "lng": 1.0},
        "last_object_clicked_tooltip": "1",
        "last_clicked": {"lat": 1.0, "lng": 1.0},
    }
    new_state = EditController(non_leaf_graph, state).handle_click(map_data)
    assert new_state.state == State.IDLE
    assert any(e.from_id == 3 and e.to_id == 1 for e in non_leaf_graph.edges)

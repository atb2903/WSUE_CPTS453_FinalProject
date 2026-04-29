import pytest
from dataclasses import FrozenInstanceError

from map.graph import CampusGraph, Node
from map.edit_controller import EditController, EditState, State


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


def test_node_from_tooltip_non_integer_returns_none():
    """Non-integer tooltips (e.g. edge labels) must consume the click to prevent ghost events."""
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0)])
    state = EditState()
    # Tooltip that cannot be parsed as int → node lookup fails, but click must be consumed
    map_data = {
        "last_object_clicked": {"lat": 0.0, "lng": 0.0},
        "last_object_clicked_tooltip": "not-an-int",
        "last_clicked": None,
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.IDLE
    assert new_state.last_object_clicked == {"lat": 0.0, "lng": 0.0}
    assert len(graph.nodes) == 1  # no new node created


def test_idle_map_click_creates_pending_node():
    """Map-click in IDLE creates a new node and transitions to PENDING_NODE."""
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


def test_node_selected_map_click_moves_node():
    """Map-click in NODE_SELECTED moves the active node and returns to IDLE."""
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0)])
    state = EditState(state=State.NODE_SELECTED, active_node_id=0)
    map_data = {
        "last_object_clicked": None,
        "last_object_clicked_tooltip": None,
        "last_clicked": {"lat": 10.0, "lng": 20.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.IDLE
    assert graph.get_node(0).y == 10.0
    assert graph.get_node(0).x == 20.0


def test_pending_node_map_click_creates_connected_node():
    """Map-click in PENDING_NODE creates a new node connected to the pending one."""
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0)])
    state = EditState(state=State.PENDING_NODE, active_node_id=0)
    map_data = {
        "last_object_clicked": None,
        "last_object_clicked_tooltip": None,
        "last_clicked": {"lat": 30.0, "lng": 40.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.IDLE
    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1
    assert graph.edges[0].from_id == 0
    assert graph.edges[0].to_id == 1


def test_pending_node_click_on_different_node_connects_and_goes_idle():
    """Node-click in PENDING_NODE on a different node adds an edge and goes IDLE."""
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


def test_pending_node_click_on_self_stays_pending():
    """Node-click in PENDING_NODE on the active node itself keeps PENDING_NODE."""
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


def test_idle_map_click_assigns_next_available_id():
    """When nodes already exist, next_node_id is used for the new pending node."""
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=1.0, x=1.0)])
    state = EditState()
    map_data = {
        "last_object_clicked": None,
        "last_object_clicked_tooltip": None,
        "last_clicked": {"lat": 50.0, "lng": 60.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.active_node_id == 2


def test_node_selected_node_click_changes_selection():
    """Clicking a different node while one is selected changes the selection."""
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


def test_node_click_takes_priority_over_concurrent_map_click():
    """When a node is clicked, streamlit-folium also updates last_clicked.
    The controller must handle the node click and consume the map click so
    the next rerun does not misread it as a new map-click event."""
    node = Node(id=0, y=100.0, x=200.0)
    graph = CampusGraph(nodes=[node])
    state = EditState()  # IDLE, both lasts = None
    map_data = {
        "last_object_clicked": {"lat": 100.0, "lng": 200.0},
        "last_object_clicked_tooltip": "0",
        "last_clicked": {"lat": 100.0, "lng": 200.0},  # concurrent — must be consumed
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.NODE_SELECTED
    assert new_state.active_node_id == 0
    assert len(graph.nodes) == 1  # no new node created
    assert new_state.last_map_click == {"lat": 100.0, "lng": 200.0}


def test_unknown_tooltip_consumes_concurrent_map_click():
    """An unresolvable tooltip must not leave the map-click unconsumed.
    If it does, the next rerun would see new_map_click=True and create a ghost node."""
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0)])
    state = EditState()  # last_map_click = None
    map_data = {
        "last_object_clicked": {"lat": 0.0, "lng": 0.0},
        "last_object_clicked_tooltip": "999",  # unknown node id
        "last_clicked": {"lat": 0.0, "lng": 0.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.IDLE
    # Map-click must be consumed so the next rerun does not create a ghost node
    assert new_state.last_map_click == {"lat": 0.0, "lng": 0.0}
    assert len(graph.nodes) == 1  # no new node created

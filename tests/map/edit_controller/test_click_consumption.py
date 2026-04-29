"""
Tests for click-event consumption: ensuring that every state transition correctly
stores the values seen in map_data so that identical values on the next Streamlit
rerun are not mistaken for new events (ghost clicks).

Rule: any transition triggered by a node-click must store last_object_clicked and
last_clicked from map_data.  Any transition triggered by a map-click must carry
last_object_clicked forward from the previous state (streamlit-folium does not
update it on empty-space clicks).
"""

from map.graph import CampusGraph, Node
from map.edit_controller import EditController, EditState, State


def test_no_change_returns_same_state_object():
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


def test_unknown_tooltip_is_consumed_without_selecting():
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0)])
    state = EditState()
    map_data = {
        "last_object_clicked": {"lat": 0.0, "lng": 0.0},
        "last_object_clicked_tooltip": "999",
        "last_clicked": {"lat": 0.0, "lng": 0.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.IDLE


def test_non_integer_tooltip_is_consumed():
    """Non-integer tooltips (e.g. edge labels) must not fall through to a map-click handler."""
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0)])
    state = EditState()
    map_data = {
        "last_object_clicked": {"lat": 0.0, "lng": 0.0},
        "last_object_clicked_tooltip": "not-an-int",
        "last_clicked": None,
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.IDLE
    assert new_state.last_object_clicked == {"lat": 0.0, "lng": 0.0}
    assert len(graph.nodes) == 1


def test_node_click_consumes_concurrent_map_click():
    """When a Folium object is clicked, streamlit-folium also updates last_clicked.
    The controller must handle the node-click and consume the map-click so the
    next rerun does not misread it as a new map-click event."""
    node = Node(id=0, y=100.0, x=200.0)
    graph = CampusGraph(nodes=[node])
    state = EditState()
    map_data = {
        "last_object_clicked": {"lat": 100.0, "lng": 200.0},
        "last_object_clicked_tooltip": "0",
        "last_clicked": {"lat": 100.0, "lng": 200.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.NODE_SELECTED
    assert new_state.active_node_id == 0
    assert len(graph.nodes) == 1
    assert new_state.last_map_click == {"lat": 100.0, "lng": 200.0}


def test_unknown_tooltip_consumes_concurrent_map_click():
    """An unresolvable tooltip must still consume the concurrent map-click.
    If it does not, the next rerun sees new_map_click=True and creates a ghost node."""
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0)])
    state = EditState()
    map_data = {
        "last_object_clicked": {"lat": 0.0, "lng": 0.0},
        "last_object_clicked_tooltip": "999",
        "last_clicked": {"lat": 0.0, "lng": 0.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.IDLE
    assert new_state.last_map_click == {"lat": 0.0, "lng": 0.0}
    assert len(graph.nodes) == 1


def test_create_pending_node_preserves_last_object_clicked():
    """A map-click in IDLE must carry forward last_object_clicked.
    Streamlit-folium does not update it on empty-space clicks, so resetting it
    to None would cause the stale value to look like a new event on the next rerun."""
    prior_obj = {"lat": 10.0, "lng": 10.0}
    graph = CampusGraph()
    state = EditState(last_object_clicked=prior_obj)
    map_data = {
        "last_object_clicked": prior_obj,
        "last_object_clicked_tooltip": None,
        "last_clicked": {"lat": 50.0, "lng": 75.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.PENDING_NODE
    assert new_state.last_object_clicked == prior_obj


def test_create_connected_node_preserves_last_object_clicked():
    """A map-click in PENDING_NODE must carry forward last_object_clicked for
    the same reason as test_create_pending_node_preserves_last_object_clicked."""
    prior_obj = {"lat": 5.0, "lng": 5.0}
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0)])
    state = EditState(
        state=State.PENDING_NODE,
        active_node_id=0,
        last_object_clicked=prior_obj,
    )
    map_data = {
        "last_object_clicked": prior_obj,
        "last_object_clicked_tooltip": None,
        "last_clicked": {"lat": 30.0, "lng": 40.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.IDLE
    assert new_state.last_object_clicked == prior_obj

"""
Multi-rerun simulation tests.

Streamlit rerenders the entire script on every interaction. Between reruns,
streamlit-folium preserves the last values it received for last_object_clicked,
last_object_clicked_tooltip, and last_clicked. A correct controller must be
idempotent: calling handle_click with the same map_data twice in a row must
return the same state and make no further graph mutations.

These tests simulate two consecutive reruns and assert that the second call
produces no side effects. This is the category of test that catches the class
of bug where a state transition fails to consume or preserve a click value,
causing a ghost event to fire on the subsequent rerun.
"""

from map.graph import CampusGraph, Edge, Node
from map.edit_controller import EditController, EditState, State


def test_creating_pending_node_does_not_ghost_connect_on_next_rerun():
    """
    Bug scenario: node 0 was previously interacted with (last_object_clicked set).
    User clicks empty space to create node 1 (PENDING_NODE). On the very next rerun
    Streamlit rerenders with identical map_data — the controller must not fire a
    spurious connection to node 0.
    """
    node_0_obj = {"lat": 0.0, "lng": 0.0}
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0)])
    state = EditState(last_object_clicked=node_0_obj)

    map_data = {
        "last_object_clicked": node_0_obj,   # stale — did not change
        "last_object_clicked_tooltip": "0",  # stale
        "last_clicked": {"lat": 50.0, "lng": 50.0},
    }

    # Rerun 1: empty-space click creates a pending node
    state = EditController(graph, state).handle_click(map_data)
    assert state.state == State.PENDING_NODE
    assert len(graph.edges) == 0

    # Rerun 2: same map_data — must be idempotent
    state2 = EditController(graph, state).handle_click(map_data)
    assert state2 is state
    assert len(graph.edges) == 0


def test_creating_connected_node_does_not_ghost_connect_on_next_rerun():
    """
    Node 0 is the active pending node. User clicks empty space to create node 1
    (connected). On the next rerun the same stale last_object_clicked is still
    present — the controller must not create a second edge or node.
    """
    node_0_obj = {"lat": 0.0, "lng": 0.0}
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0)])
    state = EditState(
        state=State.PENDING_NODE,
        active_node_id=0,
        last_object_clicked=node_0_obj,
        last_map_click={"lat": 0.0, "lng": 0.0},
    )

    map_data = {
        "last_object_clicked": node_0_obj,   # stale
        "last_object_clicked_tooltip": "0",  # stale
        "last_clicked": {"lat": 30.0, "lng": 40.0},
    }

    # Rerun 1: empty-space click creates a connected node
    state = EditController(graph, state).handle_click(map_data)
    assert state.state == State.IDLE
    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1

    # Rerun 2: same map_data — must be idempotent
    state2 = EditController(graph, state).handle_click(map_data)
    assert state2 is state
    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1


def test_moving_node_does_not_reselect_on_next_rerun():
    """
    Node 0 is selected. User clicks the map to move it (NODE_SELECTED → IDLE).
    On the next rerun the same last_object_clicked is still present — the
    controller must not re-enter NODE_SELECTED.
    """
    node_0_obj = {"lat": 0.0, "lng": 0.0}
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0)])
    state = EditState(
        state=State.NODE_SELECTED,
        active_node_id=0,
        last_object_clicked=node_0_obj,
        last_map_click={"lat": 0.0, "lng": 0.0},
    )

    map_data = {
        "last_object_clicked": node_0_obj,   # stale
        "last_object_clicked_tooltip": "0",  # stale
        "last_clicked": {"lat": 10.0, "lng": 20.0},
    }

    # Rerun 1: map click moves the node
    state = EditController(graph, state).handle_click(map_data)
    assert state.state == State.IDLE

    # Rerun 2: same map_data — must be idempotent, node must not be re-selected
    state2 = EditController(graph, state).handle_click(map_data)
    assert state2 is state
    assert state2.state == State.IDLE


def test_full_node_creation_and_connection_sequence():
    """
    Integration: simulate a complete sequence of user interactions across reruns.

    Steps:
      1. Click empty space → node 0 created (PENDING)
      2. Click empty space → node 1 created and connected to 0 (IDLE)
      3. Click node 0 → node 0 selected (NODE_SELECTED)
      4. Click empty space → node 0 moved (IDLE)

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
    assert EditController(graph, state).handle_click(map_data_1) is state  # idempotent

    # Step 2: create node 1 at (20, 20), connected to node 0
    map_data_2 = {**map_data_1, "last_clicked": {"lat": 20.0, "lng": 20.0}}
    state = EditController(graph, state).handle_click(map_data_2)
    assert state.state == State.IDLE
    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1
    assert EditController(graph, state).handle_click(map_data_2) is state  # idempotent

    # Step 3: click node 0 to select it
    map_data_3 = {
        "last_object_clicked": {"lat": 10.0, "lng": 10.0},
        "last_object_clicked_tooltip": "0",
        "last_clicked": {"lat": 10.0, "lng": 10.0},
    }
    state = EditController(graph, state).handle_click(map_data_3)
    assert state.state == State.NODE_SELECTED and state.active_node_id == 0
    assert EditController(graph, state).handle_click(map_data_3) is state  # idempotent

    # Step 4: move node 0 to (99, 99)
    map_data_4 = {**map_data_3, "last_clicked": {"lat": 99.0, "lng": 99.0}}
    state = EditController(graph, state).handle_click(map_data_4)
    assert state.state == State.IDLE
    assert graph.get_node(0).y == 99.0
    assert graph.get_node(0).x == 99.0
    assert EditController(graph, state).handle_click(map_data_4) is state  # idempotent

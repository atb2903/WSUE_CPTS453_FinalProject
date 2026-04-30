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

    # Step 4: move node 0 to (99, 99) in place
    map_data_4 = {**map_data_3, "last_clicked": {"lat": 99.0, "lng": 99.0}}
    state = EditController(graph, state).handle_click(map_data_4)
    assert state.state == State.IDLE
    assert graph.get_node(0).y == 99.0
    assert graph.get_node(0).x == 99.0
    assert EditController(graph, state).handle_click(map_data_4) is state  # idempotent


def test_connect_does_not_ghost_refire_on_next_rerun():
    """
    Bug scenario: node 0 is selected and the user clicks node 1 to connect
    them. On the very next rerun Streamlit rerenders with identical map_data.
    The controller must not fire a second connect (no second edge added).
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

    # Rerun 1: edge added, returns to IDLE
    state = EditController(graph, state).handle_click(map_data)
    assert state.state == State.IDLE
    assert len(graph.edges) == 1
    assert (graph.edges[0].from_id, graph.edges[0].to_id) == (0, 1)

    # Rerun 2: same map_data — the node-click has not changed, must be idempotent
    state2 = EditController(graph, state).handle_click(map_data)
    assert state2 is state
    assert len(graph.edges) == 1


def test_full_node_creation_and_extra_connect_sequence():
    """
    Integration: simulate a complete sequence including a NODE_SELECTED-side
    connect (clicking another node while one is selected adds an edge).

    Steps:
      1. Click empty space → node 0 created (PENDING)
      2. Click empty space → node 1 created and connected to 0 (IDLE)
      3. Click empty space → node 2 created (PENDING)
      4. Click node 0 to connect → edge 2→0 added (IDLE)
      5. Click node 2 to select it (NODE_SELECTED, node 2 is a leaf)
      6. Click node 1 to add edge 2→1 (IDLE) — both nodes survive

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
    assert graph.edges[0].from_id == 0 and graph.edges[0].to_id == 1  # edge direction: 0→1
    assert EditController(graph, state).handle_click(map_data_2) is state

    # Step 3: create node 2 at (30, 30) — pending
    # Node IDs are assigned sequentially: nodes 0 and 1 exist, so next_node_id() returns 2
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
    connecting_edge = next(e for e in graph.edges if e.from_id == 2 or e.to_id == 2)
    assert connecting_edge.from_id == 2 and connecting_edge.to_id == 0  # edge direction: 2→0
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

    # Step 6: click node 1 to add an edge from selected node 2 to node 1.
    # Both nodes remain. Existing edges (0→1, 2→0) are intact; new edge 2→1.
    node_1_obj = {"lat": 20.0, "lng": 20.0}
    map_data_6 = {
        "last_object_clicked": node_1_obj,
        "last_object_clicked_tooltip": "1",
        "last_clicked": {"lat": 20.0, "lng": 20.0},
    }
    state = EditController(graph, state).handle_click(map_data_6)
    assert state.state == State.IDLE
    assert len(graph.nodes) == 3
    assert {(0, 1), (2, 0), (2, 1)} == {(e.from_id, e.to_id) for e in graph.edges}
    assert EditController(graph, state).handle_click(map_data_6) is state


def test_non_leaf_selected_move_sequence_is_idempotent():
    """
    Integration: select a non-leaf from IDLE, then move it, and ensure the
    duplicate rerun after each step is a no-op.
    """
    graph = CampusGraph(
        nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=1.0, x=1.0), Node(id=2, y=2.0, x=2.0)],
        edges=[Edge(from_id=0, to_id=1), Edge(from_id=2, to_id=1)],
    )
    state = EditState()

    # Step 1: click non-leaf node 1 from IDLE
    map_data_1 = {
        "last_object_clicked": {"lat": 1.0, "lng": 1.0},
        "last_object_clicked_tooltip": "1",
        "last_clicked": {"lat": 1.0, "lng": 1.0},
    }
    state = EditController(graph, state).handle_click(map_data_1)
    assert state.state == State.NODE_SELECTED and state.active_node_id == 1
    assert EditController(graph, state).handle_click(map_data_1) is state

    # Step 2: move selected non-leaf node 1
    map_data_2 = {**map_data_1, "last_clicked": {"lat": 10.0, "lng": 20.0}}
    state = EditController(graph, state).handle_click(map_data_2)
    assert state.state == State.IDLE
    assert graph.get_node(1).y == 10.0
    assert graph.get_node(1).x == 20.0
    assert {(e.from_id, e.to_id) for e in graph.edges} == {(0, 1), (2, 1)}
    assert EditController(graph, state).handle_click(map_data_2) is state

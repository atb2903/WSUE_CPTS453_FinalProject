from map.graph import CampusGraph, Edge, Node
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


def test_map_click_moves_non_leaf_selected_node_and_returns_idle():
    graph = CampusGraph(
        nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=1.0, x=1.0), Node(id=2, y=2.0, x=2.0)],
        edges=[Edge(from_id=0, to_id=1), Edge(from_id=2, to_id=1)],
    )
    state = EditState(state=State.NODE_SELECTED, active_node_id=1)
    map_data = {
        "last_object_clicked": None,
        "last_object_clicked_tooltip": None,
        "last_clicked": {"lat": 10.0, "lng": 20.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.IDLE
    assert new_state.active_node_id is None
    assert graph.get_node(1).y == 10.0
    assert graph.get_node(1).x == 20.0
    assert {(e.from_id, e.to_id) for e in graph.edges} == {(0, 1), (2, 1)}


def test_node_click_in_node_selected_adds_edge_and_returns_idle():
    """Clicking another node while one is selected adds a directed edge from
    the active node to the clicked one and returns to IDLE. Both nodes
    remain in the graph."""
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=100.0, x=100.0)])
    state = EditState(state=State.NODE_SELECTED, active_node_id=0)
    map_data = {
        "last_object_clicked": {"lat": 100.0, "lng": 100.0},
        "last_object_clicked_tooltip": "1",
        "last_clicked": {"lat": 100.0, "lng": 100.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.IDLE
    assert new_state.active_node_id is None
    assert graph.get_node(0) is not None
    assert graph.get_node(1) is not None
    assert len(graph.edges) == 1
    assert graph.edges[0].from_id == 0
    assert graph.edges[0].to_id == 1


def test_connecting_to_non_leaf_target_is_allowed():
    """A selected leaf can be connected to a target of any degree — there is
    no leaf-only restriction on the target in NODE_SELECTED."""
    graph = CampusGraph(
        nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=1.0, x=1.0), Node(id=2, y=2.0, x=2.0)],
        edges=[Edge(from_id=0, to_id=1), Edge(from_id=2, to_id=1)],
    )
    state = EditState(state=State.NODE_SELECTED, active_node_id=2)
    map_data = {
        "last_object_clicked": {"lat": 1.0, "lng": 1.0},
        "last_object_clicked_tooltip": "1",
        "last_clicked": {"lat": 1.0, "lng": 1.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.IDLE
    # Existing edges intact; duplicate 2→1 is ignored by graph dedupe.
    assert len(graph.edges) == 2
    assert (2, 1) in {(e.from_id, e.to_id) for e in graph.edges}


def test_non_leaf_selected_can_connect_to_leaf_target():
    graph = CampusGraph(
        nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=1.0, x=1.0), Node(id=2, y=2.0, x=2.0)],
        edges=[Edge(from_id=0, to_id=1), Edge(from_id=2, to_id=1)],
    )
    state = EditState(state=State.NODE_SELECTED, active_node_id=1)
    map_data = {
        "last_object_clicked": {"lat": 0.0, "lng": 0.0},
        "last_object_clicked_tooltip": "0",
        "last_clicked": {"lat": 0.0, "lng": 0.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.IDLE
    assert (0, 1) in {(e.from_id, e.to_id) for e in graph.edges}
    assert (2, 1) in {(e.from_id, e.to_id) for e in graph.edges}
    assert (1, 0) not in {(e.from_id, e.to_id) for e in graph.edges}
    assert len(graph.edges) == 2


def test_connecting_two_already_connected_nodes_rejects_duplicate_edge():
    """Connecting nodes that are already connected is a no-op for edges."""
    graph = CampusGraph(
        nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=100.0, x=100.0)],
        edges=[Edge(from_id=0, to_id=1)],
    )
    state = EditState(state=State.NODE_SELECTED, active_node_id=0)
    map_data = {
        "last_object_clicked": {"lat": 100.0, "lng": 100.0},
        "last_object_clicked_tooltip": "1",
        "last_clicked": {"lat": 100.0, "lng": 100.0},
    }
    EditController(graph, state).handle_click(map_data)
    assert len(graph.edges) == 1
    assert graph.edges[0].from_id == 0
    assert graph.edges[0].to_id == 1


def test_connecting_reverse_direction_rejects_duplicate_undirected_pair():
    """If 1→0 already exists, attempting 0→1 does not add a second edge."""
    graph = CampusGraph(
        nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=100.0, x=100.0)],
        edges=[Edge(from_id=1, to_id=0)],
    )
    state = EditState(state=State.NODE_SELECTED, active_node_id=0)
    map_data = {
        "last_object_clicked": {"lat": 100.0, "lng": 100.0},
        "last_object_clicked_tooltip": "1",
        "last_clicked": {"lat": 100.0, "lng": 100.0},
    }
    EditController(graph, state).handle_click(map_data)
    assert len(graph.edges) == 1
    assert graph.edges[0].from_id == 1
    assert graph.edges[0].to_id == 0


def test_clicking_active_node_itself_stays_selected():
    """Clicking the already-selected node while in NODE_SELECTED stays selected."""
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0)])
    state = EditState(state=State.NODE_SELECTED, active_node_id=0)
    obj_clicked = {"lat": 0.0, "lng": 0.0}
    map_data = {
        "last_object_clicked": obj_clicked,
        "last_object_clicked_tooltip": "0",
        "last_clicked": {"lat": 0.0, "lng": 0.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.NODE_SELECTED
    assert new_state.active_node_id == 0
    assert len(graph.nodes) == 1


def test_connect_is_idempotent_on_second_rerun():
    """After connecting via a node click, a second rerun with identical map_data
    must not re-fire (i.e. no second edge gets added)."""
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=100.0, x=100.0)])
    state = EditState(state=State.NODE_SELECTED, active_node_id=0)
    obj_clicked = {"lat": 100.0, "lng": 100.0}
    map_data = {
        "last_object_clicked": obj_clicked,
        "last_object_clicked_tooltip": "1",
        "last_clicked": {"lat": 100.0, "lng": 100.0},
    }
    # Rerun 1: edge added
    state = EditController(graph, state).handle_click(map_data)
    assert state.state == State.IDLE
    assert len(graph.edges) == 1
    # Rerun 2: same map_data — click is not new, must be idempotent
    state2 = EditController(graph, state).handle_click(map_data)
    assert state2 is state
    assert len(graph.edges) == 1


def test_map_click_on_other_node_coords_is_no_op_in_node_selected():
    """Moving the active node onto another node's exact coordinates is rejected
    by the graph; the edit-controller must keep the selection intact."""
    graph = CampusGraph(
        nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=5.0, x=5.0)]
    )
    state = EditState(state=State.NODE_SELECTED, active_node_id=0)
    map_data = {
        "last_object_clicked": None,
        "last_object_clicked_tooltip": None,
        "last_clicked": {"lat": 5.0, "lng": 5.0},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.NODE_SELECTED
    assert new_state.active_node_id == 0
    assert graph.get_node(0).y == 0.0
    assert graph.get_node(0).x == 0.0
    assert new_state.last_map_click == {"lat": 5.0, "lng": 5.0}


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



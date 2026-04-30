from map.edit_controller import EditController, EditState, State
from map.graph import CampusGraph, Edge, Node


def test_edge_tooltip_click_transitions_to_edge_selected():
    graph = CampusGraph(
        nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=1.0, x=1.0)],
        edges=[Edge(from_id=0, to_id=1)],
    )
    state = EditState()
    map_data = {
        "last_object_clicked": {"lat": 0.5, "lng": 0.5},
        "last_object_clicked_tooltip": "edge:0-1",
        "last_clicked": {"lat": 0.5, "lng": 0.5},
    }
    new_state = EditController(graph, state).handle_click(map_data)
    assert new_state.state == State.EDGE_SELECTED
    assert new_state.selected_edge == (0, 1)


def test_delete_selected_removes_selected_edge_and_returns_idle():
    graph = CampusGraph(
        nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=1.0, x=1.0)],
        edges=[Edge(from_id=0, to_id=1)],
    )
    state = EditState(state=State.EDGE_SELECTED, selected_edge=(0, 1))
    new_state = EditController(graph, state).handle_delete_selected()
    assert new_state.state == State.IDLE
    assert new_state.selected_edge is None
    assert len(graph.edges) == 0


def test_delete_selected_removes_selected_node_and_incident_edges():
    graph = CampusGraph(
        nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=1.0, x=1.0), Node(id=2, y=2.0, x=2.0)],
        edges=[Edge(from_id=0, to_id=1), Edge(from_id=2, to_id=1)],
    )
    state = EditState(state=State.NODE_SELECTED, active_node_id=1)
    new_state = EditController(graph, state).handle_delete_selected()
    assert new_state.state == State.IDLE
    assert new_state.active_node_id is None
    assert graph.get_node(1) is None
    assert len(graph.edges) == 0


def test_delete_selected_with_no_selection_is_noop():
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0)])
    state = EditState()
    new_state = EditController(graph, state).handle_delete_selected()
    assert new_state.state == State.IDLE
    assert len(graph.nodes) == 1


def test_repeated_delete_selected_call_is_idempotent():
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0)])
    state = EditState(state=State.NODE_SELECTED, active_node_id=0)
    after_first = EditController(graph, state).handle_delete_selected()
    assert graph.get_node(0) is None
    after_second = EditController(graph, after_first).handle_delete_selected()
    assert after_second is after_first


def test_deselect_clears_selected_node_without_graph_mutation():
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0)])
    state = EditState(state=State.NODE_SELECTED, active_node_id=0)
    new_state = EditController(graph, state).handle_deselect()
    assert new_state.state == State.IDLE
    assert new_state.active_node_id is None
    assert graph.get_node(0) is not None


def test_deselect_clears_selected_edge_without_graph_mutation():
    graph = CampusGraph(
        nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=1.0, x=1.0)],
        edges=[Edge(from_id=0, to_id=1)],
    )
    state = EditState(state=State.EDGE_SELECTED, selected_edge=(0, 1))
    new_state = EditController(graph, state).handle_deselect()
    assert new_state.state == State.IDLE
    assert new_state.selected_edge is None
    assert len(graph.edges) == 1


def test_deselect_with_no_selection_is_noop():
    graph = CampusGraph()
    state = EditState()
    new_state = EditController(graph, state).handle_deselect()
    assert new_state is state

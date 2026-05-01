import pytest

from map.graph import CampusGraph, Edge, Node


def test_move_node_updates_position_in_index_and_list():
    node = Node(id=0, y=0.0, x=0.0)
    graph = CampusGraph(nodes=[node])
    graph.move_node(0, y=500.0, x=300.0)
    updated = graph.get_node(0)
    assert updated.y == 500.0
    assert updated.x == 300.0
    assert graph.nodes[0].y == 500.0
    assert graph.nodes[0].x == 300.0


def test_move_node_preserves_id():
    node = Node(id=7, y=0.0, x=0.0)
    graph = CampusGraph(nodes=[node])
    graph.move_node(7, y=100.0, x=200.0)
    updated = graph.get_node(7)
    assert updated.id == 7


def test_move_node_does_not_affect_other_nodes():
    graph = CampusGraph(nodes=[
        Node(id=0, y=0.0, x=0.0),
        Node(id=1, y=5.0, x=5.0),
        Node(id=2, y=10.0, x=10.0),
    ])
    graph.move_node(1, y=99.0, x=99.0)
    assert graph.get_node(0).y == 0.0
    assert graph.get_node(0).x == 0.0
    assert graph.get_node(2).y == 10.0
    assert graph.get_node(2).x == 10.0


def test_move_node_raises_key_error_for_unknown_id():
    graph = CampusGraph()
    with pytest.raises(KeyError):
        graph.move_node(99, y=1.0, x=1.0)


def test_move_node_raises_when_target_coordinates_match_other_node():
    graph = CampusGraph(nodes=[
        Node(id=0, y=0.0, x=0.0),
        Node(id=1, y=5.0, x=5.0),
    ])
    with pytest.raises(ValueError, match="coordinates"):
        graph.move_node(0, y=5.0, x=5.0)
    assert graph.get_node(0).y == 0.0
    assert graph.get_node(0).x == 0.0


def test_move_node_allows_setting_to_current_coordinates():
    graph = CampusGraph(nodes=[Node(id=0, y=3.0, x=4.0)])
    graph.move_node(0, y=3.0, x=4.0)
    assert graph.get_node(0).y == 3.0
    assert graph.get_node(0).x == 4.0


def test_remove_node_removes_node_from_list_and_index():
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=1.0, x=1.0)])
    graph.remove_node(0)
    assert graph.get_node(0) is None
    assert len(graph.nodes) == 1
    assert graph.nodes[0].id == 1


def test_remove_node_drops_all_incident_edges():
    graph = CampusGraph(
        nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=1.0, x=1.0), Node(id=2, y=2.0, x=2.0)],
        edges=[Edge(from_id=0, to_id=1), Edge(from_id=2, to_id=0), Edge(from_id=1, to_id=2)],
    )
    graph.remove_node(0)
    assert len(graph.edges) == 1
    assert graph.edges[0].from_id == 1
    assert graph.edges[0].to_id == 2


def test_remove_node_raises_key_error_for_unknown_id():
    graph = CampusGraph()
    with pytest.raises(KeyError):
        graph.remove_node(99)


def test_remove_edge_removes_exact_direction_match():
    graph = CampusGraph(edges=[Edge(from_id=0, to_id=1), Edge(from_id=1, to_id=2)])
    removed = graph.remove_edge(0, 1)
    assert removed is True
    assert len(graph.edges) == 1
    assert graph.edges[0].from_id == 1
    assert graph.edges[0].to_id == 2


def test_remove_edge_removes_reverse_direction_match():
    graph = CampusGraph(edges=[Edge(from_id=1, to_id=0)])
    removed = graph.remove_edge(0, 1)
    assert removed is True
    assert graph.edges == []


def test_remove_edge_returns_false_when_pair_missing():
    graph = CampusGraph(edges=[Edge(from_id=0, to_id=1)])
    removed = graph.remove_edge(0, 2)
    assert removed is False
    assert len(graph.edges) == 1

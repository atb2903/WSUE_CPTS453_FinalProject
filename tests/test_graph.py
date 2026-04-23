import pytest
from dataclasses import FrozenInstanceError

from map.graph import Node, Edge, CampusGraph


def test_node_stores_attributes():
    node = Node(id=0, label="Test Node", y=100.0, x=200.0)
    assert node.id == 0
    assert node.label == "Test Node"
    assert node.y == 100.0
    assert node.x == 200.0


def test_node_is_immutable():
    node = Node(id=0, label="Test", y=0.0, x=0.0)
    with pytest.raises(FrozenInstanceError):
        node.id = 1  # type: ignore[misc]


def test_edge_stores_from_and_to():
    edge = Edge(from_id=0, to_id=1)
    assert edge.from_id == 0
    assert edge.to_id == 1


def test_edge_is_immutable():
    edge = Edge(from_id=0, to_id=1)
    with pytest.raises(FrozenInstanceError):
        edge.from_id = 2  # type: ignore[misc]


def test_campus_graph_starts_empty():
    graph = CampusGraph()
    assert graph.nodes == []
    assert graph.edges == []


def test_campus_graph_get_node_returns_matching_node():
    node = Node(id=42, label="A", y=1.0, x=2.0)
    graph = CampusGraph(nodes=[node])
    assert graph.get_node(42) is node


def test_campus_graph_get_node_returns_none_for_unknown_id():
    graph = CampusGraph()
    assert graph.get_node(99) is None


def test_campus_graph_get_node_finds_correct_node_among_multiple():
    node_a = Node(id=0, label="A", y=0.0, x=0.0)
    node_b = Node(id=1, label="B", y=1.0, x=1.0)
    node_c = Node(id=2, label="C", y=2.0, x=2.0)
    graph = CampusGraph(nodes=[node_a, node_b, node_c])
    assert graph.get_node(1) is node_b


def test_add_node_appends_and_indexes_node():
    graph = CampusGraph()
    node = Node(id=0, label="A", y=0.0, x=0.0)
    graph.add_node(node)
    assert node in graph.nodes
    assert graph.get_node(0) is node


def test_add_node_raises_on_duplicate_id():
    graph = CampusGraph()
    node = Node(id=0, label="A", y=0.0, x=0.0)
    graph.add_node(node)
    with pytest.raises(ValueError, match="already exists"):
        graph.add_node(Node(id=0, label="B", y=1.0, x=1.0))


def test_add_edge_appends_edge():
    graph = CampusGraph()
    edge = Edge(from_id=0, to_id=1)
    graph.add_edge(edge)
    assert edge in graph.edges

import pytest

from map.graph import CampusGraph, Edge, Node


def test_campus_graph_starts_empty():
    graph = CampusGraph()
    assert graph.nodes == []
    assert graph.edges == []


def test_add_node_appends_and_indexes_node():
    graph = CampusGraph()
    node = Node(id=0, y=0.0, x=0.0)
    graph.add_node(node)
    assert node in graph.nodes
    assert graph.get_node(0) is node


def test_add_node_raises_on_duplicate_id():
    graph = CampusGraph()
    node = Node(id=0, y=0.0, x=0.0)
    graph.add_node(node)
    with pytest.raises(ValueError, match="already exists"):
        graph.add_node(Node(id=0, y=1.0, x=1.0))


def test_add_edge_appends_edge():
    graph = CampusGraph()
    edge = Edge(from_id=0, to_id=1)
    graph.add_edge(edge)
    assert edge in graph.edges


def test_add_edge_ignores_duplicate_same_direction():
    graph = CampusGraph(edges=[Edge(from_id=0, to_id=1)])
    graph.add_edge(Edge(from_id=0, to_id=1))
    assert len(graph.edges) == 1
    assert graph.edges[0].from_id == 0
    assert graph.edges[0].to_id == 1


def test_add_edge_ignores_duplicate_reverse_direction():
    graph = CampusGraph(edges=[Edge(from_id=1, to_id=0)])
    graph.add_edge(Edge(from_id=0, to_id=1))
    assert len(graph.edges) == 1
    assert graph.edges[0].from_id == 1
    assert graph.edges[0].to_id == 0


def test_add_edge_allows_distinct_node_pair():
    graph = CampusGraph(edges=[Edge(from_id=0, to_id=1)])
    graph.add_edge(Edge(from_id=1, to_id=2))
    assert len(graph.edges) == 2
    assert (0, 1) in {(e.from_id, e.to_id) for e in graph.edges}
    assert (1, 2) in {(e.from_id, e.to_id) for e in graph.edges}

from map.graph import CampusGraph, Edge, Node


def test_campus_graph_get_node_returns_matching_node():
    node = Node(id=42, y=1.0, x=2.0)
    graph = CampusGraph(nodes=[node])
    assert graph.get_node(42) is node


def test_campus_graph_get_node_returns_none_for_unknown_id():
    graph = CampusGraph()
    assert graph.get_node(99) is None


def test_campus_graph_get_node_finds_correct_node_among_multiple():
    node_a = Node(id=0, y=0.0, x=0.0)
    node_b = Node(id=1, y=1.0, x=1.0)
    node_c = Node(id=2, y=2.0, x=2.0)
    graph = CampusGraph(nodes=[node_a, node_b, node_c])
    assert graph.get_node(1) is node_b


def test_degree_isolated_node_is_zero():
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0)])
    assert graph.degree(0) == 0


def test_degree_counts_from_id_and_to_id():
    """An edge A→B contributes 1 to the degree of both A (from_id) and B (to_id)."""
    graph = CampusGraph(
        nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=1.0, x=1.0)],
        edges=[Edge(from_id=0, to_id=1)],
    )
    assert graph.degree(0) == 1
    assert graph.degree(1) == 1


def test_degree_non_leaf_node(non_leaf_graph):
    assert non_leaf_graph.degree(1) == 2


def test_degree_unknown_node_id_returns_zero():
    graph = CampusGraph()
    assert graph.degree(99) == 0


def test_next_node_id_returns_zero_for_empty_graph():
    assert CampusGraph().next_node_id() == 0


def test_next_node_id_returns_max_id_plus_one():
    graph = CampusGraph(nodes=[Node(id=0, y=0.0, x=0.0), Node(id=3, y=0.0, x=0.0)])
    assert graph.next_node_id() == 4


def test_next_node_id_reflects_added_nodes():
    graph = CampusGraph()
    graph.add_node(Node(id=5, y=0.0, x=0.0))
    assert graph.next_node_id() == 6

import pytest

from map.graph import CampusGraph, Edge, Node


@pytest.fixture
def non_leaf_graph() -> CampusGraph:
    """Three nodes where node 1 has degree 2 (connected to both 0 and 2)."""
    return CampusGraph(
        nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=1.0, x=1.0), Node(id=2, y=2.0, x=2.0)],
        edges=[Edge(from_id=0, to_id=1), Edge(from_id=2, to_id=1)],
    )

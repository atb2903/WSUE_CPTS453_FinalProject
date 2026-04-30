import pytest
from dataclasses import FrozenInstanceError

from map.graph import Edge


def test_edge_stores_from_and_to():
    edge = Edge(from_id=0, to_id=1)
    assert edge.from_id == 0
    assert edge.to_id == 1


def test_edge_is_immutable():
    edge = Edge(from_id=0, to_id=1)
    with pytest.raises(FrozenInstanceError):
        edge.from_id = 2  # type: ignore[misc]

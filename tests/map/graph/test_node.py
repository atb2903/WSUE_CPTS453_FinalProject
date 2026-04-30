import pytest
from dataclasses import FrozenInstanceError

from map.graph import Node


def test_node_stores_attributes():
    node = Node(id=0, y=100.0, x=200.0)
    assert node.id == 0
    assert node.y == 100.0
    assert node.x == 200.0


def test_node_is_immutable():
    node = Node(id=0, y=0.0, x=0.0)
    with pytest.raises(FrozenInstanceError):
        node.id = 1  # type: ignore[misc]

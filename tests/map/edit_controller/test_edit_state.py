import pytest
from dataclasses import FrozenInstanceError

from map.edit_controller import EditState, State


def test_defaults_to_idle():
    state = EditState()
    assert state.state == State.IDLE
    assert state.active_node_id is None
    assert state.selected_edge is None
    assert state.last_object_clicked is None
    assert state.last_map_click is None


def test_is_immutable():
    state = EditState()
    with pytest.raises(FrozenInstanceError):
        state.state = State.NODE_SELECTED  # type: ignore[misc]


def test_caption_idle():
    assert EditState().caption == (
        "Click a node to select it and move it, or click empty space to add a new node."
    )


def test_caption_node_selected():
    state = EditState(state=State.NODE_SELECTED, active_node_id=3)
    assert state.caption == (
        "Node 3 selected — click the map to move it, "
        "click another node to connect them, or click Delete Selected."
    )


def test_caption_edge_selected():
    state = EditState(state=State.EDGE_SELECTED, selected_edge=(2, 5))
    assert state.caption == "Edge 2-5 selected — click Delete Selected."


def test_caption_edge_selected_without_explicit_pair():
    state = EditState(state=State.EDGE_SELECTED)
    assert state.caption == "Edge selected — click Delete Selected."


def test_caption_pending_node():
    state = EditState(state=State.PENDING_NODE, active_node_id=0)
    assert state.caption == (
        "Node placed — click an existing node to connect it, "
        "or click empty space to add a connected node."
    )

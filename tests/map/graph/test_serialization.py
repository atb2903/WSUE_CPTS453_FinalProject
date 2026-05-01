import pytest

from map.graph import CampusGraph, Edge, Node


def test_to_dict_round_trip_preserves_graph_contents():
    original = CampusGraph(
        nodes=[Node(id=0, y=12.5, x=7.25), Node(id=1, y=1.0, x=2.0)],
        edges=[Edge(from_id=0, to_id=1)],
    )
    payload = original.to_dict()
    restored = CampusGraph.from_dict(payload)
    assert restored.to_dict() == payload


def test_save_and_load_file_round_trip(tmp_path):
    path = tmp_path / "graph.json"
    graph = CampusGraph(
        nodes=[Node(id=2, y=3.0, x=4.0), Node(id=4, y=5.0, x=6.0)],
        edges=[Edge(from_id=2, to_id=4)],
    )
    graph.save_to_file(path)
    loaded = CampusGraph.load_from_file(path)
    assert loaded.to_dict() == graph.to_dict()


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"nodes": [], "edges": "not-a-list"},
        {"nodes": "not-a-list", "edges": []},
    ],
)
def test_from_dict_raises_for_missing_or_non_list_top_level_fields(payload):
    with pytest.raises(ValueError, match="nodes|edges"):
        CampusGraph.from_dict(payload)


@pytest.mark.parametrize(
    "payload",
    [
        {"nodes": [{"id": 1, "y": 0.0}], "edges": []},
        {"nodes": [{}], "edges": []},
    ],
)
def test_from_dict_raises_for_invalid_node_shapes(payload):
    with pytest.raises(ValueError, match="node|id|y|x"):
        CampusGraph.from_dict(payload)


@pytest.mark.parametrize(
    "payload",
    [
        {"nodes": [{"id": 1, "y": 0.0, "x": 0.0}], "edges": [{"from_id": 1}]},
        {"nodes": [{"id": 1, "y": 0.0, "x": 0.0}], "edges": [{}]},
    ],
)
def test_from_dict_raises_for_invalid_edge_shapes(payload):
    with pytest.raises(ValueError, match="edge|from_id|to_id"):
        CampusGraph.from_dict(payload)


def test_from_dict_raises_for_duplicate_node_ids():
    payload = {
        "nodes": [
            {"id": 1, "y": 0.0, "x": 0.0},
            {"id": 1, "y": 1.0, "x": 1.0},
        ],
        "edges": [],
    }
    with pytest.raises(ValueError, match="already exists"):
        CampusGraph.from_dict(payload)


def test_from_dict_merges_duplicate_node_locations_using_first_id():
    payload = {
        "nodes": [
            {"id": 10, "y": 100.0, "x": 200.0},
            {"id": 11, "y": 100.0, "x": 200.0},
            {"id": 12, "y": 150.0, "x": 250.0},
        ],
        "edges": [],
    }

    graph = CampusGraph.from_dict(payload)

    assert graph.to_dict()["nodes"] == [
        {"id": 10, "y": 100.0, "x": 200.0},
        {"id": 12, "y": 150.0, "x": 250.0},
    ]


def test_from_dict_remaps_edges_after_duplicate_location_merge():
    payload = {
        "nodes": [
            {"id": 10, "y": 100.0, "x": 200.0},
            {"id": 11, "y": 100.0, "x": 200.0},
            {"id": 12, "y": 150.0, "x": 250.0},
        ],
        "edges": [
            {"from_id": 11, "to_id": 12},
        ],
    }

    graph = CampusGraph.from_dict(payload)

    assert graph.to_dict()["edges"] == [{"from_id": 10, "to_id": 12}]


def test_from_dict_drops_self_loop_created_by_duplicate_location_merge():
    payload = {
        "nodes": [
            {"id": 10, "y": 100.0, "x": 200.0},
            {"id": 11, "y": 100.0, "x": 200.0},
        ],
        "edges": [
            {"from_id": 10, "to_id": 11},
        ],
    }

    graph = CampusGraph.from_dict(payload)

    assert graph.to_dict()["edges"] == []


def test_from_dict_raises_for_non_dict_payload():
    with pytest.raises(ValueError, match="dictionary"):
        CampusGraph.from_dict([])  # type: ignore[arg-type]


def test_from_dict_raises_when_node_item_is_not_dict():
    payload = {"nodes": [123], "edges": []}
    with pytest.raises(ValueError, match="node"):
        CampusGraph.from_dict(payload)


def test_from_dict_raises_when_edge_item_is_not_dict():
    payload = {
        "nodes": [{"id": 1, "y": 0.0, "x": 0.0}],
        "edges": [456],
    }
    with pytest.raises(ValueError, match="edge"):
        CampusGraph.from_dict(payload)

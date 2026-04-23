import folium
from folium.vector_layers import CircleMarker, PolyLine

from map.graph import CampusGraph, Edge, Node
from map.graph_renderer import GraphOverlayRenderer


def _children_of_type(campus_map: folium.Map, kind: type) -> list:
    return [c for c in campus_map._children.values() if isinstance(c, kind)]


def _make_base_map() -> folium.Map:
    return folium.Map(crs="Simple")


def _make_two_node_graph() -> CampusGraph:
    return CampusGraph(
        nodes=[
            Node(id=0, label="Node A", y=900.0, x=100.0),
            Node(id=1, label="Node B", y=100.0, x=900.0),
        ],
        edges=[Edge(from_id=0, to_id=1)],
    )


def test_render_onto_adds_one_circle_marker_per_node():
    campus_map = _make_base_map()
    GraphOverlayRenderer(_make_two_node_graph()).render_onto(campus_map)
    assert len(_children_of_type(campus_map, CircleMarker)) == 2


def test_render_onto_adds_one_polyline_per_edge():
    campus_map = _make_base_map()
    GraphOverlayRenderer(_make_two_node_graph()).render_onto(campus_map)
    assert len(_children_of_type(campus_map, PolyLine)) == 1


def test_render_onto_skips_edge_with_unknown_from_id():
    campus_map = _make_base_map()
    graph = CampusGraph(
        nodes=[Node(id=1, label="B", y=100.0, x=900.0)],
        edges=[Edge(from_id=99, to_id=1)],
    )
    GraphOverlayRenderer(graph).render_onto(campus_map)
    assert len(_children_of_type(campus_map, PolyLine)) == 0


def test_render_onto_skips_edge_with_unknown_to_id():
    campus_map = _make_base_map()
    graph = CampusGraph(
        nodes=[Node(id=0, label="A", y=900.0, x=100.0)],
        edges=[Edge(from_id=0, to_id=99)],
    )
    GraphOverlayRenderer(graph).render_onto(campus_map)
    assert len(_children_of_type(campus_map, PolyLine)) == 0


def test_render_onto_empty_graph_adds_nothing():
    campus_map = _make_base_map()
    before = set(campus_map._children.keys())
    GraphOverlayRenderer(CampusGraph()).render_onto(campus_map)
    after = set(campus_map._children.keys())
    assert before == after

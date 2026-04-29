import folium
from folium.vector_layers import CircleMarker, PolyLine

from map.graph import CampusGraph, Edge, Node
from map.graph_renderer import GraphOverlayRenderer


def _children_of_type(parent, kind: type) -> list:
    return [c for c in parent._children.values() if isinstance(c, kind)]


def _make_base_map() -> folium.Map:
    return folium.Map(crs="Simple")


def _make_two_node_graph() -> CampusGraph:
    return CampusGraph(
        nodes=[
            Node(id=0, y=900.0, x=100.0),
            Node(id=1, y=100.0, x=900.0),
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
        nodes=[Node(id=1, y=100.0, x=900.0)],
        edges=[Edge(from_id=99, to_id=1)],
    )
    GraphOverlayRenderer(graph).render_onto(campus_map)
    assert len(_children_of_type(campus_map, PolyLine)) == 0


def test_render_onto_skips_edge_with_unknown_to_id():
    campus_map = _make_base_map()
    graph = CampusGraph(
        nodes=[Node(id=0, y=900.0, x=100.0)],
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


def test_highlighted_node_renders_in_wsu_crimson():
    campus_map = _make_base_map()
    GraphOverlayRenderer(_make_two_node_graph()).render_onto(campus_map, highlighted_node_id=0)
    markers = _children_of_type(campus_map, CircleMarker)
    assert len([m for m in markers if m.options["color"] == "#981e32"]) == 1


def test_unhighlighted_nodes_render_in_wsu_gray():
    campus_map = _make_base_map()
    GraphOverlayRenderer(_make_two_node_graph()).render_onto(campus_map, highlighted_node_id=0)
    markers = _children_of_type(campus_map, CircleMarker)
    assert len([m for m in markers if m.options["color"] == "#717c7d"]) == 1


def test_no_highlight_all_nodes_render_in_wsu_gray():
    campus_map = _make_base_map()
    GraphOverlayRenderer(_make_two_node_graph()).render_onto(campus_map)
    markers = _children_of_type(campus_map, CircleMarker)
    assert all(m.options["color"] == "#717c7d" for m in markers)


def test_node_tooltip_is_string_id():
    fg = folium.FeatureGroup()
    graph = CampusGraph(nodes=[Node(id=7, y=0.0, x=0.0)])
    GraphOverlayRenderer(graph).render_onto(fg)
    markers = _children_of_type(fg, CircleMarker)
    assert len(markers) == 1
    tooltips = [c for c in markers[0]._children.values() if isinstance(c, folium.Tooltip)]
    assert len(tooltips) == 1
    assert tooltips[0].text == "7"

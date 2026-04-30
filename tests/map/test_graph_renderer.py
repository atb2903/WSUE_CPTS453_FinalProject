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


def test_circle_marker_location_matches_node_coordinates():
    fg = folium.FeatureGroup()
    graph = CampusGraph(nodes=[Node(id=0, y=123.0, x=456.0)])
    GraphOverlayRenderer(graph).render_onto(fg)
    markers = _children_of_type(fg, CircleMarker)
    assert markers[0].location == [123.0, 456.0]


def test_render_onto_adds_one_polyline_per_edge():
    campus_map = _make_base_map()
    GraphOverlayRenderer(_make_two_node_graph()).render_onto(campus_map)
    assert len(_children_of_type(campus_map, PolyLine)) == 1


def test_polyline_locations_match_node_coordinates():
    fg = folium.FeatureGroup()
    graph = CampusGraph(
        nodes=[Node(id=0, y=0.0, x=0.0), Node(id=1, y=10.0, x=20.0)],
        edges=[Edge(from_id=0, to_id=1)],
    )
    GraphOverlayRenderer(graph).render_onto(fg)
    lines = _children_of_type(fg, PolyLine)
    assert lines[0].locations == [[0.0, 0.0], [10.0, 20.0]]


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


def _tooltip_text(marker: CircleMarker) -> str:
    tooltips = [c for c in marker._children.values() if isinstance(c, folium.Tooltip)]
    return tooltips[0].text if tooltips else ""


def test_highlighted_node_renders_in_wsu_crimson():
    campus_map = _make_base_map()
    GraphOverlayRenderer(_make_two_node_graph()).render_onto(campus_map, highlighted_node_id=0)
    markers = _children_of_type(campus_map, CircleMarker)
    highlighted = next(m for m in markers if _tooltip_text(m) == "0")
    assert highlighted.options["color"] == "#981e32"


def test_unhighlighted_nodes_render_in_wsu_gray():
    campus_map = _make_base_map()
    GraphOverlayRenderer(_make_two_node_graph()).render_onto(campus_map, highlighted_node_id=0)
    markers = _children_of_type(campus_map, CircleMarker)
    unhighlighted = next(m for m in markers if _tooltip_text(m) == "1")
    assert unhighlighted.options["color"] == "#717c7d"


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


def test_edge_tooltip_uses_canonical_edge_identifier():
    fg = folium.FeatureGroup()
    graph = CampusGraph(
        nodes=[Node(id=2, y=0.0, x=0.0), Node(id=1, y=10.0, x=20.0)],
        edges=[Edge(from_id=2, to_id=1)],
    )
    GraphOverlayRenderer(graph).render_onto(fg)
    lines = _children_of_type(fg, PolyLine)
    assert len(lines) == 1
    tooltips = [c for c in lines[0]._children.values() if isinstance(c, folium.Tooltip)]
    assert len(tooltips) == 1
    assert tooltips[0].text == "edge:1-2"


def test_highlighted_edge_renders_in_wsu_crimson():
    campus_map = _make_base_map()
    GraphOverlayRenderer(_make_two_node_graph()).render_onto(campus_map, highlighted_edge=(0, 1))
    lines = _children_of_type(campus_map, PolyLine)
    assert len(lines) == 1
    assert lines[0].options["color"] == "#981e32"


def test_unhighlighted_edge_renders_in_wsu_gray():
    campus_map = _make_base_map()
    GraphOverlayRenderer(_make_two_node_graph()).render_onto(campus_map, highlighted_edge=(1, 2))
    lines = _children_of_type(campus_map, PolyLine)
    assert len(lines) == 1
    assert lines[0].options["color"] == "#717c7d"

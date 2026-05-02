from collections.abc import Iterable

import folium

from map.graph import CampusGraph

_WSU_GRAY = "#4D4D4D"
_WSU_CRIMSON = "#A60F2D"
_NODE_RADIUS = 8
_EDGE_WEIGHT = 3


class GraphOverlayRenderer:
    """
    Renders a CampusGraph onto a folium.Map or folium.FeatureGroup using
    CRS.Simple pixel coordinates.

    Edges are drawn before nodes so nodes sit on top visually.
    Edges referencing unknown node IDs are silently skipped.
    Highlighted nodes/edges are drawn in WSU crimson; the rest in WSU gray.
    """

    def __init__(self, graph: CampusGraph) -> None:
        self._graph = graph

    def render_onto(
        self,
        parent: folium.Map | folium.FeatureGroup,
        highlighted_node_ids: Iterable[int] = (),
        highlighted_edges: Iterable[tuple[int, int]] = (),
    ) -> None:
        """Draw the graph overlay onto parent in-place."""
        node_set = set(highlighted_node_ids)
        edge_set = {(min(a, b), max(a, b)) for a, b in highlighted_edges}
        self._draw_edges(parent, edge_set)
        self._draw_nodes(parent, node_set)

    def _draw_edges(
        self,
        parent: folium.Map | folium.FeatureGroup,
        highlighted_edges: set[tuple[int, int]],
    ) -> None:
        for edge in self._graph.edges:
            from_node = self._graph.get_node(edge.from_id)
            to_node = self._graph.get_node(edge.to_id)
            if from_node is None or to_node is None:
                # TODO: add a warning to the user instead of silently skipping over the bad edge.
                continue
            first = min(edge.from_id, edge.to_id)
            second = max(edge.from_id, edge.to_id)
            color = _WSU_CRIMSON if (first, second) in highlighted_edges else _WSU_GRAY
            folium.PolyLine(
                locations = [[from_node.y, from_node.x], [to_node.y, to_node.x]],
                color = color,
                weight = _EDGE_WEIGHT,
                tooltip = f"edge:{first}-{second}",
            ).add_to(parent)

    def _draw_nodes(
        self,
        parent: folium.Map | folium.FeatureGroup,
        highlighted_node_ids: set[int],
    ) -> None:
        for node in self._graph.nodes:
            color = _WSU_CRIMSON if node.id in highlighted_node_ids else _WSU_GRAY
            folium.CircleMarker(
                location = [node.y, node.x],
                radius = _NODE_RADIUS,
                color = color,
                fill = True,
                fill_opacity = 1.0,
                tooltip = str(node.id),
            ).add_to(parent)

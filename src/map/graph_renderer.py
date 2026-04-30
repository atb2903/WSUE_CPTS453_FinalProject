import folium

from map.graph import CampusGraph

_WSU_GRAY = "#717c7d"
_WSU_CRIMSON = "#981e32"
_NODE_RADIUS = 8
_EDGE_WEIGHT = 3


class GraphOverlayRenderer:
    """
    Renders a CampusGraph onto a folium.Map or folium.FeatureGroup using
    CRS.Simple pixel coordinates.

    Edges are drawn before nodes so nodes sit on top visually.
    Edges referencing unknown node IDs are silently skipped.
    """

    def __init__(self, graph: CampusGraph) -> None:
        self._graph = graph

    def render_onto(
        self,
        parent: folium.Map | folium.FeatureGroup,
        highlighted_node_id: int | None = None,
    ) -> None:
        """Draw the graph overlay onto parent in-place."""
        self._draw_edges(parent)
        self._draw_nodes(parent, highlighted_node_id)

    def _draw_edges(self, parent: folium.Map | folium.FeatureGroup) -> None:
        for edge in self._graph.edges:
            from_node = self._graph.get_node(edge.from_id)
            to_node = self._graph.get_node(edge.to_id)
            if from_node is None or to_node is None:
                continue
            first = min(edge.from_id, edge.to_id)
            second = max(edge.from_id, edge.to_id)
            folium.PolyLine(
                locations=[[from_node.y, from_node.x], [to_node.y, to_node.x]],
                color=_WSU_GRAY,
                weight=_EDGE_WEIGHT,
                tooltip=f"edge:{first}-{second}",
            ).add_to(parent)

    def _draw_nodes(
        self, parent: folium.Map | folium.FeatureGroup, highlighted_node_id: int | None
    ) -> None:
        for node in self._graph.nodes:
            color = _WSU_CRIMSON if node.id == highlighted_node_id else _WSU_GRAY
            folium.CircleMarker(
                location=[node.y, node.x],
                radius=_NODE_RADIUS,
                color=color,
                fill=True,
                fill_opacity=1.0,
                tooltip=str(node.id),
            ).add_to(parent)

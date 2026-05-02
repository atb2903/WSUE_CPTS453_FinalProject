from dataclasses import dataclass

from map.graph import CampusGraph, Node
from map.pathfinding import dijkstra_shortest_path


@dataclass(frozen=True)
class NavState:
    """
    Navigation-mode interaction state.

    selected_node_ids holds 0, 1, or 2 endpoint ids in selection order.
    path_node_ids and path_edges are populated only after a successful
    Dijkstra run. pathfind_failed is a transient flag used to surface a
    "no path" warning on the rerun that processed the click.
    """
    selected_node_ids: tuple[int, ...] = ()
    path_node_ids: tuple[int, ...] = ()
    path_edges: frozenset[tuple[int, int]] = frozenset()
    last_object_clicked: dict | None = None
    pathfind_failed: bool = False

    @property
    def caption(self) -> str:
        count = len(self.selected_node_ids)
        if count == 0:
            return "Click a node to select it (up to 2)."
        elif count == 1:
            return (
                f"Node {self.selected_node_ids[0]} selected. "
                "Click another node to choose a destination."
            )
        elif self.path_node_ids:
            return (
                f"Shortest path from node {self.selected_node_ids[0]} "
                f"to node {self.selected_node_ids[1]} (length "
                f"{len(self.path_node_ids)} nodes)."
            )
        else:
            return (
                f"Endpoints {self.selected_node_ids[0]} and "
                f"{self.selected_node_ids[1]} selected. "
                "Click 'Find Shortest Path' to compute the route."
            )

    @property
    def highlighted_node_ids(self) -> frozenset[int]:
        return frozenset(self.selected_node_ids) | frozenset(self.path_node_ids)


class NavController:
    """
    Stateless service that applies Navigation-mode interaction logic.

    Inspects raw st_folium map_data and returns a new NavState. Does not
    mutate the graph.
    """

    def __init__(self, graph: CampusGraph, nav_state: NavState) -> None:
        self._graph = graph
        self._nav_state = nav_state

    def handle_click(self, map_data: dict) -> NavState:
        """Apply one click event; return unchanged state if nothing new."""
        obj_clicked = map_data.get("last_object_clicked")
        tooltip = map_data.get("last_object_clicked_tooltip")

        if obj_clicked == self._nav_state.last_object_clicked:
            return self._nav_state

        node = self._node_from_tooltip(tooltip) if tooltip else None
        if node is None:
            return self._consume(obj_clicked)
        return self._select_node(node, obj_clicked)

    def handle_deselect(self) -> NavState:
        """Clear all selection and any computed path."""
        if not self._nav_state.selected_node_ids and not self._nav_state.path_node_ids:
            return self._nav_state
        return NavState(last_object_clicked = self._nav_state.last_object_clicked)

    def handle_find_shortest_path(self) -> NavState:
        """Run Dijkstra between the two selected endpoints."""
        if len(self._nav_state.selected_node_ids) != 2:
            # TODO: add a warning to the user instead of silently failing.
            return self._nav_state
        start_id, end_id = self._nav_state.selected_node_ids
        path = dijkstra_shortest_path(self._graph, start_id, end_id)
        if path is None:
            # TODO: add a warning to the user instead of silently failing.
            return NavState(
                selected_node_ids = self._nav_state.selected_node_ids,
                last_object_clicked = self._nav_state.last_object_clicked,
                pathfind_failed = True,
            )
        edges = frozenset(
            (min(a, b), max(a, b)) for a, b in zip(path, path[1:])
        )
        return NavState(
            selected_node_ids = self._nav_state.selected_node_ids,
            path_node_ids = tuple(path),
            path_edges = edges,
            last_object_clicked = self._nav_state.last_object_clicked,
        )

    def _select_node(self, node: Node, obj_clicked: dict) -> NavState:
        selected = self._nav_state.selected_node_ids
        if len(selected) == 0:
            return NavState(
                selected_node_ids = (node.id,),
                last_object_clicked = obj_clicked,
            )
        elif len(selected) == 1:
            if node.id == selected[0]:
                # Already selected: ignore but consume the click event.
                # TODO: add a warning to the user instead of silently skipping the click.
                return self._consume(obj_clicked)
            return NavState(
                selected_node_ids = (selected[0], node.id),
                last_object_clicked = obj_clicked,
            )
        # 2 already selected: ignore further node clicks; require Deselect.
        # TODO: add a warning to the user instead of silently skipping the click.
        return self._consume(obj_clicked)

    def _consume(self, obj_clicked: dict | None) -> NavState:
        """Carry state forward but record the click as processed."""
        return NavState(
            selected_node_ids = self._nav_state.selected_node_ids,
            path_node_ids = self._nav_state.path_node_ids,
            path_edges = self._nav_state.path_edges,
            last_object_clicked = obj_clicked,
        )

    def _node_from_tooltip(self, tooltip: str) -> Node | None:
        try:
            return self._graph.get_node(int(tooltip))
        except (ValueError, TypeError):
            return None

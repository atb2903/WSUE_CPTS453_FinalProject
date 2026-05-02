from dataclasses import dataclass
from enum import Enum, auto

from map.graph import CampusGraph, Edge, Node


class State(Enum):
    IDLE = auto()
    NODE_SELECTED = auto()
    EDGE_SELECTED = auto()
    PENDING_NODE = auto()


@dataclass(frozen=True)
class EditState:
    state: State = State.IDLE
    active_node_id: int | None = None
    selected_edge: tuple[int, int] | None = None
    last_object_clicked: dict | None = None
    last_map_click: dict | None = None

    @property
    def caption(self) -> str:
        if self.state == State.NODE_SELECTED:
            return (
                    f"Node {self.active_node_id} selected. Click to move it or connect it to another node." if self.active_node_id is not None
                    else "WARNING: State is NODE_SELECTED but active_node_id is None"
                )
        elif self.state == State.EDGE_SELECTED:
            return (
                    f"Edge {self.selected_edge[0]}-{self.selected_edge[1]} selected." if self.active_node_id is not None
                    else "WARNING: State is EDGE_SELECTED but selected_edge is None"
                )
        elif self.state == State.PENDING_NODE:
            return (
                    f"Node {self.active_node_id} selected. Click to connect it to or create another node." if self.active_node_id is not None
                    else "WARNING: State is PENDING_NODE but active_node_id is None"
                )
        elif self.state == State.IDLE:
            return "Click a node or edge to select it, or click to create a new node."
        else:
            return f"WARNING: Unrecognized state {self.state}"


class EditController:
    """
    Stateless service that applies Edit-mode interaction logic.

    Inspects raw st_folium map_data, mutates the graph in-place for structural
    changes (add/move nodes and edges), and returns a new EditState.
    """

    def __init__(self, graph: CampusGraph, edit_state: EditState) -> None:
        self._graph = graph
        self._edit_state = edit_state

    def handle_click(self, map_data: dict) -> EditState:
        """Apply one interaction event; return unchanged state if nothing new."""
        obj_clicked = map_data.get("last_object_clicked")
        tooltip = map_data.get("last_object_clicked_tooltip")
        map_click = map_data.get("last_clicked")

        new_node_click = obj_clicked != self._edit_state.last_object_clicked
        new_map_click = map_click != self._edit_state.last_map_click

        # Node click takes priority when both change in the same rerun.
        # If a tooltip is present but refers to an unknown node, ignore the
        # entire event so the concurrent map-click is not misread as intentional.
        if new_node_click and tooltip:
            node = self._node_from_tooltip(tooltip)
            if node is not None:
                return self._handle_node_click(node, obj_clicked, map_click)
            edge = self._edge_from_tooltip(tooltip)
            if edge is not None:
                return self._handle_edge_click(edge, obj_clicked, map_click)
            # Unknown tooltip: consume both clicks to prevent a ghost map-click on the next rerun
            # TODO: add a warning to the user instead of silently failing
            return EditState(
                state = self._edit_state.state,
                active_node_id = self._edit_state.active_node_id,
                selected_edge = self._edit_state.selected_edge,
                last_object_clicked = obj_clicked,
                last_map_click = map_click,
            )

        if new_map_click and map_click:
            return self._handle_map_click(map_click)

        return self._edit_state

    def handle_delete_selected(self) -> EditState:
        """Delete currently selected node or edge."""
        if self._edit_state.state in {State.NODE_SELECTED, State.PENDING_NODE} and self._edit_state.active_node_id is not None:
            self._graph.remove_node(self._edit_state.active_node_id)
            return EditState(
                state=State.IDLE,
                last_object_clicked = self._edit_state.last_object_clicked,
                last_map_click = self._edit_state.last_map_click,
            )

        if self._edit_state.state == State.EDGE_SELECTED and self._edit_state.selected_edge is not None:
            self._graph.remove_edge(*self._edit_state.selected_edge)
            return EditState(
                state=State.IDLE,
                last_object_clicked = self._edit_state.last_object_clicked,
                last_map_click = self._edit_state.last_map_click,
            )
        
        # TODO: add a warning to the user instead of silently failing
        return self._edit_state

    def handle_deselect(self) -> EditState:
        """Clear node/edge selection without mutating the graph."""
        if self._edit_state.state not in {State.NODE_SELECTED, State.EDGE_SELECTED, State.PENDING_NODE}:
            # TODO: add a warning to the user instead of silently failing
            return self._edit_state
        return EditState(
            state=State.IDLE,
            last_object_clicked = self._edit_state.last_object_clicked,
            last_map_click = self._edit_state.last_map_click,
        )

    def _node_from_tooltip(self, tooltip: str) -> Node | None:
        try:
            return self._graph.get_node(int(tooltip))
        except (ValueError, TypeError):
            return None

    def _edge_from_tooltip(self, tooltip: str) -> tuple[int, int] | None:
        if not isinstance(tooltip, str) or not tooltip.startswith("edge:"):
            return None
        parts = tooltip.removeprefix("edge:").split("-", maxsplit = 1)
        if len(parts) != 2:
            return None
        try:
            first = int(parts[0])
            second = int(parts[1])
        except ValueError:
            return None
        return (min(first, second), max(first, second))

    def _handle_node_click(
        self, node: Node, obj_clicked: dict, map_click: dict | None
    ) -> EditState:
        # Consume any concurrent map-click by storing its value,
        # preventing the next rerun from misreading it as a new event.
        consumed_map_click = map_click
        if self._edit_state.state == State.PENDING_NODE or self._edit_state.state == State.NODE_SELECTED:
            return self._connect_node_to(node, obj_clicked, consumed_map_click, self._edit_state.state)
        # TODO: add a warning to the user instead of silently failing
        return EditState(
            state = State.NODE_SELECTED,
            active_node_id = node.id,
            selected_edge = None,
            last_object_clicked = obj_clicked,
            last_map_click = consumed_map_click,
        )

    def _handle_edge_click(
        self, edge: tuple[int, int], obj_clicked: dict, map_click: dict | None
    ) -> EditState:
        return EditState(
            state = State.EDGE_SELECTED,
            selected_edge = edge,
            last_object_clicked = obj_clicked,
            last_map_click = map_click,
        )

    def _connect_node_to(
        self, target: Node, obj_clicked: dict, map_click: dict | None, state: State
    ) -> EditState:
        if target.id == self._edit_state.active_node_id:
            # Clicking the selected node itself: stay selected, consume clicks
            return EditState(
                state = state,
                active_node_id = self._edit_state.active_node_id,
                selected_edge = None,
                last_object_clicked = obj_clicked,
                last_map_click = map_click,
            )
        self._graph.add_edge(Edge(from_id = self._edit_state.active_node_id, to_id = target.id))
        return EditState(
            state = State.IDLE,
            last_object_clicked = obj_clicked,
            last_map_click = map_click,
        )

    def _from_map_click(self, **fields) -> EditState:
        # streamlit-folium only updates last_object_clicked when a Folium object is
        # clicked, never on empty-space clicks. Centralising here ensures every map-click
        # handler carries the value forward automatically; forgetting to do so causes ghost
        # node-click events on the next Streamlit rerun.
        return EditState(
            last_object_clicked = self._edit_state.last_object_clicked,
            **fields,
        )

    def _handle_map_click(self, map_click: dict) -> EditState:
        state = self._edit_state.state
        # The graph rejects duplicate-coordinate moves/adds; if the click
        # lands on the exact pixel of an existing node, treat it as a no-op
        # and consume the click so it isn't re-processed on the next rerun.
        try:
            if state == State.NODE_SELECTED:
                self._graph.move_node(
                    self._edit_state.active_node_id,
                    y = map_click["lat"],
                    x = map_click["lng"],
                )
                return self._from_map_click(state=State.IDLE, last_map_click=map_click)
            if state == State.PENDING_NODE:
                return self._create_connected_node(map_click)
            # IDLE: create new node, enter pending
            return self._create_pending_node(map_click)
        except ValueError:
            return self._from_map_click(
                state = state,
                active_node_id = self._edit_state.active_node_id,
                selected_edge = self._edit_state.selected_edge,
                last_map_click = map_click,
            )

    def _create_pending_node(self, map_click: dict) -> EditState:
        new_id = self._graph.next_node_id()
        self._graph.add_node(Node(id = new_id, y = map_click["lat"], x = map_click["lng"]))
        return self._from_map_click(
            state = State.PENDING_NODE,
            active_node_id = new_id,
            last_map_click = map_click,
        )

    def _create_connected_node(self, map_click: dict) -> EditState:
        new_id = self._graph.next_node_id()
        self._graph.add_node(Node(id = new_id, y = map_click["lat"], x = map_click["lng"]))
        self._graph.add_edge(Edge(from_id = self._edit_state.active_node_id, to_id = new_id))
        return self._from_map_click(state=State.IDLE, last_map_click=map_click)

from dataclasses import dataclass
from enum import Enum, auto

from map.graph import CampusGraph, Edge, Node


class State(Enum):
    IDLE = auto()
    NODE_SELECTED = auto()
    PENDING_NODE = auto()


@dataclass(frozen=True)
class EditState:
    state: State = State.IDLE
    active_node_id: int | None = None
    last_object_clicked: dict | None = None
    last_map_click: dict | None = None

    @property
    def caption(self) -> str:
        if self.state == State.NODE_SELECTED:
            return f"Node {self.active_node_id} selected — click the map to move it."
        if self.state == State.PENDING_NODE:
            return (
                "Node placed — click an existing node to connect it, "
                "or click empty space to add a connected node."
            )
        return "Click a node to select it and move it, or click empty space to add a new node."


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
                # Only leaf nodes (degree ≤ 1) may be selected for moving.
                # When connecting a pending node, any target is valid regardless of degree.
                non_selectable = (
                    self._edit_state.state != State.PENDING_NODE
                    and self._graph.degree(node.id) > 1
                )
                if non_selectable:
                    return EditState(
                        state=self._edit_state.state,
                        active_node_id=self._edit_state.active_node_id,
                        last_object_clicked=obj_clicked,
                        last_map_click=map_click,
                    )
                return self._handle_node_click(node, obj_clicked, map_click)
            # Unknown tooltip: consume both clicks to prevent a ghost map-click on the next rerun
            return EditState(
                state=self._edit_state.state,
                active_node_id=self._edit_state.active_node_id,
                last_object_clicked=obj_clicked,
                last_map_click=map_click,
            )

        if new_map_click and map_click:
            return self._handle_map_click(map_click)

        return self._edit_state

    def _node_from_tooltip(self, tooltip: str) -> Node | None:
        try:
            return self._graph.get_node(int(tooltip))
        except (ValueError, TypeError):
            return None

    def _handle_node_click(
        self, node: Node, obj_clicked: dict, map_click: dict | None
    ) -> EditState:
        # Consume any concurrent map-click by storing its value,
        # preventing the next rerun from misreading it as a new event.
        consumed_map_click = map_click
        if self._edit_state.state == State.PENDING_NODE:
            return self._connect_pending_to(node, obj_clicked, consumed_map_click)
        return EditState(
            state=State.NODE_SELECTED,
            active_node_id=node.id,
            last_object_clicked=obj_clicked,
            last_map_click=consumed_map_click,
        )

    def _connect_pending_to(
        self, node: Node, obj_clicked: dict, map_click: dict | None
    ) -> EditState:
        if node.id == self._edit_state.active_node_id:
            # Clicking the pending node itself: stay pending, consume clicks
            return EditState(
                state=State.PENDING_NODE,
                active_node_id=self._edit_state.active_node_id,
                last_object_clicked=obj_clicked,
                last_map_click=map_click,
            )
        self._graph.add_edge(Edge(from_id=self._edit_state.active_node_id, to_id=node.id))
        return EditState(
            state=State.IDLE,
            last_object_clicked=obj_clicked,
            last_map_click=map_click,
        )

    def _from_map_click(self, **fields) -> EditState:
        # streamlit-folium only updates last_object_clicked when a Folium object is
        # clicked, never on empty-space clicks. Centralising here ensures every map-click
        # handler carries the value forward automatically; forgetting to do so causes ghost
        # node-click events on the next Streamlit rerun.
        return EditState(last_object_clicked=self._edit_state.last_object_clicked, **fields)

    def _handle_map_click(self, map_click: dict) -> EditState:
        state = self._edit_state.state
        if state == State.NODE_SELECTED:
            self._graph.move_node(
                self._edit_state.active_node_id,
                y=map_click["lat"],
                x=map_click["lng"],
            )
            return self._from_map_click(state=State.IDLE, last_map_click=map_click)
        if state == State.PENDING_NODE:
            return self._create_connected_node(map_click)
        # IDLE: create new node, enter pending
        return self._create_pending_node(map_click)

    def _create_pending_node(self, map_click: dict) -> EditState:
        new_id = self._graph.next_node_id()
        self._graph.add_node(Node(id=new_id, y=map_click["lat"], x=map_click["lng"]))
        return self._from_map_click(
            state=State.PENDING_NODE,
            active_node_id=new_id,
            last_map_click=map_click,
        )

    def _create_connected_node(self, map_click: dict) -> EditState:
        new_id = self._graph.next_node_id()
        self._graph.add_node(Node(id=new_id, y=map_click["lat"], x=map_click["lng"]))
        self._graph.add_edge(Edge(from_id=self._edit_state.active_node_id, to_id=new_id))
        return self._from_map_click(state=State.IDLE, last_map_click=map_click)

from pathlib import Path

import folium
import streamlit as st
from streamlit_folium import st_folium

from map.edit_controller import EditController, EditState, State
from map.graph import CampusGraph
from map.graph_renderer import GraphOverlayRenderer
from map.nav_controller import NavController, NavState
from map.renderer import CampusMapRenderer

_IMAGE_PATH = Path("assets/map.png")
_GRAPH_PATH = Path("assets/graph.json")

st.set_page_config(page_title="WSU GPS", layout="wide")
st.title("WSU GPS")

if not _IMAGE_PATH.exists():
    st.error(f"Map image not found at: {_IMAGE_PATH}")
    st.stop()


def _load_graph_or_fallback(path: Path) -> CampusGraph:
    try:
        return CampusGraph.load_from_file(path)
    except Exception as error:
        st.error(f"Failed to load graph from {path}: {error}. Starting with an empty graph.")
        return CampusGraph()


# --- Session state ---
if "graph" not in st.session_state:
    st.session_state.graph = _load_graph_or_fallback(_GRAPH_PATH)
if "edit_state" not in st.session_state:
    st.session_state.edit_state = EditState()
if "nav_state" not in st.session_state:
    st.session_state.nav_state = NavState()
if "prev_mode" not in st.session_state:
    st.session_state.prev_mode = None

mode = st.segmented_control("Mode", ["Navigation", "Edit"], default="Navigation")

graph: CampusGraph = st.session_state.graph
campus_map = CampusMapRenderer(_IMAGE_PATH).build()

# Reset per-mode state on entry so each mode starts clean without rebuilding state on every rerun.
if mode == "Navigation" and st.session_state.prev_mode != "Navigation":
    st.session_state.edit_state = EditState()
if mode == "Edit" and st.session_state.prev_mode != "Edit":
    st.session_state.nav_state = NavState()
st.session_state.prev_mode = mode

if mode == "Navigation":
    nav_state: NavState = st.session_state.nav_state
    st.caption(nav_state.caption)

    has_selection = len(nav_state.selected_node_ids) > 0 or bool(nav_state.path_node_ids)
    can_pathfind = (
        len(nav_state.selected_node_ids) == 2 and not nav_state.path_node_ids
    )
    deselect_clicked = st.button("Deselect", disabled = not has_selection)
    pathfind_clicked = st.button("Find Shortest Path", disabled = not can_pathfind)

    if nav_state.pathfind_failed:
        st.warning("No path exists between the selected nodes.")

    fg = folium.FeatureGroup()
    GraphOverlayRenderer(graph).render_onto(
        fg,
        highlighted_node_ids = nav_state.highlighted_node_ids,
        highlighted_edges = nav_state.path_edges,
    )
    map_data = st_folium(
        campus_map,
        width = None,
        height = 760,
        returned_objects = ["last_object_clicked", "last_object_clicked_tooltip"],
        feature_group_to_add = fg,
        key = "campus_map_nav",
    )

    new_nav_state = NavController(graph, nav_state).handle_click(map_data)

    if deselect_clicked:
        new_nav_state = NavController(graph, new_nav_state).handle_deselect()

    if pathfind_clicked:
        new_nav_state = NavController(graph, new_nav_state).handle_find_shortest_path()

    if new_nav_state != nav_state:
        st.session_state.nav_state = new_nav_state
        st.rerun()

else:  # Edit
    edit_state: EditState = st.session_state.edit_state
    st.caption(edit_state.caption)
    has_selection = edit_state.state in {State.NODE_SELECTED, State.EDGE_SELECTED, State.PENDING_NODE}
    deselect_clicked = st.button("Deselect", disabled = not has_selection)
    delete_clicked = st.button("Delete Selected", disabled = not has_selection)
    if st.button("Save Graph"):
        try:
            graph.save_to_file(_GRAPH_PATH)
            st.success(f"Saved graph to {_GRAPH_PATH}.")
        except Exception as error:
            st.error(f"Failed to save graph to {_GRAPH_PATH}: {error}")

    highlighted_node_ids = (
        (edit_state.active_node_id,) if edit_state.active_node_id is not None else ()
    )
    highlighted_edges = (
        (edit_state.selected_edge,) if edit_state.selected_edge is not None else ()
    )

    fg = folium.FeatureGroup()
    GraphOverlayRenderer(graph).render_onto(
        fg,
        highlighted_node_ids = highlighted_node_ids,
        highlighted_edges = highlighted_edges,
    )
    map_data = st_folium(
        campus_map,
        width=None,
        height=760,
        returned_objects=["last_object_clicked", "last_object_clicked_tooltip", "last_clicked"],
        feature_group_to_add=fg,
        key="campus_map_edit",
    )

    # TODO: add warnings to user on invalid clicks

    new_edit_state = EditController(graph, edit_state).handle_click(map_data)

    if deselect_clicked:
        new_edit_state = EditController(graph, new_edit_state).handle_deselect()

    if delete_clicked:
        new_edit_state = EditController(graph, new_edit_state).handle_delete_selected()

    # TODO: find a way to reduce/eliminate sequential reruns. They are very slow and annoying to the user (it's me I'm the user and I'm annoyed by it)
    if new_edit_state != edit_state:
        st.session_state.edit_state = new_edit_state
        st.rerun()

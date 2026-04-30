from pathlib import Path

import folium
import streamlit as st
from PIL import Image
from streamlit_folium import st_folium

from map.edit_controller import EditController, EditState, State
from map.graph import CampusGraph
from map.graph_renderer import GraphOverlayRenderer
from map.renderer import CampusMapRenderer

_IMAGE_PATH = Path("assets/map.png")
_GRAPH_PATH = Path("assets/graph.json")
Image.MAX_IMAGE_PIXELS = 200_000_000

st.set_page_config(page_title="WSU Map Viewer", layout="wide")
st.title("WSU Map Viewer")

if not _IMAGE_PATH.exists():
    st.error(f"Map image not found at: {_IMAGE_PATH}")
    st.stop()


@st.cache_data
def _image_size(path: Path) -> tuple[int, int]:
    with Image.open(path) as img:
        return img.size


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

mode = st.segmented_control("Mode", ["Navigation", "Edit"], default="Navigation")

graph: CampusGraph = st.session_state.graph
campus_map = CampusMapRenderer(_IMAGE_PATH).build()

if mode == "Navigation":
    # Reset edit state so re-entering Edit mode starts clean
    st.session_state.edit_state = EditState()
    st.caption("Pan by dragging and zoom with mouse wheel or +/- controls.")
    fg = folium.FeatureGroup()
    GraphOverlayRenderer(graph).render_onto(fg)
    st_folium(campus_map, width=None, height=760, returned_objects=[], feature_group_to_add=fg)

else:  # Edit
    edit_state: EditState = st.session_state.edit_state
    st.caption(edit_state.caption)
    has_selection = edit_state.state in {State.NODE_SELECTED, State.EDGE_SELECTED}
    deselect_clicked = st.button("Deselect", disabled=not has_selection)
    delete_clicked = st.button("Delete Selected", disabled=not has_selection)
    if st.button("Save Graph"):
        try:
            graph.save_to_file(_GRAPH_PATH)
            st.success(f"Saved graph to {_GRAPH_PATH}.")
        except Exception as error:
            st.error(f"Failed to save graph to {_GRAPH_PATH}: {error}")

    fg = folium.FeatureGroup()
    GraphOverlayRenderer(graph).render_onto(
        fg,
        highlighted_node_id=edit_state.active_node_id,
        highlighted_edge=edit_state.selected_edge,
    )
    map_data = st_folium(
        campus_map,
        width=None,
        height=760,
        returned_objects=["last_object_clicked", "last_object_clicked_tooltip", "last_clicked"],
        feature_group_to_add=fg,
        key="campus_map_edit",
    )

    new_edit_state = EditController(graph, edit_state).handle_click(map_data)

    if deselect_clicked:
        new_edit_state = EditController(graph, new_edit_state).handle_deselect()

    if delete_clicked:
        new_edit_state = EditController(graph, new_edit_state).handle_delete_selected()

    if new_edit_state != edit_state:
        st.session_state.edit_state = new_edit_state
        st.rerun()

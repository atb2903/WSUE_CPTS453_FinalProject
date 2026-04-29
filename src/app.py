from pathlib import Path

import folium
import streamlit as st
from PIL import Image
from streamlit_folium import st_folium

from map.edit_controller import EditController, EditState
from map.graph import CampusGraph, Edge, Node
from map.graph_renderer import GraphOverlayRenderer
from map.renderer import CampusMapRenderer

_IMAGE_PATH = Path("assets/map.png")
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


image_width, image_height = _image_size(_IMAGE_PATH)

# --- Session state ---
if "graph" not in st.session_state:
    st.session_state.graph = CampusGraph(
        nodes=[
            Node(id=0, y=image_height * 0.9, x=image_width * 0.1),
            Node(id=1, y=image_height * 0.1, x=image_width * 0.9),
        ],
        edges=[Edge(from_id=0, to_id=1)],
    )
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

    fg = folium.FeatureGroup()
    GraphOverlayRenderer(graph).render_onto(fg, highlighted_node_id=edit_state.active_node_id)
    map_data = st_folium(
        campus_map,
        width=None,
        height=760,
        returned_objects=["last_object_clicked", "last_object_clicked_tooltip", "last_clicked"],
        feature_group_to_add=fg,
        key="campus_map_edit",
    )

    new_edit_state = EditController(graph, edit_state).handle_click(map_data)
    if new_edit_state != edit_state:
        st.session_state.edit_state = new_edit_state
        st.rerun()

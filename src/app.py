from pathlib import Path

import folium
import streamlit as st
from PIL import Image
from streamlit_folium import st_folium

from map.edit_controller import EditController, EditState
from map.graph import CampusGraph
from map.graph_renderer import GraphOverlayRenderer
from map.renderer import CampusMapRenderer

_IMAGE_PATH = Path("assets/map.png")
_GRAPH_PATH = Path("assets/graph.json")
Image.MAX_IMAGE_PIXELS = 200_000_000

try:
    from streamlit_keypress import key_press_events
except ModuleNotFoundError:
    key_press_events = None

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
if "delete_event_counter" not in st.session_state:
    st.session_state.delete_event_counter = 0
if "last_pressed_key" not in st.session_state:
    st.session_state.last_pressed_key = None

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
    if key_press_events is None:
        st.warning(
            "Keyboard Delete requires streamlit-keypress. "
            "Install it with: pipx inject streamlit streamlit-keypress"
        )
    if st.button("Save Graph"):
        try:
            graph.save_to_file(_GRAPH_PATH)
            st.success(f"Saved graph to {_GRAPH_PATH}.")
        except Exception as error:
            st.error(f"Failed to save graph to {_GRAPH_PATH}: {error}")

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

    pressed_key = key_press_events() if key_press_events is not None else None
    delete_event = None
    if pressed_key == "Delete" and st.session_state.last_pressed_key != "Delete":
        st.session_state.delete_event_counter += 1
        delete_event = st.session_state.delete_event_counter
    st.session_state.last_pressed_key = pressed_key

    new_edit_state = EditController(graph, new_edit_state).handle_delete_key(delete_event)

    if new_edit_state != edit_state:
        st.session_state.edit_state = new_edit_state
        st.rerun()

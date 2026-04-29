from pathlib import Path

import folium
import streamlit as st
from PIL import Image
from streamlit_folium import st_folium

from map.graph import CampusGraph, Edge, Node
from map.graph_renderer import GraphOverlayRenderer
from map.renderer import CampusMapRenderer

_IMAGE_PATH = Path("assets/map.png")

st.set_page_config(page_title="WSU Map Viewer", layout="wide")
st.title("WSU Map Viewer")

if not _IMAGE_PATH.exists():
    st.error(f"Map image not found at: {_IMAGE_PATH}")
    st.stop()


@st.cache_data
def _image_size(path: Path) -> tuple[int, int]:
    Image.MAX_IMAGE_PIXELS = 200_000_000
    with Image.open(path) as img:
        return img.size


image_width, image_height = _image_size(_IMAGE_PATH)

# --- Session state ---
if "graph" not in st.session_state:
    st.session_state.graph = CampusGraph(
        nodes=[
            Node(id=0, label="Node A", y=image_height * 0.9, x=image_width * 0.1),
            Node(id=1, label="Node B", y=image_height * 0.1, x=image_width * 0.9),
        ],
        edges=[Edge(from_id=0, to_id=1)],
    )
if "selected_node_id" not in st.session_state:
    st.session_state.selected_node_id = None
if "last_object_clicked" not in st.session_state:
    st.session_state.last_object_clicked = None
if "last_map_click" not in st.session_state:
    st.session_state.last_map_click = None

mode = st.segmented_control("Mode", ["Navigation", "Edit"], default="Navigation")

graph: CampusGraph = st.session_state.graph
campus_map = CampusMapRenderer(_IMAGE_PATH).build()

if mode == "Navigation":
    st.session_state.selected_node_id = None
    st.caption("Pan by dragging and zoom with mouse wheel or +/- controls.")
    # Use feature_group_to_add rather than baking nodes into campus_map so the
    # Leaflet component hash is always the base map hash.  If nodes were moved
    # in Edit mode, baking them in would produce a different hash → initComponent
    # fires → image reloads visually on every mode switch.
    fg = folium.FeatureGroup()
    GraphOverlayRenderer(graph).render_onto(fg)
    st_folium(campus_map, width=None, height=760, returned_objects=[], feature_group_to_add=fg)

else:  # Edit
    selected_id: int | None = st.session_state.selected_node_id
    selected_node = graph.get_node(selected_id) if selected_id is not None else None
    if selected_node is not None:
        st.caption(f"'{selected_node.label}' selected — click the map to move it.")
    else:
        st.caption("Click a node to select it, then click the map to move it.")

    # Render the graph into a FeatureGroup so streamlit-folium can update it
    # dynamically without recreating the base map component.  Keeping graph
    # layers out of campus_map also keeps the component hash stable across
    # reruns, ensuring __GLOBAL_DATA__.returned_objects is always initialised
    # with the full click-tracking list rather than being stuck at the
    # Navigation-mode value of [].
    fg = folium.FeatureGroup()
    GraphOverlayRenderer(graph).render_onto(fg, selected_node_id=selected_id)
    map_data = st_folium(
        campus_map,
        width=None,
        height=760,
        returned_objects=["last_object_clicked", "last_object_clicked_tooltip", "last_clicked"],
        feature_group_to_add=fg,
        key="campus_map_edit",
    )

    obj_clicked = map_data.get("last_object_clicked")
    tooltip = map_data.get("last_object_clicked_tooltip")
    map_click = map_data.get("last_clicked")

    new_node_click = obj_clicked != st.session_state.last_object_clicked
    new_map_click = map_click != st.session_state.last_map_click

    # Node click takes priority over map click if both changed in the same rerun
    if new_node_click and tooltip:
        matching = next((n for n in graph.nodes if n.label == tooltip), None)
        if matching is not None:
            st.session_state.last_object_clicked = obj_clicked
            # Also consume the concurrent map-click that fires alongside a
            # layer click, otherwise the next re-run sees new_map_click=True
            # with a selected node and immediately moves + deselects it.
            st.session_state.last_map_click = map_click
            st.session_state.selected_node_id = matching.id
            st.rerun()
    elif new_map_click and selected_id is not None and map_click:
        graph.move_node(selected_id, y=map_click["lat"], x=map_click["lng"])
        st.session_state.last_map_click = map_click
        st.session_state.selected_node_id = None
        st.rerun()

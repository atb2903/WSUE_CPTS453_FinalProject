from pathlib import Path

import streamlit as st
from PIL import Image
from streamlit_folium import st_folium

from map.graph import CampusGraph, Edge, Node
from map.graph_renderer import GraphOverlayRenderer
from map.renderer import CampusMapRenderer

# Path to the campus map image asset, relative to the project root
_IMAGE_PATH = Path("assets/map.png")

# Wide layout maximises the available map viewport area
st.set_page_config(page_title="WSU Map Viewer", layout="wide")
st.title("WSU Map Viewer")
st.caption("Pan by dragging and zoom with mouse wheel or +/- controls.")

# Stop early with a clear error rather than letting folium fail silently
if not _IMAGE_PATH.exists():
    st.error(f"Map image not found at: {_IMAGE_PATH}")
    st.stop()

# PIL returns (width, height); CRS.Simple uses [y, x] = [lat, lng]
Image.MAX_IMAGE_PIXELS = 200_000_000
with Image.open(_IMAGE_PATH) as img:
    image_width, image_height = img.size

campus_map = CampusMapRenderer(_IMAGE_PATH).build()

# Dummy graph: two nodes at opposite corners, one connecting edge
dummy_graph = CampusGraph(
    nodes=[
        Node(id=0, label="Node A", y=image_height * 0.9, x=image_width * 0.1),
        Node(id=1, label="Node B", y=image_height * 0.1, x=image_width * 0.9),
    ],
    edges=[Edge(from_id=0, to_id=1)],
)
GraphOverlayRenderer(dummy_graph).render_onto(campus_map)

# returned_objects=[] prevents Streamlit from re-running the script on every
# pan or zoom interaction, which would otherwise reset the map viewport state
st_folium(campus_map, width=None, height=760, returned_objects=[])

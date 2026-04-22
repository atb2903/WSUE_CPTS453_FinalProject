# Partially or wholly AI-generated with Claude (claude-sonnet-4-6) via Claude Code on 2026-04-22 — https://claude.ai/code
from pathlib import Path

import streamlit as st
from streamlit_folium import st_folium

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

campus_map = CampusMapRenderer(_IMAGE_PATH).build()

# returned_objects=[] prevents Streamlit from re-running the script on every
# pan or zoom interaction, which would otherwise reset the map viewport state
st_folium(campus_map, width=None, height=760, returned_objects=[])

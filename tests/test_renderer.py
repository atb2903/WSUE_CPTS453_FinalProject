# Partially or wholly AI-generated with Claude (claude-sonnet-4-6) via Claude Code on 2026-04-22 — https://claude.ai/code
import pytest
from pathlib import Path
from PIL import Image
import folium
from folium.raster_layers import ImageOverlay

from map.renderer import CampusMapRenderer


@pytest.fixture
def image_path(tmp_path: Path) -> Path:
    """Create a minimal 800×600 PNG in a temporary directory for testing."""
    path = tmp_path / "map.png"
    Image.new("RGB", (800, 600)).save(path)
    return path


def test_build_returns_folium_map(image_path):
    result = CampusMapRenderer(image_path).build()
    assert isinstance(result, folium.Map)


def test_build_center_is_image_midpoint(image_path):
    # CRS.Simple uses [lat=y, lng=x]; for an 800×600 image the center is
    # [height/2, width/2] = [300.0, 400.0]
    result = CampusMapRenderer(image_path).build()
    assert result.location == [300.0, 400.0]


def test_build_adds_image_overlay(image_path):
    result = CampusMapRenderer(image_path).build()
    # folium stores all map children (overlays, layers, etc.) in _children
    overlays = [c for c in result._children.values() if isinstance(c, ImageOverlay)]
    assert len(overlays) == 1


def test_build_overlay_bounds_match_image_dimensions(image_path):
    result = CampusMapRenderer(image_path).build()
    overlay = next(c for c in result._children.values() if isinstance(c, ImageOverlay))
    # Bounds follow Leaflet's [[south, west], [north, east]] = [[0, 0], [height, width]]
    assert overlay.bounds == [[0, 0], [600, 800]]


def test_build_overlay_image_is_encoded(image_path):
    # folium inlines local file paths as base64 data URIs to keep the
    # rendered HTML fully self-contained
    result = CampusMapRenderer(image_path).build()
    overlay = next(c for c in result._children.values() if isinstance(c, ImageOverlay))
    assert overlay.url.startswith("data:image/png")

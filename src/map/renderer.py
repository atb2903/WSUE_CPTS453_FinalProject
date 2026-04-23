from pathlib import Path

import folium
from folium.raster_layers import ImageOverlay
from PIL import Image

# The campus map exceeds PIL's default 89 MP decompression bomb limit.
# It is a known local asset, so raise the limit to accommodate it.
Image.MAX_IMAGE_PIXELS = 200_000_000


class CampusMapRenderer:
    """
    Builds a Leaflet folium.Map using CRS.Simple (pixel coordinate space)
    with the campus map image as a full-bounds ImageOverlay.

    Follows the Builder pattern: construct with an image path, then call
    build() to get a fully configured, ready-to-render folium.Map.
    """

    def __init__(self, image_path: Path) -> None:
        self._image_path = image_path

    def build(self) -> folium.Map:
        """Orchestrate the map construction steps and return the result."""
        image_width, image_height = self._read_image_dimensions()
        bounds = self._compute_bounds(image_width, image_height)
        campus_map = self._create_base_map(image_width, image_height)
        self._add_image_overlay(campus_map, bounds)
        return campus_map

    def _read_image_dimensions(self) -> tuple[int, int]:
        """Open the image file and return its (width, height) in pixels."""
        with Image.open(self._image_path) as img:
            return img.size  # PIL returns (width, height)

    def _compute_bounds(
        self, image_width: int, image_height: int
    ) -> list[list[int]]:
        """
        Compute the Leaflet bounds for the image in CRS.Simple pixel space.

        In CRS.Simple, Leaflet maps [lat, lng] directly to [y, x] pixel
        coordinates with the origin at the bottom-left. The image therefore
        spans from [0, 0] (bottom-left) to [height, width] (top-right),
        matching Leaflet's [south, west] → [north, east] convention.
        """
        return [[0, 0], [image_height, image_width]]

    def _create_base_map(
        self, image_width: int, image_height: int
    ) -> folium.Map:
        """
        Create a folium.Map configured for pixel-coordinate rendering.

        Notable configuration decisions:
        - crs="Simple": disables geo projection; at zoom 0, one map unit
          equals one pixel (per the Leaflet CRS.Simple spec).
        - tiles=None: no background tile layer; the image overlay is the
          only visual content.
        - zoom_start=-5: fallback zoom before fit_bounds runs; negative
          values are required for large images because zoom 0 is native
          pixel resolution (e.g. 13200×10200 px would overflow any viewport).
        - minZoom/maxZoom are passed as camelCase kwargs because folium's
          min_zoom/max_zoom parameters target tile layers, not the Leaflet
          Map object itself, and are silently ignored for CRS.Simple maps.
        - maxZoom=0: allows zooming in to native pixel resolution for
          building-level detail.
        """
        map_center = [image_height / 2, image_width / 2]
        return folium.Map(
            location=map_center,
            tiles=None,
            zoom_start=-5,
            zoom_control=True,
            crs="Simple",
            prefer_canvas=True,
            minZoom=-5,
            maxZoom=0,
        )

    def _add_image_overlay(
        self, campus_map: folium.Map, bounds: list[list[int]]
    ) -> None:
        """
        Attach the campus image as an overlay and fit the viewport to it.

        folium automatically encodes local file paths as base64 data URIs,
        making the rendered HTML fully self-contained. fit_bounds ensures
        the full image is visible on load regardless of browser container
        size, overriding zoom_start once the page renders.
        """
        ImageOverlay(
            image=str(self._image_path),
            bounds=bounds,
            opacity=1.0,
            interactive=False,
        ).add_to(campus_map)

        campus_map.fit_bounds(bounds)

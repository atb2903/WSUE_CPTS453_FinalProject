# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Goal

This is the **WSU-GPS** option from the CPTS 453 (Graph Theory) Spring 2026 final project. The app overlays a graph structure on a map of WSU Pullman campus where vertices are campus locations and edges represent direct walking routes. Graph traversal algorithms suggest optimal routes between locations.

Deliverables due **Monday, May 4th at 5:00 PM**:
- Working Streamlit application (demoed live via Zoom during finals week)
- 3–5 page written narrative describing features and implementation

## Setup & Run

Install dependencies via pipx (Linux):

```bash
sudo apt install -y pipx && pipx ensurepath
pipx install streamlit
pipx inject streamlit folium streamlit-folium Pillow pytest pytest-cov --include-apps
```

Run the app:

```bash
streamlit run src/app.py
```

Run tests:

```bash
pytest
```

## Development Rules

- **Consult docs**: Always look up the official documentation for any language or library before implementing or debugging behaviour that depends on its internals.
- **SOLID principles**: Every design and refactor must respect Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, and Dependency Inversion.
- **Design & architecture patterns**: Apply appropriate design patterns (e.g. Builder, Strategy, Repository) and architecture patterns (e.g. layered architecture, separation of concerns) wherever they improve clarity or extensibility.
- **100% test coverage, all tests passing**: After every change, run `pytest` and confirm all tests pass with 100% coverage on `src/map`. Do not leave the codebase in a state where tests fail or coverage drops.
- **Readable code**: Use descriptive, self-explanatory names for variables, functions, classes, and modules. Add comments wherever the code is not self-documenting.
- **Gitignore check**: After creating any file or directory, decide whether it should be tracked in git. If it is runtime, temporary, generated, or local-only, add it to `.gitignore` immediately.

## Architecture

`app.py` is a thin Streamlit entry point. Map construction lives in `map/renderer.py`.

```
src/app.py            # Page config, existence check, renders the map
src/map/renderer.py   # CampusMapRenderer — owns all folium map construction
assets/map.png        # Campus map image
```

### Key design decisions

- **Coordinate system**: Leaflet `CRS.Simple` — no geo projection. Pixel dimensions are read via Pillow so bounds match the image exactly. Origin is bottom-left; bounds span `[[0, 0], [height, width]]`.
- `fit_bounds` ensures the full image is framed on startup regardless of `zoom_start`.
- `returned_objects=[]` on `st_folium` prevents Streamlit re-runs on every pan/zoom, which would otherwise reset interaction state.

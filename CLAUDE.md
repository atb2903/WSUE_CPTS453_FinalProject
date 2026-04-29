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
- **100% test coverage, all tests passing**: After every change, run tests and confirm all tests pass with 100% line coverage and 100% branch coverage on source files. Do not leave the codebase in a state where tests fail or coverage drops. Tests must also test boundary conditions (at, within, and outside boundaries) and integration conditions that only occur when systems are hooked together. If a bug is found by the user ask: "what changes to my testing procedure would have revealed this bug?" — then update all tests to check for bugs of a similar nature, and implement future tests to do so as well.
- **Test organisation**: Group tests into subfolders and files that mirror the module being tested. Each file covers one coherent concern (e.g. one state, one class, one behaviour category). Shared fixtures go in `conftest.py` at the appropriate level. Never put all tests for a module in a single flat file.
- **Write code with testability in mind**: Every class and function must be testable in isolation. Invariants that must hold across multiple methods should be enforced in a single place (e.g. a helper method) rather than repeated, so tests can verify the invariant once and the code cannot silently violate it. Avoid implicit shared state and side-effectful constructors. When a bug is fixed, ask: "what structural change would make this class of bug impossible?" — then make that change.
- **Readable code**: Use descriptive, self-explanatory names for variables, functions, classes, and modules. Add comments wherever the code is not self-documenting.
- **Gitignore check**: After creating any file or directory, decide whether it should be tracked in git. If it is runtime, temporary, generated, or local-only, add it to `.gitignore` immediately.
- **Maintain README**: Keep `README.md` at the project root up to date with current setup, run, and test instructions.
- **File organisation**: Group source code into subfolders and files that mirror the behavior of the source code. Each file covers one coherent concern in alignment with the Single-Responsibility Principle. Files should be well organised, named sensibly, and be grouped together based on their purpose.

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

# WSU-GPS

Interactive campus map for WSU Pullman that overlays a graph of campus locations and walking routes. Graph traversal algorithms suggest optimal routes between locations. Built with Streamlit + Folium for CPTS 453 (Graph Theory) Spring 2026.

## Setup (Linux Mint)

Install `pipx`:

```bash
sudo apt update
sudo apt install -y pipx
pipx ensurepath
```

Restart your shell (or run `source ~/.bashrc`), then install and inject app dependencies:

```bash
pipx install streamlit
pipx inject streamlit folium streamlit-folium Pillow pytest pytest-cov streamlit-keypress --include-apps
```

## Run

```bash
streamlit run src/app.py
```

Then open the local URL shown in the terminal.

## Tests

```bash
pytest --cov=src/map --cov-branch
```
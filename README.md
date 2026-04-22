# WSU Pullman Map Viewer

Minimal Python app that displays `assets/map.png` on startup with pan and zoom interactions.

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
pipx inject streamlit folium streamlit-folium Pillow pytest pytest-cov --include-apps
```

## Run

```bash
streamlit run src/app.py
```

Then open the local URL shown in the terminal.

## Tests

```bash
pytest
```
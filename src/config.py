"""Central configuration: paths, constants, and conventions.

Keep magic strings and tunable constants here so they're trivial to find and change.
"""
from pathlib import Path

# Project root: this file is at festiv-ai/src/config.py, so root is two levels up
ROOT = Path(__file__).resolve().parent.parent

# Directories
ASSETS = ROOT / "assets"
TEMPLATES = ASSETS / "templates"
ARTIST_IMAGES = ASSETS / "artists"
DATA = ROOT / "data"
OUTPUT = ROOT / "output"
POSTERS = OUTPUT / "posters"

# Data files
FESTIVALS_CSV = DATA / "festivals.csv"
ARTISTS_CSV = DATA / "artists.csv"
USERS_CSV = DATA / "users.csv"

# Output files
MANIFEST_CSV = OUTPUT / "manifest.csv"
COPY_CACHE = OUTPUT / "copy_cache.json"

# Template conventions ---------------------------------------------------------

# Marker color for the artist image zone in the SVG template.
# Dark gray — used as placeholder rectangle for artist image placement.
IMAGE_MARKER_COLOR = "#2d2d2d"

# Placeholder tokens for text zones, mapped to internal zone names.
# The strings are what you type in Illustrator. Mustache-style braces make them
# visually distinct in the design and impossible to confuse with real content.
TEXT_ZONES = {
    "{{ARTIST_NAME}}": "artist_name",
    "{{DATE}}": "date",
    "{{COPY}}": "copy_block",
}

# LLM config -------------------------------------------------------------------

OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "mistral:latest"  # decide after first iteration round
COPY_MAX_WORDS = 12
COPY_VARIANTS_PER_USER = 3

# Ensure output directories exist
POSTERS.mkdir(parents=True, exist_ok=True)
OUTPUT.mkdir(parents=True, exist_ok=True)

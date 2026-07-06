# Sphinx configuration for femic-tsa23-instance docs
import os

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_rtd_theme",
]

master_doc = "index"
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Project metadata
project = "TSA23 FEMIC Instance"
copyright = "2026, UBC-FRESH"
author = "UBC-FRESH"

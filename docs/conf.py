"""Sphinx configuration for the TSA23 FEMIC instance."""

import sys
from pathlib import Path

project = "TSA23 FEMIC Instance"
author = "UBC FRESH Lab"
copyright = "2026, UBC FRESH Lab"

# The instance's code lives in scripts/, as the lab template assumes.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

extensions: list[str] = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

autodoc_member_order = "bysource"
napoleon_numpy_docstring = True
napoleon_google_docstring = False
napoleon_use_param = True
napoleon_use_rtype = False

# The API pages import the analysis scripts. Mock the stack that needs GDAL or the
# FBP library so a docs build does not depend on a geospatial install. This is a
# deliberate divergence from the lab template, recorded in planning/sphinx_docs_plan.md.
autodoc_mock_imports = [
    "geopandas",
    "pyogrio",
    "fiona",
    "shapely",
    "pyproj",
    "cffdrs",
    "ws4",
]

html_theme = "sphinx_rtd_theme"
html_title = project
html_extra_path = ["llms.txt"]

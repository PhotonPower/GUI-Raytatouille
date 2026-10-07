"""Raytatouille Explorer: Streamlit interface for the Raytatouille optical design library."""

import matplotlib

# Headless backend: figures are rendered by Streamlit, never in a window. Must run before the
# first import of matplotlib.pyplot anywhere in the package.
matplotlib.use("Agg")

__version__ = "0.1.0"

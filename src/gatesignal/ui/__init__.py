"""Gate Signal user interface: the Signal Hub entry point.

The only package under ``gatesignal`` that imports Streamlit or Plotly. ``render()`` draws the whole app on the
current page and never calls ``st.set_page_config``; the standalone ``app.py`` or Signal Hub owns the page config.
"""

from gatesignal import __version__
from gatesignal.ui import signal_theme
from gatesignal.ui.app import render

APP_INFO = {"product": "Gate Signal", "version": __version__, "repo": "launch-decision-gate", "slug": "gate"}

__all__ = ["APP_INFO", "render", "signal_theme"]

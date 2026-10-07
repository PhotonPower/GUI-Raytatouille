"""Start from a checkout without installing: ``streamlit run streamlit_app.py``.

Needs the ``raytatouille`` package and the dependencies from ``requirements.txt``.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from rtt_explorer.app import main  # noqa: E402

main()

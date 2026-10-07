"""Command line entry point: ``rtt-explorer [streamlit options]``."""

from __future__ import annotations

import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    """Start the explorer with Streamlit; extra arguments go to ``streamlit run``."""
    from streamlit.web import cli as stcli

    script = Path(__file__).with_name("streamlit_app.py")
    sys.argv = ["streamlit", "run", str(script), *(sys.argv[1:] if argv is None else argv)]
    return int(stcli.main() or 0)


if __name__ == "__main__":
    raise SystemExit(main())

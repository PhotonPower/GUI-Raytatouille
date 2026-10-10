"""Analysis views. Each module offers ``TITLE`` and ``render(ctx)``; the order below is the tab order."""

from __future__ import annotations

from collections.abc import Callable

from ..context import AppContext
from . import (
    bundle,
    colour,
    distortion,
    layout,
    materials,
    model,
    opd,
    paths,
    polar,
    prescription,
    ray_fans,
    seidel,
    spot,
    system_file,
)

_MODULES = [layout, spot, ray_fans, opd, distortion, colour, seidel, prescription, bundle, paths, polar,
            materials, model, system_file]

# Title shown in the view selector -> render function (insertion order = display order).
VIEWS: dict[str, Callable[[AppContext], None]] = {m.TITLE: m.render for m in _MODULES}

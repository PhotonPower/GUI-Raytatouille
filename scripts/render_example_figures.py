"""Render the figures used in the documentation (needs raytatouille with ``rt.layout``).

Usage::

    RTT_REPO=/pfad/zu/Raytatouille python scripts/render_example_figures.py

Writes ``docs/images/layout-cooke-triplet.png``: lens section, stop, image plane and a ray fan per
field of the Cooke triplet from the library's reference systems. It uses the same drawing code as
the Layout view of the explorer.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import raytatouille as rt

from rtt_explorer.drawing import draw_geometry_api, surface_extents
from rtt_explorer.repo import find_repo

OUT = Path(__file__).resolve().parents[1] / "docs" / "images"


def main() -> int:
    repo = find_repo()
    if not repo:
        print("Kein Raytatouille-Repo gefunden: RTT_REPO setzen.", file=sys.stderr)
        return 1
    if not hasattr(rt, "layout"):
        print("Diese Bibliotheksversion hat kein raytatouille.layout (PR #90).", file=sys.stderr)
        return 1
    root = Path(repo)
    library = rt.MaterialLibrary()
    library.add_catalog(root / "tests" / "catalogs" / "m2" / "schott.agf")
    system = rt.System.from_json((root / "tests" / "reference" / "m2" / "cooke_triplet.rtt.json").read_text("utf-8"))
    comp = rt.compile(system, library)

    bundles = []
    for field in range(comp.field_count):
        rays = rt.trace.make_rays(comp, rt.trace.FanYPupil(n=11), path="main", fields=[field],
                                  wavelength=comp.reference_wavelength)
        _, recorded = rt.trace.trace(comp, rays, path="main", record_path=True)
        bundles.append(recorded)

    fig, ax = plt.subplots(figsize=(11, 4.8))
    extents = surface_extents(rt.layout.surfaces(comp), bundles)
    draw_geometry_api(ax, comp, "yz", extents, 8.0, False)
    colours = plt.get_cmap("tab10")
    for field, recorded in enumerate(bundles):
        pos = np.asarray(recorded.position)
        ax.plot(pos[:, :, 2].T, pos[:, :, 1].T, "-", color=colours(field % 10), lw=0.7)
    ax.set_aspect("equal", adjustable="datalim")
    ax.axhline(0, color="gray", lw=0.5, ls="--")
    ax.set_xlabel("z / mm")
    ax.set_ylabel("y / mm")
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / "layout-cooke-triplet.png"
    fig.savefig(target, dpi=110, bbox_inches="tight")
    print(f"geschrieben: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

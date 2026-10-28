"""View "Detektorbild": the image surface like a camera, with many rays and a pixel grid."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from ..context import AppContext
from ..detector_image import hits_per_pixel, image_extent, pixel_image, pixel_pitch_um, scaled
from ..detector_rays import Hits, compute_hits
from ..ui.common import show

TITLE = "Detektorbild"

RAY_STEPS = [10_000, 50_000, 100_000, 200_000, 500_000, 1_000_000, 2_000_000, 4_000_000]
COLOUR_MAPS = ["gray", "viridis", "inferno", "magma", "hot"]
MANY_PIXELS_PER_RAY = 10  # fewer rays per hit pixel than this: the image is noisy
LOG_FLOOR = 1.0e-4


@st.cache_resource(show_spinner="Strahlen werden berechnet …", max_entries=2)
def _hits(system_key: str, configuration: int | None, path: str, field: int, wavelength: int, n_rays: int,
          aiming_name: str, isotropic: bool, _comp, _aiming) -> Hits:
    """The hits of one setting; cached on the setting, so that changing pixels, field of view or colour
    map does not trace again. The arguments with an underscore are not part of the cache key."""
    return compute_hits(_comp, path, field, wavelength, n_rays, _aiming, isotropic)


def _manual_extent(auto: tuple[float, float, float, float]):
    """The field of view typed in by hand, or None for the automatic one."""
    ss = st.session_state
    if not st.checkbox("Bildfeld festlegen", value=False, key="detimg_manual",
                       help="Aus: das Bildfeld umfasst alle angekommenen Strahlen mit etwas Rand."):
        return None
    for name, value in zip(("x0", "x1", "y0", "y1"), auto):
        ss.setdefault(f"detimg_{name}", float(value))
    if st.button("Bildfeld auf die Strahlen setzen", key="detimg_reset"):
        for name, value in zip(("x0", "x1", "y0", "y1"), auto):
            ss[f"detimg_{name}"] = float(value)
    c = st.columns(4)
    values = (c[0].number_input("x von (mm)", format="%.4f", key="detimg_x0"),
              c[1].number_input("x bis (mm)", format="%.4f", key="detimg_x1"),
              c[2].number_input("y von (mm)", format="%.4f", key="detimg_y0"),
              c[3].number_input("y bis (mm)", format="%.4f", key="detimg_y1"))
    if not (values[1] > values[0] and values[3] > values[2]):
        st.error("Bildfeld leer: es muss x von < x bis und y von < y bis gelten; das automatische wird gezeigt.")
        return None
    return values


def render(ctx: AppContext) -> None:
    """Render the view "Detektorbild"."""
    if not ctx.can_aim:
        st.info("Ohne Blende kann die Pupille nicht gezielt werden; das Detektorbild braucht eine Blende.")
        return
    c1, c2, c3, c4 = st.columns(4)
    field = c1.selectbox("Feld", ctx.field_ids, format_func=ctx.field_label, key="detimg_field")
    wavelength = c2.selectbox("Wellenlänge", ctx.wl_ids, index=ctx.wl_ids.index(ctx.ref_wl),
                              format_func=ctx.wl_label, key="detimg_wl")
    n_rays = c3.select_slider(
        "Strahlen", RAY_STEPS, value=500_000, format_func=lambda n: f"{n:,}".replace(",", " "), key="detimg_rays",
        help="Ungefähre Zahl der Pupillenpunkte (gleichmäßig auf der Pupille); 4 Mio. Strahlen brauchen etwa 30 s "
             "und einige hundert MB.")
    aim_name = c4.radio("Aiming", list(ctx.aim_map), horizontal=True, key="detimg_aim")
    d1, d2, d3, d4 = st.columns(4)
    isotropic = d1.radio("Quelle", ["gleichmäßig je Pupillenpunkt", "isotrop (je Raumwinkel)"], key="detimg_source",
                         help="Gleichmäßig: jeder Pupillenpunkt hat dasselbe Gewicht, das Bild zeigt die Verteilung "
                              "der Strahlen. Isotrop: eine Punktquelle strahlt in jede Richtung gleich viel pro "
                              "Raumwinkel; die Strahlen werden mit cos³ des Winkels zur Blendennormalen gewichtet. "
                              "Wirkt nur bei einer Punktquelle (endliches Objekt), sonst wie gleichmäßig. Eine "
                              "echte Abstrahlcharakteristik (z. B. Dipol) kennt die Ansicht nicht."
                         ).startswith("isotrop")
    nx = int(d2.number_input("Pixel x", 8, 4096, 256, 8, key="detimg_nx"))
    ny = int(d3.number_input("Pixel y", 8, 4096, 256, 8, key="detimg_ny"))
    square = d4.checkbox("Quadratisches Bildfeld", value=False, key="detimg_square",
                         help="Gleiche Breite in x und y um denselben Mittelpunkt; bei gleicher Pixelzahl sind "
                              "dann auch die Pixel quadratisch.")
    e1, e2 = st.columns(2)
    scale = {"linear": "linear", "logarithmisch": "log"}[
        e1.radio("Skala", ["linear", "logarithmisch"], horizontal=True, key="detimg_scale",
                 help=f"Logarithmisch: von {LOG_FLOOR:g} bis 1 des Maximums.")]
    cmap = e2.selectbox("Farbtabelle", COLOUR_MAPS, key="detimg_cmap")

    try:
        hits = _hits(ctx.system_key, ctx.configuration, ctx.path_choice, field, wavelength, n_rays, aim_name,
                     isotropic, ctx.comp, ctx.aim_map[aim_name])
    except (ValueError, RuntimeError) as error:  # ValueError: no arriving ray; the library errors derive from it
        st.error(str(error))
        return
    except Exception as error:  # noqa: BLE001 - a library error (aiming, analysis) must not end the app
        if type(error).__module__.split(".")[0] != "raytatouille":
            raise
        st.error(str(error))
        return

    auto = image_extent(hits.x, hits.y, square=square)
    with st.expander("Bildfeld"):
        manual = _manual_extent(auto)
    extent = manual or auto
    image = pixel_image(hits.x, hits.y, hits.weight, extent, nx, ny)
    dx, dy = pixel_pitch_um(extent, nx, ny)
    per_pixel = hits_per_pixel(hits.x, hits.y, extent, nx, ny)

    m = st.columns(4)
    m[0].metric("Strahlen angekommen", f"{hits.arrived}/{hits.launched}")
    m[1].metric("Pixelgröße", f"{dx:.2f} × {dy:.2f} µm")
    m[2].metric("Strahlen je Pixel (Median)", f"{per_pixel:.0f}",
                help="Median über die Pixel, die getroffen wurden. Wenige Strahlen je Pixel heißen: das Bild rauscht.")
    m[3].metric("Leistung der Strahlen", f"{hits.weight.sum() / hits.launched:.3f}",
                help="Summe der Gewichte (Transmission des Pfads, bei isotroper Quelle mit cos³) geteilt durch die "
                     "Zahl der gestarteten Strahlen.")
    if per_pixel < MANY_PIXELS_PER_RAY:
        st.warning(f"Im Median nur {per_pixel:.0f} Strahlen je getroffenem Pixel: das Bild rauscht. Mehr Strahlen "
                   "wählen oder weniger Pixel.")
    if isotropic and not hits.isotropic:
        st.caption("Die isotrope Quelle wirkt nur bei einer Punktquelle mit Blende (endliches Objekt); hier haben "
                   "alle Pupillenpunkte dasselbe Gewicht.")

    fig, ax = plt.subplots(figsize=(7, 6))
    shown = scaled(image, scale, LOG_FLOOR)
    pic = ax.imshow(shown, extent=extent, origin="lower", cmap=cmap, vmin=0.0, vmax=1.0, interpolation="nearest",
                    aspect="equal")
    bar = fig.colorbar(pic, ax=ax)
    bar.set_label("relative Intensität" + (f" (logarithmisch, {LOG_FLOOR:g} bis 1)" if scale == "log" else ""))
    ax.set_xlabel(f"x / mm ({hits.image_surface})")
    ax.set_ylabel(f"y / mm ({hits.image_surface})")
    show(fig)
    lit = int(np.count_nonzero(image))
    st.caption(f"{lit} von {nx * ny} Pixeln beleuchtet. Koordinaten in der lokalen Ebene der Bildfläche "
               f"„{hits.image_surface}“; das Bild ist die Summe der Strahlgewichte je Pixel.")

"""Live display of the optimization (needs the library and a checkout, like ``test_app.py``)."""

from __future__ import annotations

import numpy as np
import pytest

from test_app import pick_reference, start, widget
from test_app_library_06 import need, ok, ref, view

pytestmark = pytest.mark.library


def test_live_history_follows_the_accepted_steps_of_a_real_run(rtt_repo):
    need("on_iteration")
    import raytatouille as rt

    from rtt_explorer.optim_live import LiveHistory

    path = rtt_repo / "tests" / "reference" / "m5" / "two_lens_gap.rtt.json"
    system = rt.load(str(path)) if hasattr(rt, "load") else rt.System.from_json(path.read_text())
    live = LiveHistory()
    result = rt.optim.optimize(system, on_iteration=live.add)
    h = result.history
    accepted = np.asarray(h.accepted, dtype=bool)
    assert live.count == int(accepted.sum()) > 0
    assert live.phi == pytest.approx(list(np.asarray(h.phi)[accepted]), rel=0, abs=0)
    assert live.k == [int(k) for k in np.asarray(h.k)[accepted]]


def test_view_passes_a_callback_and_keeps_the_result(rtt_repo, monkeypatch):
    need("on_iteration")
    import raytatouille as rt

    calls = []
    real = rt.optim.optimize

    def spy(*args, **kwargs):
        callback = kwargs.get("on_iteration")
        calls.append(callback)
        return real(*args, **kwargs)

    monkeypatch.setattr(rt.optim, "optimize", spy)
    import rtt_explorer.views.optimization as view_module

    drawn = []
    real_show = view_module.show
    monkeypatch.setattr(view_module, "show", lambda fig: (drawn.append(fig), real_show(fig)))
    at = pick_reference(start(rtt_repo, monkeypatch), ref("m5/two_lens_gap.rtt.json"))
    at = view(at, "Optimierung")
    at = widget(at, "button", "Optimieren").click().run()
    ok(at)
    assert len(calls) == 1 and callable(calls[0])
    assert len(drawn) >= 2  # at least one live chart plus the final history chart
    assert next(m for m in at.metric if m.label == "Status").value == "konvergiert (Schrittweite)"

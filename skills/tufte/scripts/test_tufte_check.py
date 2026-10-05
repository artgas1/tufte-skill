"""Tests for tufte_check.py. Every check has a negative control: on a clean input the check is
silent, on a defective input it fires.

Run:  python3 -m pytest -q skills/tufte/scripts/test_tufte_check.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tufte_check as tc

SCRIPT = os.path.join(HERE, "tufte_check.py")


def checks(findings, severity=None):
    return {f.check for f in findings if severity is None or f.severity == severity}


def run_fig(tmp_path, body: str):
    p = tmp_path / "plot.py"
    p.write_text("import matplotlib\nmatplotlib.use('Agg')\nimport matplotlib.pyplot as plt\nimport numpy as np\n"
                 + textwrap.dedent(body))
    return tc.figure_findings(str(p))


# ------------------------------------------------------------------ Lie Factor


def test_lf_tufte_fuel_economy_example():
    # VDQI p. 57: data 18 -> 27.5 mpg (+53%), line 0.6 -> 5.3 in (+783%), LF = 14.8
    f = tc.lf_findings(18, 27.5, shown=(0.6, 5.3))[0]
    assert f.severity == "ERROR"
    assert abs(f.data["lie_factor"] - 14.8) < 0.1


def test_lf_truncated_axis_vs_zero_baseline():
    bad = tc.lf_findings(410, 520, baseline=400)[0]
    good = tc.lf_findings(410, 520, baseline=0)[0]
    assert bad.severity == "ERROR" and abs(bad.data["lie_factor"] - 41.0) < 0.01
    assert good.severity == "INFO" and abs(good.data["lie_factor"] - 1.0) < 1e-9


def test_lf_area_encodings():
    assert tc.lf_findings(4, 10, encoding="area")[0].severity == "INFO"
    two = tc.lf_findings(4, 10, encoding="both-dims")[0]
    assert two.severity == "ERROR" and abs(two.data["lie_factor"] - 3.5) < 1e-9
    assert abs(tc.lf_findings(1, 2, encoding="volume")[0].data["lie_factor"] - 7.0) < 1e-9


def test_lf_undefined():
    with pytest.raises(ValueError):
        tc.lf_findings(0, 5)
    with pytest.raises(ValueError):
        tc.lf_findings(5, 5)


# ------------------------------------------------------------------ time spacing


def test_time_even_and_uneven():
    assert checks(tc.time_findings(["2019", "2020", "2021", "2022"]), "ERROR") == set()
    assert "time-spacing" in checks(tc.time_findings(["2019", "2020", "2021", "2023"]), "ERROR")
    assert "time-spacing" in checks(tc.time_findings(["2000", "2005", "2010", "2020", "2021"]), "ERROR")


def test_time_positions_proportional_is_fine():
    assert checks(tc.time_findings(["2000", "2005", "2006"], [0, 5, 6]), "ERROR") == set()


def test_time_formats():
    assert tc.parse_time("Q3 2021") == 2021.5
    assert tc.parse_time("2021-04") == pytest.approx(2021.25)
    assert tc.parse_time("Mar 2021") == pytest.approx(2021 + 2 / 12)
    assert tc.parse_time("мар 2021") == pytest.approx(2021 + 2 / 12)
    months = ["2024-01", "2024-02", "2024-03", "2024-06"]
    assert "time-spacing" in checks(tc.time_findings(months), "ERROR")


# ------------------------------------------------------------------ matplotlib figures

BARS = """
fig, ax = plt.subplots()
ax.bar(range(4), [410, 425, 440, 470], color='#4c72b0')
{extra}
fig.savefig('out.png')
plt.close(fig)
"""


def test_bars_truncated(tmp_path):
    assert "bar-baseline" not in checks(run_fig(tmp_path, BARS.format(extra="")))
    bad = run_fig(tmp_path, BARS.format(extra="ax.set_ylim(400, 480)"))
    f = next(f for f in bad if f.check == "bar-baseline")
    assert f.severity == "ERROR" and f.data["lie_factor"] > 5


def test_bars_bottom_offset(tmp_path):
    body = "fig, ax = plt.subplots()\nax.bar(range(3), [10, 20, 30], bottom=400)\n"
    assert "bar-baseline" in checks(run_fig(tmp_path, body), "ERROR")


DUAL = """
fig, ax = plt.subplots(figsize=(8, 4))
ax2 = ax.twinx()
x = np.arange(6)
ax.plot(x, [1, 2, 3, 4, 5, 6], color='tab:blue')
ax2.plot(x, [9, 7, 8, 6, 7, 5], color='tab:red')
ax.set_ylabel('Price', color='{left}')
ax.tick_params(axis='y', colors='{left}')
ax2.set_ylabel('Clients', color='{right}')
ax2.tick_params(axis='y', colors='{right}')
"""


def test_dual_axis_colours(tmp_path):
    honest = run_fig(tmp_path, DUAL.format(left="tab:blue", right="tab:red"))
    swapped = run_fig(tmp_path, DUAL.format(left="tab:red", right="tab:blue"))
    assert "dual-axis" in checks(honest, "WARN")
    assert "axis-colour-swap" not in checks(honest)
    assert "axis-colour-swap" in checks(swapped, "ERROR")


def test_category_colours(tmp_path):
    body = """
    fig, (a, b) = plt.subplots(1, 2)
    a.plot([0, 1], [0, 1], color='tab:blue', label='Alpha'); a.plot([0, 1], [1, 0], color='tab:orange', label='Beta')
    b.plot([0, 1], [0, 2], color='{c}', label='Alpha'); b.plot([0, 1], [2, 0], color='tab:orange', label='Beta')
    """
    assert "category-colour" not in checks(run_fig(tmp_path, body.replace("{c}", "tab:blue")))
    bad = run_fig(tmp_path, body.replace("{c}", "tab:red"))
    assert "category-colour" in checks(bad, "ERROR")


def test_time_axis_in_figure(tmp_path):
    body = """
    fig, ax = plt.subplots(figsize=(8, 4))
    labels = {labels}
    ax.plot(range(len(labels)), [1, 2, 3, 4, 5])
    ax.set_xticks(range(len(labels)), labels)
    """
    ok = run_fig(tmp_path, body.format(labels="['2019','2020','2021','2022','2023']"))
    bad = run_fig(tmp_path, body.format(labels="['2000','2005','2010','2011','2012']"))
    assert "time-spacing" not in checks(ok)
    assert "time-spacing" in checks(bad, "ERROR")


def test_grid(tmp_path):
    light = "fig, ax = plt.subplots()\nax.plot([0,1],[0,1])\nax.set_axisbelow(True)\nax.grid(color='0.9', linewidth=0.5)\n"
    dark = "fig, ax = plt.subplots()\nax.plot([0,1],[0,1])\nax.set_axisbelow(False)\nax.grid(color='black', linewidth=1)\n"
    assert "grid" not in checks(run_fig(tmp_path, light), "WARN")
    assert "grid" in checks(run_fig(tmp_path, dark), "WARN")


def test_smoothing(tmp_path):
    raw = "fig, ax = plt.subplots()\nx=[0,1,2,3]\ny=[1,3,2,4]\nax.plot(x, y, '-o', color='C0')\n"
    smooth = ("fig, ax = plt.subplots()\nx=np.arange(4)\ny=[1,3,2,4]\nxs=np.linspace(0,3,200)\n"
              "ax.plot(xs, np.interp(xs, x, y)+0.3*np.sin(xs*3), color='C0')\nax.plot(x, y, 'o', color='C0')\n")
    assert "smoothing" not in checks(run_fig(tmp_path, raw))
    assert "smoothing" in checks(run_fig(tmp_path, smooth), "WARN")


def test_pies(tmp_path):
    good = ("fig, ax = plt.subplots()\nax.pie([50, 30, 20], labels=['A','B','C'], autopct='%1.0f%%')\n")
    bad = ("fig, ax = plt.subplots()\nw = ax.pie([40, 30, 20, 10], explode=[0.2,0,0,0], shadow=True)\n"
           "for i, t in enumerate(['45%', '30%', '20%', '10%']):\n    ax.text(0.3*i-0.4, 0.1, t)\n")
    g = run_fig(tmp_path, good)
    b = run_fig(tmp_path, bad)
    assert "pie-total" not in checks(g) and "pies" not in checks(g, "WARN")
    assert "pie-total" in checks(b, "ERROR")
    assert "pies" in checks(b, "WARN")


def test_icons_scaled_in_both_dims(tmp_path):
    body = """
    from matplotlib.patches import Rectangle
    fig, ax = plt.subplots()
    for i, v in enumerate([4, 6, 8, 10]):
        w, h = {w}, {h}
        ax.add_patch(Rectangle((i, 0), w, h))
    ax.set_xlim(0, 5); ax.set_ylim(0, 1)
    """
    both = run_fig(tmp_path, body.format(w="0.05*v", h="0.08*v"))
    height_only = run_fig(tmp_path, body.format(w="0.5", h="0.08*v"))
    assert "area-encoding" in checks(both, "WARN")
    assert "area-encoding" not in checks(height_only)


def test_single_series_legend(tmp_path):
    one = "fig, ax = plt.subplots()\nax.plot([0,1],[0,1], label='Users')\nax.legend()\n"
    two = "fig, ax = plt.subplots()\nax.plot([0,1],[0,1], label='A')\nax.plot([0,1],[1,0], label='B')\nax.legend()\n"
    assert "legend" in checks(run_fig(tmp_path, one), "WARN")
    assert "legend" not in checks(run_fig(tmp_path, two))


def test_3d(tmp_path):
    flat = "fig = plt.figure()\nax = fig.add_subplot()\nax.bar([0,1],[1,2])\n"
    deep = "fig = plt.figure()\nax = fig.add_subplot(projection='3d')\nax.bar([0,1],[1,2], zs=0, zdir='y')\n"
    assert "3d" not in checks(run_fig(tmp_path, flat))
    assert "3d" in checks(run_fig(tmp_path, deep), "ERROR")


def test_fill_to_arbitrary_level(tmp_path):
    body = "fig, ax = plt.subplots()\nx=np.arange(20)\ny=1000+100*x\nax.plot(x,y)\nax.fill_between(x, y, {lvl})\nax.set_ylim(0, 3500)\n"
    assert "area-fill" not in checks(run_fig(tmp_path, body.format(lvl=0)))
    assert "area-fill" in checks(run_fig(tmp_path, body.format(lvl=1500)), "WARN")


def test_title_and_causal_text(tmp_path):
    calm = "fig, ax = plt.subplots()\nax.plot([0,1],[0,1])\nax.set_title('Users grew 27% in six years')\n"
    loud = ("fig, ax = plt.subplots()\nax.plot([0,1],[0,1])\nax.set_title('EXPLOSIVE GROWTH!')\n"
            "ax.text(0.5, 0.5, 'Price rises caused churn')\n")
    c, l = run_fig(tmp_path, calm), run_fig(tmp_path, loud)
    assert not ({"editorial-title", "causal-claim"} & checks(c))
    assert {"editorial-title", "causal-claim"} <= checks(l, "WARN")


def test_tall_figure_aspect(tmp_path):
    wide = "fig, ax = plt.subplots(figsize=(8,4))\nax.plot(range(5),[1,3,2,4,3])\n"
    tall = "fig, ax = plt.subplots(figsize=(4,9))\nax.plot(range(5),[1,3,2,4,3])\n"
    assert "aspect" not in checks(run_fig(tmp_path, wide))
    assert "aspect" in checks(run_fig(tmp_path, tall), "WARN")


def test_figure_that_is_closed_after_saving_is_still_checked(tmp_path):
    body = BARS.format(extra="ax.set_ylim(400, 480)")  # BARS calls plt.close(fig)
    assert "bar-baseline" in checks(run_fig(tmp_path, body))


# ------------------------------------------------------------------ images


def _png(tmp_path, name, body):
    p = tmp_path / f"{name}.py"
    out = tmp_path / f"{name}.png"
    p.write_text("import matplotlib\nmatplotlib.use('Agg')\nimport matplotlib.pyplot as plt\nimport numpy as np\n"
                 + textwrap.dedent(body) + f"\nplt.savefig(r'{out}', dpi=80)\n")
    subprocess.run([sys.executable, str(p)], check=True)
    return str(out)


def test_image_axis_colour_claim(tmp_path):
    coded = _png(tmp_path, "coded", DUAL.format(left="tab:red", right="tab:blue"))
    plain = _png(tmp_path, "plain", "fig, ax = plt.subplots(figsize=(8,4))\nax.plot([0,1,2],[1,3,2], color='tab:blue')\n")
    assert "axis-colour-claim" in checks(tc.image_findings(coded), "WARN")
    assert "axis-colour-claim" not in checks(tc.image_findings(plain))


def test_image_aspect(tmp_path):
    tall = _png(tmp_path, "tall", "fig, ax = plt.subplots(figsize=(4,9))\nax.plot([0,1],[0,1])\n")
    wide = _png(tmp_path, "wide", "fig, ax = plt.subplots(figsize=(8,4))\nax.plot([0,1],[0,1])\n")
    assert "aspect" in checks(tc.image_findings(tall), "WARN")
    assert "aspect" not in checks(tc.image_findings(wide))


# ------------------------------------------------------------------ Vega-Lite / Plotly


def test_vegalite_bar_baseline_and_smoothing():
    ok = {"$schema": "https://vega.github.io/schema/vega-lite/v5.json", "mark": "bar",
          "encoding": {"y": {"field": "v", "type": "quantitative"}, "x": {"field": "k", "type": "nominal"}}}
    bad = json.loads(json.dumps(ok))
    bad["encoding"]["y"]["scale"] = {"zero": False}
    assert "bar-baseline" not in checks(tc.vegalite_findings(ok))
    assert "bar-baseline" in checks(tc.vegalite_findings(bad), "ERROR")
    line = {"mark": {"type": "line", "interpolate": "basis"}, "encoding": {}}
    assert "smoothing" in checks(tc.vegalite_findings(line), "WARN")
    assert "smoothing" not in checks(tc.vegalite_findings({"mark": "line", "encoding": {}}))


def test_vegalite_dual_axis_swap():
    def spec(c1, c2):
        return {"layer": [
            {"mark": {"type": "line", "color": "#1f77b4"},
             "encoding": {"y": {"field": "a", "type": "quantitative", "axis": {"titleColor": c1}}}},
            {"mark": {"type": "line", "color": "#d62728"},
             "encoding": {"y": {"field": "b", "type": "quantitative", "axis": {"titleColor": c2}}}}],
            "resolve": {"scale": {"y": "independent"}}}
    assert "axis-colour-swap" not in checks(tc.vegalite_findings(spec("#1f77b4", "#d62728")))
    assert "axis-colour-swap" in checks(tc.vegalite_findings(spec("#d62728", "#1f77b4")), "ERROR")


def test_vegalite_category_colours_across_views():
    def view(r):
        return {"mark": "bar", "encoding": {"color": {"field": "c", "type": "nominal",
                                                      "scale": {"domain": ["A", "B"], "range": r}}}}
    ok = {"hconcat": [view(["#1f77b4", "#ff7f0e"]), view(["#1f77b4", "#ff7f0e"])]}
    bad = {"hconcat": [view(["#1f77b4", "#ff7f0e"]), view(["#ff7f0e", "#1f77b4"])]}
    assert "category-colour" not in checks(tc.vegalite_findings(ok))
    assert "category-colour" in checks(tc.vegalite_findings(bad), "ERROR")


def test_plotly_checks():
    bars = {"data": [{"type": "bar", "x": ["a", "b"], "y": [410, 520]}], "layout": {"yaxis": {"range": [400, 530]}}}
    bars_ok = {"data": [{"type": "bar", "x": ["a", "b"], "y": [410, 520]}], "layout": {}}
    assert "bar-baseline" in checks(tc.plotly_findings(bars), "ERROR")
    assert "bar-baseline" not in checks(tc.plotly_findings(bars_ok))

    bub = {"data": [{"type": "scatter", "mode": "markers", "x": [1, 2, 3], "y": [1, 2, 3],
                     "marker": {"size": [10, 20, 30]}}]}
    bub_ok = json.loads(json.dumps(bub))
    bub_ok["data"][0]["marker"]["sizemode"] = "area"
    assert "area-encoding" in checks(tc.plotly_findings(bub), "WARN")
    assert "area-encoding" not in checks(tc.plotly_findings(bub_ok))

    def pies(c2):
        return {"data": [{"type": "pie", "labels": ["A", "B"], "values": [60, 40], "marker": {"colors": ["red", "blue"]}},
                         {"type": "pie", "labels": ["A", "B"], "values": [55, 45], "marker": {"colors": c2}}]}
    assert "category-colour" not in checks(tc.plotly_findings(pies(["red", "blue"])))
    assert "category-colour" in checks(tc.plotly_findings(pies(["blue", "red"])), "ERROR")

    def dual(c1, c2):
        return {"data": [{"type": "scatter", "y": [1, 2], "line": {"color": "#1f77b4"}},
                         {"type": "scatter", "y": [5, 3], "yaxis": "y2", "line": {"color": "#d62728"}}],
                "layout": {"yaxis": {"tickfont": {"color": c1}},
                           "yaxis2": {"overlaying": "y", "side": "right", "tickfont": {"color": c2}}}}
    assert "axis-colour-swap" not in checks(tc.plotly_findings(dual("#1f77b4", "#d62728")))
    assert "axis-colour-swap" in checks(tc.plotly_findings(dual("#d62728", "#1f77b4")), "ERROR")


# ------------------------------------------------------------------ CLI


def test_cli_exit_codes():
    bad = subprocess.run([sys.executable, SCRIPT, "lf", "--data", "410", "520", "--baseline", "400"],
                         capture_output=True, text=True, check=False)
    ok = subprocess.run([sys.executable, SCRIPT, "lf", "--data", "410", "520"], capture_output=True, text=True, check=False)
    assert bad.returncode == 1 and "Lie Factor" in bad.stdout
    assert ok.returncode == 0
    js = subprocess.run([sys.executable, SCRIPT, "--json", "time", "2019", "2020", "2022"],
                        capture_output=True, text=True, check=False)
    assert json.loads(js.stdout)[0]["check"] == "time-spacing"


def test_cli_chain():
    r = subprocess.run([sys.executable, SCRIPT, "lf", "--data", "18", "27.5", "--shown", "0.6", "5.3", "--then",
                        "time", "2019", "2020", "2021"], capture_output=True, text=True, check=False)
    assert r.returncode == 1
    assert "## lf" in r.stdout and "## time" in r.stdout and "14.84" in r.stdout


# ------------------------------------------------------------------ regressions


@pytest.mark.parametrize("mode", ["spec", "figure"])
def test_no_unclosed_input_file(tmp_path, mode):
    # The input file used to be read with a bare open(...).read(): under `python -X dev`
    # that left a ResourceWarning "unclosed file" for every call.
    if mode == "spec":
        src = tmp_path / "s.json"
        src.write_text(json.dumps({"mark": "bar", "data": {"values": [{"a": "x", "b": 1}]},
                                   "encoding": {"x": {"field": "a", "type": "nominal"},
                                                "y": {"field": "b", "type": "quantitative"}}}))
    else:
        src = tmp_path / "p.py"
        src.write_text("import matplotlib.pyplot as plt\nplt.plot([1, 2, 3], [1, 2, 3])\n")
    r = subprocess.run([sys.executable, "-X", "dev", SCRIPT, mode, str(src)],
                       capture_output=True, text=True, check=False)
    assert "ResourceWarning" not in r.stderr


def test_hexc_rounds_like_before():
    # hexc() was rewritten from %-formatting; values must be identical.
    assert tc.hexc((0, 0.5, 1)) == "#0080ff"
    assert tc.hexc((-0.2, 1.7, 0.2)) == "#00ff33"


# ------------------------------------------------------------------ 1.0: measured sizes, bounds, scaling, blobs


def test_lf_measured_diameters():
    radius_rule = tc.lf_findings(1, 2, measured=(10, 20), measure="diameter")[0]
    area_rule = tc.lf_findings(1, 4, measured=(10, 20), measure="diameter")[0]
    assert radius_rule.severity == "ERROR" and abs(radius_rule.data["lie_factor"] - 3.0) < 1e-9
    assert area_rule.severity == "INFO" and abs(area_rule.data["lie_factor"] - 1.0) < 1e-9
    assert "Quote this result as: LF = 3.00" in radius_rule.message


def test_lf_bound_truncated_axis():
    f = tc.lf_bound_findings(baseline=400, axis_max=530)[0]
    assert f.severity == "ERROR" and abs(f.data["lie_factor_min"] - 530 / 130) < 1e-3
    # the bound holds for every pair of bars inside the axis
    for v in (401, 450, 529):
        assert tc.lf_findings(v, 530, baseline=400)[0].data["lie_factor"] >= f.data["lie_factor_min"] - 1e-9
    assert tc.lf_bound_findings(baseline=0, axis_max=530)[0].severity == "INFO"
    with pytest.raises(ValueError):
        tc.lf_bound_findings(baseline=400)


def test_lf_bound_size_encodings_and_unreadable():
    r = tc.lf_bound_findings(encoding="radius")[0]
    assert r.severity == "ERROR" and r.data["lie_factor_min"] == 2
    rng = tc.lf_bound_findings(encoding="radius", ratio=(2, 8))[0]
    assert abs(rng.data["lie_factor_min"] - 3.0) < 1e-9 and abs(rng.data["lie_factor_max"] - 9.0) < 1e-9
    none = tc.lf_bound_findings()[0]
    assert none.severity == "WARN" and "cannot be computed" in none.message


def test_scaling_snaps_rules():
    radius = tc.scaling_findings([10, 20, 40, 80], [16, 30, 59, 116])[0]   # anti-aliased small circle
    honest = tc.scaling_findings([15, 30, 45, 60], [59, 83, 102, 117])[0]
    assert radius.severity == "ERROR" and abs(radius.data["lie_factor"] - 9.0) < 1e-9
    assert honest.severity == "INFO" and abs(honest.data["lie_factor"] - 1.0) < 1e-9
    with pytest.raises(ValueError):
        tc.scaling_findings([1, 2], [3])


def test_blobs_measure_circles(tmp_path):
    png = _png(tmp_path, "circles", """
from matplotlib.patches import Circle
fig = plt.figure(figsize=(4, 2), dpi=100)
ax = fig.add_axes((0, 0, 1, 1)); ax.set_xlim(0, 400); ax.set_ylim(0, 200); ax.axis('off')
ax.add_patch(Circle((100, 100), 20, color='tab:blue'))
ax.add_patch(Circle((280, 100), 60, color='tab:blue'))
""")
    f = tc.blob_findings(png)[0]
    widths = [b["width"] for b in f.data["blobs"]]
    assert len(widths) == 2
    assert abs(widths[0] / 32 - 1) < 0.1 and abs(widths[1] / 96 - 1) < 0.1   # 40 and 120 units at 0.8 px/unit
    gray = _png(tmp_path, "gray", "fig, ax = plt.subplots(figsize=(4, 2))\nax.plot([0, 1], [0, 1], color='0.3')\n")
    assert "blobs" not in {g.check for g in tc.blob_findings(gray) if g.data}


BARS_TRUNC = """
fig, ax = plt.subplots()
ax.bar(range(4), [410, 425, 440, 470], color='#4c72b0')
ax.set_ylim(400, 480)
{note}
"""


def test_labelled_truncation_is_not_a_defect(tmp_path):
    plain = run_fig(tmp_path, BARS_TRUNC.format(note=""))
    noted = run_fig(tmp_path, BARS_TRUNC.format(note="ax.text(0.02, 0.95, 'Axis starts at 400', transform=ax.transAxes)"))
    noted_ru = run_fig(tmp_path, BARS_TRUNC.format(note="ax.set_ylabel('Продажи (ось Y начинается с 400)')"))
    assert "bar-baseline" in checks(plain, "ERROR")
    assert "bar-baseline" not in checks(noted, "ERROR") and "bar-baseline" in checks(noted, "INFO")
    assert "bar-baseline" not in checks(noted_ru, "ERROR")


def test_illustrative_data_counts_as_documentation(tmp_path):
    bare = run_fig(tmp_path, "fig, ax = plt.subplots()\nax.plot([0, 1], [0, 1])\n")
    noted = run_fig(tmp_path, "fig, ax = plt.subplots()\nax.plot([0, 1], [0, 1])\n"
                              "fig.text(0, 0, 'Данные условные (иллюстрация)')\n")
    assert "documentation" in checks(bare)
    assert "documentation" not in checks(noted)


def test_cli_lf_requires_data_or_bound():
    r = subprocess.run([sys.executable, SCRIPT, "lf"], capture_output=True, text=True, check=False)
    assert r.returncode == 2 and "--bound" in r.stderr
    b = subprocess.run([sys.executable, SCRIPT, "lf", "--bound", "--baseline", "400", "--axis-max", "530"],
                       capture_output=True, text=True, check=False)
    assert b.returncode == 1 and "LF ≥ 4.08" in b.stdout


# ------------------------------------------------------------------ chart-wide Lie Factor (v1.1)


def test_lfmax_takes_the_extreme_pair_across_series():
    # per series: Email 3.9->4.2 from 2 gives 2.05, Partners 2.5->3.0 gives 5.00; across series the
    # smallest bar (2.4, Ads) against any larger one gives 2.4/(2.4-2) = 6.0
    fs = tc.lfmax_findings({"Email": [3.9, 4.2], "Partners": [2.5, 3.0], "Ads": [2.4, 2.8]}, baseline=2)
    head = fs[0]
    assert head.check == "lie-factor-max" and head.severity == "ERROR"
    assert abs(head.data["lie_factor"] - 6.0) < 1e-9
    assert head.data["pair"][0] == ["Ads", 2.4]
    per = {f.data["series"]: f.data["lie_factor"] for f in fs if f.check == "lie-factor-series"}
    assert abs(per["Email"] - 3.9 / 1.9) < 1e-3 and abs(per["Partners"] - 5.0) < 1e-9


def test_lfmax_negative_control_zero_baseline():
    fs = tc.lfmax_findings({"A": [3.9, 4.2], "B": [2.4, 3.0]}, baseline=0)
    assert fs[0].severity == "INFO" and abs(fs[0].data["lie_factor"] - 1.0) < 1e-9
    assert not any(f.severity == "ERROR" for f in fs)


def test_lfmax_radius_encoding_uses_widest_ratio():
    fs = tc.lfmax_findings({"2024": [10, 20], "2025": [5, 40]}, encoding="radius")
    assert abs(fs[0].data["lie_factor"] - 9.0) < 1e-9  # r = 8 -> LF = r + 1


def test_lfmax_rejects_values_below_baseline():
    with pytest.raises(ValueError):
        tc.lfmax_findings({"A": [1.5, 3]}, baseline=2)


def test_figure_multi_series_truncated_bars(tmp_path):
    body = """
    fig, ax = plt.subplots()
    x = np.arange(3)
    ax.bar(x - 0.2, [3.9, 4.0, 4.2], 0.4, label='Email')
    ax.bar(x + 0.2, [2.4, 2.9, 3.0], 0.4, label='Partners')
    ax.set_ylim(2, 4.5)
    """
    fs = run_fig(tmp_path, body)
    head = next(f for f in fs if f.check == "lie-factor-max")
    assert head.severity == "ERROR" and abs(head.data["lie_factor"] - 6.0) < 1e-9
    clean = run_fig(tmp_path, body.replace("ax.set_ylim(2, 4.5)", "ax.set_ylim(0, 4.5)"))
    assert "lie-factor-max" not in checks(clean)


def test_plotly_multi_trace_truncated_bars():
    bad = {"data": [{"type": "bar", "name": "A", "y": [3.9, 4.2]}, {"type": "bar", "name": "B", "y": [2.4, 3.0]}],
           "layout": {"yaxis": {"range": [2, 4.5]}}}
    head = next(f for f in tc.plotly_findings(bad) if f.check == "lie-factor-max")
    assert abs(head.data["lie_factor"] - 6.0) < 1e-9
    ok = {"data": bad["data"], "layout": {}}
    assert "lie-factor-max" not in checks(tc.plotly_findings(ok))


def test_cli_lfmax(capsys):
    code = tc.main(["lfmax", "--series", "Email=3.9,4.2", "--series", "Ads=2.4,2.8", "--baseline", "2",
                    "--mark", "bar"])
    out = capsys.readouterr().out
    assert code == 1 and "chart LF = 6.00" in out
    assert tc.main(["lfmax", "--series", "bad", "--mark", "bar"]) == 2


# ------------------------------------------------------------------ v1.2: one LF per encoding, marks, all values


def test_lfmax_finds_a_minimum_in_the_middle_of_a_series():
    series = {"2024": [72, 70, 63.5, 69, 74], "2025": [75, 76, 71, 73, 78]}
    head = tc.lfmax_findings(series, baseline=60)[0]
    assert abs(head.data["lie_factor"] - 63.5 / 3.5) < 1e-3 and head.data["pair"][0] == ["2024", 63.5]
    # negative control: first and last values only miss it
    ends = tc.lfmax_findings({"2024": [72, 74], "2025": [75, 78]}, baseline=60)[0]
    assert ends.data["lie_factor"] < 7


def test_lfmax_warns_when_series_lengths_differ():
    assert "lie-factor-input" in checks(tc.lfmax_findings({"A": [72, 74], "B": [75, 76, 71, 73, 78]}, baseline=60))
    assert "lie-factor-input" not in checks(tc.lfmax_findings({"A": [72, 70, 74], "B": [75, 71, 78]}, baseline=60))


def test_lfmax_and_lf_silent_for_position_marks():
    series: dict[str, list[float]] = {"A": [64.0, 76.0], "B": [62.0, 72.0]}
    bars = tc.lfmax_findings(series, baseline=60, mark="bar")
    assert bars[0].severity == "ERROR"                          # negative control: bars from 60 do distort
    lines = tc.lfmax_findings(series, baseline=60, mark="line")
    assert [f.check for f in lines] == ["lie-factor-not-applicable"]
    assert all(f.severity == "INFO" and "Quote this result" not in f.message for f in lines)


def test_cli_lf_position_mark(capsys):
    assert tc.main(["lf", "--data", "64", "76", "--baseline", "60", "--mark", "line"]) == 0
    out = capsys.readouterr().out
    assert "not applicable" in out and "LF =" not in out
    assert tc.main(["lf", "--data", "64", "76", "--baseline", "60", "--mark", "bar"]) == 1


def test_figure_lines_on_truncated_axis_have_no_lie_factor(tmp_path):
    body = """
    fig, ax = plt.subplots()
    ax.plot(range(12), [64, 65, 66, 66, 68, 69, 71, 70, 72, 73, 74, 76], label='A')
    ax.plot(range(12), [62, 62, 63, 65, 64, 66, 67, 68, 68, 69, 71, 72], label='B')
    ax.set_ylim(60, 80)
    """
    fs = run_fig(tmp_path, body)
    assert not checks(fs) & {"lie-factor-max", "bar-baseline", "lie-factor"}


def _quoted(out: str) -> list[str]:
    return [ln for ln in out.splitlines() if "Quote this result as" in ln]


@pytest.mark.parametrize("order", ["scaling-first", "lf-first"])
def test_one_lie_factor_per_size_encoding(capsys, order):
    scaling = ["scaling", "--values", "12", "24", "48", "96", "--sizes", "13", "26", "49", "94"]
    measured = ["lf", "--data", "12", "96", "--measured", "15", "94", "--measure", "diameter"]
    parts = [scaling, measured] if order == "scaling-first" else [measured, scaling]
    tc.main_chain(parts[0] + ["--then"] + parts[1])
    out = capsys.readouterr().out
    quoted = _quoted(out)
    assert len(quoted) == 1 and "scaling" not in quoted[0] and "fit over 4 shapes" in quoted[0]
    assert "Cross-check only" in out
    # negative control: on its own, lf --measured does quote its number
    tc.main_chain(measured)
    assert len(_quoted(capsys.readouterr().out)) == 1


def test_chain_keeps_bar_lf_next_to_scaling(capsys):
    tc.main_chain(["scaling", "--values", "1", "2", "4", "--sizes", "1", "2", "4", "--then",
                   "lf", "--data", "410", "520", "--baseline", "400"])
    assert len(_quoted(capsys.readouterr().out)) == 2   # different encodings: each has its own LF

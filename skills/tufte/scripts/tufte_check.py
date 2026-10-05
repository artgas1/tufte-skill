#!/usr/bin/env python3
"""Deterministic graphical-integrity checks for charts (Edward Tufte's principles).

Subcommands
  lf      Lie Factor from numbers you read off a chart (or know from the data); `--bound` when the
          values cannot be read.
  lfmax   Chart-wide Lie Factor for several series on one axis: the strongest distortion over all marks
          (bars, lollipops, areas from a baseline; for lines and points it reports "not applicable").
  time    Are time labels evenly spaced in time when they are drawn evenly spaced?
  image   What a PNG/JPG alone can tell (aspect, axis-label colours, colour sets per half).
  blobs   Measure coloured shapes in a PNG/JPG (circles, icons): size in pixels.
  scaling Fit the rule that maps values to shape sizes (radius vs area) and give the Lie Factor.
  contrast WCAG 2.x contrast ratio of a text colour on its background, with AA/AAA verdicts.
  colours The colours drawn in a PNG/JPG or a pixel box of it: hex, share, contrast against the background.
  figure  Run a matplotlib script under the Agg backend and inspect every figure it builds.
  spec    Inspect a Vega-Lite spec or a Plotly figure JSON.

Chain several subcommands in one call with `--then`:
  tufte_check.py image chart.png --then lf --data 410 520 --baseline 400 --then time 2019 2020 2022

Every subcommand prints findings as `SEVERITY check: message` (ERROR, WARN, INFO);
`--json` prints a JSON list instead. Exit code: 1 if any ERROR, else 0.

Dependencies: Python 3.9+, numpy, matplotlib (for `figure`, `image`, `blobs`). No network.
Note: `figure` EXECUTES the given script (with plt.show/plt.close disabled). Run it only on
plotting code you are willing to run.
"""
from __future__ import annotations

import argparse
import colorsys
import json
import math
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from typing import Any, cast

# ----------------------------------------------------------------------------- findings


@dataclass
class Finding:
    severity: str  # ERROR | WARN | INFO
    check: str
    message: str
    where: str = ""
    data: dict = field(default_factory=dict)

    def line(self) -> str:
        loc = f" [{self.where}]" if self.where else ""
        return f"{self.severity} {self.check}{loc}: {self.message}"


def emit(findings: list[Finding], as_json: bool, header: str = "") -> int:
    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    findings = sorted(findings, key=lambda f: order.get(f.severity, 3))
    if as_json:
        print(json.dumps([asdict(f) for f in findings], ensure_ascii=False, indent=1))
    else:
        if header:
            print(header)
        if not findings:
            print("OK: no findings from the deterministic checks (this is not a full audit).")
        for f in findings:
            print(f.line())
    return 1 if any(f.severity == "ERROR" for f in findings) else 0


# ----------------------------------------------------------------------------- Lie Factor

LF_LOW, LF_HIGH = 0.95, 1.05  # Tufte, VDQI p. 57


def effect(a: float, b: float) -> float:
    """Tufte's 'size of effect': relative change from the first to the second value."""
    if a == 0:
        raise ValueError("size of effect is undefined when the first value is 0")
    return (b - a) / abs(a)


def lie_factor(data: tuple[float, float], shown: tuple[float, float]) -> float:
    de = effect(*data)
    if de == 0:
        raise ValueError("the data show no change; the Lie Factor is undefined")
    return effect(*shown) / de


ENCODING_POWER = {"length": 1, "area": 1, "both-dims": 2, "radius": 2, "diameter": 2, "volume": 3}
# --measured: what was measured on the chart -> power that turns it into the drawn magnitude
MEASURE_POWER = {"length": 1, "height": 1, "width": 1, "area": 1, "radius": 2, "diameter": 2, "side": 2}


def _lf_result(lf: float, msg: str, data: dict) -> list[Finding]:
    data = {**data, "lie_factor": round(lf, 3)}
    quote = f" Quote this result as: LF = {lf:.2f}."
    if LF_LOW <= lf <= LF_HIGH:
        return [Finding("INFO", "lie-factor", msg + ". Within Tufte's 0.95–1.05 band." + quote, data=data)]
    kind = "overstates" if lf > 1 else "understates"
    return [Finding("ERROR", "lie-factor", msg + f". The graphic {kind} the change; Tufte treats LF outside "
                    "0.95–1.05 as substantial distortion (VDQI p. 57)." + quote, data=data)]


def lf_findings(v1: float, v2: float, baseline: float | None = None,
                shown: tuple[float, float] | None = None, encoding: str = "length",
                measured: tuple[float, float] | None = None, measure: str = "length",
                cross_check: bool = False) -> list[Finding]:
    """Lie Factor = size of effect shown / size of effect in data (VDQI p. 57).

    The shown magnitudes come from (in order of precedence): `shown` (already the drawn magnitude),
    `measured` sizes converted by `measure` (diameters -> areas), or the values themselves through
    `encoding` and `baseline`.
    """
    how: list[str] = []
    if shown is not None:
        s1, s2 = shown
        how.append("using the drawn magnitudes you supplied")
    elif measured is not None:
        p = MEASURE_POWER[measure]
        m1, m2 = measured
        if m1 <= 0 or m2 <= 0:
            raise ValueError("measured sizes must be positive")
        s1, s2 = m1 ** p, m2 ** p
        if p == 2:
            how.append(f"measured {measure}s {m1:g}→{m2:g}; the drawn magnitude is the area, ∝ {measure}²")
        else:
            how.append(f"measured {measure}s {m1:g}→{m2:g}")
    else:
        power = ENCODING_POWER[encoding]
        b = 0.0 if baseline is None else baseline
        s1, s2 = (v1 - b) ** power, (v2 - b) ** power
        if baseline not in (None, 0):
            how.append(f"drawn from a baseline of {baseline:g}, so the marks show value−{baseline:g}; "
                       f"for bars this LF depends only on the smaller value: {min(v1, v2):g}/({min(v1, v2):g}−{b:g})")
        if power == 2:
            how.append("the marks' linear size is proportional to the value, so area grows with value²")
        if power == 3:
            how.append("all three dimensions scale with the value, so volume grows with value³")
    lf = lie_factor((v1, v2), (s1, s2))
    de, se = effect(v1, v2), effect(s1, s2)
    msg = (f"data change {v1:g}→{v2:g} = {de:+.1%}; shown change {s1:g}→{s2:g} = {se:+.1%}; "
           f"Lie Factor = {se:.4g}/{de:.4g} = {lf:.2f}")
    if how:
        msg += " (" + "; ".join(how) + ")"
    if cross_check:
        return [Finding("INFO", "lie-factor-cross-check", msg + ". Cross-check only — NOT a second Lie Factor: "
                        "`scaling` in this call fits every shape measured in pixels, so its LF is the one number to "
                        "quote for this encoding.", data={"data_effect": de, "shown_effect": se,
                                                          "lie_factor": round(lf, 3), "headline": False})]
    return _lf_result(lf, msg, {"data_effect": de, "shown_effect": se})


def scaling_findings(values: list[float], sizes: list[float], measure: str = "diameter") -> list[Finding]:
    """Which rule maps values to drawn sizes? Fits size ∝ value^k over all shapes (robust to the ±1–2 px
    anti-aliasing error of small shapes), snaps k to the honest or the radius rule when it is close, and
    returns the Lie Factor for the smallest→largest value under that rule."""
    if len(values) != len(sizes) or len(values) < 2:
        raise ValueError("--values and --sizes need the same number of items, at least 2")
    if min(values) <= 0 or min(sizes) <= 0:
        raise ValueError("values and sizes must be positive")
    lv = [math.log(v) for v in values]
    ls = [math.log(x) for x in sizes]
    mv, ms = sum(lv) / len(lv), sum(ls) / len(ls)
    var = sum((a - mv) ** 2 for a in lv)
    if var == 0:
        raise ValueError("all values are equal")
    k = sum((a - mv) * (b - ms) for a, b in zip(lv, ls)) / var
    p_meas = MEASURE_POWER[measure]          # drawn magnitude = size^p_meas
    expo = k * p_meas                       # drawn magnitude ∝ value^expo
    v1, v2 = min(values), max(values)
    if abs(expo - 1) <= 0.15:
        rule, power = "drawn magnitude ∝ value (honest)", 1.0
    elif abs(expo - 2) <= 0.3:
        rule, power = "drawn area ∝ value² (linear size ∝ value)", 2.0
    elif abs(expo - 3) <= 0.45:
        rule, power = "drawn magnitude ∝ value³", 3.0
    else:
        rule, power = f"no standard rule; using the fitted exponent {expo:.2f}", expo
    s1, s2 = v1 ** power, v2 ** power
    lf = lie_factor((v1, v2), (s1, s2))
    de, se = effect(v1, v2), effect(s1, s2)
    msg = (f"fit over {len(values)} shapes: {measure} ∝ value^{k:.2f}, so the drawn magnitude ∝ value^{expo:.2f} → "
           f"{rule}. Smallest→largest: data {v1:g}→{v2:g} = {de:+.1%}; shown {se:+.1%}; "
           f"Lie Factor = {se:.4g}/{de:.4g} = {lf:.2f}")
    msg += (". This is the one Lie Factor for these shapes: do not state a second one from two sizes read "
            "separately")
    return _lf_result(lf, msg, {"exponent": round(expo, 3), "snapped_power": power})


def lf_bound_findings(baseline: float | None = None, axis_max: float | None = None, encoding: str = "length",
                      ratio: tuple[float, float] | None = None) -> list[Finding]:
    """What can be said about the Lie Factor when the data values cannot be read.

    - Bars drawn from a baseline B > 0 inside an axis that ends at T: for any pair, LF = v/(v−B) with v the
      smaller value, and v ≤ T, so LF ≥ T/(T−B).
    - Size encodings where area grows with value^p (p = 2 or 3): for an increase, LF = (r^p − 1)/(r − 1) ≥ p.
      With a range of plausible data ratios r, the LF range follows.
    """
    if baseline is not None:
        if axis_max is None:
            raise ValueError("--bound with --baseline needs --axis-max (the top of the value axis)")
        if baseline <= 0 or axis_max <= baseline:
            return [Finding("INFO", "lie-factor-bound", f"baseline {baseline:g} is not above zero or the axis top "
                            f"{axis_max:g} is not above it: no truncation bound applies.")]
        lo = axis_max / (axis_max - baseline)
        msg = (f"bars drawn from {baseline:g} on an axis ending at {axis_max:g}: for any two bars, LF = v/(v−{baseline:g}) "
               f"with v the smaller value, and v ≤ {axis_max:g}, so LF ≥ {axis_max:g}/({axis_max:g}−{baseline:g}) = {lo:.2f}. "
               f"Quote this result as: LF ≥ {lo:.2f} (lower bound; the values themselves were not read)")
        sev = "ERROR" if lo > LF_HIGH else "INFO"
        return [Finding(sev, "lie-factor-bound", msg + ".", data={"lie_factor_min": round(lo, 3)})]
    p = ENCODING_POWER[encoding]
    if p > 1:
        if ratio is not None:
            r_lo, r_hi = sorted(ratio)
            if r_lo <= 1:
                raise ValueError("--ratio expects data ratios above 1 (larger/smaller)")
            f = lambda r: (r ** p - 1) / (r - 1)
            msg = (f"area grows with value^{p}; for data ratios {r_lo:g}…{r_hi:g} (larger/smaller), "
                   f"LF = (r^{p}−1)/(r−1) lies between {f(r_lo):.2f} and {f(r_hi):.2f}. "
                   f"Quote this result as: LF between {f(r_lo):.2f} and {f(r_hi):.2f}")
            return [Finding("ERROR", "lie-factor-bound", msg + ".", data={"lie_factor_min": round(f(r_lo), 3),
                                                                          "lie_factor_max": round(f(r_hi), 3)})]
        msg = (f"area grows with value^{p}; for any increase, LF = (r^{p}−1)/(r−1) ≥ {p} (r = larger/smaller). "
               f"Quote this result as: LF ≥ {p} (lower bound; the values themselves were not read)")
        return [Finding("ERROR", "lie-factor-bound", msg + ".", data={"lie_factor_min": p})]
    return [Finding("WARN", "lie-factor-bound", "no bound is possible without readable values or an axis range. "
                    "Report: 'Lie Factor cannot be computed: the values are not readable'. Do not estimate the values.")]


# Marks whose length or area from a baseline encodes the value: a Lie Factor applies. Lines and points
# encode by position, so a truncated value axis moves them but does not inflate any drawn magnitude.
LENGTH_MARKS = ("bar", "column", "lollipop", "area")
POSITION_MARKS = ("line", "point", "dot", "scatter", "slope", "dumbbell", "range")
NOT_APPLICABLE = ("Lie Factor not applicable (position encoding): {mark}s encode values by position, not by length "
                  "or area from a baseline, so a truncated value axis does not inflate a drawn magnitude. "
                  "Report: 'LF not applicable (position encoding)' and make NO quantitative claim about distortion — "
                  "no number and no words such as 'stretches changes N times' or 'looks several times larger'. "
                  "A labelled axis start is a disclosed choice, not a defect; an unlabelled one is a labelling note "
                  "('axis start not marked'), without figures.")


def position_mark_findings(mark: str) -> list[Finding]:
    return [Finding("INFO", "lie-factor-not-applicable", NOT_APPLICABLE.format(mark=mark),
                    data={"mark": mark, "lie_factor": None})]


def _strongest_pair(points: list[tuple[str, float]], baseline: float, power: int):
    """Over all ordered pairs of drawn marks, the pair whose Lie Factor is farthest from 1 (in log terms).
    Returns (lf, (label1, v1), (label2, v2)) or None when no pair has a defined LF."""
    best = None
    for i, (l1, v1) in enumerate(points):
        for j, (l2, v2) in enumerate(points):
            if i == j or v1 == v2 or v1 == 0:
                continue
            s1, s2 = (v1 - baseline) ** power, (v2 - baseline) ** power
            if s1 == 0:
                continue
            lf = lie_factor((v1, v2), (s1, s2))
            if lf <= 0:
                continue
            key = (round(abs(math.log(lf)), 9), v2 > v1, abs(v2 - v1))  # ties: the increase, the widest gap
            if best is None or key > best[0]:
                best = (key, lf, (l1, v1), (l2, v2))
    return None if best is None else best[1:]


def lfmax_findings(series: dict[str, list[float]], baseline: float | None = None,
                   encoding: str = "length", mark: str = "bar") -> list[Finding]:
    """Strongest distortion on a chart with several series on one value axis.

    A reader compares any two marks, across series as well as within one, so the chart's Lie Factor is
    the most extreme one over all pairs of marks. For bars from a baseline B > 0 that is the smallest bar
    against any larger one: LF = v_min/(v_min − B). Per-series values follow as supporting detail.
    """
    if mark in POSITION_MARKS:
        return position_mark_findings(mark)
    if not series or sum(len(v) for v in series.values()) < 2:
        raise ValueError("lfmax needs at least two values in total (--series NAME=v1,v2,...)")
    power = ENCODING_POWER[encoding]
    b = 0.0 if baseline is None else baseline
    points = [(name, v) for name, vals in series.items() for v in vals]
    below = [f"{n}={v:g}" for n, v in points if v <= b]
    if below:
        raise ValueError(f"values at or below the baseline {b:g} cannot be drawn from it: {', '.join(below)}")
    top = _strongest_pair(points, b, power)
    if top is None:
        raise ValueError("no pair of different values: the Lie Factor is undefined")
    lf, (n1, v1), (n2, v2) = top
    pair = f"{n1} {v1:g} → {n2} {v2:g}" if n1 != n2 else f"{n1} {v1:g} → {v2:g}"
    how = []
    if b != 0:
        how.append(f"drawn from a baseline of {b:g}: for bars LF = v/(v−{b:g}) with v the first value, "
                   "so the smallest bar against any larger one distorts most")
    if power == 2:
        how.append("linear size ∝ value, so area ∝ value²: the widest value ratio distorts most")
    if power == 3:
        how.append("volume ∝ value³: the widest value ratio distorts most")
    counts = ", ".join(f"{n} {len(v)}" for n, v in series.items())
    msg = (f"chart-wide strongest distortion over {len(points)} marks in {len(series)} series "
           f"(values received: {counts}): {pair}, Lie Factor = {lf:.2f}")
    if how:
        msg += " (" + "; ".join(how) + ")"
    head = _lf_result(lf, msg, {"pair": [[n1, v1], [n2, v2]], "series": len(series)})[0]
    head.check = "lie-factor-max"
    head.message = head.message.replace("Quote this result as: LF =", "Quote this result as: chart LF =")
    out = [head]
    sizes = {len(v) for v in series.values()}
    if len(series) > 1 and len(sizes) > 1:
        out.append(Finding("WARN", "lie-factor-input", f"series have different numbers of values ({counts}). Pass "
                           "every bar of every series, in drawing order: a minimum in the middle of a series sets the "
                           "chart LF, and leaving it out understates the distortion."))
    if len(series) > 1:
        for name, vals in series.items():
            one = _strongest_pair([(name, v) for v in vals], b, power)
            if one is None:
                continue
            slf, (_, a1), (_, a2) = one
            out.append(Finding("INFO", "lie-factor-series", f"within {name}: {a1:g} → {a2:g}, LF = {slf:.2f} "
                               "(supporting detail; the chart LF above is the headline number)",
                               data={"series": name, "lie_factor": round(slf, 3)}))
    return out


# ----------------------------------------------------------------------------- text contrast

WCAG_AA, WCAG_AAA, WCAG_AA_LARGE, WCAG_AAA_LARGE = 4.5, 7.0, 3.0, 4.5   # WCAG 2.x, 1.4.3 and 1.4.6


def parse_colour(text: str) -> tuple[float, float, float]:
    """'#555', '#555555', '555555', 'rgb(85,85,85)', 'white'/'black', or any matplotlib colour name."""
    t = text.strip().lower()
    m = re.fullmatch(r"rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)", t)
    if m:
        vals = [int(x) for x in m.groups()]
        if max(vals) > 255:
            raise ValueError(f"colour {text!r}: rgb components must be 0–255")
        return (vals[0] / 255, vals[1] / 255, vals[2] / 255)
    h = t.lstrip("#")
    if re.fullmatch(r"[0-9a-f]{3}|[0-9a-f]{6}", h):
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255)
    named = {"white": (1.0, 1.0, 1.0), "black": (0.0, 0.0, 0.0)}
    if t in named:
        return named[t]
    try:
        from matplotlib.colors import to_rgb
        r, g, b = to_rgb(t)
        return (float(r), float(g), float(b))
    except (ImportError, ValueError):
        raise ValueError(f"colour {text!r} not understood; use #rrggbb") from None


def relative_luminance(rgb: tuple[float, float, float]) -> float:
    def lin(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_findings(fg: str, bg: str, size: str = "normal") -> list[Finding]:
    """WCAG 2.x contrast ratio of text colour `fg` on background `bg`, with the AA/AAA verdicts."""
    l1, l2 = relative_luminance(parse_colour(fg)), relative_luminance(parse_colour(bg))
    ratio = (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)
    aa_n, aaa_n = ratio >= WCAG_AA, ratio >= WCAG_AAA          # WCAG: compare unrounded ratios
    aa_l, aaa_l = ratio >= WCAG_AA_LARGE, ratio >= WCAG_AAA_LARGE
    verdict = (f"normal text: AA {'PASS' if aa_n else 'FAIL'} (≥4.5), AAA {'PASS' if aaa_n else 'FAIL'} (≥7); "
               f"large text (≥18 pt, or ≥14 pt bold): AA {'PASS' if aa_l else 'FAIL'} (≥3), "
               f"AAA {'PASS' if aaa_l else 'FAIL'} (≥4.5)")
    passes = aa_l if size == "large" else aa_n
    level = "AA pass" if passes else "AA fail"
    msg = (f"{hexc(parse_colour(fg))} on {hexc(parse_colour(bg))}: contrast {ratio:.2f}:1 (WCAG 2.x). {verdict}. "
           f"Quote this result as: contrast {ratio:.2f}:1, {level} for {size} text")
    sev = "INFO" if passes else "ERROR"
    if passes:
        msg += ". Do not call this text low-contrast"
    return [Finding(sev, "contrast", msg + ".", data={"ratio": round(ratio, 3), "aa": passes, "size": size,
                                                      "aa_normal": aa_n, "aaa_normal": aaa_n})]


# ----------------------------------------------------------------------------- time spacing

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
MONTHS.update({m: i for i, m in enumerate(
    ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"], 1)})
MONTHS["мая"] = 5


def parse_time(label: str) -> float | None:
    """Label → fractional year, or None. Handles 2021, 2021-03, 2021-03-15, Q1 2021, 2021 Q1, Mar 2021."""
    s = label.strip().replace("−", "-")
    if re.fullmatch(r"(1[5-9]|2[0-1])\d\d", s):
        return float(s)
    m = re.fullmatch(r"((?:1[5-9]|2[0-1])\d\d)[-/.](\d{1,2})(?:[-/.](\d{1,2}))?", s)
    if m:
        y, mo = int(m.group(1)), int(m.group(2))
        d = int(m.group(3)) if m.group(3) else 1
        if 1 <= mo <= 12:
            return y + (mo - 1) / 12 + (d - 1) / 365
    m = re.fullmatch(r"[Qq]([1-4])[\s'’-]*((?:1[5-9]|2[0-1])\d\d)|((?:1[5-9]|2[0-1])\d\d)[\s-]*[Qq]([1-4])", s)
    if m:
        q = int(m.group(1) or m.group(4))
        y = int(m.group(2) or m.group(3))
        return y + (q - 1) / 4
    m = re.fullmatch(r"([A-Za-zА-Яа-яёЁ]{3,})\.?\s*['’]?((?:1[5-9]|2[0-1])?\d\d)", s)
    if m:
        mo = MONTHS.get(m.group(1)[:3].lower())
        if mo:
            y = int(m.group(2))
            y = y + 2000 if y < 100 else y
            return y + (mo - 1) / 12
    return None


def time_findings(labels: list[str], positions: list[float] | None = None, where: str = "") -> list[Finding]:
    times = [parse_time(x) for x in labels]
    if len(labels) < 3 or any(t is None for t in times):
        bad = [lab for lab, t in zip(labels, times) if t is None]
        return [Finding("INFO", "time-spacing", f"could not parse as times: {bad}" if bad
                        else "need at least 3 time labels", where)]
    if positions is None:
        positions = list(range(len(labels)))
    ts = [t for t in times if t is not None]  # all parsed (guard above); narrows the type
    tgaps = [b - a for a, b in zip(ts, ts[1:])]
    pgaps = [b - a for a, b in zip(positions, positions[1:])]
    if any(g <= 0 for g in tgaps):
        return [Finding("WARN", "time-spacing", f"time labels are not in increasing order: {labels}", where)]
    # time per unit of drawn distance for each interval
    rates = [tg / pg for tg, pg in zip(tgaps, pgaps) if pg > 0]
    if not rates:
        return []
    lo, hi = min(rates), max(rates)
    data = {"time_gaps": [round(g, 4) for g in tgaps], "drawn_gaps": [round(g, 4) for g in pgaps]}
    if hi / lo <= 1.1:
        return [Finding("INFO", "time-spacing", "drawn spacing is proportional to elapsed time", where, data)]
    unit = "years"
    shown = [round(g, 2) for g in tgaps]
    if all(abs(g * 12 - round(g * 12)) < 1e-6 for g in tgaps) and max(tgaps) < 2:
        unit, shown = "months", [round(g * 12) for g in tgaps]
    even = max(pgaps) / min(pgaps) <= 1.05 if min(pgaps) > 0 else False
    msg = (f"intervals of {shown} {unit} are drawn " + ("with equal spacing" if even else
           f"at spacings {[round(p, 3) for p in pgaps]}") +
           f": one unit of distance means between {lo:g} and {hi:g} {unit if unit == 'years' else 'years'} "
           "depending on where you look, so slopes and gaps are distorted")
    common = min(tgaps)
    missing = [(a, b) for (a, b), g in zip(zip(labels, labels[1:]), tgaps) if g > common * 1.5]
    if missing and len(missing) <= 3:
        msg += "; longer gaps between " + ", ".join(f"{a}→{b}" for a, b in missing) + \
               " (a period may be missing or the series is irregular)"
    return [Finding("ERROR", "time-spacing", msg + ". Use a real time axis (numeric/datetime) "
                    "or mark the breaks.", where, data)]


# ----------------------------------------------------------------------------- colour helpers

HUE_NAMES = [(15, "red"), (40, "orange"), (65, "yellow"), (160, "green"), (195, "cyan"),
             (255, "blue"), (290, "purple"), (335, "magenta"), (360, "red")]


def hue_name(rgb) -> str:
    r, g, b = rgb[:3]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    if s < 0.25 or v < 0.2:
        return "black" if v < 0.25 else ("gray" if v < 0.85 else "white")
    deg = h * 360
    for limit, name in HUE_NAMES:
        if deg < limit:
            return name
    return "red"


def chromatic(rgb, s_min=0.3, v_min=0.25) -> bool:
    _h, s, v = colorsys.rgb_to_hsv(*rgb[:3])
    return s >= s_min and v >= v_min


def rgb_dist(a, b) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a[:3], b[:3])))


def hexc(rgb) -> str:
    return "#" + "".join(f"{round(max(0, min(1, c)) * 255):02x}" for c in rgb[:3])


# ----------------------------------------------------------------------------- image mode


def image_findings(path: str) -> list[Finding]:
    import numpy as np

    rgb = _load_rgb(path)
    h, w = rgb.shape[:2]
    out: list[Finding] = [Finding(
        "INFO", "image-only",
        "pixels only: Lie Factor, baselines, time spacing and series identity cannot be computed "
        "from the image by this script. Read the values off the chart, write them down, and run "
        "`tufte_check.py lf` / `time` on them.")]

    ratio = h / w
    if ratio > 1.05:
        out.append(Finding("WARN", "aspect", f"the image is taller than wide ({w}×{h}px, height/width "
                           f"= {ratio:.2f}). For time series this steepens every slope; Tufte suggests "
                           "graphics about 50% wider than tall unless the data suggest otherwise "
                           "(VDQI p. 190), and banking to 45° (Cleveland) for line charts."))

    step = max(1, int(max(h, w) / 700))
    small = rgb[::step, ::step]
    sh, sw = small.shape[:2]
    flat = small.reshape(-1, 3)
    mx, mn = flat.max(1), flat.min(1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-9), 0).reshape(sh, sw)
    val = mx.reshape(sh, sw)
    chroma_mask = (sat >= 0.3) & (val >= 0.25)

    def region_hues(y0, y1, x0, x1):
        m = chroma_mask[int(y0 * sh):int(y1 * sh), int(x0 * sw):int(x1 * sw)]
        px = small[int(y0 * sh):int(y1 * sh), int(x0 * sw):int(x1 * sw)][m]
        counts: dict[str, list] = {}
        for p in px:
            counts.setdefault(hue_name(p), []).append(p)
        total = max(1, m.size)
        res = sorted(((k, len(v) / total, np.median(np.array(v), axis=0)) for k, v in counts.items()),
                     key=lambda t: -t[1])
        return [(k, share, hexc(c)) for k, share, c in res if share >= 0.002]

    left = region_hues(0.05, 0.95, 0.0, 0.10)
    right = region_hues(0.05, 0.95, 0.90, 1.0)
    center = region_hues(0.08, 0.92, 0.12, 0.88)
    fmt = lambda hs: ", ".join(f"{k} {hx} ({s:.1%})" for k, s, hx in hs[:4]) or "none"
    out.append(Finding("INFO", "colour-regions",
                       f"chromatic colours — left edge strip: {fmt(left)}; right edge strip: {fmt(right)}; "
                       f"plot centre: {fmt(center)}"))
    def text_like(hs):
        # axis tick labels and titles: one dominant hue, thin (a small share of the strip)
        if not hs:
            return None
        total = sum(s for _, s, _ in hs)
        k, s, _ = hs[0]
        return k if 0.002 <= s <= 0.04 and s / total >= 0.7 else None

    ln, rn = text_like(left), text_like(right)
    if ln and rn and ln != rn:
        centre_names = {k for k, _, _ in center}
        if ln in centre_names and rn in centre_names:
            out.append(Finding(
                "WARN", "axis-colour-claim",
                f"the left edge is dominated by {ln} and the right edge by {rn}, and both colours are "
                "used in the plot: this looks like two colour-coded y-axes. Axis colour is a claim about "
                "which series belongs to which axis. Establish the pairing from independent evidence "
                "(legend, direct labels, numbers stated in the title or annotations, plausibility of the "
                "values under each axis) BEFORE reading any values; if it contradicts the axis colours, "
                "the axis colours are swapped."))
    lh = region_hues(0.05, 0.95, 0.0, 0.5)
    rh = region_hues(0.05, 0.95, 0.5, 1.0)
    if len(lh) >= 3 and len(rh) >= 3:
        out.append(Finding("INFO", "colour-halves",
                           f"left half colours: {fmt(lh)}; right half colours: {fmt(rh)}. If the halves "
                           "are repeated panels of the same categories, check that each category keeps "
                           "its colour (and that any legend covers both panels)."))
    if len(center) >= 7:
        out.append(Finding("INFO", "many-hues",
                           f"{len(center)} distinct hue families in the plot area — many categories, a "
                           "rainbow scale, or decorative gradients."))
    return out


def _load_rgb(path: str):
    import numpy as np
    from matplotlib import image as mpimg

    arr = mpimg.imread(path)
    if arr.dtype not in (np.float32, np.float64):
        arr = arr.astype("float64") / 255.0
    if arr.ndim == 2:
        arr = np.stack([arr] * 3, axis=-1)
    return arr[..., :3].astype("float64")


def colour_findings(path: str, box: tuple[int, int, int, int] | None = None, top: int = 8,
                    min_share: float = 0.002) -> list[Finding]:
    """The colours actually drawn in a PNG/JPG (or in a pixel box of it), with their share of pixels and
    their contrast against the most common colour (the background). Use these hex values with `contrast`
    instead of judging colours by eye."""
    import numpy as np

    arr = _load_rgb(path)
    h, w = arr.shape[:2]
    if box is not None:
        x0, y0, x1, y1 = box
        x0, x1 = sorted((max(0, x0), min(w, x1)))
        y0, y1 = sorted((max(0, y0), min(h, y1)))
        if x1 - x0 < 1 or y1 - y0 < 1:
            raise ValueError(f"--box is empty inside a {w}×{h} image")
        arr = arr[y0:y1, x0:x1]
    px = (np.clip(arr, 0, 1) * 255).round().astype(int).reshape(-1, 3)
    keys = (px // 8)                                       # bins of 8 levels per channel
    flat = keys[:, 0] * 1024 + keys[:, 1] * 32 + keys[:, 2]
    _, inv, counts = np.unique(flat, return_inverse=True, return_counts=True)
    order = np.argsort(-counts)
    total = float(len(flat))
    rows, cols = [], []
    for k in order[: max(top * 4, 32)]:
        share = counts[k] / total
        if share < min_share:
            break
        mean = px[inv == k].mean(axis=0) / 255.0
        cols.append(((float(mean[0]), float(mean[1]), float(mean[2])), share))
        if len(cols) >= top:
            break
    if not cols:
        return [Finding("WARN", "colours", "no colour covers the minimum share; try a larger --box.")]
    bg = cols[0][0]
    lb = relative_luminance(bg)
    for rgb, share in cols:
        lc = relative_luminance(rgb)
        ratio = (max(lc, lb) + 0.05) / (min(lc, lb) + 0.05)
        rows.append(f"{hexc(rgb)}  {share:6.1%} of pixels  contrast vs {hexc(bg)}: {ratio:.2f}:1")
    where = f"box {box}" if box else f"whole image {w}×{h}px"
    return [Finding("INFO", "colours", f"most common colours ({where}; the first is taken as the background):\n  "
                    + "\n  ".join(rows) + "\nAnti-aliased edges are mixtures, so thin text may not appear as its own "
                    "colour: give `--box` around the text. For two marks or series run `contrast A B` with these "
                    "hex values. Without a ratio, make no claim about how well colours separate.",
                    data={"colours": [[hexc(c), round(sh, 4)] for c, sh in cols]})]


def blob_findings(path: str, min_px: int = 30, colour: str | None = None, tol: float = 0.12) -> list[Finding]:
    """Connected regions of chromatic pixels (or of one colour) with their pixel sizes."""
    from collections import deque

    import numpy as np

    rgb = _load_rgb(path)
    h, w = rgb.shape[:2]
    if colour:
        target = np.array(_colour(colour) or (0, 0, 0))
        mask = np.sqrt(((rgb - target) ** 2).sum(-1)) <= tol * math.sqrt(3)
    else:
        mx, mn = rgb.max(-1), rgb.min(-1)
        sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-9), 0)
        mask = (sat >= 0.25) & (mx >= 0.2)
    seen = np.zeros_like(mask, dtype=bool)
    blobs = []
    ys, xs = np.nonzero(mask)
    for y0, x0 in zip(ys.tolist(), xs.tolist()):
        if seen[y0, x0]:
            continue
        q = deque([(y0, x0)])
        seen[y0, x0] = True
        pts = []
        while q:
            y, x = q.popleft()
            pts.append((y, x))
            for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    q.append((ny, nx))
        if len(pts) < min_px:
            continue
        a = np.array(pts)
        y_min, x_min = a.min(0)
        y_max, x_max = a.max(0)
        med = np.median(rgb[a[:, 0], a[:, 1]], axis=0)
        blobs.append({"x": round(float(a[:, 1].mean()), 1), "y": round(float(a[:, 0].mean()), 1),
                      "width": int(x_max - x_min + 1), "height": int(y_max - y_min + 1), "area_px": len(pts),
                      "equiv_diameter": round(2 * math.sqrt(len(pts) / math.pi), 1), "colour": hexc(med)})
    blobs.sort(key=lambda b: (b["x"], b["y"]))
    if not blobs:
        return [Finding("INFO", "blobs", "no coloured regions found (try --colour '#rrggbb' or a lower --min-px).")]
    lines = [f"#{i + 1} {b['colour']} centre ({b['x']:g},{b['y']:g}) box {b['width']}×{b['height']}px "
             f"area {b['area_px']}px equiv. diameter {b['equiv_diameter']:g}px" for i, b in enumerate(blobs[:40])]
    more = f" (+{len(blobs) - 40} more)" if len(blobs) > 40 else ""
    return [Finding("INFO", "blobs", f"{len(blobs)} region(s){more}, left to right:\n  " + "\n  ".join(lines) +
                    "\nFor circles use the box width (diameter). Pass ALL shapes of the panel with the values they "
                    "encode, in the same order, to `scaling --values V1 V2 … --sizes D1 D2 …`: its LF is the one "
                    "number to quote. Overlapping or clipped shapes merge or shrink: check the box against the "
                    "picture.", data={"blobs": blobs})]


# ----------------------------------------------------------------------------- matplotlib mode


def _collect_figures(script: str):
    import matplotlib

    matplotlib.use("Agg", force=True)
    import runpy

    import matplotlib.pyplot as plt

    kept = []
    before = set(plt.get_fignums())
    orig_close = plt.close

    def no_close(*a, **k):
        fig = a[0] if a else None
        if fig is None:
            fig = plt.gcf() if plt.get_fignums() else None
        if fig is not None and hasattr(fig, "axes") and fig not in kept:
            kept.append(fig)

    plt.close = no_close  # keep figures the script closes after saving
    plt.show = lambda *a, **k: None
    cwd = os.getcwd()
    script = os.path.abspath(script)
    sdir = os.path.dirname(script)
    sys.path.insert(0, sdir)
    os.chdir(sdir)
    try:
        runpy.run_path(script, run_name="__main__")
    finally:
        os.chdir(cwd)
        plt.close = orig_close
    figs = list(kept)
    for n in plt.get_fignums():
        if n in before:
            continue
        f = plt.figure(n)
        if f not in figs:
            figs.append(f)
    return figs


def _neutral(rgb) -> bool:
    return not chromatic(rgb, s_min=0.25, v_min=0.2)


def _series_colors(ax):
    """Colours of data marks drawn against this Axes (lines, scatter, bars)."""
    from matplotlib.collections import PathCollection
    from matplotlib.colors import to_rgb

    cols = []
    for ln in ax.get_lines():
        if ln.get_label().startswith("_child") or ln.get_visible():
            cols.append(to_rgb(ln.get_color()))
    for c in ax.collections:
        if isinstance(c, PathCollection):
            fc = cast(Any, c.get_facecolor())  # N×4 RGBA array at runtime; the stubs say ColorType
            if len(fc):
                cols.append(tuple(fc[0][:3]))
    for cont in getattr(ax, "containers", []):
        if cont.__class__.__name__ == "BarContainer" and len(cont.patches):
            cols.append(tuple(cont.patches[0].get_facecolor()[:3]))
    return [c for c in cols if not _neutral(c)]


def _axis_colour(ax):
    from matplotlib.colors import to_rgb

    side = ax.yaxis.get_label_position()
    cands = [to_rgb(ax.yaxis.label.get_color())]
    cands += [to_rgb(t.get_color()) for t in ax.get_yticklabels() if t.get_text()]
    cands.append(to_rgb(ax.spines[side].get_edgecolor()))
    for c in cands:
        if chromatic(c, s_min=0.25, v_min=0.2):
            return c, side
    return None, side


def _bar_containers(ax):
    return [c for c in getattr(ax, "containers", []) if c.__class__.__name__ == "BarContainer"]


TRUNCATION_NOTE = re.compile(
    r"truncat|broken axis|axis break|not (?:start(?:ing)? )?(?:at|from) zero|non-?zero (?:baseline|axis)|"
    r"(?:axis|scale)\b[^.\n]{0,40}\b(?:starts?|begins?)\b[^.\n]{0,10}\b(?:at|from)\b|"
    r"не с нуля|не от нуля|усеч|обрез|разрыв|(?:ось|шкала)[^.\n]{0,30}(?:начина|от\s*\d)", re.IGNORECASE)
DISCLAIMER = re.compile(r"source|data:|источник|данные:|illustrative|hypothetical|synthetic|example data|"
                        r"fictional|условн|иллюстрац|вымышлен", re.IGNORECASE)


def _figure_texts(fig) -> str:
    parts = [t.get_text() for t in fig.texts]
    if fig._suptitle is not None:
        parts.append(fig._suptitle.get_text())
    for ax in fig.axes:
        parts += [ax.get_title(), ax.get_xlabel(), ax.get_ylabel()] + [t.get_text() for t in ax.texts]
    return " ".join(p for p in parts if p)


def _has_break_mark(ax) -> bool:
    """A drawn axis break: short lines placed in axes coordinates and not clipped (the usual `//` idiom)."""
    for ln in ax.get_lines():
        if ln.get_transform() is ax.transAxes and not ln.get_clip_on():
            return True
    return False


def _numeric_ticks(axis) -> bool:
    labels = [t.get_text().replace("−", "-").replace(",", ".").strip().rstrip("%") for t in axis.get_ticklabels()]
    labels = [lab for lab in labels if lab]
    if not labels:
        return False
    try:
        [float(lab) for lab in labels]
    except ValueError:
        return False
    return True


def _check_position_truncation(fig, ax, where):
    """Lines and points on a value axis that starts above zero. Not a distortion (no Lie Factor), but the
    start must be MARKED: a break symbol or a note. A tick label that reads the start value is not a mark."""
    data_lines = [ln for ln in ax.get_lines() if ln.get_transform() is not ax.transAxes and len(ln.get_xdata()) >= 2]
    scatters = [c for c in ax.collections if c.__class__.__name__ == "PathCollection" and len(c.get_offsets()) >= 1]
    if (not data_lines and sum(len(c.get_offsets()) for c in scatters) < 2) or _bar_containers(ax):
        return []
    marked = bool(TRUNCATION_NOTE.search(_figure_texts(fig))) or _has_break_mark(ax)
    out = []
    for name, axis, lim in (("y", ax.yaxis, ax.get_ylim()), ("x", ax.xaxis, ax.get_xlim())):
        lo = min(lim)
        vals = []
        for ln in data_lines:
            vals += [float(v) for v in (ln.get_ydata() if name == "y" else ln.get_xdata())]
        for c in scatters:
            vals += [float(p[1] if name == "y" else p[0]) for p in c.get_offsets()]
        if not vals or lo <= 0 or min(vals) <= 0 or not _numeric_ticks(axis):
            continue
        if name == "x" and data_lines and not scatters:
            continue   # a line chart's x axis is its domain (time), not a value axis
        if marked:
            out.append(Finding("INFO", "axis-start", f"{name} axis starts at {lo:g} and the chart marks it (a note or a "
                               "break symbol): a disclosed choice. Lines and points encode by position: no Lie Factor "
                               "and no distortion estimate.", where))
        else:
            out.append(Finding("WARN", "axis-start-unmarked", f"{name} axis starts at {lo:g}, and nothing marks it — no "
                               "break symbol, no note. A tick label that reads the start value is NOT a mark. Report "
                               "'axis start not marked' and the fix (a break symbol or a note such as 'axis starts at "
                               f"{lo:g}'). Lines and points encode by position: no Lie Factor, no 'N times'.", where))
    return out


def _check_bars(ax, where, labelled_truncation: bool = False):
    out = []
    truncated: dict[float, dict[str, list[float]]] = {}  # visible baseline -> series label -> values
    for n, cont in enumerate(_bar_containers(ax)):
        ps = [p for p in cont.patches if p.get_visible()]
        if len(ps) < 2 or not all(hasattr(p, "get_y") for p in ps):
            continue
        horiz = getattr(cont, "orientation", None) == "horizontal"
        if horiz:
            base = [p.get_x() for p in ps]
            size = [p.get_width() for p in ps]
            lim = ax.get_xlim()
            scale = ax.get_xscale()
        else:
            base = [p.get_y() for p in ps]
            size = [p.get_height() for p in ps]
            lim = ax.get_ylim()
            scale = ax.get_yscale()
        if scale != "linear":
            out.append(Finding("ERROR", "bar-baseline", f"bars on a {scale} value axis: bar length is no "
                               "longer proportional to the value. Use dots, or a linear axis from zero.", where))
            continue
        if max(base) - min(base) > 1e-9:
            continue  # stacked or floating bars: baseline differs per bar
        b = base[0]
        vals = [b + s for s in size]
        lo = min(lim)
        visible_from = max(b, lo) if all(v >= 0 for v in vals) else b
        if all(v > 0 for v in vals) and visible_from > 0:
            if all(v > visible_from for v in vals):
                name = _label(cont)
                group = truncated.setdefault(visible_from, {})
                if not name or name.startswith("_") or name in group:
                    name = f"series {n + 1}"
                group[name] = vals
            vmin, vmax = min(vals), max(vals)
            if vmin == vmax:
                continue
            f = lf_findings(vmin, vmax, baseline=visible_from)[0]
            if labelled_truncation:
                out.append(Finding("INFO", "bar-baseline",
                                   f"bars start at {visible_from:g}, and the chart says so in its text: a labelled, "
                                   "deliberate choice (VDQI p. 56, principle 2), not a defect. For reference, "
                                   + f.message.split(". The graphic")[0] + ".", where, f.data))
                continue
            out.append(Finding("ERROR", "bar-baseline",
                               f"bars start at {visible_from:g}, not at zero. Smallest→largest bar: "
                               + f.message.split(". The graphic")[0] + ". Start the value axis at zero, or show dots "
                               "instead of bars and label the truncation.", where, f.data))
    for base, series in truncated.items():
        if len(series) < 2:
            continue
        head = lfmax_findings(series, baseline=base)[0]
        if labelled_truncation:
            head = Finding("INFO", "lie-factor-max", "labelled truncation; for reference, "
                           + head.message.split(". The graphic")[0] + ".", where, head.data)
        else:
            head.where = where
            head.message = ("several series share this truncated axis, so readers compare bars across series; "
                            "the per-series LFs above understate it. " + head.message)
        out.append(head)
    return out


def _check_dual(fig, ax_index):
    out = []
    groups: dict[tuple, list] = {}
    for ax in fig.axes:
        key = tuple(round(v, 3) for v in ax.get_position().bounds)
        groups.setdefault(key, []).append(ax)
    for axes in groups.values():
        if len(axes) < 2:
            continue
        a, b = axes[0], axes[1]
        where = f"{ax_index(a)}+{ax_index(b)}"
        out.append(Finding("WARN", "dual-axis", "two y-scales share one plot area. Their alignment is "
                           "arbitrary, so crossings, gaps and relative slopes between the series are design "
                           "artefacts. Prefer two aligned panels, or index both series to a common base.", where))
        swapped, odd = [], []
        for this, other in ((a, b), (b, a)):
            col, side = _axis_colour(this)
            if col is None:
                continue
            own, oth = _series_colors(this), _series_colors(other)
            match_own = any(rgb_dist(col, c) < 0.2 for c in own)
            match_oth = any(rgb_dist(col, c) < 0.2 for c in oth)
            label = this.get_ylabel() or f"{side} axis"
            if not match_own and match_oth:
                swapped.append(f"the {side} axis ('{label}') is coloured {hue_name(col)} {hexc(col)}, but its own "
                               f"series is {', '.join(sorted({hue_name(c) for c in own})) or 'neutral'}")
            elif not match_own and own:
                odd.append(f"the {side} axis is coloured {hexc(col)}, which matches none of its own series")
        if swapped:
            out.append(Finding("ERROR", "axis-colour-swap", "; ".join(swapped) + ". Each axis wears the colour of "
                               "the series drawn against the OTHER axis, so readers will read each line on the "
                               "wrong scale.", where))
        for m in odd:
            out.append(Finding("WARN", "axis-colour", m + ".", where))
    return out


def _label(artist) -> str:
    """Artist label as str ('' when unset); matplotlib stores str(label) or None."""
    lab = artist.get_label()
    return lab if isinstance(lab, str) else ""


def _labelled_colours(fig, ax_index):
    from matplotlib.colors import to_rgb
    from matplotlib.patches import Wedge

    pairs = []
    for ax in fig.axes:
        w = ax_index(ax)
        for ln in ax.get_lines():
            lab = _label(ln)
            if lab and not lab.startswith("_"):
                pairs.append((lab.strip(), to_rgb(ln.get_color()), w))
        for c in ax.collections:
            lab = _label(c)
            if lab and not lab.startswith("_") and len(c.get_facecolors()):
                pairs.append((lab.strip(), tuple(c.get_facecolors()[0][:3]), w))
        for cont in _bar_containers(ax):
            lab = _label(cont)
            if lab and not lab.startswith("_") and cont.patches:
                pairs.append((lab.strip(), tuple(cont.patches[0].get_facecolor()[:3]), w))
        for p in ax.patches:
            if isinstance(p, Wedge):
                lab = _label(p)
                if lab and not lab.startswith("_"):
                    pairs.append((lab.strip(), tuple(p.get_facecolor()[:3]), w))
        leg = ax.get_legend()
        if leg is not None:
            for h, t in zip(leg.legend_handles, leg.get_texts()):
                try:
                    col = h.get_facecolor() if hasattr(h, "get_facecolor") else None
                    if col is None or len(col) == 0 or (hasattr(h, "get_color") and h.__class__.__name__ == "Line2D"):
                        col = h.get_color()
                    pairs.append((t.get_text().strip(), to_rgb(col if not hasattr(col, "shape") or col.ndim == 1
                                                              else col[0]), w + " legend"))
                except Exception:  # noqa: BLE001, S110 - legend handles can be any artist; skip unreadable ones
                    pass
    return pairs


def _check_category_colours(pairs):
    out = []
    by: dict[str, list] = {}
    for lab, col, w in pairs:
        by.setdefault(lab, []).append((col, w))
    for lab, items in by.items():
        base_col = items[0][0]
        diff = [(c, w) for c, w in items[1:] if rgb_dist(base_col, c) > 0.15]
        if diff:
            seen = "; ".join(f"{hexc(c)} in {w}" for c, w in [items[0]] + diff)
            out.append(Finding("ERROR", "category-colour", f"'{lab}' is drawn in different colours: {seen}. "
                               "A category must keep one colour across panels and charts."))
    return out


def _check_pies(fig, ax, where):
    from matplotlib.patches import Shadow, Wedge

    out = []
    wedges = [p for p in ax.patches if isinstance(p, Wedge)]
    if not wedges:
        return out
    groups: dict[tuple, list] = {}
    for wd in wedges:
        key = (round(wd.center[0], 1), round(wd.center[1], 1))
        groups.setdefault(key, []).append(wd)
    # exploded slices have a shifted centre; merge groups whose centres are close
    centres = list(groups)
    merged: list[list] = []
    for c in centres:
        for m in merged:
            mc = m[0].center
            if math.dist(c, mc) < 0.5 * m[0].r:
                m.extend(groups[c])
                break
        else:
            merged.append(list(groups[c]))
    if len(merged) > 1:
        out.append(Finding("WARN", "pies", f"{len(merged)} pies in one axes: comparing angles across pies is "
                           "harder than within one (VDQI p. 178). Use a slope chart, paired dots or a table.", where))
    for i, g in enumerate(merged):
        spans = [((w.theta2 - w.theta1) % 360) or 360 for w in g]
        if len(g) > 6:
            out.append(Finding("WARN", "pies", f"pie {i + 1} has {len(g)} slices; beyond ~6 slices a sorted bar "
                               "chart or table reads better.", where))
        small = sum(1 for s in spans if s < 18)
        if small:
            out.append(Finding("INFO", "pies", f"pie {i + 1}: {small} slice(s) under 5% are hard to read.", where))
        cents = {(round(w.center[0], 2), round(w.center[1], 2)) for w in g}
        if len(cents) > 1:
            out.append(Finding("WARN", "pies", f"pie {i + 1} has exploded slice(s): pulling a slice out "
                               "exaggerates it and breaks angle comparison.", where))
    if any(isinstance(p, Shadow) for p in ax.patches):
        out.append(Finding("WARN", "chartjunk", "drop shadow under the pie: non-data ink.", where))
    # percent labels per pie
    pct = []
    for t in ax.texts:
        m = re.search(r"(-?\d+(?:[.,]\d+)?)\s*%", t.get_text())
        if m:
            x, y = t.get_position()
            pct.append((float(m.group(1).replace(",", ".")), (x, y)))
    if pct and merged:
        sums = [0.0] * len(merged)
        for v, pos in pct:
            k = min(range(len(merged)), key=lambda i: math.dist(pos, merged[i][0].center))
            sums[k] += v
        for i, s in enumerate(sums):
            if s and abs(s - 100) > 0.6:
                out.append(Finding("ERROR", "pie-total", f"percent labels on pie {i + 1} sum to {s:.1f}%, not "
                                   "100%: the slices cannot match their labels.", where))
    return out


def _check_ink(fig, ax, where, n_series):
    from matplotlib.colors import to_rgb
    from matplotlib.patches import Shadow

    out = []
    if getattr(ax, "name", "") == "3d":
        out.append(Finding("ERROR", "3d", "3-D axes: depth adds a dimension the data may not have and makes "
                           "values unreadable (VDQI p. 71: information-carrying dimensions should not "
                           "exceed the dimensions of the data).", where))
    grid = [ln for ln in ax.get_xgridlines() + ax.get_ygridlines() if ln.get_visible()]
    for axis in (ax.xaxis, ax.yaxis):
        for t in axis.get_minor_ticks():
            if t.gridline.get_visible():
                grid.append(t.gridline)
    if grid:
        g = grid[-1]
        lum = sum(to_rgb(g.get_color())) / 3
        alpha = g.get_alpha() if g.get_alpha() is not None else 1.0
        heavy = lum < 0.45 and alpha > 0.5 and g.get_linewidth() >= 0.7
        dense = len(grid) > 16
        on_top = ax.get_axisbelow() is False
        bits = []
        if heavy:
            bits.append(f"dark ({hexc(to_rgb(g.get_color()))}, width {g.get_linewidth():g})")
        if dense:
            bits.append(f"dense ({len(grid)} lines)")
        if on_top:
            bits.append("drawn on top of the data")
        if g.get_linestyle() not in ("-", "solid"):
            bits.append("dashed")
        if bits:
            sev = "WARN" if (heavy or on_top or dense) else "INFO"
            out.append(Finding(sev, "grid", "grid is " + ", ".join(bits) + ". Dark grid lines are chartjunk "
                               "(VDQI p. 113); mute the grid (light gray, thin, behind data) or drop it.", where))
    if any(isinstance(p, Shadow) for p in ax.patches) or any(
            a.get_path_effects() for a in list(ax.patches) + list(ax.get_lines()) if hasattr(a, "get_path_effects")):
        out.append(Finding("WARN", "chartjunk", "shadow/path effects on data marks: non-data ink.", where))
    has_marks = bool(ax.get_lines() or _bar_containers(ax) or ax.collections)
    if ax.images and has_marks:
        out.append(Finding("WARN", "chartjunk", f"{len(ax.images)} raster image(s) drawn together with data marks "
                           "(gradient fill, texture or picture background): decoration that competes with data.",
                           where))
    leg = ax.get_legend()
    if leg is not None and len(leg.get_texts()) == 1 and n_series <= 1:
        out.append(Finding("WARN", "legend", "a legend for a single series: name it in the title or label it "
                           "directly.", where))
    hatched = [p for p in ax.patches if p.get_hatch()]
    if hatched:
        out.append(Finding("INFO", "moire", f"{len(hatched)} hatched patch(es): hatching vibrates (moiré); use "
                           "flat light tones.", where))
    rot = [t for t in ax.get_xticklabels() if t.get_text() and abs(t.get_rotation() % 180 - 90) < 1]
    if rot:
        out.append(Finding("INFO", "labels", "x tick labels rotated 90°: hard to read; use fewer labels or a "
                           "horizontal layout.", where))
    return out


def _check_smoothing(ax, where):
    out = []
    lines = [ln for ln in ax.get_lines() if ln.get_visible()]
    dense = [ln for ln in lines if len(ln.get_xdata()) >= 40 and ln.get_marker() in ("None", None, "", " ")]
    sparse = [ln for ln in lines if 2 < len(ln.get_xdata()) <= 40 and ln.get_marker() not in ("None", None, "", " ")]
    for d in dense:
        for s in sparse:
            if rgb_dist(_rgb(d.get_color()), _rgb(s.get_color())) > 0.15:
                continue
            xs = list(map(float, s.get_xdata()))
            xd = list(map(float, d.get_xdata()))
            if min(xd) <= min(xs) + 1e-9 and max(xd) >= max(xs) - 1e-9 and len(xd) >= 5 * len(xs):
                out.append(Finding("WARN", "smoothing", f"a smooth curve of {len(xd)} points is drawn through "
                                   f"{len(xs)} observations: values between observations are invented by the "
                                   "interpolation (and can overshoot). Connect observations with straight "
                                   "segments or show points only.", where))
                break
    return out


def _rgb(c):
    from matplotlib.colors import to_rgb
    return to_rgb(c)


def _check_fill(ax, where):
    import numpy as np

    out = []
    for c in ax.collections:
        name = c.__class__.__name__
        if name not in ("PolyCollection", "FillBetweenPolyCollection"):
            continue
        for p in c.get_paths():
            v = p.vertices
            if len(v) < 10:
                continue
            ys = np.round(v[:, 1], 6)
            vals, counts = np.unique(ys, return_counts=True)
            k = counts.argmax()
            level = float(vals[k])
            if counts[k] >= 0.3 * len(ys) and abs(level) > 1e-9 and abs(level - min(ax.get_ylim())) > 1e-6:
                out.append(Finding("WARN", "area-fill", f"an area is filled down to y = {level:g}, which is neither "
                                   "zero nor the axis floor: the size of the shaded area means nothing.", where))
                break
    return out


def _check_free_shapes(ax, where):
    """Icon-like shapes scaled in both dimensions (area grows with the square of the size)."""
    from matplotlib.patches import Ellipse, Rectangle

    out = []
    bar_patches = {id(p) for cont in _bar_containers(ax) for p in cont.patches}
    free = [p for p in ax.patches if id(p) not in bar_patches and isinstance(p, (Rectangle, Ellipse))]
    for kind in (Rectangle, Ellipse):
        ps = [p for p in free if isinstance(p, kind)]
        if len(ps) < 3:
            continue
        if kind is Rectangle:
            wh = [(p.get_width(), p.get_height()) for p in ps]
        else:
            wh = [(p.width, p.height) for p in ps if isinstance(p, Ellipse)]
        ws = [abs(w) for w, h in wh]
        hs = [abs(h) for w, h in wh]
        if min(ws) <= 0 or min(hs) <= 0 or max(ws) / min(ws) < 1.2:
            continue
        ratios = [w / h for w, h in zip(ws, hs)]
        if max(ratios) / min(ratios) < 1.05:
            f = lf_findings(min(ws), max(ws), encoding="both-dims")[0]
            out.append(Finding("WARN", "area-encoding",
                               f"{len(ps)} {kind.__name__.lower()} shapes keep their proportions while their size "
                               "changes, so their area grows with the square of their size. If their width tracks "
                               "the value linearly, then " + f.message.split(". The graphic")[0] + ". Scale icons by area "
                               "(side ∝ √value), or use bars/dots.", where, f.data))
            break
    return out


def _check_text(fig, where_of):
    out = []
    texts = []
    precise: list[str] = []
    if fig._suptitle is not None and fig._suptitle.get_text():
        texts.append(("title", fig._suptitle.get_text()))
    for ax in fig.axes:
        if ax.get_title():
            texts.append(("title", ax.get_title()))
        for t in ax.texts:
            texts.append(("text", t.get_text()))
    for t in fig.texts:
        texts.append(("text", t.get_text()))
    for kind, s in texts:
        letters = [ch for ch in s if ch.isalpha()]
        if kind == "title" and (s.strip().endswith("!") or (len(letters) >= 6 and
                                                           sum(ch.isupper() for ch in letters) / len(letters) > 0.8)):
            out.append(Finding("WARN", "editorial-title", f"title '{s.strip()}' shouts (capitals/exclamation): "
                               "state the finding in plain words the data support."))
        if re.search(r"\b(caus\w*|because|due to|leads? to|led to|drives?|driven|resulted)\b|"
                     r"вызва\w*|привел\w*|привёл\w*|из-за|благодаря|потому что", s, re.IGNORECASE):
            out.append(Finding("WARN", "causal-claim", f"text '{' '.join(s.split())}' asserts causation. "
                               "Does the chart show a mechanism, or only co-movement?"))
        if re.search(r"\d+[.,]\d{3,}", s):
            precise.append(" ".join(s.split())[:20])
    if precise:
        out.append(Finding("WARN", "precision", f"{len(precise)} label(s) with 3+ decimals (e.g. "
                           f"{', '.join(precise[:3])}): false precision; round to what the data support."))
    alltext = " ".join(s for _, s in texts) + " " + " ".join(
        a.get_xlabel() + " " + a.get_ylabel() for a in fig.axes)
    if not DISCLAIMER.search(alltext):
        out.append(Finding("INFO", "documentation", "no source line found on the figure (BE, principle 5: "
                           "documentation)."))
    return out


def _check_time_axes(ax, where):
    labels = [t.get_text() for t in ax.get_xticklabels() if t.get_text()]
    locs = [float(t.get_position()[0]) for t in ax.get_xticklabels() if t.get_text()]
    if len(labels) >= 3 and all(parse_time(lab) is not None for lab in labels):
        fs = time_findings(labels, locs, where)
        return [f for f in fs if f.severity != "INFO"]
    return []


def _check_banking(fig, ax, where):
    import numpy as np

    angles = []
    for ln in ax.get_lines():
        x, y = ln.get_xdata(), ln.get_ydata()
        if len(x) < 3:
            continue
        try:
            pts = ax.transData.transform(np.column_stack([np.asarray(x, float), np.asarray(y, float)]))
        except Exception:  # noqa: BLE001, S112 - non-numeric x/y (dates, categories): not bankable
            continue
        d = np.diff(pts, axis=0)
        d = d[np.abs(d[:, 0]) > 1e-9]
        if len(d):
            angles.extend(np.degrees(np.arctan(np.abs(d[:, 1] / d[:, 0]))))
    if len(angles) < 3:
        return []
    med = float(np.median(angles))
    w, h = fig.get_size_inches()
    out = []
    if med > 60 or med < 15:
        factor = math.tan(math.radians(med))
        out.append(Finding("INFO", "banking", f"median line-segment angle is {med:.0f}° (figure {w:g}×{h:g} in). "
                           f"Banking to 45° (Cleveland) suggests changing width/height by about ×{factor:.1f}.",
                           where))
    return out


def _check_scatter_sizes(ax, where, src: str):
    import numpy as np
    from matplotlib.collections import PathCollection

    out = []
    for c in ax.collections:
        if isinstance(c, PathCollection):
            s = np.asarray(c.get_sizes())
            if s.size > 2 and s.min() > 0 and s.max() / s.min() > 1.2:
                msg = (f"marker sizes vary ×{s.max() / s.min():.1f} in area. matplotlib's `s` is an AREA "
                       "(points²): s ∝ value is honest, s ∝ value² overstates.")
                if re.search(r"\bs\s*=\s*[^,)]*(\*\*\s*2|np\.square|pow\([^)]*,\s*2\))", src):
                    out.append(Finding("WARN", "area-encoding", msg + " The script appears to square the value "
                                       "for `s`.", where))
                else:
                    out.append(Finding("INFO", "area-encoding", msg, where))
    return out


def figure_findings(script: str) -> list[Finding]:
    with open(script, encoding="utf-8", errors="ignore") as fh:
        src = fh.read()
    figs = _collect_figures(script)
    out: list[Finding] = []
    if not figs:
        return [Finding("WARN", "figure", "the script produced no matplotlib figures.")]
    all_pairs = []
    for fi, fig in enumerate(figs):
        fig.canvas.draw()
        idx = {id(a): i for i, a in enumerate(fig.axes)}
        ax_index = lambda a, fi=fi, idx=idx: f"fig{fi + 1}/ax{idx[id(a)] + 1}"
        out += _check_dual(fig, ax_index)
        w_in, h_in = fig.get_size_inches()
        if h_in > w_in * 1.05 and any(len(a.get_lines()) for a in fig.axes):
            out.append(Finding("WARN", "aspect", f"figure is taller than wide ({w_in:g}×{h_in:g} in): slopes look "
                               "steeper than in a horizontal layout; Tufte suggests ~50% wider than tall unless "
                               "the data suggest otherwise (VDQI p. 190).", f"fig{fi + 1}"))
        out += _check_text(fig, ax_index)
        all_pairs += _labelled_colours(fig, ax_index)
        for ax in fig.axes:
            w = ax_index(ax)
            n_series = len(_bar_containers(ax)) + len([ln for ln in ax.get_lines() if not ln.get_label().startswith("_")])
            out += _check_bars(ax, w, bool(TRUNCATION_NOTE.search(_figure_texts(fig))) or _has_break_mark(ax))
            out += _check_position_truncation(fig, ax, w)
            out += _check_pies(fig, ax, w)
            out += _check_ink(fig, ax, w, n_series)
            out += _check_smoothing(ax, w)
            out += _check_fill(ax, w)
            out += _check_free_shapes(ax, w)
            out += _check_time_axes(ax, w)
            out += _check_scatter_sizes(ax, w, src)
            out += _check_banking(fig, ax, w)
    out += _check_category_colours(all_pairs)
    import matplotlib.pyplot as plt
    for fig in figs:
        plt.close(fig)
    # de-duplicate identical messages
    seen, uniq = set(), []
    for f in out:
        key = (f.severity, f.check, f.message, f.where.split("/")[0])
        if key not in seen:
            seen.add(key)
            uniq.append(f)
    return uniq


# ----------------------------------------------------------------------------- Vega-Lite / Plotly


def _colour(c):
    from matplotlib.colors import to_rgb
    try:
        return to_rgb(c)
    except (ValueError, TypeError):
        return None


def _title_text(t):
    if isinstance(t, dict):
        return t.get("text", "")
    return t or ""


def _text_checks(title: str, where: str):
    out = []
    letters = [ch for ch in title if ch.isalpha()]
    if title and (title.strip().endswith("!") or (len(letters) >= 6 and
                                                  sum(ch.isupper() for ch in letters) / len(letters) > 0.8)):
        out.append(Finding("WARN", "editorial-title", f"title '{title}' shouts: state the finding plainly.", where))
    return out


def vegalite_findings(spec: dict) -> list[Finding]:
    out: list[Finding] = []
    colour_maps: list[tuple[str, dict]] = []

    def mark_type(v):
        m = v.get("mark")
        return m.get("type") if isinstance(m, dict) else m

    def mark_colour(v):
        m = v.get("mark")
        if isinstance(m, dict) and m.get("color"):
            return m["color"]
        enc = v.get("encoding", {})
        if isinstance(enc.get("color"), dict) and "value" in enc["color"]:
            return enc["color"]["value"]
        return None

    def walk(v, path, inherited_data):
        data = v.get("data", inherited_data)
        mt = mark_type(v)
        enc = v.get("encoding", {})
        where = path or "root"
        out.extend(_text_checks(_title_text(v.get("title")), where))
        if mt in ("bar", "area"):
            for ch in ("y", "x"):
                e = enc.get(ch, {})
                if e.get("type") == "quantitative":
                    sc = e.get("scale", {}) or {}
                    dom = sc.get("domain")
                    if sc.get("zero") is False or (isinstance(dom, list) and dom and isinstance(dom[0], (int, float))
                                                   and dom[0] > 0):
                        out.append(Finding("ERROR", "bar-baseline", f"{mt} marks on a {ch} scale that does not "
                                           "start at zero (scale.zero=false or domain starts above 0).", where))
        if isinstance(v.get("mark"), dict):
            interp = v["mark"].get("interpolate")
            if interp in ("basis", "cardinal", "catmull-rom", "bundle", "natural", "monotone"):
                out.append(Finding("WARN", "smoothing", f"interpolate='{interp}' invents values between "
                                   "observations; use 'linear' (or points).", where))
        if mt == "arc":
            vals = (data or {}).get("values") if isinstance(data, dict) else None
            if vals and len(vals) > 6:
                out.append(Finding("WARN", "pies", f"pie/donut with {len(vals)} slices.", where))
        col = enc.get("color", {})
        if isinstance(col, dict) and isinstance(col.get("scale"), dict):
            sc = col["scale"]
            if isinstance(sc.get("domain"), list) and isinstance(sc.get("range"), list):
                colour_maps.append((where, dict(zip(map(str, sc["domain"]), sc["range"]))))
        x = enc.get("x", {})
        if x.get("type") in ("ordinal", "nominal") and isinstance(data, dict) and data.get("values"):
            f = x.get("field")
            labels = [str(r.get(f)) for r in data["values"] if f in r]
            uniq = list(dict.fromkeys(labels))
            if len(uniq) >= 3 and all(parse_time(u) is not None for u in uniq):
                out.extend(f for f in time_findings(uniq, None, where) if f.severity != "INFO")
        layers = v.get("layer")
        if layers:
            res = (v.get("resolve", {}) or {}).get("scale", {})
            if res.get("y") == "independent":
                out.append(Finding("WARN", "dual-axis", "layers with independent y scales (dual axis): the "
                                   "alignment of the two scales is arbitrary.", where))
                cols = [(_colour(mark_colour(lv)), (lv.get("encoding", {}).get("y", {}) or {}).get("axis") or {})
                        for lv in layers]
                for i, (mc, axis) in enumerate(cols):
                    ac = _colour(axis.get("titleColor") or axis.get("labelColor") or axis.get("domainColor"))
                    if ac is None or mc is None:
                        continue
                    others = [c for j, (c, _) in enumerate(cols) if j != i and c is not None]
                    if rgb_dist(ac, mc) > 0.2 and any(rgb_dist(ac, o) < 0.2 for o in others):
                        out.append(Finding("ERROR", "axis-colour-swap", f"layer {i}: its y axis is coloured like "
                                           "the other layer's marks.", where))
        for key in ("layer", "hconcat", "vconcat", "concat"):
            for i, sub in enumerate(v.get(key, []) or []):
                walk(sub, f"{path}/{key}[{i}]", data)
        if isinstance(v.get("spec"), dict):
            walk(v["spec"], f"{path}/spec", data)

    walk(spec, "", None)
    merged: dict[str, tuple[str, str]] = {}
    for where, cmap in colour_maps:
        for k, c in cmap.items():
            if k in merged and _colour(merged[k][0]) and _colour(c) and rgb_dist(_colour(merged[k][0]), _colour(c)) > 0.15:
                out.append(Finding("ERROR", "category-colour", f"'{k}' is {merged[k][0]} in {merged[k][1]} but {c} "
                                   f"in {where}."))
            merged.setdefault(k, (c, where))
    return out


def plotly_findings(fig: dict) -> list[Finding]:
    out: list[Finding] = []
    traces = fig.get("data", []) or []
    layout = fig.get("layout", {}) or {}
    out.extend(_text_checks(_title_text(layout.get("title")), "layout"))

    def axis_key(t, ch):
        ref = t.get(f"{ch}axis", ch)
        return ch + "axis" + ref[1:]

    truncated: dict[tuple[str, float], dict[str, list[float]]] = {}
    notes = " ".join([_title_text(layout.get("title"))] + [str(a.get("text", "")) for a in layout.get("annotations") or []
                                                           if isinstance(a, dict)])
    marked = bool(TRUNCATION_NOTE.search(notes))
    unmarked_done: set[str] = set()
    for i, t in enumerate(traces):
        typ = t.get("type", "scatter")
        if typ in ("scatter", "scattergl"):
            key = axis_key(t, "y")
            ax_y = layout.get(key, {}) or {}
            rng = ax_y.get("range")
            ys = [v for v in (t.get("y") or []) if isinstance(v, (int, float)) and not isinstance(v, bool)]
            if (isinstance(rng, list) and len(rng) == 2 and min(rng) > 0 and ys and min(ys) > 0
                    and ax_y.get("type") != "log" and key not in unmarked_done):
                unmarked_done.add(key)
                if marked:
                    out.append(Finding("INFO", "axis-start", f"{key} starts at {min(rng):g} and the title or an "
                                       "annotation says so: a disclosed choice. Position encoding: no Lie Factor.", key))
                else:
                    out.append(Finding("WARN", "axis-start-unmarked", f"{key} starts at {min(rng):g} and no title or "
                                       "annotation says so (tick labels are not a mark). Report 'axis start not "
                                       "marked'. Position encoding: no Lie Factor, no 'N times'.", key))
        where = f"trace {i} ({t.get('name') or typ})"
        if typ == "bar":
            ch = "x" if t.get("orientation") == "h" else "y"
            ax = layout.get(axis_key(t, ch), {}) or {}
            rng = ax.get("range")
            if isinstance(rng, list) and len(rng) == 2 and min(rng) > 0:
                if marked:
                    out.append(Finding("INFO", "bar-baseline", f"bars on an axis whose range starts at {min(rng):g}; the "
                                       "title or an annotation says so: a labelled choice, not a defect.", where))
                else:
                    out.append(Finding("ERROR", "bar-baseline", f"bars on an axis whose range starts at {min(rng):g}.",
                                       where))
                vals = t.get(ch)
                if (ax.get("type") != "log" and isinstance(vals, list) and vals
                        and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in vals)):
                    group = truncated.setdefault((axis_key(t, ch), float(min(rng))), {})
                    name = t.get("name") if isinstance(t.get("name"), str) and t.get("name") else f"trace {i}"
                    group[name if name not in group else f"{name} ({i})"] = [float(v) for v in vals]
            if ax.get("type") == "log":
                out.append(Finding("ERROR", "bar-baseline", "bars on a log axis.", where))
        if typ in ("scatter3d", "surface", "mesh3d", "cone", "volume", "isosurface"):
            out.append(Finding("WARN", "3d", f"{typ} trace: 3-D projection; check the data really have 3 dimensions.",
                               where))
        if (t.get("line") or {}).get("shape") == "spline":
            out.append(Finding("WARN", "smoothing", "line.shape='spline' invents values between observations.", where))
        mk = t.get("marker") or {}
        size = mk.get("size")
        if isinstance(size, list) and len(size) > 2 and min(size) > 0 and max(size) / min(size) > 1.2:
            mode = mk.get("sizemode", "diameter")
            if mode == "diameter":
                f = lf_findings(min(size), max(size), encoding="diameter")[0]
                out.append(Finding("WARN", "area-encoding", "marker.size is a DIAMETER by default "
                                   "(sizemode='diameter'): if size ∝ value, area ∝ value². "
                                   + f.message.split(". The graphic")[0] + ". Set sizemode='area'.", where, f.data))
        if typ == "pie":
            labels = t.get("labels") or []
            if len(labels) > 6:
                out.append(Finding("WARN", "pies", f"pie with {len(labels)} slices.", where))
            pull = t.get("pull")
            if (isinstance(pull, list) and any(p for p in pull)) or (isinstance(pull, (int, float)) and pull):
                out.append(Finding("WARN", "pies", "pulled (exploded) slice.", where))
        x = t.get("x")
        xa = layout.get(axis_key(t, "x"), {}) or {}
        if isinstance(x, list) and len(x) >= 3 and xa.get("type") == "category":
            labels = [str(v) for v in x]
            if all(parse_time(v) is not None for v in labels):
                out.extend(f for f in time_findings(labels, None, where) if f.severity != "INFO")
    pies = [t for t in traces if t.get("type") == "pie"]
    if len(pies) > 1:
        out.append(Finding("WARN", "pies", f"{len(pies)} pies: compare with a slope chart or paired dots instead."))
    # category colours across traces
    seen: dict[str, tuple] = {}
    for i, t in enumerate(traces):
        pairs = []
        mk = t.get("marker") or {}
        if t.get("type") == "pie" and isinstance(mk.get("colors"), list):
            pairs = list(zip(map(str, t.get("labels") or []), mk["colors"]))
        elif t.get("name") is not None:
            c = mk.get("color") if isinstance(mk.get("color"), str) else (t.get("line") or {}).get("color")
            if isinstance(c, str):
                pairs = [(str(t["name"]), c)]
        for lab, c in pairs:
            rc = _colour(c)
            if rc is None:
                continue
            if lab in seen and rgb_dist(seen[lab][0], rc) > 0.15:
                out.append(Finding("ERROR", "category-colour", f"'{lab}' is {hexc(seen[lab][0])} in trace "
                                   f"{seen[lab][1]} but {hexc(rc)} in trace {i}."))
            seen.setdefault(lab, (rc, i))
    # dual axis
    over = [k for k, v in layout.items() if k.startswith("yaxis") and isinstance(v, dict) and v.get("overlaying")]
    if over:
        out.append(Finding("WARN", "dual-axis", "overlaying y axes: their alignment is arbitrary.", "layout"))
        by_axis: dict[str, list] = {}
        for t in traces:
            ref = t.get("yaxis", "y")
            c = (t.get("line") or {}).get("color") or (t.get("marker") or {}).get("color")
            if isinstance(c, str) and _colour(c):
                by_axis.setdefault("yaxis" + ref[1:], []).append(_colour(c))
        for key, ax in layout.items():
            if not (key.startswith("yaxis") and isinstance(ax, dict)):
                continue
            ac = _colour(((ax.get("title") or {}).get("font") or {}).get("color") if isinstance(ax.get("title"), dict) else None) \
                or _colour((ax.get("tickfont") or {}).get("color")) or _colour(ax.get("color"))
            if ac is None:
                continue
            own = by_axis.get(key, [])
            others = [c for k2, cs in by_axis.items() if k2 != key for c in cs]
            if own and not any(rgb_dist(ac, c) < 0.2 for c in own) and any(rgb_dist(ac, c) < 0.2 for c in others):
                out.append(Finding("ERROR", "axis-colour-swap", f"{key} is coloured like the series on the other "
                                   "axis.", "layout"))
    # Lie Factor of bars on a truncated axis, chart-wide (across every bar trace on that axis)
    for (key, base), series in truncated.items():
        vals = [v for vs in series.values() for v in vs]
        if len(vals) < 2 or min(vals) <= base or min(vals) == max(vals):
            continue
        head = lfmax_findings(series, baseline=base)[0]
        head.where = key
        if marked:
            head = Finding("INFO", "lie-factor-max", "labelled truncation; for reference, "
                           + head.message.split(". The graphic")[0] + ".", key, head.data)
        out.append(head)
    return out


def spec_findings(path: str) -> list[Finding]:
    with open(path, encoding="utf-8") as fh:
        spec = json.load(fh)
    if isinstance(spec, dict) and ("$schema" in spec and "vega-lite" in str(spec["$schema"]) or
                                   any(k in spec for k in ("mark", "layer", "hconcat", "vconcat", "concat", "facet"))):
        return vegalite_findings(spec)
    if isinstance(spec, dict) and ("data" in spec or "layout" in spec):
        return plotly_findings(spec)
    return [Finding("WARN", "spec", "not recognised as a Vega-Lite spec or a Plotly figure.")]


# ----------------------------------------------------------------------------- CLI


def parse_series(items: list[str]) -> dict[str, list[float]]:
    """`NAME=1,2,3` (one per --series flag) -> {NAME: [1.0, 2.0, 3.0]}; names must be unique."""
    out: dict[str, list[float]] = {}
    for item in items:
        name, sep, raw = item.rpartition("=")
        if not sep or not name.strip():
            raise ValueError(f"--series expects NAME=V1,V2,...; got {item!r}")
        try:
            vals = [float(x) for x in raw.replace(";", ",").split(",") if x.strip()]
        except ValueError:
            raise ValueError(f"--series {name.strip()!r}: values must be numbers, got {raw!r}") from None
        if not vals:
            raise ValueError(f"--series {name.strip()!r} has no values")
        if name.strip() in out:
            raise ValueError(f"--series name {name.strip()!r} is repeated")
        out[name.strip()] = vals
    return out


def main(argv=None, cross_check: bool = False) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--json", action="store_true", help="print findings as JSON")
    sub = p.add_subparsers(dest="cmd", required=True)

    q = sub.add_parser("lf", help="Lie Factor from two data values (or a bound when values are unreadable)")
    q.add_argument("--data", nargs=2, type=float, metavar=("FIRST", "SECOND"),
                   help="the two data values being compared (printed labels or read off a labelled axis)")
    g = q.add_mutually_exclusive_group()
    g.add_argument("--baseline", type=float, help="value where the bars/axis start (truncated axis)")
    g.add_argument("--shown", nargs=2, type=float, metavar=("S1", "S2"), help="drawn magnitudes (e.g. areas)")
    g.add_argument("--measured", nargs=2, type=float, metavar=("M1", "M2"),
                   help="sizes measured on the chart (pixels), converted with --measure")
    q.add_argument("--measure", choices=sorted(MEASURE_POWER), default="length",
                   help="what --measured holds: radius|diameter|side (area ∝ size²) or length|height|width|area")
    q.add_argument("--encoding", choices=sorted(ENCODING_POWER), default="length",
                   help="how the value is encoded: length/area (honest), both-dims|radius|diameter (area ∝ v²), "
                        "volume (∝ v³)")
    q.add_argument("--bound", action="store_true",
                   help="values cannot be read: bound the LF from --baseline/--axis-max or --encoding")
    q.add_argument("--axis-max", type=float, help="with --bound --baseline: the top of the value axis")
    q.add_argument("--ratio", nargs=2, type=float, metavar=("RMIN", "RMAX"),
                   help="with --bound --encoding: plausible range of the data ratio larger/smaller")
    q.add_argument("--mark", choices=LENGTH_MARKS + POSITION_MARKS + ("shape",),
                   help="what is drawn: bar|column|lollipop|area (length from a baseline), shape (circle, icon, "
                        "bubble), or line|point|dot|scatter|slope (position: the LF does not apply)")

    q = sub.add_parser("lfmax", help="chart-wide Lie Factor: strongest distortion over all marks of several series")
    q.add_argument("--series", action="append", required=True, metavar="NAME=V1,V2,...",
                   help="one series per flag: its name and every value drawn from the shared axis")
    q.add_argument("--baseline", type=float, help="value where the bars start (truncated axis)")
    q.add_argument("--encoding", choices=sorted(ENCODING_POWER), default="length")
    q.add_argument("--mark", required=True, choices=LENGTH_MARKS + POSITION_MARKS,
                   help="what is drawn. bar|column|lollipop|area: length from a baseline, LF applies. "
                        "line|point|dot|scatter|slope: position encoding, LF does not apply")

    q = sub.add_parser("colours", help="colours drawn in a PNG/JPG (or a pixel box), share and contrast vs background")
    q.add_argument("path")
    q.add_argument("--box", nargs=4, type=int, metavar=("X0", "Y0", "X1", "Y1"), help="pixel box, top-left origin")
    q.add_argument("--top", type=int, default=8)

    q = sub.add_parser("contrast", help="WCAG 2.x contrast ratio of a text colour on a background, AA/AAA")
    q.add_argument("fg", help="text colour, e.g. #555555")
    q.add_argument("bg", help="background colour, e.g. #ffffff")
    q.add_argument("--size", choices=("normal", "large"), default="normal",
                   help="large = at least 18 pt, or 14 pt bold")

    q = sub.add_parser("scaling", help="which rule maps values to shape sizes? LF for smallest→largest")
    q.add_argument("--values", nargs="+", type=float, required=True)
    q.add_argument("--sizes", nargs="+", type=float, required=True, help="measured sizes, same order as --values")
    q.add_argument("--measure", choices=sorted(MEASURE_POWER), default="diameter")

    q = sub.add_parser("time", help="check time labels drawn at given (or equal) spacing")
    q.add_argument("labels", nargs="+")
    q.add_argument("--positions", nargs="+", type=float)

    q = sub.add_parser("image", help="what a PNG/JPG alone can tell")
    q.add_argument("path")
    q = sub.add_parser("blobs", help="measure coloured shapes in an image (pixels)")
    q.add_argument("path")
    q.add_argument("--min-px", type=int, default=30, help="ignore regions smaller than this many pixels")
    q.add_argument("--colour", help="measure only this colour (#rrggbb or a matplotlib colour name)")
    q.add_argument("--tol", type=float, default=0.12, help="colour tolerance for --colour (0–1)")
    q = sub.add_parser("figure", help="run a matplotlib script and inspect its figures")
    q.add_argument("script")
    q = sub.add_parser("spec", help="inspect a Vega-Lite spec or Plotly figure JSON")
    q.add_argument("path")

    a = p.parse_args(argv)
    try:
        if a.cmd == "lf" and a.mark in POSITION_MARKS:
            fs = position_mark_findings(a.mark)
        elif a.cmd == "lf":
            if a.bound:
                fs = lf_bound_findings(a.baseline, a.axis_max, a.encoding, tuple(a.ratio) if a.ratio else None)
            elif a.data is None:
                p.error("lf needs --data FIRST SECOND (or --bound when the values cannot be read)")
            else:
                size_encoding = a.measured is not None or ENCODING_POWER[a.encoding] > 1 or a.mark == "shape"
                fs = lf_findings(a.data[0], a.data[1], a.baseline, tuple(a.shown) if a.shown else None, a.encoding,
                                 tuple(a.measured) if a.measured else None, a.measure,
                                 cross_check=cross_check and size_encoding)
        elif a.cmd == "lfmax":
            fs = lfmax_findings(parse_series(a.series), a.baseline, a.encoding, a.mark)
        elif a.cmd == "colours":
            fs = colour_findings(a.path, tuple(a.box) if a.box else None, a.top)
        elif a.cmd == "contrast":
            fs = contrast_findings(a.fg, a.bg, a.size)
        elif a.cmd == "scaling":
            fs = scaling_findings(a.values, a.sizes, a.measure)
        elif a.cmd == "time":
            if a.positions and len(a.positions) != len(a.labels):
                p.error("--positions needs one number per label")
            fs = time_findings(a.labels, a.positions)
        elif a.cmd == "image":
            fs = image_findings(a.path)
        elif a.cmd == "blobs":
            fs = blob_findings(a.path, a.min_px, a.colour, a.tol)
        elif a.cmd == "figure":
            fs = figure_findings(a.script)
        else:
            fs = spec_findings(a.path)
    except ValueError as e:
        print(f"ERROR input: {e}")
        return 2
    return emit(fs, a.json)


def main_chain(argv=None) -> int:
    """Several subcommands in one process: `image a.png --then lf --data 1 2 --then time 2001 2002 2004`."""
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--then" not in argv:
        return main(argv)
    glob = [a for a in argv[:1] if a == "--json"]
    rest = argv[len(glob):]
    parts, cur = [], []
    for a in rest:
        if a == "--then":
            parts.append(cur)
            cur = []
        else:
            cur.append(a)
    parts.append(cur)
    # One Lie Factor per encoding: when `scaling` runs in the same call, an `lf` for a size encoding
    # (measured sizes or an assumed radius rule) is printed as a cross-check, not as a second LF to quote.
    has_scaling = any(part[:1] == ["scaling"] for part in parts)
    code = 0
    for part in parts:
        if not part:
            continue
        print(f"## {' '.join(part)}")
        code = max(code, main(glob + part, cross_check=has_scaling and part[:1] == ["lf"]))
    return code


if __name__ == "__main__":
    sys.exit(main_chain())

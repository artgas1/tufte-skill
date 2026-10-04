# Build recipes — honest defaults in code

Short idioms for the fixes the audit asks for. Run `scripts/tufte_check.py figure <script>` (or
`spec <file.json>`) after drawing.

## matplotlib

**Bars from zero, light grid behind the data, no box**
```python
fig, ax = plt.subplots(figsize=(7.5, 4.5))          # ~1.6 : 1
ax.bar(x, values, color="#4c72b0")
ax.set_ylim(bottom=0)
ax.set_axisbelow(True)
ax.grid(axis="y", color="0.9", linewidth=0.6)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
```
If small differences matter more than magnitude, do not truncate bars — switch to dots
(`ax.plot(values, x, "o")`) on a truncated axis and say so in the axis label.

**Range-frame (VDQI pp. 130–132): the axis line spans only the data**
```python
ax.spines["left"].set_bounds(min(y), max(y))
ax.spines["bottom"].set_bounds(min(x), max(x))
```

**Two measures without a second y-axis**
```python
fig, (a1, a2) = plt.subplots(2, 1, sharex=True, figsize=(8, 5))   # aligned panels
a1.plot(t, price); a1.set_ylabel("Price, $")
a2.plot(t, clients); a2.set_ylabel("Clients, thousands")
# or one axis, both indexed to 100 at the first point:
ax.plot(t, 100 * price / price[0], label="Price")
ax.plot(t, 100 * clients / clients[0], label="Clients")
```

**Real time axis** — pass numbers or datetimes, never strings:
```python
years = [2000, 2005, 2010, 2015, 2020, 2021, 2022]
ax.plot(years, values, "-o")       # spacing now follows elapsed time
```

**Area-honest bubbles and icons** — matplotlib `s` is an area in points²:
```python
ax.scatter(x, y, s=values / values.max() * 400)   # area ∝ value — NOT values**2
# icons: scale each side by sqrt(value) so the area tracks the value
side = base_side * np.sqrt(v / v_max)
```

**Direct labels instead of a legend**
```python
for name, ys, color in series:
    ax.plot(t, ys, color=color)
    ax.annotate(name, (t[-1], ys[-1]), xytext=(4, 0), textcoords="offset points",
                va="center", color=color)
```

**Same category, same colour in every panel**
```python
COLORS = dict(zip(categories, plt.get_cmap("tab10").colors))   # one mapping, reused everywhere
ax.bar(cats, vals, color=[COLORS[c] for c in cats])
```

**Small multiples with a shared scale**
```python
fig, axes = plt.subplots(2, 3, sharex=True, sharey=True, figsize=(9, 5))
for ax, (name, df) in zip(axes.flat, groups):
    ax.plot(df.t, df.v, color="0.2"); ax.set_title(name, fontsize=9, loc="left")
```

**Slopegraph (the two-column table-graphic of VDQI pp. 158–159)**
```python
for name, a, b in rows:
    ax.plot([0, 1], [a, b], color="0.4", marker="o")
    ax.text(-0.03, a, f"{name} {a}", ha="right", va="center")
    ax.text(1.03, b, f"{b}", ha="left", va="center")
ax.set_xticks([0, 1], [year_a, year_b]); ax.set_yticks([])
```

**Sparkline**
```python
fig, ax = plt.subplots(figsize=(1.6, 0.35))
ax.plot(series, color="0.3", linewidth=0.8)
ax.plot(len(series) - 1, series[-1], "o", color="#d62728", markersize=2)
ax.axis("off")
```

**Real money** — deflate before plotting long nominal series, and say which index and base year:
`real = nominal * cpi[base_year] / cpi[year]`, axis label "Price, $ of 2020".

## Plotly

```python
fig.update_yaxes(rangemode="tozero")                       # bars from zero
fig.update_traces(marker_sizemode="area", selector=dict(mode="markers"))   # bubbles by area
fig.update_traces(line_shape="linear")                     # no spline smoothing
fig.update_layout(template="simple_white")                 # light chrome
```
Use `make_subplots(rows=2, shared_xaxes=True)` instead of `yaxis2` with `overlaying`.

## Vega-Lite

```json
{"mark": {"type": "line", "interpolate": "linear"},
 "encoding": {
   "x": {"field": "date", "type": "temporal"},
   "y": {"field": "value", "type": "quantitative", "scale": {"zero": true}},
   "color": {"field": "group", "type": "nominal",
             "scale": {"domain": ["A", "B", "C"], "range": ["#4c72b0", "#dd8452", "#55a868"]}}}}
```
Fix `scale.domain`/`range` once and reuse it in every view so colours stay with categories; use
`"type": "temporal"` (not ordinal) for time.

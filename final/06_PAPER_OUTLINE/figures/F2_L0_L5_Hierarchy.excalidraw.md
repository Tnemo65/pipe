# F2: L0–L5 Hierarchical Context-Aware Threshold Fallback
# StreamDQ — Context Decomposition and Fallback Chain

**Chapter**: 2 (Architecture) — Hierarchical Thresholds
**Type**: Decision hierarchy diagram (Excalidraw)
**Color Palette**:
- L0 (finest): `#1E3A8A` (darkest blue) — most context-specific
- L1: `#2563EB` (dark blue)
- L2: `#3B82F6` (blue)
- L3: `#60A5FA` (light blue)
- L4: `#93C5FD` (lighter blue)
- L5: `#DBEAFE` (lightest blue) — coarsest, always fallback
- Gold: `#E8B949` — physics priors annotation

---

## RECREATION INSTRUCTIONS (Excalidraw UI)

### Canvas Setup
- Canvas: 1100 × 750 px
- Background: white
- Use Rectangle tool for boxes, Arrow tool for decision flow

### Layout: Top-to-bottom decision cascade

#### TOP: Event Input
```
Box: "Event arrives at Flink operator"
x=450, y=20, w=200, h=50
Fill: #F3F4F6, Stroke: #374151
Text: "Raw Event e ∈ Stream"
Font: Computer Modern, 14px
```

#### CONTEXT EXTRACTION (blue box)
```
Box: "Context Extraction"
x=380, y=90, w=340, h=80
Fill: #EFF6FF, Stroke: #00468C (2px)
Text inside (4 smaller boxes stacked):
  D1 Temporal:   hour, weekday/weekend      x=400, y=100, w=150, h=15
  D2 Spatial:    zone_category (airport/downtown/midtown/outer)
  D3 Operational: entity_type (taxi/bus)
  D4 External:   is_holiday [STUB - dashed border]
  D5 Data Char: null_rate, schema_version
Font: 11px
```

#### L0 DECISION NODE
```
Box: "L0: H{hour}_{zone_cat}_{WE|WD}"
x=200, y=200, w=300, h=50
Fill: #1E3A8A (darkest blue), Text: white
Text: "L0: H10_midtown_WD  |  min_samples ≥ 100"
Font: 13px white bold

Diamond below: "count ≥ 100?"
x=300, y=265, w=100, h=40
Fill: #DBEAFE, Stroke: #00468C
```

YES arrow (right): → "YES → Use L0 bounds → P10/P90"
NO arrow (below): ↓ → "NO → Try L1"

#### L1 NODE
```
Box: "L1: {bucket}_{zone_cat}_{WE|WD}"
x=200, y=340, w=300, h=50
Fill: #2563EB (dark blue), Text: white
Text: "L1: morning_midtown_WD  |  min_samples ≥ 50"
Font: 13px white

Diamond: "count ≥ 50?"
YES (right): → "YES → Use L1 bounds"
NO (below): ↓ → "Try L2"
```

#### L2 NODE
```
Box: "L2: {bucket}_{borough}_{WE|WD}"
x=200, y=430, w=300, h=50
Fill: #3B82F6 (blue), Text: white
Text: "L2: morning_Manhattan_WD  |  min_samples ≥ 25"
```

YES: → "Use L2 bounds"
NO: ↓ → "Try L3"

#### L3 NODE
```
Box: "L3: {time_category}"
x=200, y=520, w=300, h=50
Fill: #60A5FA (light blue), Text: black
Text: "L3: morning  |  min_samples ≥ 10"
```

YES: → "Use L3 bounds"
NO: ↓ → "Try L4"

#### L4 NODE
```
Box: "L4: global"
x=200, y=610, w=300, h=50
Fill: #93C5FD (lighter blue), Text: black
Text: "L4: global  |  min_samples ≥ 5"
```

YES: → "Use L4 bounds"
NO: ↓ → "L5 PHYSICS PRIORS"

#### L5 NODE (Gold — Always Fallback)
```
Box: "L5: physics priors"
x=200, y=690, w=300, h=50
Fill: #FEF9C3 (gold), Stroke: #E8B949 (3px gold border)
Text: "L5: [2.0, 100.0] km/h  |  ALWAYS FALLBACK"
Font: 13px bold black
```

#### COVERAGE ANNOTATIONS (right side)
```
Text boxes on right (x=550):
L0: "~2–5% of events"       — #1E3A8A
L1: "~5–15% of events"      — #2563EB
L2: "~15–30% of events"     — #3B82F6
L3: "~30–50% of events"     — #60A5FA
L4: "~20–40% of events"     — #93C5FD
L5: "100% fallback"         — #E8B949

Arrow from each Lx box → its coverage annotation
```

#### D4 STUB ANNOTATION
```
Box with dashed border (x=750, y=100, w=300, h=60)
Fill: #FEF3C7, Stroke: #E8B949, dashed
Text: "D4 (External) is a STUB\nHoliday indicator not implemented"
Font: 11px italic
```

#### CRS BOUNDS ANNOTATION
```
Box (x=750, y=180, w=300, h=80)
Fill: #FEF9C3, Stroke: #E8B949
Text:
"CRS Rules (GPS only):
CRS001: speed ∈ [2.0, 100.0] km/h
CRS002: jump > 400m in 30s
CRS003: dedup, 300s window
CRS001/CRS002: L5 physics priors"
Font: 11px
```

### Arrow Style
- YES paths: solid arrows, rightward
- NO paths: solid arrows, downward
- All arrows: stroke #00468C, 2px

### Legend (bottom-left)
```
Rectangle: x=20, y=680, w=160, h=80
Fill: white, Stroke: #374151
Text:
"Legend:
■ Dark blue = finest context
■ Light blue = coarser context
■ Gold = physics prior (L5)
- - - = D4 stub (future work)"
```

---

## CAPTION

```latex
\caption{L0\u2013L5 hierarchical context-aware threshold fallback. For each event,
the system extracts five context dimensions (D1\u2013D5), constructs the L0 context key
(e.g., H10\_midtown\_WD), and traverses the L0\u2013L4 hierarchy until sufficient
samples are found. Each level provides P10/P90 bounds from rolling windows. If no
level has sufficient samples, L5 physics priors are used as a hard fallback.
L0 provides the finest-grained bounds but covers only 2\u20135\% of events due to
zone-hour sparsity in the NYC TLC dataset. D4 (External, holiday indicator) is a
stub. CRS rules (GPS speed and jump bounds) use L5 physics priors exclusively.}
```

## LaTeX INCLUDE

```latex
\begin{figure}[htbp]
  \centering
  \includesvg[width=0.95\textwidth]{figures/f2_l05_hierarchy.svg}
  \caption{L0\u2013L5 hierarchical context-aware threshold fallback.
    For each event the system extracts five context dimensions (D1\u2013D5),
    constructs the L0 context key, and traverses the L0\u2013L4 hierarchy.
    Each level provides P10/P90 bounds. L5 physics priors are the hard fallback.
    L0 covers only 2\u20135\% of events due to zone-hour sparsity.
    D4 (External) is a stub. CRS rules use L5 physics priors.}
  \label{fig:l05-hierarchy}
\end{figure}
```

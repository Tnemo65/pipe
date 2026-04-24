# F3: Rule Pipeline — SYN → SEM → CRS Data Flow
# StreamDQ — Three-Layer Rule Evaluation Pipeline

**Chapter**: 2 (Architecture) — Rule Taxonomy
**Type**: Data flow / pipeline diagram (Excalidraw)
**Color Palette**:
- SYN: `#00468C` (blue) — Python, record-level
- SEM: `#2563EB` (lighter blue) — Python, plausibility
- CRS: `#E8B949` (gold) — Java, stateful
- TQS: `#6B7280` (gray) — aggregation
- Background: `#FFFFFF` (white)

---

## RECREATION INSTRUCTIONS (Excalidraw UI)

### Canvas Setup
- Canvas: 1200 × 650 px
- Background: white
- Grid: off

### Layout: Left-to-right horizontal flow

#### STEP 0: RAW EVENT (far left)
```
Large box: x=20, y=100, w=140, h=120
Fill: #F3F4F6, Stroke: #374151
Text (stacked):
  "Raw Event"
  ""
  "NYC TLC:\n  trip_id, fare_amount,\n  trip_distance, lat?, lon?"
  ""
  "NYC MTA Bus:\n  vehicle_id, lat, lon, ts"
Font: 12px, centered
```

#### STEP 1: CONTEXT EXTRACTION (left)
```
Box: x=180, y=100, w=120, h=120
Fill: #EFF6FF, Stroke: #00468C
Text:
  "Context\nExtraction"
  ""
  "hour, zone_cat\nborough\nentity_type"
Font: 12px, centered
```

#### STEP 2: THRESHOLD LOOKUP (BroadcastState)
```
Box: x=320, y=100, w=120, h=120
Fill: #EFF6FF, Stroke: #00468C
Text:
  "Threshold\nLookup"
  "(BroadcastState)"
  ""
  "O(1) amortized"
Font: 12px, centered
Note: dashed border to indicate state lookup
```

#### STEP 3A: SYN RULES (blue, top path)
```
Box: x=480, y=30, w=160, h=100
Fill: #DBEAFE, Stroke: #00468C
Text:
  "SYN Rules (Python)"
  "━━━━━━━━━━━━━━━━━"
  "SYN001: NULL/NaN check\n"
  "SYN002: fare ≥ 0\n"
  "SYN003: lat/lon in bounds"
Font: 11px, centered
```

#### STEP 3B: SEM RULES (lighter blue, middle path)
```
Box: x=480, y=150, w=160, h=100
Fill: #DBEAFE, Stroke: #2563EB
Text:
  "SEM Rules (Python)"
  "━━━━━━━━━━━━━━━━━"
  "SEM001: fare > P90 (ctx)\n"
  "SEM002: dist > P90 (ctx)\n"
  "SEM003: tip > 50% fare\n"
  "GTFSSem002: stale > 5min"
Font: 11px, centered
```

#### STEP 3C: CRS RULES (gold, bottom path — separate box)
```
Box: x=480, y=280, w=160, h=100
Fill: #FEF9C3, Stroke: #E8B949, strokeWidth=3
Text:
  "CRS Rules (Java)"
  "━━━━━━━━━━━━━━━━━"
  "CRS001: speed [2,100] km/h\n"
  "CRS002: jump >400m/30s\n"
  "CRS003: dedup 300s window"
Font: 11px, bold, centered
Note: "GPS events only"
Note2: "gRPC call from Flink"
```

#### GPS FILTER (diamond before CRS)
```
Diamond: x=440, y=310, w=80, h=40
Fill: #FEF9C3, Stroke: #E8B949
Text: "GPS?\nlat/lon?"
Font: 10px
YES arrow down: → CRS rules
NO arrow right: → Skip CRS
```

#### STEP 4: TQS AGGREGATOR (right side, gray)
```
Box: x=700, y=130, w=140, h=120
Fill: #F3F4F6, Stroke: #6B7280
Text:
  "TQS Aggregator"
  "━━━━━━━━━━━━━━━━"
  "Tm (Timeliness)\n"
  "Cn (Completeness)\n"
  "Ac (Accuracy)\n"
  "Cs (Consistency)\n"
  "Uv (Uniqueness)"
Font: 11px, centered
```

#### STEP 5: VIOLATION EMIT (far right)
```
Box: x=900, y=100, w=140, h=120
Fill: #FEE2E2, Stroke: #DC2626
Text:
  "Violation Emit"
  "━━━━━━━━━━━━━━━━"
  "rule_id, entity_id\n"
  "severity\n"
  "processing_latency_ms\n"
  "record_snapshot"
Font: 11px, centered
```

#### ARROWS (horizontal flow)
```
Event → Context: arrow x=160→180, y=160
Context → Threshold: arrow x=300→320, y=160
Threshold → SYN: arrow up to SYN
Threshold → SEM: arrow to SEM
Threshold → CRS: arrow down to CRS filter
SYN → TQS: arrow right, below SEM
SEM → TQS: arrow right
CRS → TQS: arrow right (parallel)
TQS → Violation: arrow right
```

#### PARALLEL PATHS ANNOTATION
```
Text: x=500, y=240
Text: "All paths run in parallel"
Font: 10px italic, #6B7280
Dashed line connecting SYN→TQS, SEM→TQS, CRS→TQS
```

#### LAYER LABELS (left side)
```
Text box: x=20, y=30, w=100, h=30
Fill: #00468C, Text: "Layer 1: Context"
Font: 12px white

Text box: x=480, y=5, w=160, h=25
Fill: #00468C, Text: "Layer 2: Rule Evaluation"
Font: 12px white

Text box: x=700, y=105, w=140, h=25
Fill: #6B7280, Text: "Layer 3: TQS"
Font: 12px white

Text box: x=900, y=75, w=140, h=25
Fill: #DC2626, Text: "Layer 4: Violations"
Font: 12px white
```

#### DATASET ANNOTATIONS
```
Box: x=20, y=240, w=140, h=40
Fill: #DBEAFE, Stroke: #00468C
Text: "NYC TLC: SYN/SEM only\nCRS: not applicable"
Font: 10px

Box: x=20, y=290, w=140, h=40
Fill: #FEF9C3, Stroke: #E8B949
Text: "NYC MTA Bus: SYN/SEM/CRS\nAll rules applicable"
Font: 10px
```

#### ML PHASE 3 NOTE (bottom)
```
Box: x=480, y=400, w=360, h=50
Fill: #EDE9FE, Stroke: #7C3AED, dashed
Text: "ML Phase 3 (async, out-of-band): BO calibrates thresholds hourly;\nIsolation Forest scores anomaly confidence → adjusts effective_k"
Font: 10px
Arrow from box → TQS (dashed arrow)
```

---

## CAPTION

```latex
\caption{StreamDQ rule evaluation pipeline. Raw events from NYC TLC (zone-level)
and NYC MTA Bus (GPS) flow through context extraction and threshold lookup
(BroadcastState, O(1) amortized). SYN rules (Python, blue) evaluate record-level
constraints; SEM rules (Python, lighter blue) evaluate plausibility with
context-aware thresholds; CRS rules (Java, gold) evaluate cross-record GPS
constraints via gRPC. All three layers run in parallel; CRS rules require GPS
coordinates and are skipped for NYC TLC zone-level events. TQS aggregates five
quality dimensions per context cell. Violations are emitted with full metadata
and routed to PostgreSQL. ML Phase 3 (dashed, async) calibrates thresholds
hourly; rules remain authoritative.}
```

## LaTeX INCLUDE

```latex
\begin{figure}[htbp]
  \centering
  \includesvg[width=0.95\textwidth]{figures/f3_rule_pipeline.svg}
  \caption{StreamDQ rule evaluation pipeline. Events flow through context extraction,
    threshold lookup, and three parallel rule layers (SYN/SEM in Python, CRS in Java
    via gRPC). CRS rules require GPS coordinates and apply to NYC MTA Bus only.
    TQS aggregates five quality dimensions. Violations are emitted with metadata.
    ML Phase 3 (dashed) calibrates thresholds asynchronously.}
  \label{fig:rule-pipeline}
\end{figure}
```

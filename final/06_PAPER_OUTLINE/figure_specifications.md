# Figure Specifications

**Project**: A Context-Aware Framework for Streaming Data Quality Monitoring
**Step**: Step 11 — Figure Specifications (Revised)
**Date**: April 24, 2026
**Sources**: Steps 1–10 output documents; thesis template

---

## Overview

Figures are numbered sequentially: F1–F8. All figures follow publication standards: 300 DPI minimum, PDF/SVG preferred, consistent color palette, descriptive captions.

**Color palette**: Use a consistent 4-color palette:
- Primary: `#00468C` (VNU blue)
- Secondary: `#265499` (lighter blue)
- Accent: `#E8B949` (gold)
- Neutral: `#6B7280` (gray)

**Font**: Computer Modern or Latin Modern (LaTeX standard)
**Format**: SVG + PDF (architecture); PNG + PDF (charts)
**Caption style**: "Figure N: [Descriptive title]. [Key insight in 1–2 sentences.]"

---

## F1: Overall System Architecture

**Chapter**: 2 (Architecture) — System Overview
**Status**: Needed
**Type**: Architecture diagram (Excalidraw)

### Content

```
┌──────────────────────────────────────────────────────────────────┐
│                     STREAMDQ SYSTEM ARCHITECTURE                   │
│                   A Context-Aware Framework for                    │
│               Streaming Data Quality Monitoring                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────┐              ┌─────────────────────────┐   │
│  │ NYC TLC Yellow  │              │  NYC MTA Bus            │   │
│  │ Taxi Data       │              │  GTFS-realtime Feed     │   │
│  │ (Parquet Replay)│              │  (Live GPS, 30s updates)│   │
│  │ Zone-level only │              │  Real GPS coordinates    │   │
│  │ No raw GPS      │              │                        │   │
│  └────────┬────────┘              └───────────┬────────────┘   │
│           │                                   │                  │
│           ▼                                   ▼                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              APACHE KAFKA (Message Broker)               │   │
│  │     Topics: taxi_raw_events, bus_raw_events              │   │
│  │     replay_topic (controlled injection)                   │   │
│  └────────────────────────────┬────────────────────────────┘   │
│                               │                                 │
│                               ▼                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           APACHE FLINK (Streaming Engine)               │   │
│  │                                                          │   │
│  │  ┌──────────────────────────────────────────────────┐   │   │
│  │  │            RULE EVALUATION PIPELINE               │   │   │
│  │  │                                                   │   │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌──────────┐  │   │   │
│  │  │  │ SYN Rules   │  │ SEM Rules   │  │ CRS Rules│  │   │   │
│  │  │  │ (Python)    │  │ (Python)    │  │ (Java)   │  │   │   │
│  │  │  │ SYN001-003  │  │ SEM001-003  │  │ CRS001-  │  │   │   │
│  │  │  │             │  │ GTFSSem002  │  │ 003      │  │   │   │
│  │  │  └─────────────┘  └─────────────┘  └────┬─────┘  │   │   │
│  │  │                                           │        │   │   │
│  │  │                              ┌────────────▼────┐    │   │   │
│  │  │                              │   TQS Aggregator │    │   │   │
│  │  │                              │   Tm,Cn,Ac,Cs,Uv │    │   │   │
│  │  │                              └────────────┬────┘    │   │   │
│  │  └───────────────────────────────────────────┼────────┘   │   │
│  │                                                  │        │   │
│  │  ┌──────────────────────────────────────────────▼──┐    │   │
│  │  │         ML AUGMENTATION LAYER (Phase 3)         │    │   │
│  │  │  BO (Priority 1) → IF (Priority 2, conditional)│    │   │
│  │  │  Rules remain AUTHORITATIVE                     │    │   │
│  │  └──────────────────────────────────────────────────┘    │   │
│  └────────────────────────────┬────────────────────────────┘   │
│                                 │                                 │
│           ┌─────────────────────┼─────────────────────┐         │
│           ▼                     ▼                     ▼         │
│  ┌─────────────┐       ┌─────────────┐       ┌─────────────┐   │
│  │ PostgreSQL │       │ Prometheus  │       │ ML Service  │   │
│  │ Violations │       │ Metrics    │       │ (gRPC RPC)  │   │
│  │ + Ground   │       │ + TQS      │       │ Phase 3     │   │
│  │   Truth    │       │   Scores   │       │             │   │
│  └─────────────┘       └──────┬──────┘       └─────────────┘   │
│                                │                              │
│                                ▼                              │
│                         ┌────────────┐                       │
│                         │  Grafana   │                       │
│                         │ Dashboard  │                       │
│                         │ (Real-time)│                       │
│                         └────────────┘                       │
└──────────────────────────────────────────────────────────────────┘
```

### Design Notes
- Rectangles for components, arrows for data flow
- Python components: blue (`#00468C`); Java components: gold (`#E8B949`)
- Flink box is the central hub
- Arrow labels: Kafka → Flink (<10ms), Flink → sinks (<50ms)
- Show two datasets clearly: NYC TLC (no GPS) vs NYC MTA Bus (GPS)
- ML layer shown as dashed border (Phase 3 — conditional)

### Caption
> **Figure 1: StreamDQ overall system architecture.** Events flow from NYC TLC Yellow Taxi (parquet replay, zone-level) and NYC MTA Bus GTFS-realtime (live GPS, 30s updates) through Apache Kafka into Apache Flink. SYN/SEM rules (Python) evaluate all events; CRS rules (Java, gRPC) evaluate GPS events. Violations are stored in PostgreSQL with ground-truth labels, metrics exported to Prometheus, and ML inference (Phase 3) runs as async gRPC. Grafana provides real-time dashboards.

### LaTeX Include
```latex
\begin{figure}[htbp]
  \centering
  \includesvg[width=0.95\textwidth]{figures/f1_system_architecture.svg}
  \caption{StreamDQ overall system architecture. Events flow from NYC TLC Yellow Taxi
    (parquet replay, zone-level) and NYC MTA Bus GTFS-realtime (live GPS, 30s updates)
    through Apache Kafka into Apache Flink. SYN/SEM rules (Python) evaluate all events;
    CRS rules (Java, gRPC) evaluate GPS events. Violations are stored in PostgreSQL,
    metrics exported to Prometheus, and ML inference (Phase 3) runs as async gRPC.}
  \label{fig:system-architecture}
\end{figure}
```

---

## F2: Layered Architecture

**Chapter**: 2 (Architecture) — System Overview
**Status**: Needed
**Type**: Layer diagram (Excalidraw)

### Content

```
┌─────────────────────────────────────────────────────────────────┐
│               STREAMDQ LAYERED ARCHITECTURE                       │
│                    (from data to insight)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  LAYER 4: MONITORING & ALERTING                         │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌──────────┐  │   │
│  │  │ Grafana        │  │ Prometheus      │  │ Alert    │  │   │
│  │  │ Dashboards     │  │ Metrics Export  │  │ Rules    │  │   │
│  │  └────────────────┘  └────────────────┘  └──────────┘  │   │
│  └────────────────────────────────────┬───────────────────────┘   │
│                                       │                           │
│  ┌────────────────────────────────────▼───────────────────────┐   │
│  │  LAYER 3: TRAJECTORY QUALITY SCORING (TQS)                 │   │
│  │                                                           │   │
│  │  TQS = α·Tm + β·Cn + γ·Ac + δ·Cs + ε·Uv                  │   │
│  │                                                           │   │
│  │  V2 Weights: α=0.25, β=0.20, γ=0.25, δ=0.10, ε=0.20      │   │
│  └────────────────────────────────────┬───────────────────────┘   │
│                                       │                           │
│  ┌────────────────────────────────────▼───────────────────────┐   │
│  │  LAYER 2: RULE EVALUATION                                  │   │
│  │                                                           │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │ SYN Layer (Python)    │ SEM Layer (Python)          │  │   │
│  │  │ SYN001: NULL/NaN      │ SEM001: fare > P90 (ctx)    │  │   │
│  │  │ SYN002: neg fare     │ SEM002: dist > P90 (ctx)    │  │   │
│  │  │ SYN003: out-of-bounds│ SEM003: tip > 50% fare     │  │   │
│  │  │                      │ GTFSSem002: stale > 5min   │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │                         │                                 │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │ CRS Layer (Java, gRPC)                             │  │   │
│  │  │ CRS001: GPS speed [0.5, 100] km/h + 60s           │  │   │
│  │  │ CRS002: GPS jump > 400m / 30s                     │  │   │
│  │  │ CRS003: duplicate hash, 300s window               │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  └────────────────────────────────────┬───────────────────────┘   │
│                                       │                           │
│  ┌────────────────────────────────────▼───────────────────────┐   │
│  │  LAYER 1: CONTEXT-AWARE THRESHOLDS (L0–L5)                 │   │
│  │                                                           │   │
│  │     L0: H{hour}_{zone}_{WE|WD}  (≥100 samples)            │   │
│  │         ↓ insufficient                                     │   │
│  │     L1: bucket_zone_{WE|WD}    (≥50 samples)              │   │
│  │         ↓ insufficient                                     │   │
│  │     L2: bucket_boro_{WE|WD}   (≥25 samples)               │   │
│  │         ↓ insufficient                                     │   │
│  │     L3: time_category          (≥10 samples)               │   │
│  │         ↓ insufficient                                     │   │
│  │     L4: global               (≥5 samples)                  │   │
│  │         ↓ insufficient                                     │   │
│  │     L5: physics priors       (≥0 samples) ← ALWAYS FALLBACK│   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  LAYER 0: DATA INGESTION                                 │   │
│  │  ┌─────────────────────┐  ┌────────────────────────────┐  │   │
│  │  │ Kafka Consumer     │  │ Synthetic Anomaly Injector  │  │   │
│  │  │ (Flink Connector)  │  │ (Ground Truth Generator)   │  │   │
│  │  └─────────────────────┘  └────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

### Design Notes
- 4 distinct layers, clearly labeled with layer numbers
- Layer 0 (bottom) = data; Layer 4 (top) = insight
- SYN/SEM: blue; CRS: gold; TQS: neutral; Monitoring: gray
- L0–L5 shown as downward cascade (fallback hierarchy)
- ML layer (Phase 3) not shown here — shown in F5

### Caption
> **Figure 2: StreamDQ layered architecture.** Layer 0 (data ingestion) feeds raw events from Kafka. Layer 1 (context-aware thresholds) applies L0–L5 hierarchical thresholds to determine rule bounds. Layer 2 (rule evaluation) runs SYN/SEM rules (Python) and CRS rules (Java) against events. Layer 3 (TQS) aggregates five quality dimensions. Layer 4 (monitoring) exports metrics to Prometheus/Grafana. All CRS rules operate on GPS coordinates; SYN/SEM rules operate on all events.

### LaTeX Include
```latex
\begin{figure}[htbp]
  \centering
  \includesvg[width=0.95\textwidth]{figures/f2_layered_architecture.svg}
  \caption{StreamDQ layered architecture. Layer 0 (data ingestion) feeds raw events.
    Layer 1 (context-aware thresholds) applies L0\u2013L5 hierarchical thresholds.
    Layer 2 (rule evaluation) runs SYN/SEM rules (Python) and CRS rules (Java).
    Layer 3 (TQS) aggregates five quality dimensions.
    Layer 4 (monitoring) exports metrics to Prometheus/Grafana.}
  \label{fig:layered-architecture}
\end{figure}
```

---

## F3: Data Flow Diagram

**Chapter**: 2 (Architecture) — Rule Taxonomy
**Status**: Needed
**Type**: Data flow diagram (Excalidraw)

### Content

```
┌─────────────────────────────────────────────────────────────────────┐
│                      STREAMDQ DATA FLOW DIAGRAM                      │
│                   (from event ingestion to output)                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ EVENT INGESTION                                                  │  │
│  │                                                                  │  │
│  │  NYC TLC Taxi Event              NYC MTA Bus Event              │  │
│  │  {passenger_count, fare_amount,         {vehicle_id,             │  │
│  │   trip_distance, tip_amount,             lat, lon,               │  │
│  │   PULocationID, DOLocationID,           timestamp,              │  │
│  │   tpep_pickup_datetime}                  trip_id}               │  │
│  │         │                                    │                  │  │
│  │         └────────────┬────────────────────────┘                  │  │
│  │                      ▼                                          │  │
│  │              Raw Event Stream                                    │  │
│  │              (Kafka Topic: raw_events)                          │  │
│  └─────────────────────┬────────────────────────────────────────────┘  │
│                        │                                               │
│                        ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ CONTEXT EXTRACTION                                               │  │
│  │                                                                  │  │
│  │  Extract: hour, weekday/weekend, zone_category,                  │  │
│  │           borough, entity_type                                   │  │
│  │                                                                  │  │
│  │  context_key = H{hour}_{zone_cat}_{WE|WD}  ← L0 key           │  │
│  └─────────────────────┬───────────────────────────────────────────┘  │
│                        │                                              │
│                        ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ THRESHOLD LOOKUP (BroadcastState)                                │  │
│  │                                                                  │  │
│  │  L0 lookup: count ≥ 100? → P10, P90 from 1h window             │  │
│  │  Else L1: count ≥ 50?  → broader bucket                        │  │
│  │  Else L2: count ≥ 25?  → borough level                         │  │
│  │  Else L3: count ≥ 10?  → time category                        │  │
│  │  Else L4: count ≥ 5?   → global P10/P90                       │  │
│  │  Else L5: count < 5    → physics priors [0.5, 100] km/h       │  │
│  └─────────────────────┬───────────────────────────────────────────┘  │
│                        │                                              │
│           ┌────────────┴────────────┐                               │
│           ▼                         ▼                               │
│  ┌─────────────────────┐    ┌─────────────────────┐                │
│  │  SYNTACTIC LAYER   │    │   SEMANTIC LAYER   │                │
│  │   (SYN001–SYN003)  │    │  (SEM001–SEM003)  │                │
│  │                    │    │   + GTFSSem002     │                │
│  │                    │    │                    │                │
│  │ SYN001: required   │    │ SEM001: fare > P90 │                │
│  │ fields NULL?       │    │ (context-aware)    │                │
│  │                    │    │                    │                │
│  │ SYN002: fare < 0?  │    │ SEM002: dist > P90 │                │
│  │                    │    │ (context-aware)    │                │
│  │ SYN003: lat/lon    │    │                    │                │
│  │ outside NYC box?   │    │ SEM003: tip > 50% │                │
│  └────────┬────────────┘    └─────────┬───────────┘                │
│           │                         │                             │
│           └────────────┬────────────┘                             │
│                        │                                           │
│                        ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ CROSS-RECORD LAYER (Java via gRPC)                               │  │
│  │  (GPS events only — NYC MTA Bus)                                 │  │
│  │                                                                  │  │
│  │  CRS001: speed = dist / Δt  < 0.5 km/h AND Δt > 60s?           │  │
│  │         OR > 100 km/h?  → VIOLATION                            │  │
│  │                                                                  │  │
│  │  CRS002: dist > 400m in 30s?  → VIOLATION                      │  │
│  │                                                                  │  │
│  │  CRS003: SHA256(event) seen in 300s window?  → VIOLATION        │  │
│  │                                                                  │  │
│  │  [async gRPC call, 50ms timeout, fallback = pass]               │  │
│  └─────────────────────┬───────────────────────────────────────────┘  │
│                        │                                              │
│                        ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ VIOLATION EMISSION                                               │  │
│  │                                                                  │  │
│  │  Violation = {                                                   │  │
│  │    rule_id, entity_id, severity,                                 │  │
│  │    violation_type, details{}, record_snapshot,                   │  │
│  │    detected_at, processing_latency_ms                            │  │
│  │  }                                                               │  │
│  └─────────────┬───────────────────────────────────────────────────┘  │
│                │                                                        │
│  ┌─────────────┼───────────────────────┐                              │
│  ▼             ▼                       ▼                              │
│ PostgreSQL  Prometheus              ML Service                        │
│ violations  counters               (Phase 3)                         │
│ + gt_labels  + TQS                                           │
└─────────────────────────────────────────────────────────────────────┘
```

### Design Notes
- Show the flow clearly: event → context → threshold → rules → violation
- Use swimlanes or zones to separate layers
- Color code: SYN = blue, SEM = lighter blue, CRS = gold
- gRPC call shown as dotted arrow (async)
- Timeout/fallback shown explicitly
- Two paths before CRS layer: SYN/SEM (all events) vs CRS (GPS only)

### Caption
> **Figure 3: StreamDQ data flow diagram.** Raw events from NYC TLC (zone-level) and NYC MTA Bus (GPS) flow through context extraction, threshold lookup (L0\u2013L5 hierarchy), and three rule layers. SYN/SEM rules (Python) evaluate all events; CRS rules (Java, gRPC) evaluate GPS events only. Violations are emitted with full metadata and routed to PostgreSQL (storage), Prometheus (metrics), and the ML service (Phase 3 calibration).

### LaTeX Include
```latex
\begin{figure}[htbp]
  \centering
  \includesvg[width=0.95\textwidth]{figures/f3_data_flow.svg}
  \caption{StreamDQ data flow. Raw events flow through context extraction,
    threshold lookup (L0\u2013L5 hierarchy), and three rule layers.
    SYN/SEM rules (Python) evaluate all events; CRS rules (Java, gRPC)
    evaluate GPS events only. Violations are emitted with metadata
    and routed to PostgreSQL, Prometheus, and ML service.}
  \label{fig:data-flow}
\end{figure}
```

---

## F4: Context-Aware Decision Flow

**Chapter**: 2 (Architecture) — Hierarchical Thresholds
**Status**: Needed
**Type**: Decision flowchart (Excalidraw)

### Content

```
┌─────────────────────────────────────────────────────────────────┐
│              CONTEXT-AWARE DECISION FLOW                          │
│            (How an event gets evaluated)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ STEP 1: Event arrives at Flink operator                   │    │
│  │          Extract: entity_id, lat, lon, ts, fields...     │    │
│  └────────────────────────────┬────────────────────────────┘    │
│                               ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ STEP 2: Context dimensions extracted                      │    │
│  │                                                          │    │
│  │  D1 Temporal:  hour = extract_hour(ts)                   │    │
│  │               is_weekend = (day ∈ {Sat, Sun})           │    │
│  │                                                          │    │
│  │  D2 Spatial:   zone = lookup_zone(PULocationID)           │    │
│  │               category = zone.category  {airport,         │    │
│  │                                        downtown,          │    │
│  │                                        midtown, outer}    │    │
│  │                                                          │    │
│  │  D3 Operational: entity_type = "taxi" | "bus"            │    │
│  │                                                          │    │
│  │  D4 External:   is_holiday = holiday_lookup(date)  [STUB]│    │
│  │                                                          │    │
│  │  D5 Data Char:  null_rate, schema_version                │    │
│  └────────────────────────────┬────────────────────────────┘    │
│                               ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ STEP 3: Context key lookup (BroadcastState)              │    │
│  │                                                          │    │
│  │  L0 key = "H{hour}_{zone_category}_{WE|WD}"             │    │
│  │           e.g., "H10_midtown_WD"                        │    │
│  │                                                          │    │
│  │  Check: count ≥ 100?                                    │    │
│  └────────────────────┬───────────────────────────────────┘    │
│                       │                                           │
│           ┌───────────┴───────────┐                              │
│           ▼                       ▼                              │
│      YES (≥100)            NO (<100)                             │
│           │                       │                              │
│           ▼                       ▼                              │
│    ┌────────────────┐     ┌────────────────────┐               │
│    │ Use L0 bounds  │     │ Check L1 count      │               │
│    │ P10/P90 from   │     │ bucket_zone_WD      │               │
│    │ 1h window      │     │ ≥50?               │               │
│    │                │     └─────────┬──────────┘               │
│    │ Context: finest│               │                         │
│    └───────┬────────┘       ┌────────┴────────┐                │
│            │              YES│            NO│                  │
│            │                ▼              ▼                    │
│            │          ┌──────────┐   ┌─────────────┐           │
│            │          │ Use L1   │   │ Check L2... │           │
│            │          │ bounds   │   │ ≥25?        │           │
│            │          └────┬─────┘   └──────┬──────┘           │
│            │               │             ┌──┴────────┐         │
│            │               │        YES │       NO │           │
│            │               │            ▼           ▼          │
│            │               │        ┌───────┐ ┌──────────┐     │
│            │               │        │ Use L2│ │ Check L3 │     │
│            │               │        └───┬───┘ └────┬────┘     │
│            │               │            │        ┌─┴────┐    │
│            │               │            │     YES│    NO│     │
│            │               │            │        ▼      ▼      │
│            │               │        ┌───────┐ ┌─────┐ ┌─────┐  │
│            │               │        │ Use L3│ │L4 ok│ │L5!  │  │
│            │               │        └───┬───┘ └──┬──┘ │HARD │  │
│            │               │            │        │    │BOUND│  │
│            │               │            └────────┴────┴──┬──┘  │
│            │               │                           │       │
│            └───────────────┼───────────────────────────┘       │
│                            ▼                                     │
│                 ┌─────────────────────┐                          │
│                 │ STEP 4: Apply bounds │                          │
│                 │ to rule evaluation   │                          │
│                 │                     │                          │
│                 │ e.g., SYN001: P90  │                          │
│                 │      = $45 for      │                          │
│                 │      H10_midtown_WD │                          │
│                 │ (L0 finest context)│                          │
│                 └──────────┬──────────┘                          │
│                            │                                       │
│                            ▼                                       │
│                 ┌─────────────────────┐                            │
│                 │ STEP 5: Emit result │                           │
│                 │ Violation or PASS   │                            │
│                 │ + update rolling    │                            │
│                 │ window counts       │                            │
│                 └─────────────────────┘                            │
└──────────────────────────────────────────────────────────────────┘
```

### Design Notes
- Show decision cascade clearly (L0 → L1 → L2 → L3 → L4 → L5)
- Color gradient: L0 = darkest blue (finest), L5 = lightest (coarsest)
- Stub (D4 External) shown with dashed border
- Each level shows its min_samples threshold
- Final step shows how bounds feed into rule evaluation

### Caption
> **Figure 4: Context-aware decision flow.** For each event, the system extracts context dimensions (D1\u2013D5), constructs the L0 context key, and traverses the L0\u2013L5 hierarchy until it finds a level with sufficient samples. Each level provides P10/P90 bounds from rolling windows. If no level has sufficient samples, L5 physics priors ([0.5, 100] km/h for GPS) are used as a hard fallback. D4 (External, holiday) is a stub. L0 provides the finest-grained bounds but covers only 2\u20135% of events due to NYC TLC zone-hour sparsity.

### LaTeX Include
```latex
\begin{figure}[htbp]
  \centering
  \includesvg[width=0.95\textwidth]{figures/f4_context_decision_flow.svg}
  \caption{Context-aware decision flow. For each event, the system extracts context
    dimensions (D1\u2013D5), constructs the L0 context key, and traverses the L0\u2013L5
    hierarchy until a level with sufficient samples is found. If no level has sufficient
    samples, L5 physics priors are used as a hard fallback. D4 (External, holiday)
    is a stub. L0 covers only 2\u20135\% of events due to zone-hour sparsity.}
  \label{fig:context-decision-flow}
\end{figure}
```

---

## F5: Rule Taxonomy / Data Quality Dimensions Map

**Chapter**: 2 (Architecture) — Rule Taxonomy
**Status**: Ready (from FORMULATION.md)
**Type**: Taxonomy diagram (Excalidraw or structured table-as-figure)

### Content

```
┌──────────────────────────────────────────────────────────────────────────┐
│               STREAMDQ RULE TAXONOMY & DATA QUALITY DIMENSIONS             │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │                     DATA QUALITY DIMENSIONS                          │   │
│  │   (Redman 1998; Otto et al.)                                        │   │
│  │                                                                      │   │
│  │   Completeness   Validity   Timeliness   Consistency   Uniqueness  │   │
│  │   (Cn)           (Vl)       (Tm)         (Cs)         (Uv)          │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                   │                                       │
│                                   ▼                                       │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │                      RULE TAXONOMY                                  │   │
│  │                                                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │ SYN: SYNTACTIC LAYER (Record-level, Python)                  │   │   │
│  │  │                                                            │   │   │
│  │  │  SYN001: Completeness — NULL/NaN in required fields         │   │   │
│  │  │           → dimension: Cn (Completeness)                   │   │   │
│  │  │                                                            │   │   │
│  │  │  SYN002: Validity — negative fare_amount                    │   │   │
│  │  │           → dimension: Vl (Validity)                        │   │   │
│  │  │                                                            │   │   │
│  │  │  SYN003: Validity — lat/lon outside NYC bounding box        │   │   │
│  │  │           → dimension: Vl (Validity)                        │   │   │
│  │  │                                                            │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                               │                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │ SEM: SEMANTIC LAYER (Plausibility, Python)                  │   │   │
│  │  │  Bounds: context-aware (L0–L4) or physics priors (L5)       │   │   │
│  │  │                                                            │   │   │
│  │  │  SEM001: Accuracy — fare_amount > P90 (ctx-aware)           │   │   │
│  │  │           → dimension: Ac (Accuracy)                        │   │   │
│  │  │                                                            │   │   │
│  │  │  SEM002: Accuracy — trip_distance > P90 (ctx-aware)         │   │   │
│  │  │           → dimension: Ac (Accuracy)                        │   │   │
│  │  │                                                            │   │   │
│  │  │  SEM003: Consistency — tip_amount > 50% of fare_amount      │   │   │
│  │  │           → dimension: Cs (Consistency)                     │   │   │
│  │  │                                                            │   │   │
│  │  │  GTFSSem002: Timeliness — position stale > 5 min            │   │   │
│  │  │              → dimension: Tm (Timeliness)                   │   │   │
│  │  │                                                            │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                               │                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │ CRS: CROSS-RECORD LAYER (Stateful, Java via gRPC)           │   │   │
│  │  │  Dataset: NYC MTA Bus GPS events only                       │   │   │
│  │  │                                                            │   │   │
│  │  │  CRS001: Consistency — GPS speed ∉ [0.5, 100] km/h        │   │   │
│  │  │             + 60s sustained violation requirement           │   │   │
│  │  │             → dimension: Cs (Consistency)                  │   │   │
│  │  │             Note: GPS error ±3–5m → apparent speed 0.3–1.2 │   │   │
│  │  │                   km/h avoided by 0.5 km/h + 60s rule      │   │   │
│  │  │                                                            │   │   │
│  │  │  CRS002: Consistency — GPS jump > 400m in 30s              │   │   │
│  │  │             → dimension: Cs (Consistency)                  │   │   │
│  │  │             Note: 400m >> GPS noise floor (~10m)           │   │   │
│  │  │                                                            │   │   │
│  │  │  CRS003: Uniqueness — duplicate SHA256 hash in 300s window │   │   │
│  │  │             → dimension: Uv (Uniqueness)                   │   │   │
│  │  │             Note: [TIER-3 UNMEASURABLE] — NG-4 blocker    │   │   │
│  │  │                                                            │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  └────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
```

### Design Notes
- Map each rule to its corresponding DQ dimension
- Color code layers: SYN = blue, SEM = lighter blue, CRS = gold
- CRS rules clearly labeled as NYC MTA Bus GPS only
- CRS003 shown with strikethrough or dashed border (UNMEASURABLE)
- GPS error notes shown as annotations on CRS001 and CRS002

### Caption
> **Figure 5: StreamDQ rule taxonomy mapped to data quality dimensions.** Three layers: SYN (syntactic, record-level), SEM (semantic, plausibility), CRS (cross-record, stateful, Java). Each rule maps to a Redman/Otto data quality dimension: Completeness (Cn), Validity (Vl), Timeliness (Tm), Accuracy (Ac), Consistency (Cs), Uniqueness (Uv). CRS rules require GPS coordinates and are evaluated on NYC MTA Bus only. CRS003 is Tier 3\u2014Unmeasurable due to replay suppression gate (NG-4).

### LaTeX Include
```latex
\begin{figure}[htbp]
  \centering
  \includesvg[width=0.95\textwidth]{figures/f5_rule_taxonomy.svg}
  \caption{StreamDQ rule taxonomy mapped to data quality dimensions.
    Three layers: SYN (syntactic), SEM (semantic), CRS (cross-record, Java).
    Each rule maps to a data quality dimension (Redman/Otto).
    CRS rules require GPS coordinates and are evaluated on NYC MTA Bus only.
    CRS003 is Tier 3\u2014Unmeasurable due to replay suppression gate (NG-4).}
  \label{fig:rule-taxonomy}
\end{figure}
```

---

## F6: Sequence Diagram

**Chapter**: 2 (Architecture) — CRS Rules / ML Augmentation
**Status**: Needed
**Type**: Sequence diagram (Excalidraw)

### Content

```
┌─────────────────┐   ┌──────────────────┐   ┌────────────────────┐   ┌────────────────┐
│  Kafka Topic    │   │  Flink Python    │   │  Flink JVM         │   │  Java gRPC     │
│  (raw_events)   │   │  Operator        │   │  KeyedProcess       │   │  Service       │
│                 │   │  (SYN/SEM)       │   │  Function           │   │  (CRS Rules)   │
└────────┬────────┘   └────────┬─────────┘   └──────────┬─────────┘   └───────┬────────┘
         │                      │                        │                      │
         │ emitRawEvent()       │                        │                      │
         │──────────────────────►                        │                      │
         │                      │                        │                      │
         │                      │ processElement()       │                      │
         │                      │───────────────────────►│                      │
         │                      │                        │                      │
         │                      │                        │ SYN/SEM evaluate()   │
         │                      │                        │ [pass or violation]  │
         │                      │                        │                      │
         │                      │                        │                      │
         │                      │                        │ Is GPS event?        │
         │                      │                        │ (lat/lon present?)   │
         │                      │                        │                      │
         │                      │                        │         YES          │
         │                      │                        │              ┌──────┘
         │                      │                        │              │
         │                      │                        │ asyncDataStream        │
         │                      │                        │ .asyncInvoke(          │
         │                      │                        │   CRSGrpcService.Score│
         │                      │                        │──────────────────────►
         │                      │                        │              │
         │                      │                        │              │ CRS001: check speed
         │                      │                        │              │ [0.5, 100] km/h + 60s
         │                      │                        │              │
         │                      │                        │              │ CRS002: check jump
         │                      │                        │              │ > 400m / 30s
         │                      │                        │              │
         │                      │                        │              │ CRS003: check hash
         │                      │                        │              │ in 300s window
         │                      │                        │              │
         │                      │                        │              │ Result(violation|null)
         │                      │                        │◄───────────────────────
         │                      │                        │              │
         │                      │                        │ [emit: violation       │
         │                      │                        │  or pass through]     │
         │                      │                        │                      │
         │                      │ Violation emitted      │                      │
         │                      │◄──────────────────────│                      │
         │                      │                        │                      │
         │                      │                        │ [on timeout: 50ms]    │
         │                      │                        │ emit PASS (graceful   │
         │                      │                        │  degradation)         │
         │                      │                        │──────────────────────►
         │                      │                        │              │
         │                      │                        │              │ [log: timeout,
         │                      │                        │              │  CRS bypassed]
         │                      │                        │              │
         │                      │ Violation → PostgreSQL │              │
         │                      │ Counter → Prometheus   │              │
         │                      │                        │              │
         ▼                      ▼                        ▼              ▼
        [T=0ms]              [T=5ms]               [T=10ms]        [T=60ms]

        Note: ML Phase 3 (Bayesian Optimization, Isolation Forest)
        runs asynchronously every hour on calibration window.
        ML results written to BroadcastState → used by CRS rules next cycle.
        ML never blocks or vetoes rule evaluation.
```

### Design Notes
- Lifelines clearly labeled for each component
- Time annotations (T=0ms, T=5ms, etc.) for latency context
- Timeout path shown with dotted line
- GPS check branching shown explicitly
- ML Phase 3 shown as dashed box annotation (out-of-band)
- Graceful degradation labeled clearly

### Caption
> **Figure 6: Sequence diagram for CRS rule evaluation via gRPC.** A raw event flows from Kafka into a Flink Python operator (SYN/SEM evaluation, ~5ms). If the event has GPS coordinates, the JVM operator makes an async gRPC call to the Java CRS service (~50ms timeout). The Java service evaluates CRS001 (speed bounds), CRS002 (GPS jump), and CRS003 (deduplication). Results flow back through the JVM operator, which emits violations or passes events through. On gRPC timeout (50ms), the system degrades gracefully: the event passes without CRS evaluation. ML Phase 3 runs asynchronously every hour on a calibration window and writes updated thresholds to BroadcastState; it never blocks or vetoes real-time evaluation.

### LaTeX Include
```latex
\begin{figure}[htbp]
  \centering
  \includesvg[width=0.95\textwidth]{figures/f6_sequence_diagram.svg}
  \caption{Sequence diagram for CRS rule evaluation via gRPC. A raw event flows from Kafka
    into a Flink Python operator (SYN/SEM evaluation, ~5ms). GPS events trigger an async
    gRPC call to the Java CRS service (~50ms timeout). On timeout, the system degrades
    gracefully: the event passes without CRS evaluation. ML Phase 3 runs asynchronously
    every hour and writes to BroadcastState; it never blocks real-time evaluation.}
  \label{fig:sequence-diagram}
\end{figure}
```

---

## F7: Experimental Pipeline

**Chapter**: 3 (Experiments) — Evaluation Methodology
**Status**: Needed
**Type**: Pipeline diagram (Excalidraw)

### Content

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      EXPERIMENTAL PIPELINE                                   │
│              (Synthetic Injection + Ground Truth + Evaluation)               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ PHASE 0: GROUND TRUTH EVENT GENERATION                               │    │
│  │                                                                        │    │
│  │  ┌────────────────────┐     ┌──────────────────────┐                 │    │
│  │  │ NYC TLC Parquet   │     │ NYC MTA Bus          │                 │    │
│  │  │ (~3M records)     │     │ GTFS-realtime        │                 │    │
│  │  │ Jan 2024          │     │ (historical replay)  │                 │    │
│  │  └─────────┬──────────┘     └──────────┬───────────┘                 │    │
│  │            │                           │                             │    │
│  │            └───────────────┬───────────┘                             │    │
│  │                            ▼                                          │    │
│  │                    Ground Truth Events                                 │    │
│  │                    (entity_index, timestamp,                           │    │
│  │                     original values)                                   │    │
│  └─────────────────────────────┬──────────────────────────────────────────┘    │
│                                │                                              │
│                                ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ PHASE 1: SYNTHETIC ANOMALY INJECTION                                  │    │
│  │                                                                        │    │
│  │  SyntheticInjector processes ground truth events:                     │    │
│  │                                                                        │    │
│  │  ┌────────────────────────────────────────────────────────────────┐  │    │
│  │  │ Scenario 1: Schema Violation (SYN001)                          │  │    │
│  │  │   → Set field = NULL / NaN randomly at 0.5%, 1%, 2%, 5% rate  │  │    │
│  │  └────────────────────────────────────────────────────────────────┘  │    │
│  │  ┌────────────────────────────────────────────────────────────────┐  │    │
│  │  │ Scenario 2: Completeness Issue (SYN001)                        │  │    │
│  │  │   → Same as Scenario 1 — NULL fields                           │  │    │
│  │  └────────────────────────────────────────────────────────────────┘  │    │
│  │  ┌────────────────────────────────────────────────────────────────┐  │    │
│  │  │ Scenario 3: Freshness Issue (GTFSSem002)                       │  │    │
│  │  │   → Set timestamp = timestamp - (6 to 10 min)                  │  │    │
│  │  └────────────────────────────────────────────────────────────────┘  │    │
│  │  ┌────────────────────────────────────────────────────────────────┐  │    │
│  │  │ Scenario 4: Volume Anomaly (SYN001/SYN002)                     │  │    │
│  │  │   → Flag clusters of anomalous events (burst injection)        │  │    │
│  │  └────────────────────────────────────────────────────────────────┘  │    │
│  │  ┌────────────────────────────────────────────────────────────────┐  │    │
│  │  │ Scenario 5: Business Rule Violation (SEM001/SEM002/SEM003)     │  │    │
│  │  │   → Inject fare > P95, distance > P95, tip > 60% fare         │  │    │
│  │  └────────────────────────────────────────────────────────────────┘  │    │
│  │  ┌────────────────────────────────────────────────────────────────┐  │    │
│  │  │ Scenario 6: Context-Dependent Violation (CRS001/CRS002)        │  │    │
│  │  │   → GPS speed: inject 0.2 km/h (sustained), 110 km/h          │  │    │
│  │  │   → GPS jump: inject jump of 500m in 30s                       │  │    │
│  │  └────────────────────────────────────────────────────────────────┘  │    │
│  │                                                                        │    │
│  │  Output: {injected_events, anomaly_metadata{entity_index,            │    │
│  │            anomaly_type, injection_rate, timestamp}}                   │    │
│  └─────────────────────────────┬──────────────────────────────────────────┘    │
│                                │                                              │
│                                ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ PHASE 2: KAFKA REPLAY                                                │    │
│  │                                                                        │    │
│  │  Kafka Producer: replay injected events to raw_events topic           │    │
│  │  with known entity_index in each message                              │    │
│  │                                                                        │    │
│  │  Warmup: 10,000 events BEFORE measurement window                      │    │
│  │  Measurement: 600s window                                             │    │
│  │  Trials: 3 (independent runs)                                        │    │
│  └─────────────────────────────┬──────────────────────────────────────────┘    │
│                                │                                              │
│                                ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ PHASE 3: STREAMDQ EVALUATION                                         │    │
│  │                                                                        │    │
│  │  Flink evaluates injected events through SYN/SEM/CRS rules             │    │
│  │  Violations emitted with:                                             │    │
│  │    {rule_id, entity_id, violation_type, processing_latency_ms}        │    │
│  │                                                                        │    │
│  │  Violations stored in PostgreSQL:                                      │    │
│  │    violations table + ground_truth_events table                         │    │
│  └─────────────────────────────┬──────────────────────────────────────────┘    │
│                                │                                              │
│                                ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ PHASE 4: GROUND TRUTH MATCHING & METRICS                             │    │
│  │                                                                        │    │
│  │  GroundTruthTracker:                                                  │    │
│  │    matched = violations WHERE entity_index IN injected_indices        │    │
│  │    tp = matched.anomaly_type == injected.anomaly_type                 │    │
│  │    fp = matched BUT not in injected set                               │    │
│  │    fn = injected BUT not in matched set                               │    │
│  │                                                                        │    │
│  │  Metrics computed:                                                    │    │
│  │    Precision = TP / (TP + FP)                                         │    │
│  │    Recall    = TP / (TP + FN)                                         │    │
│  │    F1        = 2·P·R / (P + R)                                        │    │
│  │                                                                        │    │
│  │  Bootstrap CI: 10,000 iterations (BCa method)                          │    │
│  └─────────────────────────────┬──────────────────────────────────────────┘    │
│                                │                                              │
│                                ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ PHASE 5: RESULTS AGGREGATION                                          │    │
│  │                                                                        │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                    │    │
│  │  │ Precision   │  │ Recall      │  │ F1          │                    │    │
│  │  │ per rule    │  │ per rule    │  │ per rule    │                    │    │
│  │  │ + 95% CI    │  │ + 95% CI    │  │ + 95% CI    │                    │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                    │    │
│  │                                                                        │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │    │
│  │  │ Statistical Tests:                                               │  │    │
│  │  │   Wilcoxon signed-rank (RQ1: context vs. static)                 │  │    │
│  │  │   Pearson ρ (RQ2: L4↔L0 TQS; RQ3: TQS↔injection rate)           │  │    │
│  │  │   Holm-Bonferroni correction (α_adj = 0.0083 between families)  │  │    │
│  │  └─────────────────────────────────────────────────────────────────┘  │    │
│  │                                                                        │    │
│  │  Structured JSON report:                                               │    │
│  │    {n_events, n_anomalies, anomaly_rate, precision, recall, F1,       │    │
│  │     bootstrap_CI, seed, warmup_events, pipeline_version}               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Design Notes
- 5 phases clearly separated
- 6 scenarios shown as parallel boxes within Phase 1
- Ground truth tracking shown at every step
- Bootstrap CI and statistical tests shown in Phase 5
- Structured JSON report shown as output artifact

### Caption
> **Figure 7: Experimental pipeline for StreamDQ evaluation.** Phase 0 generates ground truth events from NYC TLC parquet and NYC MTA Bus GTFS-realtime. Phase 1 injects synthetic anomalies (6 scenarios) at controlled rates (0.5\u20135%). Phase 2 replays injected events through Kafka with warmup (10,000 events) and measurement window (600s, 3 trials). Phase 3 evaluates events through StreamDQ rules. Phase 4 matches detected violations against ground truth to compute TP/FP/FN. Phase 5 computes precision, recall, F1 with 95\% bootstrap CI (10,000 iterations, BCa method) and applies Holm-Bonferroni correction across research questions.

### LaTeX Include
```latex
\begin{figure}[htbp]
  \centering
  \includesvg[width=0.95\textwidth]{figures/f7_experimental_pipeline.svg}
  \caption{Experimental pipeline. Phase 0 generates ground truth from NYC TLC and NYC MTA Bus.
    Phase 1 injects synthetic anomalies (6 scenarios) at 0.5\u20135\% rates.
    Phase 2 replays through Kafka with 10,000-event warmup and 600s measurement window (3 trials).
    Phase 3 evaluates through StreamDQ rules.
    Phase 4 matches violations against ground truth for TP/FP/FN computation.
    Phase 5 computes precision, recall, F1 with 95\% bootstrap CI (10,000 iter, BCa)
    and Holm\u2013Bonferroni correction (\u03b1_adj=0.0083).}
  \label{fig:experimental-pipeline}
\end{figure}
```

---

## F8: Dashboard Mockup / Screenshot

**Chapter**: 3 (Experiments) / Appendix
**Status**: Needed (mockup; screenshot when deployed)
**Type**: Dashboard mockup (Figma/Excalidraw) → real screenshot after deployment

### Content

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          STREAMDQ MONITORING DASHBOARD                      │
│                       (Grafana — Real-Time Streaming View)                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  [StreamDQ]  [Dashboard]  [Alerts]  [Explore]  [Plugins]  [Settings]        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │ TIME RANGE: [Last 1 hour ▼]    REFRESH: [5s ▼]    [Auto-refresh: ON]   │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌──────────────────────────────┐  ┌──────────────────────────────┐        │
│  │  TOTAL EVENTS PROCESSED      │  │  VIOLATIONS OVER TIME        │        │
│  │  ████████████████████████    │  │  ▓▓▓  Violations            │        │
│  │  1,234,567                  │  │  ░░░  Violations            │        │
│  │  Events/sec: 3,456          │  │  ══════════════════════════  │        │
│  │  (up from 2,100 avg)         │  │  [Time series, last 1h]      │        │
│  └──────────────────────────────┘  └──────────────────────────────┘        │
│                                                                              │
│  ┌──────────────────────────────┐  ┌──────────────────────────────┐        │
│  │  RULE VIOLATIONS BY LAYER    │  │  VIOLATIONS BY TYPE          │        │
│  │                               │  │                               │        │
│  │  SYN │██████████████│ 45%    │  │  SYN001 (NULL)   │████│ 23%   │        │
│  │  SEM │████████│      │ 30%    │  │  SYN002 (NEG)   │██│   │ 12%   │        │
│  │  CRS │████│          │ 15%    │  │  SYN003 (OOB)   │█│    │  5%   │        │
│  │  CRS003│██│ (UNMEAS) │  5%    │  │  SEM001         │████│ 18%   │        │
│  │  TQS  │██│          │  5%    │  │  CRS001 (GPS)   │██│    │ 15%   │        │
│  │                               │  │  CRS002 (JUMP)  │█│    │  7%   │        │
│  │  [Pie chart]                  │  │  CRS003 (DUP)   │█│    │  5%   │        │
│  │                               │  │  [Stacked bar]              │        │
│  └──────────────────────────────┘  └──────────────────────────────┘        │
│                                                                              │
│  ┌──────────────────────────────┐  ┌──────────────────────────────┐        │
│  │  TQS OVER TIME               │  │  CONTEXT LEVEL COVERAGE      │        │
│  │                               │  │                               │        │
│  │  TQS = 0.87                  │  │  L0 │███│ 3%                │        │
│  │  ↑ 0.02 vs. last hour        │  │  L1 │████│ 8%               │        │
│  │                               │  │  L2 │████████│ 22%         │        │
│  │  Tm=0.91  Cn=0.88            │  │  L3 │████████████│ 35%      │        │
│  │  Ac=0.85  Cs=0.89  Uv=0.82   │  │  L4 │████████████│ 28%      │        │
│  │                               │  │  L5 │██│ 4%                │        │
│  │  [Area chart]                 │  │  [Stacked bar]              │        │
│  └──────────────────────────────┘  └──────────────────────────────┘        │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  RECENT VIOLATIONS TABLE (last 100)                                   │  │
│  │  ┌────────────────┬────────┬──────────┬──────────┬──────────────────┐  │  │
│  │  │ Timestamp      │ Rule   │ Entity   │ Severity │ Details          │  │  │
│  │  ├────────────────┼────────┼──────────┼──────────┼──────────────────┤  │  │
│  │  │ 14:32:05.123  │ CRS001 │ BUS_1234 │ HIGH     │ speed=0.3km/h   │  │  │
│  │  │ 14:31:58.456  │ SYN001 │ TAXI_789 │ HIGH     │ fare_amount=NULL │  │  │
│  │  │ 14:31:52.001  │ SEM001 │ TAXI_456 │ HIGH     │ fare=245>P90=180 │  │  │
│  │  │ 14:31:48.334  │ CRS002 │ BUS_5678 │ HIGH     │ jump=523m/30s   │  │  │
│  │  │ 14:31:40.987  │ GTFSSem│ BUS_9012 │ MEDIUM   │ stale=6m23s      │  │  │
│  │  └────────────────┴────────┴──────────┴──────────┴──────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  ALERT RULES                                                         │  │
│  │  🔴 CRITICAL: CRS001 triggered 5x in 1 min → Email + Slack         │  │
│  │  🟡 WARNING: Violation rate > 5% in 5 min → Slack                  │  │
│  │  🟢 INFO: TQS dropped below 0.80 → Log entry                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Design Notes
- Dark theme (Grafana default) with VNU blue accents
- Real-time feel: refresh indicators, live counters
- GPS violations highlighted (CRS001, CRS002) in gold
- CRS003 shown as separate segment (with "UNMEAS" note)
- TQS shown with individual dimension scores
- Context level coverage shown as stacked bar (L0 small, L4 large)
- Alert rules shown at bottom with severity colors

### Caption
> **Figure 8: StreamDQ real-time monitoring dashboard (Grafana).** The dashboard shows live metrics: total events processed (events/sec), violation rates by layer (SYN/SEM/CRS) and type, TQS composite score with individual dimensions, and context level coverage (L0\u2013L5). The violations table shows recent violations with rule ID, entity ID, severity, and details. Alert rules trigger at configurable thresholds. CRS003 is shown as a separate segment (Tier 3\u2014Unmeasurable, NG-4 blocker). Note: this is a mockup; actual dashboard requires Flink + Prometheus + Grafana deployment.

### LaTeX Include
```latex
\begin{figure}[htbp]
  \centering
  \includesvg[width=0.95\textwidth]{figures/f8_dashboard_mockup.svg}
  % OR: for real screenshot after deployment:
  % \includegraphics[width=0.95\textwidth]{figures/f8_dashboard_screenshot.png}
  \caption{StreamDQ real-time monitoring dashboard (Grafana). The dashboard shows
    live metrics: total events processed, violation rates by layer (SYN/SEM/CRS) and type,
    TQS composite score with individual dimensions, and context level coverage (L0\u2013L5).
    CRS003 is shown as a separate segment (Tier 3\u2014Unmeasurable, NG-4 blocker).
    Note: mockup\u2014actual screenshot requires Flink + Prometheus + Grafana deployment.}
  \label{fig:dashboard-mockup}
\end{figure}
```

---

## Figure Production Checklist

|| ID | Figure | Tool | Format | Deadline | Status |
|----|------|-------|-------|---------|---------|--------|
|| F1 | Overall System Architecture | Excalidraw | SVG + PDF | Week 3 | Needed |
|| F2 | Layered Architecture | Excalidraw | SVG + PDF | Week 3 | Needed |
|| F3 | Data Flow Diagram | Excalidraw | SVG + PDF | Week 3 | Needed |
|| F4 | Context-Aware Decision Flow | Excalidraw | SVG + PDF | Week 4 | Needed |
|| F5 | Rule Taxonomy / DQ Dimensions Map | Excalidraw | SVG + PDF | Week 4 | Needed |
|| F6 | Sequence Diagram | Excalidraw | SVG + PDF | Week 5 | Needed |
|| F7 | Experimental Pipeline | Excalidraw | SVG + PDF | Week 5 | Needed |
|| F8 | Dashboard Mockup / Screenshot | Excalidraw + Grafana | SVG + PNG | Week 7 | Needed |

**All figures**: 300 DPI minimum, Computer Modern / Latin Modern font, consistent VNU color palette, numbered captions with labels, LaTeX `\includesvg` or `\includegraphics` ready.

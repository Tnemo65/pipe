# F1: System Architecture Diagram
# StreamDQ — A Context-Aware Framework for Streaming Data Quality Monitoring

**Chapter**: 2 (Architecture) — System Overview
**Type**: Architecture diagram (Excalidraw)
**Color Palette**:
- Primary: `#00468C` (VNU blue) — Python components
- Secondary: `#265499` (lighter blue)
- Accent: `#E8B949` (gold) — Java components
- Neutral: `#6B7280` (gray) — storage/monitoring
- Background: `#FFFFFF` (white)

---

## EXCALIDRAW JSON STRUCTURE

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [
    {
      "id": "box_datasource_1",
      "type": "rectangle",
      "x": 80, "y": 40,
      "width": 200, "height": 100,
      "fillColor": "#EFF6FF",
      "strokeColor": "#00468C",
      "strokeWidth": 2,
      "label": {
        "text": "NYC TLC Yellow Taxi\nParquet Replay",
        "fontSize": 14,
        "fontFamily": "Computer Modern"
      }
    },
    {
      "id": "box_datasource_2",
      "type": "rectangle",
      "x": 80, "y": 180,
      "width": 200, "height": 100,
      "fillColor": "#EFF6FF",
      "strokeColor": "#00468C",
      "strokeWidth": 2,
      "label": {
        "text": "NYC MTA Bus\nGTFS-realtime (Live)",
        "fontSize": 14,
        "fontFamily": "Computer Modern"
      }
    },
    {
      "id": "box_kafka",
      "type": "rectangle",
      "x": 350, "y": 90,
      "width": 220, "height": 80,
      "fillColor": "#FEF3C7",
      "strokeColor": "#92400E",
      "strokeWidth": 2,
      "label": {
        "text": "Apache Kafka\nraw_events topic",
        "fontSize": 14,
        "fontFamily": "Computer Modern"
      }
    },
    {
      "id": "box_flink",
      "type": "rectangle",
      "x": 640, "y": 40,
      "width": 320, "height": 300,
      "fillColor": "#EFF6FF",
      "strokeColor": "#00468C",
      "strokeWidth": 3,
      "label": {
        "text": "Apache Flink Streaming Engine",
        "fontSize": 16,
        "fontFamily": "Computer Modern"
      }
    },
    {
      "id": "box_syn",
      "type": "rectangle",
      "x": 660, "y": 80,
      "width": 120, "height": 60,
      "fillColor": "#DBEAFE",
      "strokeColor": "#00468C",
      "strokeWidth": 1,
      "label": {
        "text": "SYN Rules\n(Python)\nSYN001–003",
        "fontSize": 11,
        "fontFamily": "Computer Modern"
      }
    },
    {
      "id": "box_sem",
      "type": "rectangle",
      "x": 800, "y": 80,
      "width": 120, "height": 60,
      "fillColor": "#DBEAFE",
      "strokeColor": "#00468C",
      "strokeWidth": 1,
      "label": {
        "text": "SEM Rules\n(Python)\nSEM001–003 + GTFSSem002",
        "fontSize": 11,
        "fontFamily": "Computer Modern"
      }
    },
    {
      "id": "box_crs",
      "type": "rectangle",
      "x": 660, "y": 160,
      "width": 120, "height": 60,
      "fillColor": "#FEF9C3",
      "strokeColor": "#E8B949",
      "strokeWidth": 2,
      "label": {
        "text": "CRS Rules\n(Java)\nCRS001–003",
        "fontSize": 11,
        "fontFamily": "Computer Modern"
      }
    },
    {
      "id": "box_tqs",
      "type": "rectangle",
      "x": 800, "y": 160,
      "width": 120, "height": 60,
      "fillColor": "#F3F4F6",
      "strokeColor": "#6B7280",
      "strokeWidth": 1,
      "label": {
        "text": "TQS\nAggregator\nTm,Cn,Ac,Cs,Uv",
        "fontSize": 11,
        "fontFamily": "Computer Modern"
      }
    },
    {
      "id": "box_ml",
      "type": "rectangle",
      "x": 660, "y": 240,
      "width": 260, "height": 60,
      "fillColor": "#EDE9FE",
      "strokeColor": "#7C3AED",
      "strokeWidth": 1,
      "strokeStyle": "dashed",
      "label": {
        "text": "ML Augmentation Layer (Phase 3)\nBO + Isolation Forest · Rules remain AUTHORITATIVE",
        "fontSize": 11,
        "fontFamily": "Computer Modern"
      }
    },
    {
      "id": "box_postgres",
      "type": "rectangle",
      "x": 1020, "y": 60,
      "width": 140, "height": 80,
      "fillColor": "#ECFDF5",
      "strokeColor": "#059669",
      "strokeWidth": 2,
      "label": {
        "text": "PostgreSQL\nViolations +\nGround Truth",
        "fontSize": 12,
        "fontFamily": "Computer Modern"
      }
    },
    {
      "id": "box_prometheus",
      "type": "rectangle",
      "x": 1020, "y": 160,
      "width": 140, "height": 60,
      "fillColor": "#FEF2F2",
      "strokeColor": "#DC2626",
      "strokeWidth": 2,
      "label": {
        "text": "Prometheus\nMetrics + TQS",
        "fontSize": 12,
        "fontFamily": "Computer Modern"
      }
    },
    {
      "id": "box_grafana",
      "type": "rectangle",
      "x": 1020, "y": 240,
      "width": 140, "height": 60,
      "fillColor": "#FEF2F2",
      "strokeColor": "#DC2626",
      "strokeWidth": 2,
      "label": {
        "text": "Grafana\nDashboard",
        "fontSize": 12,
        "fontFamily": "Computer Modern"
      }
    },
    {
      "id": "arrow_ds1_to_kafka",
      "type": "arrow",
      "points": [[280, 90], [350, 130]],
      "strokeColor": "#00468C",
      "strokeWidth": 2
    },
    {
      "id": "arrow_ds2_to_kafka",
      "type": "arrow",
      "points": [[280, 230], [350, 130]],
      "strokeColor": "#00468C",
      "strokeWidth": 2
    },
    {
      "id": "arrow_kafka_to_flink",
      "type": "arrow",
      "points": [[570, 130], [640, 130]],
      "strokeColor": "#00468C",
      "strokeWidth": 2,
      "label": { "text": "Kafka <10ms", "fontSize": 11 }
    },
    {
      "id": "arrow_flink_to_postgres",
      "type": "arrow",
      "points": [[960, 100], [1020, 100]],
      "strokeColor": "#059669",
      "strokeWidth": 2,
      "label": { "text": "Violations", "fontSize": 11 }
    },
    {
      "id": "arrow_flink_to_prometheus",
      "type": "arrow",
      "points": [[960, 190], [1020, 190]],
      "strokeColor": "#DC2626",
      "strokeWidth": 2,
      "label": { "text": "Metrics", "fontSize": 11 }
    },
    {
      "id": "arrow_prometheus_to_grafana",
      "type": "arrow",
      "points": [[1090, 220], [1090, 240]],
      "strokeColor": "#DC2626",
      "strokeWidth": 1
    },
    {
      "id": "annotation_gps",
      "type": "text",
      "x": 680, "y": 320,
      "text": "CRS rules require GPS coordinates\n→ NYC MTA Bus only (not NYC TLC)",
      "fontSize": 10,
      "fontFamily": "Computer Modern",
      "fillColor": "#FEF3C7",
      "strokeColor": "#E8B949"
    },
    {
      "id": "annotation_ml",
      "type": "text",
      "x": 680, "y": 340,
      "text": "ML Phase 3: BO (Priority 1) + IF (Priority 2, conditional)",
      "fontSize": 10,
      "fontFamily": "Computer Modern",
      "fillColor": "#EDE9FE",
      "strokeColor": "#7C3AED"
    }
  ]
}
```

---

## RECREATION INSTRUCTIONS (Excalidraw UI)

### Step 1: Open Excalidraw
Go to https://excalidraw.com or open the Excalidraw desktop app.

### Step 2: Set Canvas
- Canvas size: 1200 × 400 px
- Background: white
- Grid: off

### Step 3: Draw Boxes (use Rectangle tool)

**Data Sources (top-left, blue boxes)**:
1. Box 1: `x=80, y=40, w=200, h=100`
   - Fill: `#EFF6FF`, Stroke: `#00468C` (2px)
   - Label: "NYC TLC Yellow Taxi\nParquet Replay"
   - Note below: "Zone-level only (no GPS)"

2. Box 2: `x=80, y=180, w=200, h=100`
   - Fill: `#EFF6FF`, Stroke: `#00468C` (2px)
   - Label: "NYC MTA Bus\nGTFS-realtime (Live)"
   - Note below: "GPS coordinates available"

**Kafka (center, yellow box)**:
3. Box: `x=350, y=90, w=220, h=80`
   - Fill: `#FEF3C7`, Stroke: `#92400E` (2px)
   - Label: "Apache Kafka\nraw_events topic"

**Flink (right, large blue box)**:
4. Box: `x=640, y=40, w=320, h=300`
   - Fill: `#EFF6FF`, Stroke: `#00468C` (3px, thick border)
   - Label: "Apache Flink Streaming Engine"

**Inside Flink — rule boxes**:
5. SYN box: `x=660, y=80, w=120, h=60` — Blue `#DBEAFE`
6. SEM box: `x=800, y=80, w=120, h=60` — Blue `#DBEAFE`
7. CRS box: `x=660, y=160, w=120, h=60` — Gold `#FEF9C3`, Gold border `#E8B949`
8. TQS box: `x=800, y=160, w=120, h=60` — Gray `#F3F4F6`
9. ML box: `x=660, y=240, w=260, h=60` — Purple dashed border `#EDE9FE`, dashed stroke

**Sinks (right side)**:
10. PostgreSQL: `x=1020, y=60, w=140, h=80` — Green `#ECFDF5`
11. Prometheus: `x=1020, y=160, w=140, h=60` — Red `#FEF2F2`
12. Grafana: `x=1020, y=240, w=140, h=60` — Red `#FEF2F2`

### Step 4: Draw Arrows (use Arrow tool)
- DS → Kafka: from right of boxes to Kafka left side
- Kafka → Flink: labeled "Kafka <10ms"
- Flink → PostgreSQL: labeled "Violations"
- Flink → Prometheus: labeled "Metrics"
- Prometheus → Grafana: downward arrow

### Step 5: Add Annotations (use Text tool)
- "CRS rules require GPS → NYC MTA Bus only" (gold text box)
- "ML Phase 3: BO + IF · Rules remain AUTHORITATIVE" (purple text box)
- Color code legend: Blue = Python, Gold = Java, Gray = Storage

### Step 6: Font
- All text: Computer Modern or Latin Modern
- Font size: 11–14px

---

## CAPTION (LaTeX)

```latex
\caption{StreamDQ overall system architecture. Events flow from NYC TLC Yellow Taxi
(parquet replay, zone-level) and NYC MTA Bus GTFS-realtime (live GPS, 30s updates)
through Apache Kafka into Apache Flink. SYN/SEM rules (Python, blue) evaluate all events;
CRS rules (Java, gold) evaluate GPS events only. Violations are stored in PostgreSQL
with ground-truth labels, metrics exported to Prometheus, and ML inference (Phase 3)
runs as async gRPC. Grafana provides real-time dashboards. CRS rules require
GPS coordinates and cannot be evaluated on NYC TLC zone-level data.}
```

---

## LaTeX INCLUDE

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

**Color guide for recreation**:
- Python boxes: `#00468C` stroke, `#DBEAFE` fill
- Java boxes: `#E8B949` stroke (gold), `#FEF9C3` fill
- Storage/Monitoring: `#059669` stroke (green), `#FEF2F2` stroke (red)
- ML (Phase 3): `#7C3AED` stroke (purple), dashed border

# F4: CRS Java Integration — Flink → Java gRPC Sequence
# StreamDQ — CRS Rule Evaluation via Async gRPC

**Chapter**: 2 (Architecture) — CRS Rules
**Type**: Sequence diagram (Excalidraw)
**Color Palette**:
- Flink Python: `#00468C` (blue)
- Flink JVM: `#2563EB` (lighter blue)
- Java Service: `#E8B949` (gold)
- Timeout: `#DC2626` (red)
- Success: `#059669` (green)

---

## RECREATION INSTRUCTIONS (Excalidraw UI)

### Canvas Setup
- Canvas: 1200 × 500 px
- Background: white

### Layout: Horizontal sequence diagram

### LIFELINES (vertical dashed lines)

| Lifeline | x position | Color | Label |
|----------|-------------|-------|-------|
| Kafka Topic | x=50 | gray | Kafka (raw_events) |
| Flink Python Operator | x=300 | blue | Flink Python (SYN/SEM) |
| Flink JVM KeyedProcess | x=500 | lighter blue | Flink JVM (CRS Router) |
| Java gRPC Service | x=750 | gold | Java CRS Service |
| PostgreSQL | x=950 | green | PostgreSQL |
| Prometheus | x=1050 | red | Prometheus |

Draw vertical dashed lines for each lifeline.

### STEP 1: EVENT ARRIVAL
```
Arrow: from Kafka (x=50) to Flink Python (x=300)
y=40, horizontal arrow
Label above: "emitRawEvent()"
Stroke: #00468C, 2px
```

### STEP 2: SYN/SEM EVALUATION
```
Box on Flink Python lifeline:
x=240, y=70, w=120, h=40
Fill: #DBEAFE, Stroke: #00468C
Text: "SYN/SEM evaluate()\n~5ms"
Font: 11px
Label: "processElement()"
```

### STEP 3: GPS CHECK
```
Diamond: x=440, y=80, w=100, h=50
Fill: #FEF9C3, Stroke: #E8B949
Text: "Has GPS?\nlat/lon?"
Font: 11px

YES arrow: downward to Java gRPC call
NO arrow: rightward → "PASS through"
```

### STEP 4: gRPC CALL (async)
```
Arrow: from Flink JVM (x=500) to Java Service (x=750)
y=150, horizontal dashed arrow
Label: "asyncDataStream.asyncInvoke(\n  CRSGrpcService.Score())"
Stroke: #E8B949, 2px
Note: "async ~50ms"
```

### STEP 5: JAVA CRS EVALUATION (inside Java box)
```
Box inside Java Service area:
x=690, y=150, w=140, h=80
Fill: #FEF9C3, Stroke: #E8B949
Text:
  "CRS001: check speed [2,100] km/h\n"
  "CRS002: check jump >400m/30s\n"
  "CRS003: check hash 300s window\n"
  "Haversine distance (Java)"
Font: 10px
```

### STEP 6: RESULT RETURN
```
Arrow: from Java Service (x=750) back to Flink JVM (x=500)
y=250, horizontal arrow
Label: "Result(violation | null)"
Stroke: #E8B949, 2px
Solid arrow (success path)
```

### STEP 7: VIOLATION EMIT
```
Arrow: from Flink JVM downward
y=270, to PostgreSQL
Label: "Violation → INSERT"
Stroke: #059669, 2px

Arrow: from Flink JVM to Prometheus
y=270
Label: "Counter++"
Stroke: #DC2626, 2px
```

### STEP 8: TIMEOUT PATH (critical — dashed red)
```
Dashed arrow from Flink JVM to Java Service
y=300, same x positions
Label: "50ms timeout"
Stroke: #DC2626, dashed

Box on timeout path:
x=540, y=280, w=160, h=50
Fill: #FEE2E2, Stroke: #DC2626
Text: "TIMEOUT: emit PASS\nCRS rules skipped\nLog: CRS bypassed"
Font: 10px
Label: "graceful degradation"
```

### ACTIVATION BOXES (show when each component is active)

**Flink Python**:
```
Box: x=260, y=70, w=80, h=120
Fill: #DBEAFE (light blue), transparent stroke
```

**Flink JVM**:
```
Box: x=460, y=70, w=80, h=250
Fill: #EFF6FF, transparent stroke
```

**Java Service**:
```
Box: x=710, y=150, w=120, h=100
Fill: #FEF9C3, transparent stroke
```

### ML PHASE 3 ANNOTATION (below diagram)
```
Box: x=500, y=380, w=400, h=50
Fill: #EDE9FE, Stroke: #7C3AED, dashed
Text:
  "ML Phase 3 (out-of-band, hourly):\n"
  "BO writes updated thresholds → BroadcastState → used next cycle"
Font: 10px
Dashed arrow from box → Flink JVM
```

### TIMING ANNOTATIONS
```
Text boxes at top:
T=0ms:   "Event arrives at Flink Python"
T=5ms:   "SYN/SEM evaluation complete"
T=10ms:  "gRPC call to Java CRS service"
T=60ms:  "Result returned (or timeout)"
T=65ms:  "Violation stored in PostgreSQL"
```

### LEGEND (bottom-left)
```
Box: x=20, y=400, w=180, h=80
Fill: white, Stroke: #374151
Text:
  "Legend:\n"
  "─ → Synchronous call\n"
  "- - → Async gRPC call\n"
  "─ → Timeout path (dashed)\n"
  "■ Blue = Python\n"
  "■ Gold = Java"
Font: 10px
```

---

## CAPTION

```latex
\caption{Sequence diagram for CRS rule evaluation via gRPC. A raw event flows from
Kafka into a Flink Python operator (SYN/SEM evaluation, ~5ms). If the event has
GPS coordinates, the JVM operator makes an async gRPC call to the Java CRS service
(~50ms timeout). The Java service evaluates CRS001 (speed bounds), CRS002 (GPS jump),
and CRS003 (deduplication) using Haversine distance. On timeout, the system degrades
gracefully: the event passes without CRS evaluation and a log entry is written.
ML Phase 3 runs asynchronously every hour and writes calibrated thresholds to
BroadcastState; it never blocks real-time evaluation. Rules remain authoritative.}
```

## LaTeX INCLUDE

```latex
\begin{figure}[htbp]
  \centering
  \includesvg[width=0.95\textwidth]{figures/f4_crs_grpc_sequence.svg}
  \caption{Sequence diagram for CRS rule evaluation via gRPC. A raw event flows from
    Kafka into a Flink Python operator (SYN/SEM, ~5ms). GPS events trigger an async
    gRPC call to the Java CRS service (~50ms timeout). On timeout, the system degrades
    gracefully: the event passes without CRS evaluation. ML Phase 3 runs asynchronously
    every hour and writes to BroadcastState; it never blocks real-time evaluation.}
  \label{fig:crs-grpc-sequence}
\end{figure}
```

---

## KEY DESIGN DECISIONS TO HIGHLIGHT

1. **Async pattern**: gRPC is non-blocking — Flink continues processing other events
2. **Timeout = graceful degradation**: CRS rules skipped on timeout, event passes
3. **Java required**: JVM↔Python serialization overhead too high for PyFlink stateful operations
4. **GPS filter**: CRS rules skipped for non-GPS events (NYC TLC zone-level)
5. **ML out-of-band**: BO runs hourly, writes to BroadcastState, never blocks real-time path

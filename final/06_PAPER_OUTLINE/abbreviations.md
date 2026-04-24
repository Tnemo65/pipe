# Abbreviations — Complete List

**Project**: A Context-Aware Framework for Streaming Data Quality Monitoring
**Date**: April 24, 2026

---

## Proposed LaTeX `acronym` Entries

Add to the `acronym` environment in `thesis_template.tex`. Replace the current placeholder acronyms.

```tex
\begin{acronym}[GTFS-realtime]
  \acro{API}{Application Programming Interface}
  \acro{BoT}{Bag of Thresholds}
  \acro{CDF}{Cumulative Distribution Function}
  \acro{CI}{Confidence Interval}
  \acro{CRS}{Cross-Record, Stateful}
  \acro{DAQ}{Data Quality}
  \acro{DC}{Discovery Chance}
  \acro{DQ}{Data Quality}
  \acro{ETA}{Estimated Time of Arrival}
  \acro{FI}{False Inclusion}
  \acro{FN}{False Negative}
  \acro{FP}{False Positive}
  \acro{FPR}{False Positive Rate}
  \acro{GeT}{Great Expectations}
  \acro{GPS}{Global Positioning System}
  \acro{GTFS}{General Transit Feed Specification}
  \acro{Haversine}{Haversine distance formula for great-circle distance between GPS coordinates}
  \acro{IoT}{Internet of Things}
  \acro{JVM}{Java Virtual Machine}
  \acro{k8s}{Kubernetes}
  \acro{km/h}{kilometers per hour}
  \acro{L0--L5}{Level 0 through Level 5 (hierarchical context levels)}
  \acro{LLM}{Large Language Model}
  \acro{LSTM}{Long Short-Term Memory (recurrent neural network)}
  \acro{MC}{Monte Carlo}
  \acro{ML}{Machine Learning}
  \acro{m}{meters}
  \acro{ms}{milliseconds}
  \acro{NYC TLC}{New York City Taxi and Limousine Commission}
  \acro{NYC MTA}{New York City Metropolitan Transportation Authority}
  \acro{P50}{50th percentile (median)}
  \acro{P90}{90th percentile}
  \acro{P95}{95th percentile}
  \acro{P99}{99th percentile}
  \acro{P10}{10th percentile}
  \acro{PVLBDB}{Proceedings of the VLDB Endowment}
  \acro{RPC}{Remote Procedure Call}
  \acro{SEM}{Semantic (rule layer)}
  \acro{SYN}{Syntactic (rule layer)}
  \acro{TN}{True Negative}
  \acro{TP}{True Positive}
  \acro{TQS}{Trajectory Quality Score}
  \acro{TTL}{Time-to-Live}
  \acro{UET}{University of Engineering and Technology}
  \acro{VLDB}{Very Large Data Bases (conference)}
  \acro{VNU}{Vietnam National University}
\end{acronym}
```

---

## Abbreviation Index

### A

| Abbr | Full Form | Definition |
|------|-----------|-----------|
| API | Application Programming Interface | Standard interface for service communication |
| BoT | Bag of Thresholds | Ensemble of threshold values across context cells |

### B

| Abbr | Full Form | Definition |
|------|-----------|-----------|
| BO | Bayesian Optimization | GP surrogate model for parameter calibration |

### C

| Abbr | Full Form | Definition |
|------|-----------|-----------|
| CDF | Cumulative Distribution Function | Cumulative probability of a random variable |
| CI | Confidence Interval | Statistical interval estimate |
| CRS | Cross-Record, Stateful | Rule layer requiring per-entity state |
| CRS001 | Cross-Record Rule 001 | GPS speed bounds check |
| CRS002 | Cross-Record Rule 002 | GPS jump detection |
| CRS003 | Cross-Record Rule 003 | Event deduplication via hash |

### D

| Abbr | Full Form | Definition |
|------|-----------|-----------|
| DAQ | Data Quality | Same as DQ |
| DC | Discovery Chance | Rate of finding true anomalies |
| DQ | Data Quality | Fitness of data for purpose |
| D4 | Dimension 4 (External) | Holiday indicator context dimension |

### E–I

| Abbr | Full Form | Definition |
|------|-----------|-----------|
| ETA | Estimated Time of Arrival | Predicted arrival time |
| FI | False Inclusion | Same as False Positive |
| FN | False Negative | Missed detection |
| FP | False Positive | False alarm |
| FPR | False Positive Rate | FP / (FP + TN) |
| GeT | Great Expectations | Python DQ library (batch) |

### G–I

| Abbr | Full Form | Definition |
|------|-----------|-----------|
| GPS | Global Positioning System | Satellite-based positioning system |
| GTFS | General Transit Feed Specification | Open standard for transit schedules |
| GTFS-realtime | GTFS-realtime | Live transit data extension (VehiclePosition, TripUpdate) |
| Haversine | Haversine formula | Great-circle distance on sphere from GPS coordinates |

### J–L

| Abbr | Full Form | Definition |
|------|-----------|-----------|
| JVM | Java Virtual Machine | Runtime for Java CRS rules |
| k8s | Kubernetes | Container orchestration |
| km/h | kilometers per hour | Speed unit |
| L0–L5 | Level 0–5 | Hierarchical context threshold levels |

### M–N

| Abbr | Full Form | Definition |
|------|-----------|-----------|
| m | meters | Distance unit |
| MC | Monte Carlo | Simulation method |
| ML | Machine Learning | Algorithmic learning from data |
| ms | milliseconds | Time unit |
| NYC MTA | NYC Metropolitan Transportation Authority | NYC transit authority |
| NYC TLC | NYC Taxi and Limousine Commission | NYC taxi regulator |

### P–Q

| Abbr | Full Form | Definition |
|------|-----------|-----------|
| P50 | 50th percentile | Median |
| P90 | 90th percentile | Upper threshold |
| P95 | 95th percentile | High percentile |
| P99 | 99th percentile | Near-maximum |
| P10 | 10th percentile | Lower threshold |

### R–S

| Abbr | Full Form | Definition |
|------|-----------|-----------|
| RPC | Remote Procedure Call | gRPC call to ML service |
| SEM | Semantic (rule layer) | Rule layer for plausibility checks |
| SYN | Syntactic (rule layer) | Rule layer for null/type checks |

### T–U

| Abbr | Full Form | Definition |
|------|-----------|-----------|
| TN | True Negative | Correct pass |
| TP | True Positive | Correct detection |
| TQS | Trajectory Quality Score | Composite quality metric |
| TTL | Time-to-Live | State expiration period |

---

## Note on Acronym Usage

1. **First use**: Write out full term, then abbreviation in parentheses
   - Example: "Bayesian Optimization (BO)" first time, then "BO" subsequently
2. **LaTeX**: Use `\ac{}` for auto-plural handling and first-use expansion
3. **Figures**: Expand all acronyms in figure captions
4. **Tables**: Expand all acronyms in table headers
5. **No acronym left unexplained**: Every abbreviation must be defined at first use

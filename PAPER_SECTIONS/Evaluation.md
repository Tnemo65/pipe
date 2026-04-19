# 4. Evaluation

## 4.1 Evaluation Framework Design

StreamDQ's evaluation framework is designed around **anomaly injection with ground-truth tracking**. The methodology consists of four components:

**Anomaly injection.** Synthetic anomalies are injected into the data stream at a controlled rate. Eight anomaly types are defined: `fare_negative` (fare < $0), `fare_outlier` (fare $500–$2,000), `location_invalid` (PULocationID outside 1–263), `timestamp_future` (pickup time 7 days in future), `duration_negative` (dropoff before pickup), `duration_outlier` (trip duration > 20 hours), `speed_outlier` (100 miles in 30 minutes), and `duplicate` (identical record injected twice within deduplication window).

Each anomaly type maps to one or more rules. The injection rate is configurable (default 5% of events) to simulate realistic error rates.

**Ground-truth correlation.** A metrics tracker records every injected anomaly with its position in the event stream. When a rule generates a violation, the tracker correlates the violation's entity index against the ground-truth record of injected anomalies. This enables per-rule and per-type precision and recall computation.

**Metric computation.** The framework computes: precision (fraction of detected violations that are true positives), recall (fraction of injected anomalies that are detected), F1 score, detection rate by anomaly type, and latency percentiles (P50, P95, P99).

**Comparative benchmarking.** StreamDQ's precision and recall are compared against Great Expectations and Soda Core under identical evaluation conditions.

## 4.2 Dataset

Experiments use the NYC Yellow Taxi Trip Records dataset (January 2023, approximately 3 million records). Each record contains 19 fields including fare amount, trip distance, pickup/dropoff timestamps and locations, passenger count, and payment type.

For streaming evaluation, records are replayed through Kafka at configurable rates (1,000–5,000 events/sec). Anomaly injection is applied before Kafka replay to ensure realistic timing characteristics.

## 4.3 Reproducible Evaluation Protocol

The following protocol ensures reproducibility of benchmark results:

1. **Dataset preparation.** Download NYC TLC parquet files for the evaluation period. Pre-shuffle with fixed random seed (42) to ensure consistent ordering across runs.

2. **Anomaly injection.** Set anomaly rate to 5% (configurable). Use fixed seed for anomaly type selection. Record the index and type of every injected anomaly as ground truth.

3. **Pipeline warmup.** Process 10,000 events before beginning measurement to ensure adaptive thresholds have stabilized and cross-record state has populated.

4. **Measurement window.** Process the full evaluation dataset (100,000 events default) with all metrics recording active.

5. **Metric computation.** After processing completes, compute precision, recall, F1, and latency percentiles. Report 95% confidence intervals via bootstrap resampling (1,000 iterations).

6. **Comparative runs.** Run Great Expectations and Soda Core on the same evaluation dataset under identical anomaly injection conditions.

## 4.4 Metrics

**Precision** = TP / (TP + FP). Measures how many of the detected violations are genuine quality issues. A precision of 85% means 15% of detected violations are false alarms.

**Recall** = TP / (TP + FN). Measures how many of the injected anomalies are caught by the rules. A recall of 82% means 18% of anomalies slip through the quality gate.

**F1** = 2 × (Precision × Recall) / (Precision + Recall). The harmonic mean of precision and recall.

**Latency** = time from event arrival to violation recorded. Measured in milliseconds. P50 (median), P95, and P99 percentiles reported.

## 4.5 Latency Characteristics

StreamDQ's micro-batch architecture introduces latency characteristics distinct from both batch and true streaming systems.

The **minimum end-to-end latency** is dominated by Spark's micro-batch interval, which defaults to 500ms but is configurable down to 100ms for lower-latency requirements. This sets a floor on achievable P50 latency.

**Processing latency** (time from batch availability to violation stored) varies with event count per batch. Our LocalPipeline measurements (in-process, no Kafka) show 5–15ms per event at typical violation rates. The Spark pipeline adds deserialization overhead (~5–20ms per batch) and SQLite commit overhead (~1–5ms per violation batch).

**P99 latency** is dominated by batch boundary effects — when a batch contains an unexpectedly large number of events or violations, processing time increases superlinearly. At 500ms micro-batch intervals with ~500 events per batch, P99 is estimated at 500ms–2s.

For sub-second latency requirements, a true streaming architecture (Apache Flink, Apache Pathway via Stream DaQ) is more appropriate than Spark's micro-batch model.

## 4.6 Discussion

The evaluation framework demonstrates that StreamDQ achieves measurable precision and recall on a real-world dataset under controlled anomaly injection. However, several caveats apply:

The evaluation uses **LocalPipeline** (in-process) rather than the distributed Spark pipeline. While LocalPipeline shares the same rule implementations, it does not capture Kafka transport overhead, Spark scheduling latency, or distributed execution characteristics.

The **anomaly injection types** are synthetic and may not represent the full spectrum of real-world data quality issues. Real errors often involve correlated anomalies, partial corruption, and domain-specific error patterns not captured by the eight injection types.

The **ground-truth correlation** relies on entity index matching. In production streaming deployments, event ordering is not guaranteed, and duplicate detection windows may evict entries before their duplicates arrive. The evaluation framework assumes ordered, replayed data.

**Future work** will extend the evaluation framework to: (1) measure end-to-end latency from Kafka produce to violation detection in the distributed Spark pipeline; (2) evaluate on streaming GTFS vehicle position data with real GPS spoofing scenarios; (3) add bootstrap confidence intervals for all reported metrics; (4) validate precision and recall against Stream DaQ under identical evaluation conditions.

---

*All evaluation results should be interpreted as preliminary. See Section 5 for a complete discussion of limitations and the conditions under which these results are valid.*

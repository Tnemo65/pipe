# 5. Limitations

This section provides an honest, self-critical discussion of StreamDQ's current limitations. We believe transparent disclosure of methodological and technical constraints is essential for credible research and responsible engineering.

## 5.1 Adaptive Thresholds: Driver-Only Computation

The adaptive threshold implementation (`AdaptiveThresholdEngine`) operates on the Spark driver node within the `foreachBatch` API. All threshold updates and rule evaluations occur on the driver after `batch_df.collect()` brings all rows from executors to the driver process.

This design has two implications. First, **throughput is bounded by single-driver capacity**. The pipeline cannot scale horizontally — all processing happens on one node regardless of the Spark cluster size. Second, **thresholds reflect only the current micro-batch's data** distributed across partitions, not a true global state across the cluster. For workloads with many executors processing different data partitions simultaneously, this creates a consistency window of up to one micro-batch duration.

Future work will explore `mapInPandas` or `FlatMapGroupsWithState` to push rule evaluation to partition level while maintaining threshold consistency through broadcast variables or approximate state aggregation.

## 5.2 Cross-Record State Not Checkpointed

Layer 2 (cross-record) rules maintain state in Python dictionaries (`_VEHICLE_STATES`, `_DEDUP_STATES`) that reside in process memory. This state is not persisted through Spark's checkpointing mechanism. Upon pipeline restart — whether due to failure, deployment, or scaling events — the cross-record state is lost.

This means CRS001 (impossible speed detection), CRS002 (GPS spoofing detection), and CRS003 (duplicate detection) will miss violations during the post-restart warmup period until state is rebuilt from fresh data. The current implementation includes checkpoint save/restore functions (`save_cross_record_state`, `load_cross_record_state`) that can be called manually at the end of each micro-batch, but these are not yet integrated into the automated recovery path.

**Production deployments should not rely on cross-record rules for fault-tolerant quality monitoring** without implementing external state persistence (e.g., Redis, RocksDB, or Spark's state store API).

## 5.3 Benchmark Numbers Are Estimates

The performance numbers presented throughout this paper — 85% precision, 82% recall, P50=150ms, P99=890ms, >5,000 events/sec throughput — are derived from the LocalPipeline evaluation and code inspection. The Spark pipeline's latency measurement captures only internal batch processing time; no end-to-end timestamp from Kafka produce to violation storage has been instrumented.

The Spark pipeline P99 latency is estimated at 500ms–5s based on the dominant contribution of Kafka's micro-batch consumption interval (~500ms default). This estimate should be validated with proper instrumentation before making production claims.

All quantitative claims should be treated as **preliminary engineering estimates pending formal benchmark runs** against the distributed Spark pipeline deployment.

## 5.4 Single-Broker Kafka Deployment

The demonstration deployment uses a single-node Kafka broker with replication factor of 1. This configuration provides no fault tolerance — any broker failure results in data loss for both the event stream and the quality-violations topic. The SQLite violation store uses per-batch synchronous commits without WAL mode optimization.

**This configuration is suitable only for local development and demonstration purposes.** Production deployments require multi-broker Kafka clusters (minimum RF=3) and either a production-grade violation sink (PostgreSQL with connection pooling, or Kafka as the primary sink) or optimized SQLite with WAL mode enabled.

## 5.5 Duplicate Injection Bug in Evaluation Framework

The evaluation framework's `duplicate` anomaly injection was identified as a no-op during code audit. The injection function returns the unchanged event, meaning CRS003's duplicate detection capability was not measurable in the original evaluation. This bug has been fixed in the current version by injecting an actual duplicate event immediately after the original, but it means **prior recall measurements did not include CRS003 performance**.

The corrected recall ceiling accounting for this limitation is 87.5% (assuming all other rules achieve 100% detection), with the realistic estimate being 73–80% based on the remaining evaluation framework's methodology.

## 5.6 NaN Silent-Pass in SYN001

The original SYN001 (fare amount validity) rule was found to silently pass NaN-valued `fare_amount` fields. IEEE 754 NaN values fail all comparison checks (`NaN < 0` returns `False`), and `isinstance(float('nan'), float)` returns `True`. This means a corrupted record with `fare_amount = NaN` would pass through the quality gate without generating a violation.

This bug has been fixed by adding an explicit `math.isnan()` check. We disclose it here to ensure reproducibility of prior results and to document the scope of the quality gate's coverage.

## 5.7 Comparison with Stream DaQ

Stream DaQ (Papastergios & Gounaris, 2025), published in June 2025, is the most significant recent development in the streaming DQ space. It is a stream-native framework built on Apache Pathway with dynamic constraint adaptation and drift detection — a more sophisticated architecture than StreamDQ's micro-batch approach.

StreamDQ should not be positioned as a production competitor to Stream DaQ. Stream DaQ's stream-native architecture provides lower latency and more mature state management. StreamDQ's value proposition lies in its domain-specific rule design, evaluation framework, and educational value — not in architectural superiority.

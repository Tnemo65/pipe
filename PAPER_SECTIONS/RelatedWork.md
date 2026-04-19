# 2. Related Work

## 2.1 Streaming Data Quality Frameworks

The most directly relevant recent work is **Stream DaQ** (Papastergios & Gounaris, 2025), a stream-first data quality monitoring framework that introduced the concept of configurable windowing mechanisms and dynamic constraint adaptation for unbounded data streams. Stream DaQ unifies over 30 quality checks using Apache Pathway as its underlying engine, producing quality meta-streams for real-time alerting. Their evaluation demonstrates significant throughput and latency improvements over Soda Core as a representative batch-based alternative. Stream DaQ represents the current state-of-the-art for stream-native DQ frameworks and serves as the primary competitive benchmark for this work.

**AutoDQM** (Brinkerhoff et al., 2025) addresses automated data quality monitoring for the CMS detector at CERN, combining beta-binomial probability functions with PCA and neural network autoencoders for anomaly detection. Of particular relevance is AutoDQM's use of beta-binomial confidence bounds for adaptive threshold calibration, which provides a principled statistical foundation for handling the distributional uncertainty inherent in streaming data. StreamDQ's rolling percentile approach is simpler than AutoDQM's beta-binomial method but lacks its statistical rigor during low-sample warmup periods.

**Agent-based environmental monitoring** (Athanasiadis & Mitkas, 2004) and the **context-dependent numerical data quality framework** (Marev et al., 2018) provide foundational conceptual models for multi-dimensional data quality assessment. While not directly applicable to streaming contexts, these works inform StreamDQ's rule taxonomy and quality dimension classification.

## 2.2 Adaptive Threshold Algorithms

**strAEm++DD** (Li et al., 2023) proposes autoencoder-based anomaly detection with incremental learning and concept drift adaptation. The key contribution is the integration of drift detection that triggers adaptive threshold recalibration when the underlying data distribution shifts. This approach is more sophisticated than StreamDQ's naive rolling percentile method in that it explicitly models the distinction between transient fluctuations and genuine distributional changes.

**Adaptive NAD** (Yuan et al., 2024) introduces a two-layer anomaly detection strategy with self-adaptive threshold calculation for online unsupervised detection. The two-layer approach (anomaly scoring followed by adaptive threshold adaptation) provides a principled framework for threshold evolution that does not require offline retraining. StreamDQ's fixed-window rolling percentile approach lacks this adaptive capacity.

**Trustworthy Anomaly Detection** (Yuan & Wu, 2022) surveys the challenges of threshold calibration in high-stakes domains, emphasizing that static thresholds fail in production environments where data distributions evolve. This finding motivates the adaptive threshold component of StreamDQ and validates the need for domain-specific threshold adaptation.

## 2.3 Cross-Record Anomaly Detection

**Continuous Outlier Mining of Streaming Data in Flink** (Toliopoulos et al., 2019) implements distance-based outlier detection for streaming data in Apache Flink, demonstrating 117x speedups over naive parallel implementations. This work provides foundational techniques for cross-record anomaly detection in distributed streaming systems.

**DQOps** provides a comprehensive open-source DQ platform with ~150 built-in checks covering all major quality dimensions. While DQOps lacks streaming support, its extensive check catalog informs StreamDQ's rule design and categorization strategy.

## 2.4 Comparative Positioning

| Framework | Streaming | Adaptive Thresholds | Cross-Record | Latency | Maturity |
|-----------|-----------|-------------------|--------------|---------|----------|
| **Stream DaQ** (2025) | Native | Dynamic + drift | Yes (windows) | Sub-second | Beta |
| **AutoDQM** (2025) | Near-real-time | Beta-binomial | Limited | Near-RT | Production |
| **strAEm++DD** (2023) | Streaming | Autoencoder + drift | Not DQ-specific | Streaming | Research |
| **Adaptive NAD** (2024) | Streaming | Two-layer self-adaptive | Not DQ-specific | Streaming | Research |
| **Great Expectations** | Limited | None | Yes (batch) | Batch | Production |
| **Soda Core v3** | None | ML-based | Limited | Batch | Production |
| **StreamDQ** (this work) | Micro-batch | Rolling P10/P90 | Yes | ~500ms+ | Prototype |

StreamDQ differentiates from Stream DaQ through its domain-specific rule design (GTFS GPS validation, NYC taxi domain rules) and its evaluation framework with ground-truth tracking. It differentiates from batch tools (GE, Soda, dbt) through its native streaming support and cross-record detection capability. It differentiates from research frameworks (strAEm++DD, Adaptive NAD) through its practical focus on declarative rule authoring, operational tooling, and an extensible evaluation framework.

---

*All citations verified against arXiv and Semantic Scholar as of April 2026.*

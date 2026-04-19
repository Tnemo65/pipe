# 1. Introduction

## 1.1 Motivation

Modern data pipelines increasingly rely on continuous data streams for real-time analytics, machine learning inference, and operational decision-making. Unlike batch processing, where data quality can be assessed after the fact, streaming pipelines demand quality checks that operate at the pace of data arrival — without slowing the stream. This shift from retrospective validation to continuous, in-stream quality monitoring introduces novel challenges that existing data quality frameworks were not designed to address.

Traditional data quality tools such as Great Expectations, Soda Core, and dbt tests operate on static snapshots or batch materializations. While these tools excel at declarative, expectation-based validation, they assume data is at rest. In a streaming context, data quality monitoring must reason about unbounded, continuously evolving data distributions; adapt to concept drift without manual threshold reconfiguration; and detect anomalies that span multiple records within a sliding temporal window — all while meeting sub-second latency requirements.

## 1.2 The Streaming Data Quality Gap

Existing approaches to data quality in streaming environments fall into three categories, each with significant limitations:

**Batch-oriented tools with streaming extensions.** Great Expectations and Soda Core provide mature, production-grade quality validation but are fundamentally designed for batch processing. Their streaming "support" amounts to validating micro-batches as they arrive — effectively treating streaming as a series of small batches. This approach inherits the latency of batch tools and cannot natively handle stateful, cross-record validation without significant custom engineering.

**Custom streaming pipelines.** Organizations with Apache Flink or Apache Spark Streaming deployments often build custom quality checks into their processing logic. While flexible, these implementations are ad-hoc, difficult to generalize, and lack the declarative expressiveness of established DQ frameworks. Every organization reinvents the same quality checks (null detection, range validation, anomaly detection) from scratch.

**Academic anomaly detection frameworks.** Research frameworks such as strAEm++DD (Li et al., 2023), AutoDQM (Brinkerhoff et al., 2025), and Adaptive NAD (Yuan et al., 2024) provide sophisticated algorithms for adaptive threshold management and concept drift detection. However, these frameworks are designed as general-purpose anomaly detectors, not as practical data quality monitoring systems with domain-specific rule authoring, evaluation frameworks, and operational tooling.

This gap — between mature batch DQ tools and specialized streaming anomaly detectors — is where StreamDQ operates.

## 1.3 StreamDQ: A Domain-Specific Streaming DQ Framework

StreamDQ is a domain-aware, open-source framework for streaming data quality monitoring. It is designed around three core principles:

**Stream-native processing.** StreamDQ processes data as it arrives via Apache Spark Structured Streaming micro-batch execution, providing continuous quality assessment without blocking the data flow. While micro-batch introduces higher latency than true streaming engines (see Section 4.5), it offers tighter integration with the Spark ecosystem and simpler deployment for teams already invested in Spark infrastructure.

**Domain-specific rule taxonomy.** Rather than a flat list of quality checks, StreamDQ organizes rules into three layers — syntactic, semantic, and cross-record — each with distinct computational requirements and applicability domains. This taxonomy provides a clear mental model for rule authoring and enables layer-specific optimization.

**Adaptive threshold management.** Static quality thresholds quickly become obsolete as data distributions evolve. StreamDQ computes rolling percentile-based thresholds (P10/P90) over sliding windows, enabling rules to automatically adapt to changing baselines without manual reconfiguration. Future work will integrate drift detection (inspired by strAEm++DD) and beta-binomial confidence bounds (inspired by AutoDQM) for more robust adaptive thresholding.

## 1.4 Paper Structure

The remainder of this paper is organized as follows. Section 2 surveys related work in streaming anomaly detection, adaptive threshold algorithms, and DQ frameworks. Section 3 describes the StreamDQ architecture and rule taxonomy. Section 4 presents the evaluation framework and experimental results. Section 5 discusses limitations and future work. Section 6 concludes.

---

*Note: Claims regarding quantitative performance (precision, recall, latency) in this paper are based on the evaluation framework described in Section 4. All benchmark numbers should be treated as preliminary pending formal measurement against the distributed Spark pipeline deployment. See Section 5 for a complete discussion of limitations.*

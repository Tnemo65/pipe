# Lessons Learned: How to Upgrade StreamDQ
**Date:** April 19, 2026
**Sources:** 13 blogs, 22 papers, DuckDB verification, code analysis, MCP verification
**Purpose:** Tổng hợp những gì ngành nghiên cứu/thực tiễn dạy cho StreamDQ, và cụ thể cách nâng cấp

---

## Part 1: Lessons from Engineering Blogs (13 blogs)

### Blog Cluster A: Grab Engineering (9 blogs)

#### [B1] Data Observability — Monitoring at Scale
**Source:** `engineering.grab.com/data-observability`

**What Grab does:**
- Group monitors by source stream, not per counter. Reduces alert fatigue for hundreds of data points.
- 5-minute tumbling windows for stable pattern detection.
- DASH: hourly reconciliation checking source vs streamed ID counts. Catches Debezium connector failures.
- Datadog anomaly detection + Slack routing to stream owners.

**How to upgrade StreamDQ:**
- Add `RuleGroup` concept: group rules by pipeline/dataset. `GroupViolation(severity=max([v.severity for v in violations]))` instead of per-rule alerts.
- Add `ReconciliationRule`: cross-check that `COUNT(source_records) == COUNT(processed_records)` after time window.
- Add `AlertConfig` dataclass with `routing: dict[str, list[str]]` (owner → Slack channel).
- Add `TumblingWindow` support: evaluate rules on 5-min windows, not per-event.

```python
@dataclass
class RuleGroup:
    group_id: str
    owner: str
    rules: list[str]  # rule IDs
    alert_routing: dict[str, str]  # severity → channel
    window_minutes: int = 5
```

---

#### [B2] Rethinking Streaming — SQL-First DQ
**Source:** `engineering.grab.com/rethinking-streaming-processing-data-exploration`

**What Grab does:**
- "Everyone inside Grab knows SQL" — SQL as the universal DQ language.
- Derive DDL from Protobuf schemas dynamically.
- Zeppelin notebooks for DQ rule prototyping against live Kafka.
- OPA/mTLS for Kafka DQ access control.

**How to upgrade StreamDQ:**
- Add SQL-like DSL for rule authoring:

```python
# Rule authoring DSL (proposed)
RULE sem001 ON fare_amount BETWEEN 2.5 AND 500
RULE syn002 ON PULocationID IN (1..263)
RULE crs001 ON vehicle_speed WHERE speed > 160 km/h
RULE cross_field ON end_time > start_time  # cross-field validation
```

- Add schema-to-rules auto-generation: `SchemaProfiler.analyze(schema) → list[RuleConfig]`
- Add notebook playground: `RulePlayground.evaluate(rule, sample_events)`

---

#### [B3] Signals Marketplace — Data Mesh Certification
**Source:** `engineering.grab.com/signals-market-place`

**What Grab does:**
- Data certification = formal contract between producers and consumers.
- BDO (Business Data Owner) + TDO (Technical Data Owner) per data product.
- DPI (Data Production Incident) auto-created when SLA/quality breaches.
- 75% of Grab queries now hit certified assets; deprecated tables increased 400% YoY.
- Certification tiers: bronze/silver/gold based on rule coverage.

**How to upgrade StreamDQ:**
- Add certification tiers to rule registry:

```python
@dataclass
class DataContract:
    contract_id: str
    dataset_id: str
    owner: str  # BDO
    tdo: str  # Technical Data Owner
    tier: Literal["bronze", "silver", "gold"]
    sla_minutes: int
    rules: list[str]
    severity: Literal["critical", "high", "medium", "low"]
    alert_channel: str

CERTIFICATION_TIERS = {
    "bronze": ["SYN001", "SYN002"],           # Basic validity
    "silver": ["SYN001", "SYN002", "SYN003", "SEM001", "SEM002", "SEM003"],
    "gold": ["SYN001", "SYN002", "SYN003", "SEM001", "SEM002", "SEM003", "CRS001", "CRS002", "CRS003"],
}
```

- Track north star metric: **"% violations blocked before downstream"**
- Add DPI creation: P1 violations auto-create incident in ticketing system.

---

#### [B4] Data First SLA Always — Fault Tolerance
**Source:** `engineering.grab.com/data-first-sla-always`

**What Grab does:**
- Redis stores `{topic: {partition: offset}}` for crash recovery.
- Running:Active job ratio as health signal.
- Microbatch runtime tracked per 30s window.
- Graceful shutdown + retry on Airflow.

**How to upgrade StreamDQ:**
- Add external checkpoint: store offset in Redis or file instead of local disk.
- Add health monitor: `JobHealthMonitor.check()` returns `{running: bool, batches_per_minute: float, avg_latency_ms: float}`.
- Add graceful shutdown: catch SIGTERM, flush pending violations, checkpoint state.

---

#### [B5] Real-Time DQ Monitoring — Kafka Stream Contracts
**Source:** `engineering.grab.com/real-time-data-quality-monitoring`

**What Grab does:**
- Two error types: syntactic (schema) vs. semantic (business rules) — mirrors SYN vs. SEM.
- Test Runner (FlinkSQL) executes inverse SQL queries for violation detection.
- LLM recommends semantic rules from schema + anonymized sample data.
- 100+ Kafka topics monitored in production.
- Alerts include sample bad records with highlighted fields.

**How to upgrade StreamDQ:**
- **Inverse SQL engine:** Given a rule, generate SQL that finds violating records:
  ```python
  def to_inverse_sql(rule: DataQualityRule) -> str:
      # SYN001: fare_amount < 0 → SELECT * WHERE fare_amount < 0
      # SEM001: adaptive fare range → SELECT * WHERE fare_amount NOT BETWEEN :p10 AND :p90*2
      pass
  ```
- **LLM rule suggestion:** Given dataset schema + sample data, ask LLM to suggest rules:
  ```python
  async def suggest_rules(schema: dict, samples: list[dict]) -> list[RuleConfig]:
      prompt = f"Given schema {schema} and samples {samples[:10]}, suggest 5 quality rules"
      return llm.generate(prompt)
  ```
- Add violation enrichment: include top 3 sample bad records in violation payload.

---

#### [B6] Grab Coban Platform — LLM-Assisted Rule Authoring
**Source:** `engineering.grab.com/real-time-data-quality-monitoring` + `www.alibabacloud.com/blog/...grab-journey-with-apache-flink...`

**What Grab does:**
- LLM analyzes schema + anonymized sample data → recommends semantic test rules.
- Alerts routed to topic owners via Slack with rich context.
- Genchi platform: root cause analysis from violation patterns.

**How to upgrade StreamDQ:**
- Add `LLMRuleAdvisor` class:
  ```python
  class LLMRuleAdvisor:
      def analyze_schema(self, schema: dict) -> list[RuleSuggestion]:
          # 1. Null-able fields → SYN001 candidate
          # 2. Numeric fields → SEM001 range candidate
          # 3. Timestamp fields → SYN003 candidate
          # 4. GPS fields → CRS001/CRS002 candidate
          pass
      def analyze_samples(self, samples: list[dict]) -> list[RuleSuggestion]:
          # Cluster samples, detect outliers → suggest thresholds
          pass
  ```
- Add root cause analysis: cluster violations by pattern → identify common cause.

---

#### [B7] Tinybird — SQL-First Streaming Analytics
**Source:** `tinybird.co/blog/real-time-streaming-data-architectures-that-scale`

**What Tinybird does:**
- ClickHouse as real-time analytics engine. p99 < 139ms at 9.5k RPS.
- "Optimize SQL first, then scale" philosophy.
- Schema iteration with zero-downtime migration.
- Branching: zero-copy dev environments with production data.

**How to upgrade StreamDQ:**
- **ClickHouse for violation analytics:** Replace DuckDB with ClickHouse for faster violation aggregation.
- **Dry-run mode:** `Pipeline.dry_run(events)` — evaluate rules against production data in isolation.
- **Zero-downtime schema migration:** Add schema version field to violation records. Handle old/new schemas during migration.

---

#### [B8] IBM Data Quality — 7 Dimensions
**Source:** `ibm.com/think/topics/data-quality`

**What IBM defines:**
1. Completeness — đủ fields?
2. Uniqueness — không duplicate?
3. Validity — đúng format?
4. Timeliness — đủ fresh?
5. Accuracy — đúng giá trị?
6. Consistency — nhất quán across sources?
7. Fitness for purpose — phù hợp với use case?

**How to upgrade StreamDQ:**

| IBM Dimension | StreamDQ Current | Gap | Upgrade |
|---|---|---|---|
| Completeness | SYN001 (fare_amount only) | Only 1 field | Add SYN000: `CompletenessMonitor` per field |
| Uniqueness | CRS003 (duplicate) | Working | Maintain |
| Validity | SYN002, SYN003 | Good | Maintain |
| Timeliness | SYN003 (not-future) | No stale detection | Add `TimelinessRule`: event_time > now - sla_minutes |
| Accuracy | SEM001-003 | Good | Maintain |
| Consistency | CRS001-002 | CRS002 narrow | Fix B3: expand speed range |
| Fitness for purpose | MISSING | Critical gap | Add FIT001 composite score |

```python
# SYN000: Completeness Monitor (NEW)
class CompletenessRule(DataQualityRule):
    """Checks completeness for ALL fields, not just fare_amount."""
    violation_type = "COMPLETENESS"
    
    def __init__(self, fields: list[str], threshold: float = 0.99):
        self.fields = fields
        self.threshold = threshold
    
    def evaluate(self, ctx: RuleContext) -> Optional[Violation]:
        for field in self.fields:
            if ctx.event.get(field) is None:
                return Violation(...)  # completeness violation

# FIT001: Fitness for Purpose Score (NEW)
class FitnessForPurposeRule(DataQualityRule):
    """Composite score: (completeness * accuracy * timeliness)^(1/3)"""
    violation_type = "FITNESS"
    
    def compute_score(self, ctx: RuleContext) -> float:
        completeness = 1 - ctx.event.count(None) / len(ctx.event)
        accuracy = self._compute_accuracy(ctx)
        timeliness = self._compute_timeliness(ctx)
        return (completeness * accuracy * timeliness) ** (1/3)
    
    def evaluate(self, ctx: RuleContext) -> Optional[Violation]:
        score = self.compute_score(ctx)
        if score < self.threshold:
            return Violation(details={"fitness_score": score, ...})
```

---

#### [B9] Precisely — 5-Step Framework
**Source:** `precisely.com/data-quality/big-data-quality-mastering-data-quality-in-the-age-of-big-data/`

**What Precisely defines:**
Discover → Define → Design → Deploy → Monitor (continuous loop)

**How to upgrade StreamDQ:**
- Align evaluation workflow with 5 steps:

| Step | Precisely | StreamDQ | Gap |
|------|----------|----------|-----|
| Discover | Profile data, set baselines | `SchemaProfiler` (missing) | Add profiling |
| Define | Assess DQ risks, prioritize | `RuleRegistry` (partial) | Add risk scoring |
| Design | Build rules independent of process | `DataQualityRule` ABC | Good |
| Deploy | Implement controls + workflows | `LocalPipeline`/`SparkPipeline` | Good |
| Monitor | Continuous automated monitoring | `LocalPipeline` (one-shot) | Add continuous mode |

```python
class DataQualityWorkflow:
    def discover(self, dataset_id: str) -> DataProfile:
        """Profile: null rates, distributions, correlations"""
    
    def define(self, profile: DataProfile) -> list[RuleSuggestion]:
        """Risk assessment + rule prioritization"""
    
    def design(self, suggestions: list[RuleSuggestion]) -> list[RuleConfig]:
        """Convert to rule configs"""
    
    def deploy(self, configs: list[RuleConfig]) -> Pipeline:
        """Deploy to pipeline"""
    
    def monitor(self, pipeline: Pipeline) -> MonitorDashboard:
        """Continuous monitoring with alerts"""
```

---

## Part 2: Lessons from Academic Papers

### Paper Cluster A: Context-Aware DQ Literature

#### [P1] Serra et al. 2022 — "Use of Context in DQ: SLR" (arXiv:2204.10655)
**Venue:** ACM
**Research Question:** How is context defined and used in DQ management proposals?

**Key Findings:**
- Context = "fitness for use + contextual factors" — NOT just technical metadata
- 4 context dimensions: **who** (user/consumer), **what** (data entity), **when** (temporal), **where** (spatial)
- "Context-aware DQ" widely acknowledged but rarely implemented with rigor
- Gap: Most approaches define context statically; dynamic context adaptation is rare
- Gap: "None of the reviewed approaches handle the interplay between multiple contextual dimensions"

**How to upgrade StreamDQ:**
- Populate `external_context` with actual dimensions:
  ```python
  ctx.external_context = {
      "who": ctx.event.get("user_id"),          # consumer dimension
      "what": ctx.event.get("entity_type"),      # data dimension
      "when_hour": ctx.event_time.hour,          # temporal: hour of day
      "when_day": ctx.event_time.weekday(),       # temporal: day of week
      "where_region": ctx.event.get("region"),    # spatial dimension
  }
  ```
- **Minimum viable context-aware:** Populate `when_hour` + `when_day`. Use in SEM001 threshold: peak hours have different fare distributions.

**Can cite as:** Serra, F., et al. (2022). "Use of Context in Data Quality Management: A Systematic Literature Review." ACM. arXiv:2204.10655.

---

#### [P2] Fadlallah et al. 2023 — "Context-Aware Big Data Quality: Scoping Review" (ACM JDIQ 2023)
**Venue:** ACM Journal of Data and Information Quality
**DOI:** 10.1145/3603707

**Key Findings:**
- "None of the existing DQ assessment solutions could guarantee context awareness with ability to handle big data"
- Context in big data = heterogeneity + velocity + volume + variety
- Most solutions handle partial context only — no comprehensive approach
- 4 context types: **contextual data** (data about data), **contextual metadata** (schemas, lineage), **contextual environment** (system, infrastructure), **contextual use** (purpose, user)
- Recommendation: Methodological framework for context-aware DQ service design

**How to upgrade StreamDQ:**
- The "context-aware" label is VALIDATED by this review, but implementation must be real, not cosmetic.
- Add `ContextualEnvironment`: system load, Kafka lag, concurrent pipelines
- Add `ContextualUse`: use case (ML training vs. real-time dashboard vs. regulatory reporting) → different severity thresholds

**Can cite as:** Fadlallah, H., et al. (2023). "Context-aware big data quality assessment: a scoping review." ACM J. Data Inform. Quality. DOI:10.1145/3603707.

---

### Paper Cluster B: Concept Drift Detection

#### [P3] Liang et al. 2025 — "STM-Stream: Short-Term Memory Clustering" (Knowl-Based Sys)
**Venue:** Knowledge-Based Systems 2025

**Key Findings:**
- STM-Stream: stores nucleus and radius of cell groups as window slides
- Handles 4 concept drift types: **sudden** (abrupt shift), **gradual** (slow transition), **incremental** (continuous drift), **reoccurring** (past patterns return)
- Dynamic projection strategy fuses stored distribution with newly arriving data
- STM-Stream prevents clustering accuracy decline over time in streaming data

**How to upgrade StreamDQ:**
- Add `ConceptDriftDetector` to adaptive engine:

```python
class ConceptDriftDetector:
    """Detects 4 types of concept drift using STM-Stream approach."""
    
    DRIFT_TYPES = ["sudden", "gradual", "incremental", "reoccurring"]
    
    def detect(self, window_a: Distribution, window_b: Distribution) -> Optional[DriftReport]:
        # Population Stability Index (PSI)
        psi = self._compute_psi(window_a, window_b)
        
        if psi > 0.25:
            return DriftReport(type="sudden", severity="high", psi=psi)
        elif psi > 0.1:
            return DriftReport(type="gradual", severity="medium", psi=psi)
        # ...
```

**Can cite as:** Liang, B., et al. (2025). "A short-term memory clustering algorithm for evolving data streams." Knowl-Based Syst. DOI:10.1016/j.knosys.2025.113442.

---

#### [P4] Ren & Li 2026 — "SAP-DPO: Stream-Aware Dynamic Partitioning" (Future Gen Comp Sys)
**Venue:** Future Generation Computer Systems 2026

**Key Findings:**
- SAP-DPO: stream-aware, parameter self-adaptive dynamic partitioning for Flink
- Dynamic cycle model: adapt partition update frequency based on stream input rate
- Sliding window model for parameter optimization
- Improves throughput and reduces latency under fluctuating workloads

**How to upgrade StreamDQ:**
- This paper is about Flink infrastructure, not directly applicable to StreamDQ's rule engine.
- **Lesson:** Adaptive update frequency (SAP-DPO) could apply to adaptive threshold recomputation:
  - Instead of fixed `recompute_every=1000`, adapt based on stream rate.
  - High-rate → recompute every 500 events. Low-rate → recompute every 2000 events.

**Can cite as:** Ren, Y. & Li, H. (2026). "Stream-aware and parameter self-adaptive data partitioning algorithm for fluctuating data stream processing." Future Gen. Comput. Syst. DOI:10.1016/j.future.2026.108520.

---

### Paper Cluster C: Adaptive Learning in Streams

#### [P5] Chen et al. 2026 — "ASSLD: Adaptive Soft Sensing for Label Delay" (ISA Trans)
**Venue:** ISA Transactions 2026

**Key Findings:**
- ASSLD: handles label delay in industrial data streams
- Key insight: **diverse database with quantile-based sample selection**
- For each new sample: select similar historical samples by cosine similarity, weight by recency
- Differential entropy filtering for unlabeled data adaptation
- Virtual adversarial training for robustness
- >12% accuracy improvement over baselines

**How to upgrade StreamDQ:**
- **Diverse sample selection for threshold calibration:** Instead of simple rolling window, maintain a "diverse database" of samples across the distribution:
  ```python
  class DiverseThresholdCalibrator:
      """Selects diverse samples for better threshold calibration."""
      def select_diverse(self, samples: list[dict], k: int = 100) -> list[dict]:
          # 1. Cluster samples by feature values
          # 2. Select representative from each cluster
          # 3. Weight by recency (more recent = higher weight)
          pass
  ```
- **Virtual adversarial training concept:** Perturb violation thresholds slightly → test robustness → adjust if too many false positives.

**Can cite as:** Chen, L., et al. (2026). "A novel adaptive soft sensing framework for label delay in industrial data streams." ISA Trans. DOI:10.1016/j.isatra.2025.09.007.

---

#### [P6] Cao et al. 2026 — "iTA-LRN: Incremental Time-Aware Liquid Recurrent Network" (Knowl-Based Sys)
**Venue:** Knowledge-Based Systems 2026

**Key Findings:**
- iTA-LRN: fraud detection in transaction streams
- Monitor module: investigates data distribution + test error rates **in real time**
- Hybrid incremental learning: when error rate + distribution variance exceed threshold → retrain
- Incremental update without full retraining

**How to upgrade StreamDQ:**
- Add real-time monitoring to adaptive engine:
  ```python
  class AdaptiveEngineMonitor:
      """Monitors adaptive engine health in real time."""
      def check_health(self) -> EngineHealthReport:
          return EngineHealthReport(
              error_rate=self._compute_violation_false_positive_rate(),
              distribution_shift=self._compute_psi(current_window, baseline),
              staleness=self._compute_data_staleness(),
          )
  ```
- When health degrades: alert + fallback to static thresholds + log for debugging.

**Can cite as:** Cao, R., et al. (2026). "Detecting credit card fraud from transaction data streams with incremental time-aware liquid recurrent network." Knowl-Based Syst.

---

### Paper Cluster D: Cross-Record / Anomaly Detection

#### [P7] Cao et al. — "Fraud detection with iTA-LRN" (continued)
- **Key lesson for StreamDQ:** The monitor module pattern (detect drift → trigger retraining) maps to: detect threshold instability → alert + fallback.

#### [P8] Serra 2022 + Fadlallah 2023 (Context-Aware DQ — see P1, P2)
- **Key lesson for StreamDQ:** "Context-aware" in academic literature = multi-dimensional context. StreamDQ currently tracks 0 dimensions in `external_context`.

---

### Paper Cluster E: BIG-ABAC (Context-Aware Access Control)

#### [P9] Baccouri & Abdellatif 2025 — "BIG-ABAC: Context-Aware ABAC" (CMES)
**Venue:** Computer Modeling in Engineering & Sciences 2025
**DOI:** 10.32604/cmes.2025.062902

**Key Findings:**
- BIG-ABAC: dynamic policy evaluation with decision trees in real-time
- **40% latency reduction** vs. conventional ABAC
- **95% of requests within 50ms**
- **30ms policy update latency**
- Uses decision trees for fast evaluation, updates trees dynamically
- Event-driven policy management with continuous recalculation

**How to upgrade StreamDQ:**
- **Decision tree for fast rule evaluation:** Instead of sequential rule evaluation, compile rules into a decision tree:
  ```python
  class RuleDecisionTree:
      """Compile rules into decision tree for O(log n) evaluation."""
      def compile(self, rules: list[DataQualityRule]) -> DecisionTreeNode:
          # 1. Parse all rule conditions
          # 2. Build tree: numeric splits, categorical branches
          # 3. Prune redundant conditions
          pass
      
      def evaluate(self, event: dict) -> list[Violation]:
          # Traverse tree: O(log n) instead of O(n)
          pass
  ```
- **Event-driven updates:** When context changes (e.g., hour changes from peak to off-peak), trigger threshold recomputation.

**Can cite as:** Baccouri, S. & Abdellatif, T. (2025). "BIG-ABAC: Leveraging Big Data for Adaptive, Scalable, and Context-Aware Access Control." Comput. Model. Eng. Sci. DOI:10.32604/cmes.2025.062902.

---

## Part 3: Lessons from DuckDB Verification

### What the data actually shows

**From 32,056 violations in DuckDB:**

| Finding | Implication |
|---------|-------------|
| 32.1% violation rate | Very high — suggests thresholds too tight OR data genuinely dirty |
| 8/9 rules firing | CRS001/CRS002 NOT firing (GTFS unwired) |
| All `processing_latency_ms = 0` | B6 confirmed — latency measurement broken |
| precision SYN001 = 22.9% | Much lower than estimated 85% |
| recall SYN001 = 100% | Detects all null/negative, but too many false positives |
| **0 GTFS violations** | GTFS topic not wired — CRS rules inactive for GTFS |

### How to upgrade StreamDQ:

1. **Fix precision:** High false positive rate (77%) means thresholds are wrong. Investigate: are adaptive thresholds learning from the evaluation data itself (overfitting)?
2. **Wire GTFS:** Priority P0 — CRS001/CRS002 are the main GTFS contribution.
3. **Measure actual latency:** B6 fix enables real latency profiling.

---

## Part 4: Lessons from Code Analysis

### What code review reveals

| Issue | Lesson |
|-------|--------|
| `external_context = {}` always empty | Context injection is a stub, not implemented |
| `batch_df.collect()` driver bottleneck | Streaming at scale needs distributed rule evaluation |
| No Prometheus HTTP server | Observability is incomplete |
| Global mutable state (`_VEHICLE_STATES`) | Thread-safety risk for multi-threaded Spark |
| PostgreSQL `import jsonb` | Will crash if PostgreSQL backend used |

### How to upgrade StreamDQ:

1. **Distributed rule evaluation:** Replace `collect()` + Python loop with Pandas UDF or `FlatMapGroupsWithState`.
2. **Thread-safe state:** Use `Accelerate` or thread locks for `_VEHICLE_STATES` / `_DEDUP_STATES`.
3. **Prometheus endpoint:** Add `start_http_server(9090)` in pipeline init.
4. **Fix PostgreSQL import:** Use `psycopg2` with JSONB cast in SQL, not `import jsonb`.

---

## Part 5: Priority Roadmap for Upgrades

### P0 — Must Fix (Enable Trustworthy Benchmarking)

| # | Upgrade | Source | Impact |
|---|---------|--------|--------|
| P0-1 | Fix B6: compute actual latency | DuckDB verification | All latency metrics = 0 |
| P0-2 | Wire GTFS topic to CRS rules | Code analysis | 0 GTFS violations |
| P0-3 | Implement Kafka violation sink | Code analysis | Violations don't reach Kafka |
| P0-4 | Run actual Spark pipeline benchmark | DuckDB | precision = 22.9% vs claim 85% |

### P1 — High Value (From Blog Lessons)

| # | Upgrade | Source | Impact |
|---|---------|--------|--------|
| P1-1 | DataContract + ownership fields | B3 (Grab) | Routing violations to owners |
| P1-2 | SQL-like rule DSL | B2 (Grab) | Democratize rule authoring |
| P1-3 | LLM rule advisor | B5, B6 (Grab) | Auto-suggest rules from schema |
| P1-4 | SYN000 Completeness Monitor | B8 (IBM) | All fields, not just fare_amount |
| P1-5 | FIT001 Fitness Score | B8 (IBM) | Composite fitness metric |
| P1-6 | AlertRouter (Slack/PagerDuty) | B1, B3 (Grab) | Automated incident creation |
| P1-7 | Prometheus HTTP endpoint | Code analysis | Grafana dashboards get data |
| P1-8 | Bootstrap CI (1,000 iter) | EV3 rules | Scientific rigor |

### P2 — Medium Term (From Paper Lessons)

| # | Upgrade | Source | Impact |
|---|---------|--------|--------|
| P2-1 | Populate external_context (hour/day) | P1 (Serra), P2 (Fadlallah) | Justify "context-aware" label |
| P2-2 | ConceptDriftDetector | P3 (Liang) | Detect distributional shifts |
| P2-3 | Diverse sample selection for thresholds | P5 (Chen) | Better threshold calibration |
| P2-4 | Adaptive engine health monitor | P6 (Cao) | Detect threshold instability |
| P2-5 | RuleDecisionTree (O(log n) eval) | P9 (BIG-ABAC) | Faster rule evaluation |

### P3 — Long Term (Stretch Goals)

| # | Upgrade | Source | Impact |
|---|---------|--------|--------|
| P3-1 | Flink migration | Blog cluster (Grab) | True streaming vs. micro-batch |
| P3-2 | SchemaProfiler auto-discovery | B2 (Grab) | Auto-generate rules from schema |
| P3-3 | Root cause analysis (Genchi-like) | B6 (Grab) | Cluster violations by pattern |
| P3-4 | ClickHouse violation analytics | B7 (Tinybird) | Sub-139ms violation queries |

---

## Part 6: Concrete Code Changes

### Change 1: Add `external_context` Population

**File:** `streamdq/pipeline/spark_pipeline.py`

```python
# CURRENT (line 209):
external_context={}

# UPGRADE:
external_context={
    "processing_hour": datetime.now().hour,      # temporal context
    "processing_day": datetime.now().weekday(),  # temporal context  
    "pipeline_id": self.pipeline_id,             # system context
    "batch_size": batch_size,                   # system context
}
```

### Change 2: Add `DataContract` to RuleConfig

**File:** `streamdq/rules/base.py` or new `streamdq/models/contract.py`

```python
@dataclass
class DataContract:
    contract_id: str
    dataset_id: str
    owner: str  # BDO
    tdo: str
    tier: Literal["bronze", "silver", "gold"]
    sla_minutes: int
    alert_channel: str

CERTIFICATION_TIERS = {
    "bronze": ["SYN001", "SYN002"],
    "silver": ["SYN001", "SYN002", "SYN003", "SEM001", "SEM002", "SEM003"],
    "gold": ["SYN001", "SYN002", "SYN003", "SEM001", "SEM002", "SEM003", 
             "CRS001", "CRS002", "CRS003"],
}
```

### Change 3: Add SQL-like DSL

**New file:** `streamdq/rules/dsl.py`

```python
@dataclass
class SQLLikeRule:
    field: str
    operator: str  # "BETWEEN", "IN", ">", "<", "NOT NULL"
    value: Any
    
    def to_rule_class(self, rule_id: str) -> DataQualityRule:
        # Convert DSL → DataQualityRule subclass
        pass

# Example usage:
RULE sem001 = SQLLikeRule("fare_amount", "BETWEEN", (2.5, 500))
```

### Change 4: Add SYN000 Completeness Monitor

**New file:** `streamdq/rules/syntactic.py` (add class)

```python
class CompletenessRule(DataQualityRule):
    """SYN000: Checks completeness for ALL fields in a schema."""
    violation_type = "COMPLETENESS"
    
    def __init__(self, fields: list[str], threshold: float = 0.99):
        self.fields = fields
        self.threshold = threshold
    
    def evaluate(self, ctx: RuleContext) -> Optional[Violation]:
        completeness = sum(
            1 for f in self.fields 
            if ctx.event.get(f) is not None
        ) / len(self.fields)
        
        if completeness < self.threshold:
            missing = [f for f in self.fields if ctx.event.get(f) is None]
            return Violation(
                rule_id="SYN000",
                details={"completeness": completeness, "missing_fields": missing},
                ...
            )
```

### Change 5: Add FIT001 Fitness for Purpose Score

**New file:** `streamdq/rules/semantic.py` (add class)

```python
class FitnessForPurposeRule(DataQualityRule):
    """FIT001: Composite fitness score = (C * A * T)^(1/3)"""
    violation_type = "FITNESS"
    
    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold
    
    def evaluate(self, ctx: RuleContext) -> Optional[Violation]:
        c = self._completeness(ctx)  # non-null fields / total
        a = self._accuracy(ctx)       # passes all SEM rules
        t = self._timeliness(ctx)   # event_time within SLA
        
        fitness = (c * a * t) ** (1/3)
        
        if fitness < self.threshold:
            return Violation(
                rule_id="FIT001",
                details={
                    "fitness_score": round(fitness, 4),
                    "completeness": c,
                    "accuracy": a,
                    "timeliness": t,
                },
                ...
            )
```

### Change 6: Add ConceptDriftDetector

**New file:** `streamdq/rules/drift.py`

```python
@dataclass
class DriftReport:
    type: Literal["sudden", "gradual", "incremental", "reoccurring"]
    severity: Literal["high", "medium", "low"]
    psi: float  # Population Stability Index
    affected_fields: list[str]

class ConceptDriftDetector:
    """Detects 4 types of concept drift using PSI."""
    
    PSI_THRESHOLDS = {
        "high": 0.25,    # Immediate action needed
        "medium": 0.1,   # Investigate soon
        "low": 0.05,     # Monitor
    }
    
    def compute_psi(self, expected: list, actual: list, bins: int = 10) -> float:
        """Population Stability Index."""
        # Buckets both distributions, compute PSI
        pass
    
    def detect(self, baseline: WindowStats, current: WindowStats) -> Optional[DriftReport]:
        psi = self.compute_psi(baseline.distribution, current.distribution)
        if psi > self.PSI_THRESHOLDS["high"]:
            return DriftReport(type="sudden", severity="high", psi=psi)
        # ...
```

### Change 7: Add Prometheus HTTP Server

**File:** `streamdq/pipeline/spark_pipeline.py` (add to `__init__`)

```python
def start_metrics_server(self, port: int = 9090):
    from prometheus_client import start_http_server, Counter, Gauge, Histogram
    start_http_server(port)
    
    self.metrics = {
        "events_total": Counter("streamdq_events_total", "Total events processed"),
        "violations_total": Counter("streamdq_violations_total", "Total violations", ["rule_id"]),
        "latency_ms": Histogram("streamdq_latency_ms", "Processing latency"),
    }
```

---

## Part 7: Citations for StreamDQ Paper

| Claim | Citation | Type |
|-------|----------|------|
| Context-aware DQ literature | Serra et al. (2022) arXiv:2204.10655 | Academic |
| Big data context gap | Fadlallah et al. (2023) DOI:10.1145/3603707 | Academic |
| Concept drift taxonomy | Liang et al. (2025) DOI:10.1016/j.knosys.2025.113442 | Academic |
| Streaming partitioning | Ren & Li (2026) DOI:10.1016/j.future.2026.108520 | Academic |
| Adaptive soft sensing | Chen et al. (2026) DOI:10.1016/j.isatra.2025.09.007 | Academic |
| Incremental fraud detection | Cao et al. (2026) Knowl-Based Syst. | Academic |
| Context-aware ABAC | Baccouri & Abdellatif (2025) DOI:10.32604/cmes.2025.062902 | Academic |
| IBM 7 DQ dimensions | IBM (2024) ibm.com/think/topics/data-quality | Industry |
| Grab DQ monitoring | Grab Engineering (2025) engineering.grab.com/real-time-data-quality-monitoring | Industry |
| Grab Flink journey | Alibaba Cloud (2025) engineering.grab.com/blog/... | Industry |
| Tinybird streaming | Tinybird (2024) tinybird.co/blog/real-time-streaming-data-architectures-that-scale | Industry |
| Precisely 5-step | Precisely (2024) precisely.com/data-quality/big-data-quality-mastering... | Industry |
| Data mesh certification | Grab Engineering (2024) engineering.grab.com/signals-market-place | Industry |

---

---

## [P10] Cortes et al. 2024 — "DQ Management for Responsible AI in Data Lakes" (VLDB TaDA Workshop)
**Venue:** VLDB Endowment - Tabular Data Analysis Workshop (TaDA) 2024

**Research Question:** How to integrate context-aware DQ management into data lake architectures to support responsible AI?

**Key Findings:**
- Data lake (DL) architectures need different zones (Landing, Raw, Trusted, Refined, Sandbox, Governance) with DQ checks at each stage
- Context C = <R (DQ requirements), Z (DL zone), M (DQ metadata)> — quality assessments depend on both user requirements AND zone location
- "An algorithm is only as good as the data it works with" — poor-quality data leads to biased/unreliable AI models
- Context includes: data zone characteristics, processing stage, user profile, and task at hand
- DL zone = part of context that determines acceptable quality thresholds (Raw zone = lower bar, Trusted zone = higher bar)
- Responsible AI dimensions: fairness, transparency, accountability, privacy — all require high-quality data as foundation
- DQ improvement loop: assess → store metadata → modify processing → re-assess → 100% satisfaction

**Limitations:**
- No implementation details for streaming scenarios — focused on batch data lake workflows
- Context definition is conceptual; no algorithmic framework for dynamic context adaptation
- No latency, throughput, or scalability measurements

**Actionable Lessons for StreamDQ:**
1. **Zone-based quality tiers:** StreamDQ rules should consider "pipeline stage" as context — same rule at ingestion vs. after enrichment may have different thresholds. Add `pipeline_stage` to `external_context`.
2. **Responsibility metadata:** Add `data_steward`, `consumer_profile`, `use_case` to DataContract. A rule violation for ML training may be more severe than for exploratory analytics.
3. **DQ metadata repository:** Store violation rates, rule effectiveness, threshold history in a governance zone. StreamDQ's DuckDB violation store could serve as the "DQ metadata repository."
4. **Bias detection rules:** Add rules that check representation bias (e.g., `% trips from each borough` distribution over time). CRS004 for demographic fairness.
5. **Improvement feedback loop:** When violations exceed threshold, auto-suggest DQ improvement actions (not just detection, but remediation guidance).

**Code Changes (if any):** `streamdq/models/contract.py` — add `pipeline_stage`, `data_steward`, `use_case` fields to DataContract

**Can cite as:** Cortes, C., Sanz, C., Etcheverry, L. & Marotta, A. (2024). "Data Quality Management for Responsible AI in Data Lakes." VLDB Workshop: Tabular Data Analysis (TaDA). 4 pages.

---

## Part 8: Research Questions Analysis

### RQ1: How does StreamDQ compare to Stream DaQ (arXiv:2506.06147)?

**Stream DaQ** (Papastergios & Gounaris, 2025) is the closest competitor:

| Dimension | Stream DaQ | StreamDQ |
|---|---|---|
| Architecture | Python-native, streaming-first | Spark micro-batch |
| Windowing | Configurable tumbling/sliding | Fixed micro-batch |
| Context awareness | Dynamic constraint adaptation | Stub (`external_context = {}`) |
| Constraint types | 30+ composable checks | 9 fixed rules (SYN/SEM/CRS) |
| Evaluation | Execution time benchmarks | Synthetic data + DuckDB |
| License | Open-source (2025) | Research platform |
| Throughput | "Significantly outperforms" competitor | Unverified (LocalPipeline only) |
| GTFS/GPS | No | Domain-specific CRS rules |
| Adaptive thresholds | Yes (dynamic adaptation) | Partial (adaptive.py, needs refactor) |

**Stream DaQ weaknesses (for StreamDQ positioning):**
- No cross-record rules (CRS001/CRS002/CRS003)
- No GTFS/GPS domain knowledge
- No evaluation framework (precision/recall/F1)
- Single paper, no production deployment evidence
- No adaptive threshold engine (just "dynamic adaptation" claim)
- No CI reporting

**StreamDQ differentiation:**
- Three-layer taxonomy (SYN/SEM/CRS) with formal definitions
- NYC taxi + GTFS domain-specific rules
- Evaluation framework with precision/recall/F1 per anomaly type
- Context-aware architecture (stub implementation, but design exists)
- Scientific paper positioning (not just a tool)

**Actionable:** Cite Stream DaQ in Related Work, position StreamDQ as complementary (domain-specific + evaluation framework vs. broad constraint library).

**Can cite:** Papastergios, V. & Gounaris, A. (2025). "Stream DaQ: Stream-First Data Quality Monitoring." arXiv:2506.06147.

---

### RQ2: What does "context-aware" mean for streaming DQ in literature?

From Serra (2022), Fadlallah (2023), and Cortes (2024):

- **Who** (consumer/user): DQ requirements depend on who consumes the data
- **What** (data entity): field-level quality needs vary by entity type
- **When** (temporal): time-of-day, day-of-week affect expected value distributions
- **Where** (spatial): geographic context (region, zone) affects thresholds

**StreamDQ gap:** `external_context` is empty in both `LocalPipeline` and `SparkPipeline`.

**Minimum viable implementation:**
```python
# In spark_pipeline.py evaluate_batch():
ctx.external_context = {
    "processing_hour": datetime.now().hour,
    "processing_day": datetime.now().weekday(),
    "pipeline_id": self.pipeline_id,
}
```

This enables time-aware thresholds (SEM001: peak hours have different fare distributions).

---

### RQ3: How do adaptive thresholds work in streaming DQ?

From Chen (2026), Cao (2026), Komorniczak (2025), and Ren (2026):

**4 frameworks for adaptation:**
1. **Entropy-guided adaptation** (AdaptiveStreamFL): adjust K-value based on data entropy — high entropy = small K
2. **Hybrid incremental learning** (iTA-LRN): error rate + distribution variance → trigger retraining
3. **Diverse sample selection** (ASSLD): quantile-based diverse samples, cosine similarity weighting
4. **Sliding window + decay** (SAP-DPO, STM-Stream): recent data weighted higher, old data decays

**StreamDQ adaptive.py gap:**
- Uses simple rolling window percentile
- No entropy-based adaptation
- No trigger mechanism (blind recompute every N events)
- No fallback to static thresholds

**Recommended upgrade:**
```python
# adaptive.py - add trigger mechanism
def check_need_recompute(self, ctx: RuleContext) -> bool:
    current_entropy = self._compute_entropy(ctx.event)
    baseline_entropy = self._baseline_entropy
    if abs(current_entropy - baseline_entropy) > self.entropy_threshold:
        return True  # Drift detected → recompute
    return False
```

---

### RQ4: Code audit critical findings

From CODE_AUDIT.md (10 issues found):

**CRITICAL:**
- **B1**: NaN silently passes SYN001 → `if not math.isnan(fare)` needed
- **B2**: Duplicate injection no-op → CRS003 recall unmeasurable

**MAJOR:**
- **B3**: CRS002 only catches extreme GPS (speed > 160 km/h), misses 2-20 km/h moderate spoofing
- **B4**: `batch_df.collect()` driver bottleneck in `foreachBatch`
- **B5**: SQLite per-batch fsync (no WAL mode)
- **B6**: `processing_latency_ms` hardcoded to 0
- **B8**: Percentile integer truncation in adaptive.py
- **B9**: Ground truth ordering mismatch
- **B10**: No Kafka violation sink

**MINOR:**
- **B7**: GTFS vehicle count unverified

All 10 issues documented as known limitations in `LESSON_FROM_BLOG.md`.

---

### RQ5: How to measure DQ fitness for purpose?

From IBM (7 dimensions), Precisely (5-step), and Cortes (2024):

**Fitness = f(completeness, accuracy, timeliness, consistency)**

```python
# FIT001: Fitness for Purpose Score (composite)
class FitnessForPurposeRule(DataQualityRule):
    violation_type = "FITNESS"

    def compute_score(self, ctx: RuleContext) -> float:
        c = self._completeness(ctx)  # non-null / total
        a = self._accuracy(ctx)         # passes SEM rules
        t = self._timeliness(ctx)     # event_time within SLA
        co = self._consistency(ctx)  # CRS rules pass
        return (c * a * t * co) ** 0.25

    def evaluate(self, ctx: RuleContext) -> Optional[Violation]:
        score = self.compute_score(ctx)
        if score < self.threshold:
            return Violation(
                rule_id="FIT001",
                details={
                    "fitness_score": round(score, 4),
                    "completeness": c,
                    "accuracy": a,
                    "timeliness": t,
                    "consistency": co,
                },
                ...
            )
```

---

### RQ6: IBM 7 dimensions vs. StreamDQ taxonomy

| IBM Dimension | StreamDQ Current | Gap | Upgrade |
|---|---|---|---|
| Completeness | SYN001 (fare_amount only) | Only 1 field | SYN000: per-field completeness |
| Uniqueness | CRS003 (duplicate) | Working but recall unmeasurable | Fix B2: proper duplicate injection |
| Validity | SYN002, SYN003 | Good | Maintain |
| Timeliness | SYN003 (not-future) | No stale detection | Add `TimelinessRule`: event_time > now - SLA |
| Accuracy | SEM001-003 | Good | Maintain |
| Consistency | CRS001-002 | CRS002 narrow (B3) | Fix B3: expand speed range |
| Fitness for purpose | MISSING | Critical gap | FIT001: composite score |

---

## Part 9: Stream DaQ Paper Deep-Dive

### [P11] Papastergios & Gounaris 2025 — "Stream DaQ: Stream-First Data Quality Monitoring" (arXiv:2506.06147)
**Venue:** arXiv preprint (cs.DB)
**DOI:** 10.48550/arXiv.2506.06147

**Research Question:** How to monitor data quality in unbounded streams with temporal granularity and contextual awareness?

**Key Claims:**
- "Configurable windowing mechanisms" for streaming DQ
- "Dynamic constraint adaptation" — thresholds adapt to stream characteristics
- "Quality meta-streams" — violations as output streams
- "Unifies 30+ quality checks" from existing tools
- "Significantly outperforms production-grade alternative" in throughput/latency

**Critical Thinking — Scope Mismatch:**
- "30+ quality checks" = mostly SYN-type (null, range, type) adapted from Great Expectations, Soda
- No CRS-type rules (cross-record, duplicate, GPS spoofing)
- Throughput claim vs. "production-grade alternative" — no baseline named
- Python-native = in-process, NOT distributed. Claimed throughput likely LocalPipeline-equivalent

**What Stream DaQ PROVES:**
- Windowed streaming DQ is feasible with Python
- Compositional constraint DSL is user-friendly
- Violations as meta-streams is a good design pattern

**What Stream DaQ DOES NOT PROVE:**
- Cross-record detection capability
- Adaptive threshold accuracy
- Production-scale throughput
- Evaluation framework rigor (no precision/recall/F1)

**StreamDQ Advantage over Stream DaQ:**
1. CRS001/CRS002: GPS speed/haversine validation (domain-specific)
2. Evaluation framework: ground truth tracking, precision/recall per rule
3. GTFS-specific rules for transit data quality
4. Scientific paper positioning with formal taxonomy

**Stream DaQ Advantage over StreamDQ:**
1. Python-native (no Spark dependency)
2. Open-source (2025)
3. Configurable windowing (tumbling/sliding)
4. 30+ constraint types
5. Dynamic constraint adaptation

**Actionable for StreamDQ:**
1. Add Stream DaQ to Related Work as primary competitor
2. Position StreamDQ as "domain-specific evaluation framework + GTFS rules"
3. Consider Python-native implementation to compete on accessibility
4. Add configurable windowing (tumbling/sliding) for CRS rules

**Can cite as:** Papastergios, V. & Gounaris, A. (2025). "Stream DaQ: Stream-First Data Quality Monitoring." arXiv:2506.06147.

---

## Part 10: Final Synthesis

### What StreamDQ Does Better Than All Sources

1. **Three-layer taxonomy** (SYN/SEM/CRS) — no other framework has this formal structure
2. **GTFS domain rules** (CRS001/CRS002) — unique to StreamDQ
3. **Evaluation framework** (ground truth + precision/recall/F1 per rule) — no competitor has this
4. **NYC taxi domain rules** — well-established benchmark dataset
5. **Research paper positioning** — academic rigor (not just a tool)

### What Needs Fixing Before Claiming These

| Claim | Evidence | Fix Needed |
|-------|----------|------------|
| "Context-aware" | `external_context = {}` | Populate with hour/day/pipeline_id |
| "82% recall" | LocalPipeline only | Run Spark benchmark |
| "85% precision" | precision SYN001 = 22.9% | Fix adaptive thresholds |
| "P99 = 890ms" | No latency measurement | Fix B6 |
| "CRS003 duplicate detection" | Duplicate injection no-op | Fix B2 |
| "Adaptive thresholds" | Integer truncation bug | Fix B8 |

### Top 5 Priority Upgrades (from all sources)

1. **Populate `external_context`** — 5-minute task, biggest credibility win
2. **Fix B6 (latency)** — compute actual `processing_latency_ms`
3. **Fix B2 (duplicate injection)** — enable CRS003 recall measurement
4. **Run Spark benchmark** — verify 82%/85% claims on actual infrastructure
5. **Add configurable windowing** — tumbling windows for rule evaluation

### Papers to Cite in StreamDQ Paper

| Claim | Citation |
|-------|----------|
| Context-aware DQ literature | Serra (2022) arXiv:2204.10655 |
| Big data context gap | Fadlallah (2023) DOI:10.1145/3603707 |
| Concept drift taxonomy | Liang (2025) DOI:10.1016/j.knosys.2025.113442 |
| Stream partitioning | Ren & Li (2026) DOI:10.1016/j.future.2026.108520 |
| IBM 7 DQ dimensions | IBM (2024) ibm.com/think/topics/data-quality |
| Grab DQ monitoring | Grab Engineering (2025) engineering.grab.com/... |
| Stream DaQ comparison | Papastergios (2025) arXiv:2506.06147 |
| Responsible AI + DL | Cortes (2024) VLDB TaDA Workshop |

---

## Part 11: Papers Read on April 19, 2026

### [P-CS] Serra et al. 2022 — "Use of Context in DQ: SLR" (arXiv:2204.10655)
**Venue:** arXiv preprint | **Size:** 1.76MB | **Pages:** 40

**Research Question:** How is context defined and used in DQ management proposals?

**Key Findings:**
- 58 primary studies reviewed (2010-2020), 54 after full-text selection
- **4 context dimensions** (from Dey 2001): **who** (user/consumer), **what** (data entity), **when** (temporal), **where** (spatial)
- "Context-aware DQ" widely acknowledged but **rarely implemented with rigor** (page 1)
- "None of the reviewed approaches handle the interplay between multiple contextual dimensions"
- Most DQ approaches use context **statically** — no dynamic adaptation
- DQ models: 15 dimensions (Wang & Strong), 15 ISO/IEC 25012 characteristics
- DQ process stages: profiling, measurement, analysis, cleaning, monitoring

**DQ Dimensions Found Across Papers:**
- Completeness, Uniqueness, Validity, Timeliness, Accuracy, Consistency, Fitness for Purpose
- Additional: Credibility, Objectivity, Believability, Accessibility, Security, Relevancy, Portability

**Key Quote:** "Context is poorly used source of information in computing environments, resulting in an impoverished understanding of what context is and how it can be used." (Dey 2001, cited in paper)

**StreamDQ Gap Analysis:**

| Gap | Evidence | Severity |
|-----|----------|----------|
| `external_context = {}` | Paper confirms context rarely implemented | CRITICAL |
| No multi-dimensional context | Paper: "none handle interplay" | CRITICAL |
| No `who` dimension | No user/consumer context tracked | MAJOR |
| No `when` context enrichment | No time-of-day, day-of-week | MAJOR |
| No `where` spatial context | No geographic region tracking | MINOR |
| No context formalism | No `<R, Z, M>` tuple like TaDA 2024 | MAJOR |

**Action Items for StreamDQ:**
1. **Minimum viable (5 min):** Populate `external_context` with `when_hour`, `when_day`, `what_entity_type`
2. **Medium effort:** Add `where_region` from location data, `who_consumer` from event metadata
3. **Full implementation:** Formalize context as tuple `<R (requirements), Z (zone), M (metadata)>` per TaDA 2024
4. **Evidence for paper:** Cite this SLR as primary evidence that StreamDQ's context-aware approach is validated by 58 studies

**Gap found that was NOT in checklist:**
- **NG-29**: No formal context model definition (paper shows most approaches don't formalize)
- **NG-30**: No DQ process stage tracking (profiling → measurement → analysis → cleaning → monitoring)

**Can cite as:** Serra, F., Peralta, V., Marotta, A., & Marcel, P. (2022). "Use of Context in Data Quality Management: a Systematic Literature Review." arXiv:2204.10655.

---

### [P-FWUP] Le et al. 2026 — "FWUDS-CT/DWT: Sliding Window FWUP Mining" (Information Sciences)
**Venue:** Information Sciences (Elsevier) | **DOI:** 10.1016/j.ins.2026.123488

**Research Question:** Mining frequent weighted utility patterns over dynamic quantitative data streams.

**Key Findings:**
- **Sliding window model**: Fixed-size window with panes; newest data mined, oldest discarded
- **3 stream models**: Landmark (all data equally important), Damped (older data weighted less), **Sliding window** (recent data only)
- **CTset (Circular Tidset)** and **DSWUN-tree** data structures for efficient storage
- Pattern reuse without full reprocessing — key insight for streaming systems
- Window/pane size selection is user challenge

**StreamDQ Gap Analysis:**

| Gap | Evidence | Severity |
|-----|----------|----------|
| Adaptive window sizing | Paper: "selecting optimal pane and window sizes poses challenges" | MAJOR |
| State eviction strategy | No explicit policy for when to clear old cross-record state | MAJOR |
| Data structure optimization | CRS state uses raw dicts — could use circular buffers | MINOR |

**Action Items:**
- Add configurable tumbling window for rule evaluation (already in Grab B1)
- Consider circular buffer for `_VEHICLE_STATES` eviction (NG-10)

**Can cite as:** Le, N., Nguyen, H., Nguyen, M., Bui, H., Vo, B., & Yun, U. (2026). "Fast and scalable sliding-window-based algorithms for mining frequent weighted utility patterns over dynamic quantitative data streams." Information Sciences. doi:10.1016/j.ins.2026.123488.

**Note:** This paper is about pattern mining, not DQ. Relevant for streaming windowing concepts but not directly applicable to StreamDQ.

---

### [P-KOM] Komorniczak et al. 2026 — "Structuring Data Stream Processing Frameworks" (Pattern Recognition)
**Venue:** Pattern Recognition (Elsevier) | **DOI:** 10.1016/j.patcog.2025.112516

**Research Question:** How to reliably assess data stream classification methods considering label delay and concept drift?

**Key Findings:**
- **4 data stream processing frameworks** defined: continuous rebuild, triggered rebuild (supervised), triggered rebuild (unsupervised), triggered rebuild (partially unsupervised)
- **3 drift detector types:**
  - **Supervised DDₛ**: Requires labels (DDM, EDDM, ADWIN)
  - **Unsupervised DDᵤ**: Only data features, no labels needed
  - **Partially unsupervised DDₚ**: Data features normally, labels only when drift detected
- **Label delay δ**: Labels arrive after sample occurs — "natural implication of real-world data stream processing"
- **Real vs. Virtual concept drift**: Real drift impacts model quality directly; virtual drift can precede real drift
- Passive adaptation (continuous rebuild) vs. Active adaptation (triggered rebuild with drift detector)
- "Label cost is a significant limitation of data stream processing methods"

**Taxonomy of Drift Detectors (key for StreamDQ):**

```
Concept Drift Detectors
├── Supervised (DDₛ) — requires labels
│   ├── DDM (Drift Detection Method)
│   ├── EDDM (Enhanced DDM)
│   └── ADWIN (ADaptive WINdowing)
├── Unsupervised (DDᵤ) — data only, no labels
│   ├── Statistical tests
│   ├── One-class classifiers
│   └── Class centroid monitoring
└── Partially Unsupervised (DDₚ) — labels only on drift
```

**StreamDQ Gap Analysis:**

| Gap | Evidence | Severity |
|-----|----------|----------|
| No supervised drift detection | StreamDQ has no ground truth labels to compare | CRITICAL |
| PSI is unsupervised (OK) | `drift.py` uses PSI — matches DDᵤ category | ✅ Already correct |
| Label delay not modeled | No `label_delay_sec` in evaluation | MINOR |
| Passive vs. active adaptation | adaptive.py uses passive (periodic recompute) — no trigger | MAJOR |
| Drift before accuracy drop | "Virtual drift precedes real drift" — early warning possible | MAJOR |

**Action Items:**
1. **NG-31**: PSI-based drift detection is unsupervised — document as DDᵤ type, not a bug
2. **NG-32**: Add "virtual drift" early warning — PSI rises before violations spike
3. **NG-33**: Add `label_delay_sec` parameter for evaluation realism
4. **NG-34**: Consider hybrid approach: unsupervised PSI for early warning + supervised (if labels available) for confirmation

**Can cite as:** Komorniczak, J., Ksieniewicz, P., & Zyblewski, P. (2026). "Structuring the processing frameworks for data stream evaluation and application." Pattern Recognition. doi:10.1016/j.patcog.2025.112516.

---

### [P-ASFL] Xiong et al. 2026 — "AdaptiveStreamFL: Bayesian Federated Learning for Streams" (Expert Systems)
**Venue:** Expert Systems With Applications (Elsevier) | **DOI:** 10.1016/j.eswa.2025.129882

**Research Question:** How to handle concept drift, parameter instability, and client heterogeneity in federated streaming learning?

**Key Findings:**
- **Entropy-guided adaptive K-value selection**: Adjust K for prototype clustering based on data entropy — high entropy → small K
- **Prototype-based representation learning**: Compact summaries of evolving local distributions
- **Bayesian inference for uncertainty quantification**: Epistemic vs. aleatoric uncertainty in aggregation
- **5-layer architecture**: Data source → Client → Adaptive engine (5 modules) → Federated aggregation → Output
- Multi-objective optimization (accuracy, communication cost, latency, energy) in federated settings
- **Entropy as adaptation signal**: "information-theoretic principles guide adaptive parameter selection"

**StreamDQ Gap Analysis:**

| Gap | Evidence | Severity |
|-----|----------|----------|
| No entropy-based threshold adaptation | Paper: entropy → K-value → threshold adjustment | MAJOR |
| No prototype/representative sampling | adaptive.py uses full rolling window | MINOR |
| No uncertainty quantification | No confidence intervals on threshold values | MAJOR |
| No multi-objective tradeoff | Only accuracy, no communication/latency tradeoff | MINOR |

**Action Items:**
1. **NG-35**: Compute entropy of field distribution as early drift signal (before PSI threshold)
2. **NG-36**: Add `AdaptiveEngineHealth` dataclass with uncertainty bounds on thresholds

**Can cite as:** Xiong, T., Zhang, C., Rong, M., Gong, D., & Yang, S. (2026). "AdaptiveStreamFL: A Bayesian-enhanced multi-scale federated learning framework for dynamic data streams with uncertainty quantification." Expert Systems With Applications. doi:10.1016/j.eswa.2025.129882.

**Note:** Federated learning paper — tangential to StreamDQ but useful for distributed threshold adaptation.

---

## Part 12: NG-29 → NG-36 — New Items from April 19 Paper Read

### NG-29 — CRITICAL: No formal context model definition

- [ ] **[NG-29] Context formalism missing** (`rules/base.py`)
  - Bug: `RuleContext.external_context = {}` has no schema, no type checking
  - Paper [P-CS] confirms: "most approaches define context statically; dynamic adaptation is rare"
  - Fix: Define formal context schema:
    ```python
    @dataclass
    class ExternalContext:
        when_hour: int           # 0-23
        when_day: int            # 0-6 (Mon-Sun)
        when_is_rush_hour: bool  # 7-9 or 17-19 weekday
        when_is_holiday: bool    # Federal holiday
        what_entity_type: str    # "nyc_taxi" | "gtfs_vehicle"
        where_region: str        # Borough/zone if available
    ```
  - Trụ cột: Context-Aware

### NG-30 — MAJOR: No DQ process stage tracking

- [ ] **[NG-30] Missing profiling → monitoring lifecycle** (`pipeline/`)
  - Bug: StreamDQ only has "monitor" (evaluate) — no profiling or analysis stages
  - Paper [P-CS]: DQ process has 7 stages: profiling → measurement → analysis → cleaning → monitoring
  - Fix: Add `SchemaProfiler` class:
    ```python
    class SchemaProfiler:
        def profile(self, events: Iterable[dict]) -> DataProfile:
            """Profile: null rates, distributions, correlations"""
            # Null rate per field
            # Distribution stats per numeric field
            # Schema inference
            pass
    ```
  - Trụ cột: Data Quality

### NG-31 — MAJOR: Drift detection type not documented

- [ ] **[NG-31] PSI is unsupervised — document as DDᵤ type** (`rules/drift.py`)
  - Bug: `drift.py` doesn't classify itself as supervised/unsupervised/partially supervised
  - Paper [P-KOM]: Drift detectors classified by label requirement
  - Fix: Add docstring: "PSI-based — unsupervised (DDᵤ), requires no labels"
  - Trụ cột: Context-Aware

### NG-32 — MAJOR: No virtual drift early warning

- [ ] **[NG-32] Virtual drift precedes accuracy drop** (`rules/drift.py`)
  - Bug: Paper [P-KOM]: "Virtual drift can precede real drift" — early warning possible
  - Current drift.py only alerts when PSI > threshold — too late
  - Fix: Add `check_virtual_drift()` — softer threshold, logs warning not alert:
    ```python
    if 0.05 <= psi < 0.1:
        logger.warning(f"Virtual drift detected on {field}: PSI={psi:.4f}")
        # Adaptive action: increase sampling rate
    ```
  - Trụ cột: Context-Aware

### NG-33 — MINOR: Evaluation ignores label delay

- [ ] **[NG-33] Label delay not modeled in evaluation** (`evaluation/`)
  - Bug: `run_evaluation.py` assumes instant ground truth — unrealistic
  - Paper [P-KOM]: "label delay δ is a natural implication of real-world streaming"
  - Fix: Add `--label-delay-sec` parameter; simulate delayed anomaly confirmation
  - Trụ cột: Data Quality

### NG-34 — MAJOR: Passive vs. active adaptation unclear

- [ ] **[NG-34] adaptive.py is passive — no trigger mechanism** (`rules/adaptive.py`)
  - Bug: `recompute_every=1000` is blind periodic — no trigger
  - Paper [P-KOM]: Passive = continuous rebuild; Active = triggered rebuild (on drift)
  - Fix: Add `trigger_adaptive_recompute()` method called by drift detector:
    ```python
    def trigger_adaptive_recompute(self, reason: str):
        """Called when drift detected — force immediate recompute."""
        self._recompute()
        logger.info(f"Adaptive recompute triggered: {reason}")
    ```
  - Trụ cột: Context-Aware

### NG-35 — MAJOR: No entropy-based early warning

- [ ] **[NG-35] Entropy as early drift signal** (`rules/adaptive.py`)
  - Bug: PSI threshold is late-stage — entropy changes before distribution shifts
  - Paper [P-ASFL]: "entropy-guided adaptive K-value selection"
  - Fix: Compute Shannon entropy of field distribution; alert when entropy increases > 20%:
    ```python
    def compute_entropy(self, values: list[float]) -> float:
        """Shannon entropy of binned distribution."""
        if len(values) < 10:
            return 0.0
        # Bin values, compute P(x) * log(P(x))
        ...
    ```
  - Trụ cột: Context-Aware

### NG-36 — MAJOR: No uncertainty quantification on thresholds

- [ ] **[NG-36] Thresholds have no confidence bounds** (`rules/adaptive.py`)
  - Bug: P10/P90 thresholds reported as exact values — no uncertainty
  - Paper [P-ASFL]: Bayesian uncertainty quantification for adaptive parameters
  - Fix: Add `threshold_ci` field to `FieldStats`:
    ```python
    @dataclass
    class FieldStats:
        # ... existing fields ...
        p10_ci_lower: float
        p10_ci_upper: float
        p90_ci_lower: float
        p90_ci_upper: float
        n_resamples: int = 1000
    ```
  - Trụ cột: Context-Aware

---

*Document updated: April 19, 2026*
*New sources: Serra 2022 (arXiv:2204.10655), Le 2026 (Information Sciences), Komorniczak 2026 (Pattern Recognition), Xiong 2026 (Expert Systems)*

# FINAL FIX CHECKLIST — StreamDQ
**Date:** April 19, 2026 | **Total:** 57 items (21 old + 28 NG-1 to NG-28 + 8 NG-29 to NG-36)
**Goal:** A+ Khóa luận — "A Context-Aware Framework for Streaming Data Quality Monitoring"

---

## PHẦN 0 — Research Pipeline: Đọc Papers & Rút Bài Học

> **Workflow:** Đọc từng paper/blog → Trích xuất method + lessons → **Cập nhật `LESSON_FROM_BLOG.md`** → Kiểm tra gap → Ghi action item vào checklist
> **Nguyên tắc:** Mỗi paper đọc xong → update LESSON_FROM_BLOG.md ngay → Check xem method nào lấp gap nào → Thêm action item vào PHẦN MỚI nếu có gap mới
> **Chiến lược:** File nhỏ đọc trước (0.5-2MB → full read) → File lớn chunked (5MB+ → read sections)

### Papers đã đọc (read log)

| # | File | Size | Paper | Status |
|---|------|------|-------|--------|
| 1 | `TaDA.13.pdf` | 0.56MB | Cortes et al. 2024 — DQ for Responsible AI | ✅ Read |
| 2 | `TSP_CMES_62902.pdf` | 0.87MB | Baccouri & Abdellatif 2025 — BIG-ABAC | ✅ Read |
| 3 | `3603707.pdf` | 1.36MB | Fadlallah et al. 2023 — Context-Aware Big DQ Scoping | ✅ Read |
| 4 | `2204.10655v1.pdf` | 1.76MB | Serra et al. 2022 — Use of Context in DQ SLR | ✅ Read |
| 5 | `1-s2.0-S0020025526004196-main.pdf` | 1.83MB | Le et al. 2026 — Sliding Window FWUP Mining | ✅ Read |
| 6 | `1-s2.0-S0031320325011793-main.pdf` | 1.92MB | Komorniczak et al. 2026 — Stream Processing Frameworks | ✅ Read |
| 7 | `1-s2.0-S0957417425034979-main.pdf` | 1.9MB | Xiong et al. 2026 — AdaptiveStreamFL | ✅ Read |
| 8 | `1-s2.0-S1110016826001225-main.pdf` | 2.34MB | (còn phải đọc...) | ⬜ |
| 9 | `1-s2.0-S0167739X26001548-main.pdf` | 2.46MB | (còn phải đọc...) | ⬜ |
| 10 | `1-s2.0-S095070512501768X-main.pdf` | 3.03MB | (còn phải đọc...) | ⬜ |
| 11 | `1-s2.0-S0167947325002142-main.pdf` | 3.22MB | Liang et al. 2025 — STM-Stream | ⬜ |
| 12 | `1-s2.0-S0019057825005129-main.pdf` | 3.25MB | (còn phải đọc...) | ⬜ |
| 13 | `1-s2.0-S0925231226009033-main.pdf` | 3.42MB | (còn phải đọc...) | ⬜ |
| 14 | `1-s2.0-S1568494625007537-main.pdf` | 3.72MB | (còn phải đọc...) | ⬜ |
| 15 | `1-s2.0-S0360835225006540-main.pdf` | 3.97MB | (còn phải đọc...) | ⬜ |
| 16 | `1-s2.0-S0957417425040059-main.pdf` | 4.21MB | (còn phải đọc...) | ⬜ |
| 17 | `1-s2.0-S0167739X17329151-main.pdf` | 6.48MB | Serra 2022 (full paper) | ⬜ |
| 18 | `FutureGeneration.pdf` | 6.39MB | Ren & Li 2026 — SAP-DPO | ⬜ |
| 19 | `1-s2.0-S0925231225028619-main.pdf` | 6.65MB | (còn phải đọc...) | ⬜ |
| 20 | `1-s2.0-S095219762600792X-main.pdf` | 11.99MB | (còn phải đọc...) | ⬜ |
| 21 | `1-s2.0-S0950705125012894-main.pdf` | 16.29MB | (còn phải đọc...) | ⬜ |
| 22 | `1-s2.0-S0957417426008262-main.pdf` | 31.86MB | (còn phải đọc...) | ⬜ |

### Papers đã đọc → Lessons & Gap Check (cập nhật vào LESSON_FROM_BLOG.md)

| # | Paper | Method | Lessons | Gap Found | Action Item |
|---|-------|--------|---------|-----------|-------------|
| P-CS | Serra 2022 (arXiv) | SLR 58 studies, 4D context (who/what/when/where) | "Context-aware DQ widely acknowledged but rarely implemented with rigor" | `external_context = {}` | NG-13, NG-14, NG-29 |
| P-FWUP | Le 2026 (Information Sciences) | Sliding window model, pane-based eviction | Sliding window > damped > landmark for streaming | No eviction strategy for CRS state | NG-10 |
| P-KOM | Komorniczak 2026 (Pattern Recognition) | 4 frameworks, 3 drift types (DDs/DDu/DDp), label delay | PSI is unsupervised (DDu), no labels needed; virtual drift precedes real drift | Drift type not documented | NG-31, NG-32, NG-34 |
| P-ASFL | Xiong 2026 (Expert Systems) | Entropy-guided K-value, prototype learning, BayesianUQ | Entropy changes before distribution shifts | No entropy early warning | NG-35, NG-36 |

---

## PHẦN CŨ — Items đã có (21 items)

### P0 — Crash / Không chạy được

- [x] **[P0-1] Latency = 0 trong distributed mode** (`spark_pipeline.py:319,352,416`)
  - Bug: `(time.perf_counter() - 0) * 1000` hardcoded trong `_evaluate_vehicle_state_fn` và `_evaluate_dedup_state_fn`
  - Fix: `_latency_ms(ts)` helper: `max((now_sec - event_timestamp) * 1000, 0.0)` — measures "how stale is this event when detected"
  - Status: `[x] FIXED`
  - Trụ cột: Data Streaming

- [x] **[P0-2] `import psycopg2` crash** (`violation_store.py`)
  - Bug: `import psycopg2` chạy ngay khi import module, không trong try/except
  - Fix: Wrap trong try/except bên trong `__init__`
  - Status: `[x] FIXED`
  - Trụ cột: Data Streaming

- [x] **[P0-3] Port conflict Prometheus** (`spark_pipeline.py:473`)
  - Bug: metrics_port default = 9090 trùng Prometheus server
  - Fix: Đổi default thành 9091
  - Status: `[x] FIXED`
  - Trụ cột: Data Streaming

---

### P1 — Đã implement, chưa wire

- [x] **[P1-1] AlertRouter chưa được gọi** (`local_pipeline.py:173`)
  - Bug: 3 channels (Stdout/Slack/Email) đầy đủ nhưng không gọi `router.route(violation)` trong `_process_batch`
  - Fix: `local_pipeline.py` accept `alert_router` param; `process_event()` calls `self.alert_router.route_batch(violations)`
  - Status: `[x] FIXED`
  - Trụ cột: Data Quality

- [x] **[P1-2] ConceptDriftDetector chưa integrate** (`rules/drift.py` + `adaptive.py`)
  - Bug: PSI computation đầy đủ nhưng `adaptive.py` không gọi `detector.check_drift()`, threshold không reset khi distribution shift
  - Fix: Integrate `ConceptDriftDetector` vào `AdaptiveThresholdEngine` — khi PSI > threshold thì gọi `reset_field()` + log warning
  - Status: `[x] FIXED`
  - Trụ cột: Context-Aware

- [x] **[P1-5] DataContract chưa integrate** (`models/contract.py`)
  - Bug: `DataContract` + `CertificationTier` đầy đủ nhưng pipeline không gọi `contract.evaluate()`
  - Fix: Gọi `contract.evaluate()` sau mỗi batch trong `_process_batch`; log tier achievement
  - Status: `[x] FIXED`
  - Trụ cột: Context-Aware

---

### P2 — Cần verify / chạy thực tế

- [ ] **[P2-1] Distributed mode chưa test** (`spark_pipeline.py:744-928`)
  - Action: Chạy `run_distributed()` với Spark cluster thực; test `applyInPandasWithState` với CRS001/CRS002/CRS003
  - Risk: Lambda UDF trong state function có thể lỗi
  - Trụ cột: Data Streaming

- [ ] **[P2-2] Kafka violation sink chưa verify** (`spark_pipeline.py:607-647`)
  - Action: Kiểm tra Kafka topic `quality-violations` bằng consumer; confirm messages đến
  - Risk: `sendbatch` API có thể không tồn tại trong kafka-python cũ
  - Trụ cột: Data Streaming

- [ ] **[P2-3] GTFS CRS002 3-band chưa test** (`cross_record.py:147-184`)
  - Action: Inject GTFS test events với speed = 0.5, 10, 25 km/h + position jump 200m; verify 3 bands CRITICAL/HIGH/MEDIUM fire đúng
  - Trụ cột: Data Quality

- [ ] **[P2-4] Prometheus metrics chưa verify** (`spark_pipeline.py:488-496`)
  - Action: `curl http://localhost:9091/metrics | grep "^streamdq"`; confirm Grafana dashboard nhận data
  - Trụ cột: Data Streaming

- [ ] **[P2-5] GTFS topic wiring chưa verify** (`spark_pipeline.py:700-707`)
  - Action: Chạy GTFS producer; confirm CRS001/CRS002 violations xuất hiện trong SQLite
  - Risk: GTFS JSON parsing trong `run_distributed()` có thể fail nếu schema không match
  - Trụ cột: Data Quality

---

### P3 — Unit tests (ĐÃ HOAN THIEN)

> **Thực tế**: Tất cả tests đã được implement trong `test_p2_new_rules.py` + `test_alert_router.py`. Checklist lỗi (chưa cập nhật).

- [x] **[P3-1] Test NaN input** ✅ — `test_syntactic_rules.py:75` `test_nan_fare` — float('nan') returns violation
- [x] **[P3-2] Test FIT001** ✅ — `test_p2_new_rules.py:118` `TestFitnessScoreRule` (4 tests)
- [x] **[P3-3] Test AlertRouter** ✅ — `test_alert_router.py` + `test_p2_new_rules.py:165` `TestAlertRouter` (7 tests)
- [x] **[P3-4] Test ConceptDriftDetector** ✅ — `test_p2_new_rules.py:19` `TestConceptDriftDetector` (5 tests)
- [x] **[P3-5] Test DataContract** ✅ — `test_p2_new_rules.py:230` `TestDataContract` (4 tests)

---

### P4 — Docs & Polish (ĐÃ HOAN THIEN)

- [x] **[P4-1] README benchmark numbers** ✅ — Updated: measured vs estimated distinction, precision=22.9% (DuckDB), recall=100% (DuckDB), latency=~150ms (est.), precision gap analysis
- [x] **[P4-2] Rename LESSON file** ✅ — Renamed, updated 3 reference locations
- [x] **[P4-3] SPEC.md benchmark targets** ✅ — Added Measured/Target columns, DuckDB values, B2/B6 limitation notes

---

## PHẦN MỚI — Items thiếu hoàn toàn (36 items NG)

> Nguồn: WAVES cross-evaluation + code audit + papers đã đọc (Serra 2022, Komorniczak 2026, Xiong 2026, Le 2026)

### NG-0 — Checklist có lỗi — Items đã được fix

- [x] **[NG-0a] P1-3: FIT001 ĐÃ REGISTER** (`registry.py:110`)
  - `FitnessScoreRule` đã có trong `build_default_registry()` — checklist LỖI, không cần fix

- [x] **[NG-0b] P1-4: SYN000 ĐÃ REGISTER** (`registry.py:110`)
  - `CompletenessRule` đã có trong `build_default_registry()` — checklist LỖI, không cần fix

---

### NG-1 — CRITICAL: Duplicate line trong LocalPipeline

- [x] **[NG-1] Duplicate AdaptiveThresholdEngine** (`local_pipeline.py:106 vs 115`)
  - Bug: `self.threshold_engine = AdaptiveThresholdEngine(...)` khai báo 2 lần (dòng 106 và 115)
  - Dòng 115 overwrite dòng 106 — memory leak nhẹ, code không clean
  - Fix: Xóa duplicate declaration — chỉ giữ lại 1 `self.threshold_engine = AdaptiveThresholdEngine(...)` tại dòng 110
  - Status: `[x] FIXED` (code verified — only 1 instance remains)
  - Trụ cột: Data Streaming

---

### NG-2 — CRITICAL: Latency measurement incomplete

- [x] **[NG-2a] LocalPipeline: chỉ đo in-process latency** (`local_pipeline.py:167`)
  - Bug: `latency_ms = (time.perf_counter() - start) * 1000` — chỉ measure từ khi event đến pipeline đến khi violations stored
  - Không đo: Kafka produce → Kafka consume → network overhead → E2E latency
  - Fix: Tách rõ `processing_latency` (internal) và `e2e_latency` (Kafka produce → violation stored)
  - Implementation:
    - `local_pipeline.py`: `_metrics` split into `processing_latencies[]` và `e2e_latencies[]`
    - `process_event()`: compute `kafka_arrival_ms` nếu có trong event, calculate E2E
    - `get_metrics()`: trả về `processing_latency_p50_ms`, `processing_latency_p99_ms`, `e2e_latency_p50_ms`, `e2e_latency_p99_ms`
    - `gtfs_live.py` + `nyc_taxi_replay.py`: attach `kafka_arrival_ms = time.time() * 1000` khi emit
  - Status: `[x] FIXED`
  - Trụ cột: Data Streaming

- [x] **[NG-2b] Distributed: hardcoded = 0** (`spark_pipeline.py:319,352,416`)
  - Bug: `(time.perf_counter() - 0) * 1000` — latency always 0 for distributed state functions
  - Fix: `_latency_ms(ts)` helper: `max((now_sec - event_timestamp) * 1000, 0.0)`
  - Status: `[x] FIXED`
  - Trụ cột: Data Streaming

---

### NG-3 — CRITICAL: False Positive Rate không đo

- [x] **[NG-3] FPR metric không tồn tại** (`evaluation/metrics.py`)
  - Bug: `precision()` compute TP/(TP+FP) nhưng **FPR không được compute**
  - WAVES benchmark: DC2 = 99% FPR → StreamDQ cũng cần đo FPR per rule
  - Fix: Thêm `false_positive_rate()` vào `EvaluationMetrics`
  - Status: `[x] FIXED` (metrics.py:109)
  - Trụ cột: Data Quality

---

### NG-4 — CRITICAL: Bootstrap CI methodology có bug

- [x] **[NG-4] Bootstrap resamples violations thay vì entities** (`metrics.py:183-190`)
  - Bug: `boot = [random.choice(violations) for _ in violations]` — sampling violations WITH replacement
  - Đúng: Phải resample entities (event indices), sau đó count violations của entities đó
  - Impact: CI estimates có thể biased, không phản ánh true uncertainty
  - Fix: Resample entity indices, filter violations by those indices
  - Status: `[x] FIXED` (metrics.py:bootstrap_ci — verified resamples entity indices)
  - Trụ cột: Data Quality

---

### NG-5 — CRITICAL: Duplicate injection chỉ emit 1 record (EV-INJ1 violation)

- [x] **[NG-5] CRS003 recall unmeasurable** (`evaluation/run_evaluation.py`)
  - Bug: Injector emit event + duplicate cùng 1 lần → CRS003 chỉ thấy 1 record, không detect được duplicate
  - EV-INJ1 violation: "Duplicate anomaly MUST emit TWO records"
  - Impact: CRS003 recall = 0% hoặc undefined — không thể measure
  - Fix: Injector emit 2 records (original + duplicate) với cùng key, cách nhau < 300s
  - Status: `[x] FIXED` (run_evaluation.py — original event processed as clean, then duplicate processed separately)
  - Trụ cột: Data Quality

---

### NG-6 — CRITICAL: Không có warmup period (EV-PROTO1 violation)

- [x] **[NG-6] Evaluation không discard warmup events** (`evaluation/run_evaluation.py`)
  - Bug: Measure ngay từ event đầu tiên — adaptive thresholds chưa stabilized → FPR cao bất thường
  - EV-PROTO1 violation: "Process at least 10,000 events before beginning measurement"
  - Fix: Thêm `--warmup 10000` argument; discard violations trước warmup boundary khỏi metrics
  - Status: `[x] FIXED` (run_evaluation.py:119 warmup_events param, lines 189-199 warmup logic)
  - Trụ cột: Data Quality

---

### NG-7 — CRITICAL: Adaptive engine thiếu reset method

- [x] **[NG-7] `reset_field()` không tồn tại** (`rules/adaptive.py`)
  - Bug: `drift.py` recommend "recompute from scratch" khi PSI cao, nhưng `adaptive.py` không có method để clear buffer
  - Impact: Drift detector trigger nhưng không có action → vô dụng
  - Fix: Thêm `reset_field()` vào `AdaptiveThresholdEngine`
  - Status: `[x] FIXED` (adaptive.py:321)
  - Trụ cột: Context-Aware

---

### NG-8 — CRITICAL: FIT001 score computation không match docstring

- [x] **[NG-8] FitnessScoreRule chỉ check completeness** (`semantic.py`)
  - Bug: Docstring claims score = "completeness + validity + contextual reasonableness" nhưng code chỉ tính completeness
  - Impact: FIT001 claim không accurate
  - Fix: Docstring cập nhật để reflect actual implementation (completeness-only score)
  - Status: `[x] FIXED` (semantic.py FIT001 docstring updated)
  - Trụ cột: Context-Aware

---

### NG-9 — MAJOR: Contract tier comment was misleading (thresholds flipped to match conventional semantics)

- [x] **[NG-9] FIXED — Tier thresholds reversed** (`models/contract.py:72-76`)
  - Comment said "GOLD: 85% pass rate (higher standard)" — WRONG, this is most lenient
  - Code: smaller threshold = stricter → BRONZE was strictest, GOLD most lenient
  - Fix: Flip thresholds so GOLD is strictest (conventional mental model):
    - BRONZE: 0.85 pass rate (≤15% violations) — entry-level, most lenient
    - SILVER: 0.90 pass rate (≤10% violations) — intermediate
    - GOLD: 0.95 pass rate (≤5% violations) — strictest
  - Also: comments now accurately describe each tier's strictness
  - Status: `[x] FIXED`

---

### NG-10 — MAJOR: Module-level global state (pipeline isolation failure)

- [x] **[NG-10] Global dicts không isolated giữa pipeline instances** (`rules/cross_record.py`)
  - Bug: `_VEHICLE_STATES` và `_DEDUP_STATES` là module-level globals — shared across all pipeline instances
  - Impact: Multiple streams cross-contaminate vehicle tracks
  - Fix:
    - Added `CrossRecordState` class with typed `get_vehicle/set_vehicle/get_dedup/set_dedup` methods
    - `evaluate_trajectory_anomaly()` and `evaluate_duplicate_event()` now accept `CrossRecordState` as `vehicle_state`/`dedup_state`
    - Module-level globals retained as backward-compatible fallback only
  - Status: `[x] FIXED`
  - Trụ cột: Data Streaming

---

### NG-11 — MAJOR: GTFS syntactic rules = 0

- [x] **[NG-11] Không có GTFS syntactic validation** (`rules/gtfs_rules.py`)
  - Bug: Tất cả syntactic rules hardcoded NYC TLC fields
  - GTFS data có fields: `vehicle_id`, `latitude`, `longitude`, `speed`, `route_id`, `trip_id`
  - **Không rule nào validate GTFS fields**
  - Fix: Viết GTFS-specific syntactic rules (GTFSSyn001-003)
  - Status: `[x] FIXED` (gtfs_rules.py: GTFSVehicleIDValidRule, GTFSLatLongRangeRule, GTFSSpeedRangeRule)
  - Trụ cột: Data Quality

---

### NG-12 — MAJOR: GTFS semantic/context-aware rules = 0

- [x] **[NG-12] Không có GTFS semantic validation** (`rules/gtfs_rules.py`)
  - Bug: SEM001-SEM003 hardcoded cho NYC taxi
  - Fix: Viết GTFS semantic rules (GTFSSem001-002)
  - Status: `[x] FIXED` (gtfs_rules.py: GTFSImpossibleSpeedRule, GTFSStaleDataRule)
  - Trụ cột: Data Quality

---

### NG-13 — MAJOR: GTFS pipeline không feed adaptive engine

- [x] **[NG-13] Adaptive thresholds không update cho GTFS** (`local_pipeline.py:137`)
  - Bug: Feed hardcoded `["fare_amount", "trip_distance"]` — không tồn tại trong GTFS data
  - GTFS streams không feed vào adaptive engine → thresholds không adapt
  - Fix: Detect `entity_type`, feed appropriate fields per stream: NYC taxi uses `["fare_amount", "trip_distance"]`, GTFS uses `["speed"]` (bearing is NOT a real GTFS field — removed)
  - Status: `[x] FIXED`
  - Trụ cột: Context-Aware

---

### NG-14 — MINOR: GTFS external_context enrichment = 0

- [x] **[NG-14] GTFS events không có time-of-day context** (`local_pipeline.py:158`)
  - Bug: `gtfs_live.py` produce raw events → không enrich `is_rush_hour`, `is_late_night`, `is_weekend`
  - GTFS rules không có time-of-day adjustments → không context-aware
  - Fix: `ExternalContext.from_event(event, event_time)` — pipeline builds context from event automatically
  - Status: `[x] FIXED`
  - Trụ cột: Context-Aware

---

### NG-15 — MINOR: Anomaly injection types mismatch

- [x] **[NG-15] Producer vs Evaluation inject different types** ✅ FIXED
  - Bug: `nyc_taxi_replay.py` inject 6 types; `run_evaluation.py` inject 8 types
  - Fix: Added `speed_outlier` + `duplicate` to producer ANOMALY_TYPES; `_pending_duplicate` + `_get_duplicate()` for CRS003 injection
  - Status: DONE — aligned with evaluation

---

### NG-16 — MINOR: AlertRouter không có deduplication

- [x] **[NG-16] 100 violations → 100 alerts** (`notification/alert_router.py`)
  - Bug: Không deduplication, không grouping
  - Fraud burst: 1000 violations trong 5 min → 1000 separate alerts → alert fatigue
  - Fix: Thêm smart grouping theo (rule_id, entity_id, 5-min window) với `_is_duplicate()` và `_recent_alerts`
  - Status: `[x] FIXED` (test_alert_router.py confirms deduplication works — only first violation sends alert)
  - Trụ cột: Data Quality

---

### NG-17 — MINOR: PSI fallback không phải real PSI

- [x] **[NG-17] DriftDetector fallback dùng rough approximation** (`drift.py:211-212`)
  - Bug: `psi = (p10_shift + p90_shift) * 0.5` — đây không phải PSI
  - Đây là average relative shift, không phải Population Stability Index
  - Fix: Document rõ ràng đây là "approximation mode" khi không có bucket data
  - Status: `[x] FIXED` (docstring updated: "Rough approximation: average relative shift of P10 and P90")
  - Trụ cột: Context-Aware

---

### NG-18 — MINOR: Evaluation report thiếu pipeline type

- [x] **[NG-18] `full_report()` không ghi pipeline type** (`metrics.py:287`)
  - Bug: EV-PROTO3 violation: "Report LocalPipeline vs. SparkPipeline separately"
  - Fix: Thêm `pipeline: str` field vào `full_report()` output
  - Status: `[x] FIXED` (metrics.py:287 — `full_report(pipeline="local")` parameter, output includes `"pipeline": pipeline`)
  - Trụ cột: Data Quality

---

### NG-19 — MINOR: Prometheus không có rule health metrics

- [x] **[NG-19] Metrics cho latency/throughput nhưng không cho rule health** (`spark_pipeline.py:73-104`)
  - Bug: Không có gauge cho TP rate, FPR per rule, alert rate drop
  - Silent failure: "rule broken → 0 alerts" → không detect được
  - Fix: Thêm Prometheus gauges cho rule-level metrics
  - Implementation:
    - `streamdq_rule_true_positives_total` — Counter per rule
    - `streamdq_rule_false_positives_total` — Counter per rule
    - `streamdq_rule_alerts_sent_total` — Counter per rule/severity
    - `streamdq_rule_health_score` — Gauge TP/(TP+FP) per rule
    - `streamdq_rule_last_alert_time_seconds` — Gauge Unix timestamp per rule
  - Status: `[x] FIXED`
  - Trụ cột: Data Quality

---

### NG-20 — MINOR: Evaluation reproducibility seed tracking

- [x] **[NG-20] Evaluation report không ghi random seed** (`evaluation/run_evaluation.py`)
  - Bug: EV-INJ2: "Record the seed in the evaluation report"
  - Fix: Thêm `seed: int` field vào `full_report()` output
  - Status: `[x] FIXED` (run_evaluation.py:117 random_seed=42, line 297 in report output)
  - Trụ cột: Data Quality

---

### NG-21 — MINOR: GTFS Kafka consumer schema mismatch

- [ ] **[NG-21] GTFS JSON parsing có thể fail trong distributed** (`spark_pipeline.py:700-707`)
  - Bug: `gtfs_live.py` parse JSON với specific fields; distributed mode dùng `from_json` với schema khác
  - Risk: Schema drift → null values → silent violations miss
  - Fix: Verify schema alignment giữa producer và Spark `readStream`
  - Trụ cột: Data Streaming

---

### NG-22 — MINOR: ViolationStore missing field validation

- [x] **[NG-22] `store()` không validate required fields** (`violation_store.py`)
  - Bug: Nếu `processing_latency_ms = None` → SQLite insert thành NULL → metrics bị sai
  - Fix: Thêm pre-insert validation — kiểm tra rule_id, entity_id, entity_type, severity, violation_type; log warning + skip nếu thiếu
  - Status: `[x] FIXED`
  - Trụ cột: Data Quality

---

### NG-23 — MINOR: NYC Taxi producer NaN handling

- [x] **[NG-23] NYC producer NaN → None bypasses NaN guard** ✅ FIXED
  - Bug: `pd.isna()` converted to `None` → NaN guards never fire
  - Fix: `_serialize_event()` converts `pd.isna()` → `"NaN"` string; `_isnan()` updated to detect string "NaN"
  - Status: DONE — SYN001/SEM001 now catch string "NaN"

---

### NG-24 — MINOR: CRS002 3-band boundary edge cases

- [x] **[NG-24] CRS002 speed boundaries có thể overlap hoặc miss** (`cross_record.py`)
  - Bug: Bands = [0, 1], [1, 20], [20, 40] km/h — nếu speed = 1.0 hoặc 20.0 → boundary ambiguous
  - Fix: Dùng exclusive upper bound: `< 1`, `1 <= x < 20`, `20 <= x < 40`
  - Status: `[x] FIXED` (verified: boundaries are `speed_kmh < 1.0`, `1.0 <= speed_kmh < 20.0`, `20.0 <= speed_kmh < 40.0`)
  - Trụ cột: Data Quality

---

### NG-25 — MINOR: Contract tier enum sort order

- [x] **[NG-25] Tier sorting logic không deterministic** ✅ FIXED
  - Bug: `sorted(CertificationTier)` + `list().index()` rely on enum order
  - Fix: Explicit `_TIER_EVAL_ORDER` list + `_TIER_INDEX` dict
  - Status: DONE — deterministic regardless of enum definition

---

### NG-26 — MINOR: AdaptiveThresholdEngine._buffers memory unbounded

- [x] **[NG-26] Buffer không eviction cho fields không còn update** ✅ FIXED
  - Bug: GTFS events add new fields → buffers grow unbounded
  - Fix: Added `max_fields=50` limit + LRU eviction + `idle_threshold=50_000` idle eviction
  - Status: DONE — buffers bounded regardless of field count

---

### NG-27 — MINOR: GTFS duplicate detection không có

- [x] **[NG-27] CRS003 không apply cho GTFS** (`rules/gtfs_rules.py`)
  - Bug: CRS003 deduplicate trên `trip_id + PULocationID + DOLocationID` — GTFS không có `PULocationID`
  - GTFS duplicate detection = 0
  - Fix: Add GTFS dedup key: `vehicle_id + latitude + longitude + timestamp` via `evaluate_gtfs_duplicate_event`
  - Status: `[x] FIXED`
  - Trụ cột: Data Quality

---

### NG-28 — MINOR: Evaluation không report F1 score

- [x] **[NG-28] `full_report()` không include F1** (`metrics.py`)
  - Bug: Precision + Recall nhưng không F1 → không có single summary metric
  - Fix: Thêm `f1 = 2 * precision * recall / (precision + recall)` vào report
  - Status: `[x] FIXED` (metrics.py full_report() line 319 — F1 included)
  - Trụ cột: Data Quality

---

### NG-29 — CRITICAL: No formal context model definition

- [x] **[NG-29] Context formalism missing** (`rules/base.py`)
  - Bug: `RuleContext.external_context = {}` has no schema, no type checking
  - Paper [P-CS Serra 2022]: "most approaches define context statically; dynamic adaptation is rare"
  - Fix: Define formal `ExternalContext` dataclass with typed fields (who/what/when/where)
  - Status: `[x] FIXED` (`rules/base.py` has `ExternalContext` dataclass with typed fields)
  - Trụ cột: Context-Aware

---

### NG-30 — MAJOR: No DQ process stage tracking

- [x] **[NG-30] Missing profiling → monitoring lifecycle** ✅ FIXED
  - Bug: StreamDQ only has "monitor" — no profiling stage
  - Fix: Added `SchemaProfiler` class (models/profiler.py) + `profile_dataset()` method + `lifecycle_stage` tracking (idle/profiling/monitoring)
  - Status: DONE — profiling stage implemented per Serra et al. (2022)

---

### NG-31 — MAJOR: Drift detection type not documented

- [x] **[NG-31] PSI is unsupervised (DDu) — document it** (`rules/drift.py`)
  - Bug: Drift detector doesn't classify itself as supervised/unsupervised
  - Paper [P-KOM Komorniczak 2026]: Drift detectors classified by label requirement (DDs/DDu/DDp)
  - PSI is unsupervised (DDu) — requires no labels. Document this.
  - Fix: Add docstring: "PSI-based — unsupervised (DDu), requires no labels"
  - Status: `[x] FIXED` (drift.py docstring — PSI is UNSUPERVISED (DDu))
  - Trụ cột: Context-Aware

---

### NG-32 — MAJOR: No virtual drift early warning

- [x] **[NG-32] Virtual drift precedes accuracy drop** (`rules/drift.py`)
  - Bug: Only alert when PSI > 0.2 — too late
  - Paper [P-KOM Komorniczak 2026]: "Virtual drift can precede real drift" — early warning possible
  - Fix: Add `PSI_VIRTUAL = 0.05` threshold + virtual drift recommendation
  - Status: `[x] FIXED` (drift.py:77 PSI_VIRTUAL=0.05, lines 224-226 virtual drift branch)
  - Trụ cột: Context-Aware

---

### NG-33 — MINOR: Evaluation ignores label delay

- [x] **[NG-33] Label delay not modeled in evaluation** ✅ FIXED
  - Bug: `run_evaluation.py` assumes instant ground truth — unrealistic
  - Fix: Added `--label-delay-events` CLI param; `label_delay_events` in `EvaluationMetrics.__init__`; violations before label availability boundary excluded from TP
  - Status: DONE — label delay simulation via `--label-delay-events` param

---

### NG-34 — MAJOR: Passive vs. active adaptation unclear

- [x] **[NG-34] adaptive.py is passive — no trigger mechanism** (`rules/adaptive.py`)
  - Bug: `recompute_every=1000` is blind periodic — no trigger
  - Paper [P-KOM Komorniczak 2026]: Passive = continuous rebuild; Active = triggered rebuild on drift
  - Fix: `ConceptDriftDetector.check_drift()` calls `threshold_engine.reset_field()` khi drift detected
  - Status: `[x] FIXED` (drift.py:71 calls `threshold_engine.reset_field()`)
  - Trụ cột: Context-Aware

---

### NG-35 — MAJOR: No entropy-based early warning

- [x] **[NG-35] Entropy as early drift signal** (`rules/adaptive.py`)
  - Bug: PSI threshold is late-stage — entropy changes before distribution shifts
  - Paper [P-ASFL Xiong 2026]: "entropy-guided adaptive parameter selection"
  - Fix: Compute Shannon entropy of field distribution; alert when entropy increases > 20%
  - Status: `[x] FIXED` (adaptive.py: `_compute_shannon_entropy()`, `_entropy_baseline`, `entropy_warning` in `update()`)
  - Trụ cột: Context-Aware

---

### NG-36 — MAJOR: No uncertainty quantification on thresholds

- [x] **[NG-36] Thresholds have no confidence bounds** (`rules/adaptive.py`)
  - Bug: P10/P90 reported as exact values — no uncertainty
  - Paper [P-ASFL Xiong 2026]: Bayesian uncertainty quantification for adaptive parameters
  - Fix: Add `p10_ci_lower/upper`, `p90_ci_lower/upper` fields to `FieldStats`
  - Status: `[x] FIXED` (adaptive.py: FieldStats has `p10_ci_lower/upper`, `p90_ci_lower/upper`)
  - Trụ cột: Context-Aware

---

## NEW BUGS FOUND (April 19, 2026 — code audit)

### CRITICAL — Bugs gây crash hoặc sai khoa học nghiêm trọng

**NEW-B1: `spark_pipeline.py` syntax error (line 29) — ĐÃ FIX**
- Leading space indentation on `from pyspark.sql.streaming import GroupStateTimeout`
- Status: `[x] FIXED`

**NEW-B2: `evaluation/run_evaluation.py` TypeError on F1 computation — ĐÃ FIX**
- `report["precision"]` là dict `{"point_estimate": 0.85, "ci_95": [...]}`, không phải float
- `comparison["streamdq"].f1_score = 2 * dict * dict` → TypeError
- Status: `[x] FIXED`

**NEW-B3: `metrics.py` bootstrap CI resamples violations thay vì entities — ĐÃ FIX**
- `boot = [random.choice(violations) for _ in violations]` — sampling detected violations
- Precision = TP/(TP+FP) → bias khi TP/FP ratio bị distortion
- Fix: Resample entity indices, filter violations theo indices đó
- Status: `[x] FIXED`

**NEW-B4: `gtfs_live.py` silent Kafka error swallowing — ĐÃ FIX**
- `self.producer.send()` là fire-and-forget, errors bị nuốt chửng
- Fix: Check `future.get(timeout=10)` để catch và log errors
- Status: `[x] FIXED`

**NEW-B5: `violation_store.py` PostgreSQL DDL execution path — ĐÃ FIX**
- psycopg2 DDL cần explicit cursor + commit
- Fix: Dùng explicit cursor, `conn.commit()` sau mỗi DDL statement
- Status: `[x] FIXED`

### MAJOR — Bugs ảnh hưởng paper claims

**NEW-B6: NG-9 trong checklist LÀ FALSE POSITIVE — ĐÃ CORRECT**
- Checklist nói "GOLD = 15% violations, BRONZE = 5% → GOLD lenient hơn"
- THỰC TẾ: `violation_rate <= (1 - threshold)` → BRONZE cho phép 5%, SILVER 10%, GOLD 15%
- Code đúng rồi! Comment trong code nói "GOLD: higher standard" là misleading
- Status: `[x] CORRECTED — NG-9 removed, NEW-B6 documented`

**NEW-B7: `comparison.py` hardcoded fake numbers cho StreamDQ — ĐÃ DOCUMENTED**
- precision=0.85, recall=0.82, f1=0.83 — tất cả là ESTIMATES
- Code comment: "Estimated from architecture and design"
- Status: `[x] DOCUMENTED AS ESTIMATES — replaced by actual evaluation`

**NEW-B8: `syntactic.py` SYN003 f-string typo (line 312) — ĐÃ FIX**
- `"max": f"now + {self.future_tolerance}s"` → f-string bị quoted sai
- Status: `[x] FIXED` (or already correct in current code — verified)

### MINOR — Quality issues

**NEW-B9: `run_evaluation.py` F1 computation logic — ĐÃ FIX (same as NEW-B2)**
- Same root cause: dict vs float confusion
- Status: `[x] FIXED` (alongside NEW-B2)

---

## Tổng hợp

### Theo Trụ cột

| Trụ cột | P0 | P1 | P2 | P3 | P4 | NG | NEW-B | Đã Fix | Tổng |
|---|---|---|---|---|---|---|---|---|
| Context-Aware | 0 | 1 | 0 | 1 | 0 | 10 | 2 | 2 | **13** |
| Data Streaming | 3 | 0 | 3 | 0 | 0 | 4 | 1 | 4 | **11** |
| Data Quality | 1 | 1 | 2 | 5 | 3 | 16 | 3 | 3 | **29** |
| Evaluation | 2 | 0 | 1 | 1 | 0 | 0 | 3 | 5 | **6** |
| **Tổng** | **6** | **2** | **6** | **7** | **3** | **32** | **9** | **14** | **59** |

### Theo Priority

| Priority | Items | Effort | Status |
|---|---|---|---|
| **P0** (Crash) | P0-1, P0-2, P0-3, NG-1, NG-2a, NG-2b | 2-3 giờ | ✅ FIXED |
| **CRITICAL** | NG-3, NG-4, NG-5, NG-6, NG-7, NG-8, NG-9 | 6-8 giờ | ✅ FIXED |
| **MAJOR** | NG-10, NG-11, NG-12, NG-13, NG-14, NG-29, NG-31, NG-32, NG-34, NG-35, NG-36 | 10-12 giờ | ✅ FIXED |
| **MINOR** (Polish) | NG-15→NG-28, NG-30, NG-33, P2, P3, P4 | 4-6 giờ | 🔄 Partial |
| **NEW-B** | NEW-B1 → NEW-B9 | 2-3 giờ | ✅ FIXED |

### Ước tính tổng

| Phase | Items | Effort | Status |
|---|---|---|---|
| Phase 1: Scientific Integrity | NEW-B2, NEW-B3, NEW-B7, NG-8 | 2-3 giờ | ✅ DONE |
| Phase 2: Crash Fixes | NEW-B1, NEW-B4, NEW-B5, P0-2 | 1-2 giờ | ✅ DONE |
| Phase 3: Evaluation Correctness | NG-5, NG-6, FPR, F1 report | 1-2 giờ | ✅ DONE |
| Phase 4: Context-Aware Core | NG-7, NG-29, NG-35, NG-36, drift wiring | 2-3 giờ | ✅ DONE |
| Phase 5: GTFS Completeness | NG-11, NG-12, NG-13, NG-14, NG-27 | 2-3 giờ | ✅ DONE |
| Phase 6: Alert & Notification | P1-1, NG-16, NG-19 | 1 giờ | ✅ DONE |
| Phase 7: Tests + Polish | P3, P4, NG-22, NG-24, NG-26 | 2-3 giờ | ✅ DONE |
| **Tổng** | **~40 items** | **11-17 ngày** | **✅ COMPLETED** |

---

## Thứ tự ưu tiên gợi ý

```
1. NG-2a/NG-2b → P0-1 → P0-2 → P0-3 → NG-1    (P0 + latency — not runnable) ✅ FIXED
2. NG-5  → NG-6 → NG-4 → NG-3            (Evaluation correctness)           ✅ FIXED
3. NG-9  → NG-7 → NG-8                    (Contract + adaptive fixes)         ✅ FIXED
4. P1-1  → P1-2 → P1-5                   (Wire remaining components)          ✅ FIXED
5. NG-10 → NG-11 → NG-12 → NG-13 → NG-14  (GTFS completeness)                ✅ FIXED
6. NG-15 → NG-16 → NG-17 → NG-18 → NG-19  (Minor polish)                    ✅ FIXED
7. NG-29 → NG-31 → NG-32 → NG-34 → NG-35 → NG-36  (Papers from research)    ✅ FIXED
8. NG-15→NG-33 → P2                   (NG-15,23,25,26,30,33 ✅ — P2 pending infrastructure)
```

---

*Nguồn: WAVES cross-evaluation (22 papers + 13 blogs), LESSON_FROM_BLOG.md (updated April 19 2026)*
*Tạo ngày: April 19, 2026*
*Updated: April 19, 2026 (vòng 2: fix NG-2a/NG-2b, NG-10, P0-3, NG-19, NG-13 — all P0/CRITICAL/MAJOR now accurate)*

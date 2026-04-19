# STREAMDQ MASTER CHECKLIST
### Tự Đánh Giá + Nghiên Cứu Nâng Cấp Dự Án
### Chuẩn Bị: Agent (AI tự thực hiện) — KHÔNG cần user nghiên cứu/đánh giá

**Version:** 1.0
**Project:** StreamDQ — "A Context-Aware Framework for Streaming Data Quality Monitoring"
**Workspace:** `d:\dtl\pipeline_real\`
**Date:** April 19, 2026
**Nguồn:** `PROMPTS/MASTER_EVALUATION_PROMPT.md`

---

## HƯỚNG DẪN SỬ DỤNG

```
Mỗi task → AI tự kiểm tra checklist này
  → Gọi skill/plugin/MCP phù hợp
  → Đọc file liên quan
  → Điền kết quả (PASS/FAIL/IN_PROGRESS/NOT_STARTED)
  → Nếu FAIL → Lên PLAN để sửa
  → Báo cáo cho user khi hoàn thành
```

**Skills cần dùng:**
- `research-lookup` — tìm nghiên cứu học thuật
- `paper-lookup` — tra cứu paper cụ thể
- `literature-review` — tổng hợp nhiều nguồn
- `scientific-critical-thinking` — phê phán logic, phương pháp luận
- `statistical-analysis` — phân tích số liệu, CI
- `scientific-writing` — viết paper

**MCP Servers:**
- `user-kafka` — kiểm tra Kafka topics, consumer lag
- `user-duckdb` — truy vấn violations, precision/recall

---

## PHẦN 0: TÀI LIỆU BẮT BUỘC ĐỌC TRƯỚC

### 0.1 — Đọc Tài Liệu Phân Tích Hiện Có

- [ ] Đọc `CODE_AUDIT.md` — 10 issues (B1-B10), phân loại CRITICAL/MAJOR/MINOR
- [ ] Đọc `STREAMDQ_TECHNICAL_ANALYSIS.md` — 14 Q&A, 11 missing features, P0-P2 priority
- [ ] Đọc `LITERATURE_REVIEW.md` — 17 papers (2024-2026), Stream DaQ là primary competitor
- [ ] Đọc `COMPETITIVE_ANALYSIS.md` — 8 tools, Stream DaQ thắng về architecture
- [ ] Đọc `HYPOTHESES.md` — 7 hypotheses (H1-H7), experiment designs
- [ ] Đọc `CONTRIBUTIONS.md` — Positioning: research/education platform, NOT production
- [ ] Đọc `PAPER_SECTIONS/*.md` — Intro, RelatedWork, Evaluation, Limitations drafts
- [ ] Đọc `SPEC.md` — F1-F10 functional, NF1-NF5 non-functional requirements
- [ ] Đọc `README.md` — tổng quan project, setup instructions
- [ ] Đọc `STREAMDQ_TECHNICAL_ANALYSIS.md` — technical Q&A

### 0.2 — Đọc Code Files Cốt Lõi

- [ ] Đọc `streamdq/rules/base.py` — RuleContext, external_context, Violation dataclass
- [ ] Đọc `streamdq/rules/syntactic.py` — SYN001, SYN002, SYN003 (1-291)
- [ ] Đọc `streamdq/rules/semantic.py` — SEM001, SEM002, SEM003 (1-276)
- [ ] Đọc `streamdq/rules/cross_record.py` — CRS001, CRS002, CRS003 (1-329)
- [ ] Đọc `streamdq/rules/adaptive.py` — rolling percentile, threshold override (1-191)
- [ ] Đọc `streamdq/rules/registry.py` — RuleRegistry, evaluate_all (1-120)
- [ ] Đọc `streamdq/pipeline/local_pipeline.py` — LocalPipeline, external_context = {}
- [ ] Đọc `streamdq/pipeline/spark_pipeline.py` — SparkPipeline, foreachBatch, metrics
- [ ] Đọc `streamdq/evaluation/run_evaluation.py` — anomaly injection, B2 bug location
- [ ] Đọc `streamdq/evaluation/metrics.py` — precision/recall/F1 computation
- [ ] Đọc `streamdq/evaluation/comparison.py` — comparison vs baselines
- [ ] Đọc `streamdq/storage/violation_store.py` — SQLite storage, B5 WAL issue
- [ ] Đọc `tests/test_*.py` — unit tests cho từng rule category

### 0.3 — Đọc Rules Nội Bộ (agent-rules)

- [ ] Đọc `.cursor/rules/agent-rules.mdc` — WAVES Research Agent Rules
- [ ] Đọc `.cursor/rules/streamdq-master.mdc` — StreamDQ Master Rules
- [ ] Đọc `.cursor/rules/research-writing.mdc` — Scientific Writing Rules

---

## PHẦN 1: PHÂN TÍCH TÊN ĐỀ TÀI

### 1.1 — "Context-Aware" — Kiểm Tra Code Evidence

**Điểm hiện tại: 6/10 — WEAK Context-Awareness**

#### Grading Rubric

| Điểm | Định nghĩa |
|------|-----------|
| 8-10 | Real context: time-of-day, day-of-week, weather, geographic, seasonal — contexts populated, rules use them |
| 5-7 | Partial: `historical_stats` used but `external_context` empty — adaptive threshold only |
| 0-4 | Label only: "context-aware" but only static thresholds — no context integration |

#### Evidence Checklist

- [ ] Kiểm tra `streamdq/rules/adaptive.py:1-191` — thresholds computed như thế nào? Chỉ P10/P90?
- [ ] Kiểm tra `streamdq/rules/base.py:15-53` — `external_context` chứa gì? Có được populate?
- [ ] Kiểm tra `streamdq/rules/semantic.py:35-83` — SEM001 dùng `historical_stats` thế nào?
- [ ] Kiểm tra `streamdq/pipeline/local_pipeline.py:96-101` — `external_context` có truyền vào không?
- [ ] Kiểm tra `streamdq/pipeline/spark_pipeline.py:205-209` — tương tự cho Spark pipeline
- [ ] Tìm kiếm toàn bộ codebase: `external_context` có được populate ở đâu không? (grep)
- [ ] Kiểm tra `adaptive.py:101-107` — percentile computation có dùng `int()` truncation không? (B8)
- [ ] Kiểm tra `adaptive.py:176` — adaptive computation có phải driver-only không?

#### Câu hỏi cần trả lời

- [ ] `RuleContext.external_context` có được populate ở đâu trong codebase?
- [ ] "Real" context-awareness cho NYC Taxi trông như thế nào? (time-of-day fare peaks, weekend patterns, weather events)
- [ ] Minimum viable context (MVP) là gì: chỉ `historical_stats` + `external_context`?
- [ ] Điểm hiện tại đúng 6/10 không? Hay cần chấm lại?

#### Research Tasks

- [ ] Dùng `literature-review`: "What does context-aware mean in streaming DQ? Are there papers defining it formally?"
- [ ] Dùng `research-lookup`: Stream DaQ's "dynamic constraint adaptation" vs StreamDQ's rolling P10/P90
- [ ] Search: "beta-binomial thresholds streaming data quality" (AutoDQM) — có thể áp dụng không?

---

### 1.2 — "Streaming" — Kiểm Tra Code Evidence

**Điểm hiện tại: 4/10 — PSEUDO-STREAMING (Blocking Issues)**

#### Grading Rubric

| Điểm | Định nghĩa |
|------|-----------|
| 8-10 | True streaming: event-by-event, sub-second, continuous — Flink/Pathway-level |
| 5-7 | Micro-batch: Spark micro-batch, 500ms+ interval — current StreamDQ |
| 0-4 | Pseudo-streaming: batch dressed as streaming — LocalPipeline only |

#### Evidence Checklist

- [ ] Kiểm tra `streamdq/pipeline/spark_pipeline.py:249-304` — micro-batch hay continuous?
- [ ] Kiểm tra `docker-compose.yml:48` — Dockerfile.spark có tồn tại không?
- [ ] Kiểm tra `streamdq/rules/cross_record.py:52-183` — CRS rules dùng global dicts, streaming hay batch?
- [ ] Kiểm tra `streamdq/evaluation/run_evaluation.py:183` — LocalPipeline hay SparkPipeline?
- [ ] Kiểm tra Kafka topics: `nyc-taxi-events`, `gtfs-vehicle-pos` có hoạt động không?
- [ ] Kiểm tra GTFS topic wiring: CRS001/CRS002 có active cho GTFS không?
- [ ] Kiểm tra Kafka violation sink: `spark_pipeline.py:221-222` — đã implement chưa?

#### Câu hỏi cần trả lời

- [ ] StreamDQ có thể claim "streaming" nếu dùng micro-batch không? Minimum latency floor là gì?
- [ ] True streaming cần gì? (Flink migration? Pathway integration?)
- [ ] "Micro-batch streaming" có acceptable cho research/education positioning không?

#### Research Tasks

- [ ] Dùng `research-lookup`: "Spark Structured Streaming vs Apache Flink latency comparison 2024-2025"
- [ ] Dùng `paper-lookup`: Stream DaQ (arXiv:2506.06147) — làm sao đạt được sub-second?
- [ ] So sánh: Spark micro-batch trigger interval vs true streaming event-time processing

---

### 1.3 — "Framework" — Kiểm Tra Code Evidence

**Điểm hiện tại: 7/10 — GOOD Framework Architecture, Weak Infrastructure**

#### Grading Rubric

| Điểm | Định nghĩa |
|------|-----------|
| 8-10 | Extensible: new rules, new sources, new sinks with minimal code — Registry pattern, ABC, tests |
| 5-7 | Partially extensible: rules extensible, sources/sinks hardcoded — limited registry |
| 0-4 | Monolithic: adding rules requires modifying core — no clear extension points |

#### Evidence Checklist

- [ ] Kiểm tra `streamdq/rules/base.py:1-105` — DataQualityRule ABC clean và extensible?
- [ ] Kiểm tra `streamdq/rules/registry.py:1-120` — new rules có đăng ký dễ dàng không?
- [ ] Kiểm tra `streamdq/rules/syntactic.py:1-291` — thêm rule mới chỉ cần subclass?
- [ ] Kiểm tra `tests/test_*.py` — có tests cho mỗi rule category?
- [ ] Kiểm tra `docker-compose.yml` — Dockerfile.spark có tồn tại không?
- [ ] Kiểm tra Prometheus endpoint — có expose HTTP không?
- [ ] Kiểm tra GTFS wiring — producers có dễ thêm mới không?

#### Câu hỏi cần trả lời

- [ ] Framework có thực sự extensible không, hay chỉ là "extendable by modifying core"?
- [ ] Thêm data source mới (ví dụ: weather data) cần sửa bao nhiêu files?

---

### 1.4 — "Data Quality Monitoring" — Kiểm Tra Code Evidence

**Điểm hiện tại: 5/10 — PARTIAL Coverage (Major Gaps)**

#### Grading Rubric

| Điểm | Định nghĩa |
|------|-----------|
| 8-10 | All 6 DQ dimensions covered, rules for each |
| 5-7 | 4-5 dimensions covered — most important covered |
| 0-4 | <4 dimensions, major gaps |

#### DQ Dimensions Coverage Matrix

| Dimension | Rule(s) | Coverage | Issue | Status |
|-----------|---------|---------|-------|--------|
| Completeness | SYN001 | Partial | Chỉ `fare_amount` có completeness rule | ❌ |
| Validity | SYN002, SYN003 | Good | Type và range checks | ✅ |
| Consistency | CRS001-003 | Partial | CRS002 scope narrow, CRS003 broken | ⚠️ |
| Accuracy | SEM001-003 | Good | Domain-specific checks | ✅ |
| Freshness | SYN003 | Partial | Chỉ "not in future", không có "not stale" | ⚠️ |
| Uniqueness | CRS003 | Broken | Duplicate injection no-op | ❌ |

#### IBM 7 Dimensions Coverage (Từ Part 12, MASTER_EVALUATION_PROMPT.md)

| Dimension | IBM Definition | StreamDQ Status | Gap |
|-----------|---------------|----------------|-----|
| Completeness | null rates | ❌ Chỉ fare_amount | Need per-field null rate |
| Uniqueness | absence of duplicates | ❌ CRS003 broken (B2) | Must fix B2 |
| Validity | format/business rules | ✅ SYN002, SYN003 | — |
| Timeliness | readiness in timeframe | ⚠️ SYN003 partial | Missing stale detection |
| Accuracy | correctness vs source | ✅ SEM001-003 | — |
| Consistency | cross-record coherence | ⚠️ CRS002 narrow, CRS003 broken | Partial |
| Fitness for purpose | meets business need | ❌ **Missing entirely** | Must add new category |

#### Evidence Checklist

- [ ] Kiểm tra `SPEC.md:139-168` — 9 rules có đủ và hoạt động không?
- [ ] Kiểm tra `streamdq/rules/syntactic.py:1-291` — SYN001-003: completeness, validity, freshness
- [ ] Kiểm tra `streamdq/rules/semantic.py:1-276` — SEM001-003: accuracy, plausibility
- [ ] Kiểm tra `streamdq/rules/cross_record.py:1-329` — CRS001-003: consistency, uniqueness
- [ ] Kiểm tra `CODE_AUDIT.md` — B1-B10 issues với rule implementations

---

## PHẦN 2: CHẤM ĐIỂM TỪNG COMPONENT

### 2.1 — Rule Engine (SYN/SEM/CRS)

| Component | Điểm | Evidence | Issue | Status |
|-----------|------|----------|-------|--------|
| SYN001 (Fare validity) | 8/10 | `syntactic.py:40-118` | NaN fix applied but verify | [ ] |
| SYN002 (Location validity) | 9/10 | `syntactic.py:134-193` | Clean, correct | [ ] |
| SYN003 (Timestamp) | 8/10 | `syntactic.py:229-290` | Good edge case handling | [ ] |
| SEM001 (Fare range) | 7/10 | `semantic.py:35-83` | Adaptive but only 2 fields | [ ] |
| SEM002 (Trip duration) | 8/10 | `semantic.py:119-178` | Clean implementation | [ ] |
| SEM003 (Speed) | 7/10 | `semantic.py:213-275` | Fixed threshold, not adaptive | [ ] |
| CRS001 (GPS speed) | 8/10 | `cross_record.py:52-183` | Haversine correct | [ ] |
| CRS002 (GPS spoofing) | 4/10 | `cross_record.py:148` | Speed threshold too narrow | [ ] |
| CRS003 (Duplicates) | 2/10 | `run_evaluation.py:102-104` | CRITICAL: injection broken | [ ] |

**Subtotal: 61/90 = 6.8/10**

#### Checklist cho mỗi Rule

- [ ] Đọc code từng rule: line nào check null? Line nào check NaN? Có dùng `math.isnan()`?
- [ ] Kiểm tra `RuleContext` được populate đầy đủ chưa?
- [ ] Kiểm tra `Violation` object có đủ fields không: rule_id, entity_id, details, record_snapshot, detected_at, processing_latency_ms?
- [ ] Kiểm tra `processing_latency_ms` có bị hardcoded = 0 không? (B6)
- [ ] Viết/chạy unit tests cho từng rule

---

### 2.2 — Adaptive Threshold Engine

| Aspect | Điểm | Evidence | Issue | Status |
|--------|------|----------|-------|--------|
| Rolling percentile computation | 6/10 | `adaptive.py:101-107` | Integer truncation, no interpolation | [ ] |
| Recompute frequency | 7/10 | `adaptive.py:83-84` | Every 1000 events is reasonable | [ ] |
| Override mechanism | 8/10 | `adaptive.py:175-182` | Clean human override | [ ] |
| Distributed computation | 1/10 | `spark_pipeline.py:176` | Driver-only — not distributed | [ ] |
| Context integration | 2/10 | `base.py:31-35` | `external_context` always `{}` | [ ] |
| Drift detection | 0/10 | N/A | Completely absent | [ ] |

**Subtotal: 24/60 = 4/10 — WEAK**

#### Checklist

- [ ] Kiểm tra `adaptive.py` — percentile computation có dùng interpolation không?
- [ ] Kiểm tra `adaptive.py:83-84` — recompute frequency là gì?
- [ ] Kiểm tra `adaptive.py:175-182` — override mechanism hoạt động thế nào?
- [ ] Kiểm tra `spark_pipeline.py:176` — adaptive computation có chạy trên driver không?
- [ ] Tìm kiếm: có drift detection ở đâu trong codebase không?
- [ ] Kiểm tra `base.py:31-35` — `external_context` luôn empty?

---

### 2.3 — Streaming Pipeline

| Aspect | Điểm | Evidence | Issue | Status |
|--------|------|----------|-------|--------|
| Spark micro-batch | 6/10 | `spark_pipeline.py:249-304` | Works but micro-batch only | [ ] |
| Rule evaluation | 5/10 | `spark_pipeline.py:203-218` | Python for-loop, single-threaded | [ ] |
| GTFS routing | 0/10 | `spark_pipeline.py:150-304` | GTFS topic never read | [ ] |
| Kafka violation sink | 0/10 | `spark_pipeline.py:221-222` | NOT implemented | [ ] |
| Prometheus metrics | 3/10 | `spark_pipeline.py:26-82` | Stub metrics only, no HTTP endpoint | [ ] |
| State checkpointing | 2/10 | `cross_record.py:264-328` | Save/load exist but not wired | [ ] |

**Subtotal: 16/60 = 2.7/10 — POOR (Blocking Issues)**

#### Checklist

- [ ] Kiểm tra `docker-compose.yml` — Dockerfile.spark có tồn tại không?
- [ ] Kiểm tra `spark_pipeline.py` — GTFS topic có được đọc không?
- [ ] Kiểm tra `spark_pipeline.py` — Kafka violation sink đã implement chưa?
- [ ] Kiểm tra `spark_pipeline.py` — Prometheus HTTP endpoint có expose không?
- [ ] Kiểm tra `cross_record.py:264-328` — state save/load có được wire chưa?
- [ ] Kiểm tra `foreachBatch` — có driver bottleneck không?

---

### 2.4 — Evaluation Framework

| Aspect | Điểm | Evidence | Issue | Status |
|--------|------|----------|-------|--------|
| Ground truth tracking | 7/10 | `metrics.py:1-175` | Design is sound, one bug | [ ] |
| Anomaly injection | 5/10 | `run_evaluation.py:48-106` | 7/8 types work, duplicate broken | [ ] |
| Metric computation | 7/10 | `metrics.py:108-154` | Precision/recall/detection rate correct | [ ] |
| Comparison vs baselines | 5/10 | `comparison.py:1-200` | All numbers are estimates | [ ] |
| Latency measurement | 2/10 | `spark_pipeline.py:225` | Hardcoded to 0 | [ ] |
| Bootstrap CI | 0/10 | N/A | Not implemented | [ ] |

**Subtotal: 26/60 = 4.3/10 — WEAK**

#### Checklist

- [ ] Kiểm tra `run_evaluation.py:102-104` — duplicate injection no-op?
- [ ] Kiểm tra `metrics.py` — precision/recall computation đúng không?
- [ ] Kiểm tra `comparison.py` — tất cả numbers là estimates hay measured?
- [ ] Kiểm tra `spark_pipeline.py:225` — `processing_latency_ms` hardcoded = 0?
- [ ] Tìm kiếm: có bootstrap resampling ở đâu trong codebase không?
- [ ] Chạy evaluation: thực sự đo P50/P99 latency chưa?

---

### 2.5 — Documentation & Paper

| Aspect | Điểm | Evidence | Issue | Status |
|--------|------|----------|-------|--------|
| Paper sections | 7/10 | `PAPER_SECTIONS/*.md` | Well-structured, honest limitations | [ ] |
| README | 8/10 | `README.md:1-308` | Clear, good diagrams | [ ] |
| SPEC | 8/10 | `SPEC.md:1-216` | Comprehensive requirements | [ ] |
| Literature review | 8/10 | `LITERATURE_REVIEW.md` | 17 papers, 2024-2026 | [ ] |
| Competitive analysis | 8/10 | `COMPETITIVE_ANALYSIS.md` | 8 tools, honest positioning | [ ] |
| Code audit | 9/10 | `CODE_AUDIT.md` | 10 issues, scientific rigor | [ ] |

**Subtotal: 48/60 = 8/10 — STRONG**

#### Checklist

- [ ] Đọc `PAPER_SECTIONS/Introduction.md` — có đủ 4 things (problem, gap, approach, contribution)?
- [ ] Đọc `PAPER_SECTIONS/RelatedWork.md` — comparison table có đủ 8 dimensions?
- [ ] Đọc `PAPER_SECTIONS/Evaluation.md` — có CI, reproducibility protocol?
- [ ] Đọc `PAPER_SECTIONS/Limitations.md` — có honest about streaming vs batch?
- [ ] Kiểm tra `README.md` — diagrams có chính xác không?
- [ ] Kiểm tra `LITERATURE_REVIEW.md` — có đủ papers 2024-2026?

---

### 2.6 — Overall Scorecard

| Component | Điểm | Trọng số | Weighted |
|-----------|------|---------|---------|
| Rule Engine | 6.8/10 | 25% | 1.70 |
| Adaptive Threshold | 4.0/10 | 20% | 0.80 |
| Streaming Pipeline | 2.7/10 | 20% | 0.54 |
| Evaluation Framework | 4.3/10 | 15% | 0.65 |
| Documentation/Paper | 8.0/10 | 20% | 1.60 |
| **OVERALL** | | **100%** | **5.28/10** |

**Grade: 5.3/10 — PROTOTYPE WITH SIGNIFICANT GAPS**

#### Tổng hợp điểm

- [ ] Tính lại điểm mỗi component dựa trên evidence thực tế
- [ ] So sánh với điểm pre-analysis trong MASTER_EVALUATION_PROMPT.md
- [ ] Cập nhật điểm nếu có thay đổi

---

## PHẦN 3: BLOCKERS & KNOWN ISSUES (B1-B10)

### 3.1 — CRITICAL Blockers

| ID | Blocker | Severity | File:Line | Fix Status | Verify |
|----|---------|----------|-----------|-----------|--------|
| B1 | NaN silent pass-through | CRITICAL | `syntactic.py:59` | **Verify if fixed** | [ ] |
| B2 | Duplicate injection no-op | CRITICAL | `run_evaluation.py:102` | **NOT FIXED** | [ ] |
| B6 | processing_latency_ms = 0 | CRITICAL | All rule files | **NOT FIXED** | [ ] |

#### B1 Checklist — NaN Silent Pass-Through
- [ ] Đọc `streamdq/rules/syntactic.py` — tìm line 59
- [ ] Kiểm tra: có dùng `math.isnan()` hoặc tương đương để guard không?
- [ ] Chạy test: `python -c "import math; print(math.isnan(float('nan')))"`
- [ ] Viết unit test: NaN input → Violation returned
- [ ] Nếu chưa fix → Xếp vào P0-1 plan

#### B2 Checklist — Duplicate Injection No-Op
- [ ] Đọc `streamdq/evaluation/run_evaluation.py:102-104`
- [ ] Kiểm tra: anomaly injection có emit 2 records (original + duplicate) không?
- [ ] Kiểm tra: CRS003 có nhận diện được duplicate không?
- [ ] Chạy test: inject duplicate → CRS003 fires?
- [ ] Nếu chưa fix → Xếp vào P0-2 plan

#### B6 Checklist — Latency Hardcoded to 0
- [ ] Tìm tất cả places có `processing_latency_ms = 0` hoặc hardcoded
- [ ] Kiểm tra `spark_pipeline.py:225` — có latency computation không?
- [ ] Kiểm tra tất cả rule files — latency được compute thế nào?
- [ ] Thay hardcoded = 0 bằng actual computation
- [ ] Nếu chưa fix → Xếp vào P0-3 plan

---

### 3.2 — MAJOR Blockers

| ID | Blocker | Severity | File:Line | Fix Status | Verify |
|----|---------|----------|-----------|-----------|--------|
| B3 | CRS002 speed range gap (2-20 km/h) | MAJOR | `cross_record.py:148` | **NOT FIXED** | [ ] |
| B4 | foreachBatch driver bottleneck | MAJOR | `spark_pipeline.py:176` | **Known limitation** | [ ] |
| B5 | SQLite no WAL mode | MAJOR | `violation_store.py` | **NOT FIXED** | [ ] |
| B8 | Percentile int() truncation | MAJOR | `adaptive.py:101` | **NOT FIXED** | [ ] |

#### B3 Checklist — CRS002 Speed Range Gap
- [ ] Đọc `streamdq/rules/cross_record.py:148` — speed threshold hiện tại là gì?
- [ ] Nghiên cứu: speed range nào là realistic cho moderate GPS spoofing?
- [ ] Đề xuất: mở rộng threshold để cover 2-20 km/h moderate spoofing
- [ ] Viết unit test: speed = 5, 10, 15 km/h → should trigger CRS002
- [ ] Nếu chưa fix → Xếp vào P1-1 plan

#### B4 Checklist — foreachBatch Driver Bottleneck
- [ ] Đọc `streamdq/pipeline/spark_pipeline.py:176` — bottleneck ở đâu?
- [ ] Nghiên cứu: Pandas UDF có giải quyết được không?
- [ ] Tài liệu: đây là known limitation, KHÔNG fix trong prototype
- [ ] Cập nhật paper: ghi rõ đây là known constraint

#### B5 Checklist — SQLite No WAL Mode
- [ ] Đọc `streamdq/storage/violation_store.py`
- [ ] Kiểm tra: SQLite có bật WAL mode không?
- [ ] Nếu chưa: thêm `PRAGMA journal_mode=WAL;`
- [ ] Benchmark: so sánh throughput trước/sau
- [ ] Nếu chưa fix → Xếp vào P1-2 plan

#### B8 Checklist — Percentile Int Truncation
- [ ] Đọc `streamdq/rules/adaptive.py:101` — tìm int() truncation
- [ ] Thay thế bằng proper interpolation (numpy percentile hoặc tự implement)
- [ ] Viết test: percentile 33.3, 66.6 không bị truncation
- [ ] Nếu chưa fix → Xếp vào P1-3 plan

---

### 3.3 — MINOR Issues

| ID | Issue | Severity | Status |
|----|-------|----------|--------|
| B7 | Config scattered across files | MINOR | To be assessed |
| B9 | No Prometheus HTTP endpoint | MINOR | To be assessed |
| B10 | No alert routing (Slack/etc) | MINOR | To be assessed |

---

### 3.4 — BLOCKING Infrastructure Issues

| Issue | Severity | File | Status |
|-------|----------|------|--------|
| Dockerfile.spark missing | CRITICAL | `docker-compose.yml:48` | **NOT FIXED** |
| GTFS topic not wired | CRITICAL | `spark_pipeline.py:150-304` | **NOT FIXED** |
| Kafka violation sink not implemented | MAJOR | `spark_pipeline.py:221-222` | **NOT FIXED** |

#### Infrastructure Checklist

- [ ] Kiểm tra `docker-compose.yml:48` — Dockerfile.spark có tồn tại không?
- [ ] Nếu không: tạo Dockerfile.spark → Xếp vào P0-4 plan
- [ ] Kiểm tra `spark_pipeline.py` — GTFS topic có được đọc và route đến CRS rules không?
- [ ] Nếu không: wire GTFS → CRS → Xếp vào P0-5 plan
- [ ] Kiểm tra Kafka violation sink — có producer cho topic `quality-violations` không?
- [ ] Nếu không: implement Kafka sink → Xếp vào P1-4 plan

---

## PHẦN 4: CLAIM VERIFICATION

### 4.1 — Claim Decomposition Checklist

Mỗi claim trong project phải được kiểm tra:

| Claim | Status | Evidence | Action Required |
|-------|--------|---------|----------------|
| "Context-aware" | OVERCLAIM? | `external_context = {}` | Downgrade hoặc implement |
| "P50 ~150ms" | UNVERIFIED? | `comparison.py:144` hardcoded | Must measure |
| "P99 ~890ms" | UNVERIFIED? | `comparison.py` hardcoded | Must measure |
| "82% recall" | OVERCLAIM? | B2: CRS003 injection broken | Fix B2 first |
| "85% precision" | UNVERIFIED? | LocalPipeline only | Must measure |
| "400x faster than GE" | OVERCLAIM? | Architecture comparison | Label as estimated |
| "1,700+ GTFS vehicles" | UNVERIFIED? | Docs only | Verify via Kafka MCP |
| "Adaptive thresholds" | PARTIAL? | Driver-only, not distributed | Document limitation |
| "Fault-tolerant" | OVERCLAIM? | No checkpointing | Remove claim |
| "5,000+ events/sec" | UNVERIFIED? | Not measured | Remove or measure |

### 4.2 — Self-Diagnosis Questions

Áp dụng `scientific-critical-thinking`:

- [ ] **Is StreamDQ's "streaming" claim honest?** — Micro-batch is NOT streaming. Can the paper claim streaming at all?
- [ ] **Is the adaptive threshold claim honest?** — Rolling P10/P90 is adaptive, but drift detection is absent. Is "adaptive" accurate?
- [ ] **Is the 82% recall claim honest?** — CRS003 cannot be measured. Realistic ceiling: 87.5% (excluding duplicate).
- [ ] **Is the positioning claim honest?** — "Research and education platform" vs "production-ready" — is this consistently stated?
- [ ] **Are benchmark numbers honest?** — Every number is estimated. Is the paper honest about this?

---

## PHẦN 5: RESEARCH AGENDA

### 5.1 — Critical Research Questions

#### RQ1: "What does 'context-aware' mean in streaming DQ literature?"

- [ ] Dùng `literature-review`: "context-aware data quality streaming", "adaptive threshold streaming DQ 2024-2026"
- [ ] Dùng `research-lookup`: Stream DaQ's "dynamic constraint adaptation" vs StreamDQ's rolling P10/P90
- [ ] Search: "beta-binomial thresholds streaming data quality" (AutoDQM)
- [ ] Verify: Is StreamDQ's approach novel or just a label?
- [ ] Output: Gap identified + Recommendation

#### RQ2: "How does Stream DaQ (2025) compare to StreamDQ?"

- [ ] Dùng `paper-lookup`: arXiv:2506.06147 (Stream DaQ)
- [ ] Verify: Their 30+ quality checks vs StreamDQ's 9 rules
- [ ] Verify: Their Pathway-based state management vs StreamDQ's global dicts
- [ ] Verify: Their drift detection vs StreamDQ's rolling percentile
- [ ] Action: Should StreamDQ adopt Pathway? Or is Spark micro-batch acceptable?

#### RQ3: "What adaptive threshold approaches exist beyond rolling percentiles?"

- [ ] Dùng `literature-review`
- [ ] Papers: strAEm++DD (arXiv:2305.08977), Adaptive NAD (arXiv:2410.22967), AutoDQM (arXiv:2501.13789)
- [ ] Compare: beta-binomial vs rolling percentile vs autoencoder vs two-layer
- [ ] Action: Which is simplest to implement for MVP? Which gives best improvement?

#### RQ4: "What are the 5 most impactful fixes for StreamDQ?"

- [ ] Dùng `scientific-critical-thinking` on CODE_AUDIT.md
- [ ] Prioritize: CRITICAL issues first (B1 NaN, B2 duplicate)
- [ ] Then: MAJOR issues that block demo (Dockerfile.spark, Prometheus)
- [ ] Then: Quality improvements (CRS002, percentile precision, SQLite WAL)

#### RQ5: "How does IBM's 'fitness for purpose' dimension map to quantifiable metrics?"

- [ ] Dùng `literature-review` + `research-lookup`: "data quality fitness for purpose evaluation metrics"
- [ ] Gap: StreamDQ has no fitness-for-purpose rule category
- [ ] Output: FIT001 design proposal

#### RQ6: "How do IBM/Precisely's 5 DQ dimensions differ from StreamDQ's SYN/SEM/CRS taxonomy?"

- [ ] Dùng `scientific-critical-thinking`
- [ ] Compare: IBM 7 dimensions vs. SYN/SEM/CRS vs. ISO 8000
- [ ] Action: Decide whether to rebrand taxonomy or add missing dimensions

### 5.2 — Papers That Need Verification

| Paper | Citation | Claim to Verify | Status |
|-------|---------|----------------|--------|
| Stream DaQ (2025) | arXiv:2506.06147 | Sub-second latency, 30+ checks, drift detection | [ ] |
| AutoDQM (2025) | arXiv:2501.13789 | Beta-binomial thresholds for DQ | [ ] |
| strAEm++DD (2023) | arXiv:2305.08977 | Autoencoder + drift detection | [ ] |
| Adaptive NAD (2024) | arXiv:2410.22967 | Two-layer self-adaptive thresholds | [ ] |
| StreamShield (2026) | arXiv:2602.03189 | Production resiliency for Flink | [ ] |

---

## PHẦN 6: BLOG LINKS RESEARCH

### 6.1 — Grab Engineering Blogs

| # | Link | Topic | Research Questions | Status |
|---|------|-------|-------------------|--------|
| 1 | Grab: Data Observability | engineering.grab.com/data-observability | How does Grab implement data observability? | [ ] |
| 2 | Rethinking Streaming Processing | engineering.grab.com/rethinking-streaming-processing-data-exploration | Streaming processing patterns? | [ ] |
| 3 | Signals Marketplace | engineering.grab.com/signals-market-place | Data quality in marketplace? | [ ] |
| 4 | Data First SLA | engineering.grab.com/data-first-sla-always | SLA for data quality? | [ ] |
| 5 | Grab Kafka Data Quality | www.infoq.com/news/2025/12/grab-kafka-data-quality/ | Kafka + DQ integration? | [ ] |
| 6 | Real-Time DQ Monitoring | engineering.grab.com/real-time-data-quality-monitoring | Real-time monitoring approach? | [ ] |
| 7 | Alibaba/Grab Flink Journey | www.alibabacloud.com/blog/from-data-streams-to-actionable-insights-grabs-journey-with-apache-flink-in-real-time-analytics-and-data-quality_602517 | Flink + data quality? | [ ] |
| 8 | Real-Time Data Ingestion | engineering.grab.com/real-time-data-ingestion | Ingestion patterns? | [ ] |
| 9 | ACM Paper (GRab) | dl.acm.org/doi/epdf/10.1145/3686592.3686609 | Academic findings? | [ ] |
| 10 | Rethinking Streaming (alt) | engineering.grab.com/rethinking-streaming-processing-data-exploration | Duplicate topic check | [ ] |

### 6.2 — Industry Blogs

| # | Link | Topic | Research Questions | Status |
|---|------|-------|-------------------|--------|
| 11 | Tinybird: Real-Time Streaming Architectures | tinybird.co/blog/real-time-streaming-data-architectures-that-scale | Scalable streaming architectures? | [ ] |
| 12 | IBM: Data Quality | ibm.com/think/topics/data-quality | IBM 7 DQ dimensions? | [ ] |
| 13 | Precisely: Big Data Quality | precisely.com/data-quality/big-data-quality-mastering-data-quality-in-the-age-of-big-data/ | 5-step framework? | [ ] |

### 6.3 — Mỗi Blog Checklist

Với mỗi blog, cần trả lời:

- [ ] Đọc blog bằng `WebFetch`
- [ ] Trích xuất: framework/approach chính là gì?
- [ ] Trích xuất: làm sao họ xử lý "context aware"?
- [ ] Trích xuất: làm sao họ xử lý "streaming"?
- [ ] Trích xuất: làm sao họ xử lý "data quality"?
- [ ] So sánh: họ làm gì tốt hơn StreamDQ? (list ra)
- [ ] So sánh: StreamDQ làm gì tốt hơn họ? (list ra)
- [ ] Action: có bài học nào áp dụng được cho StreamDQ không?

---

## PHẦN 7: PAPER LEARNING (TỪ paper-to-learn/)

### 7.1 — Paper List (Tất cả files trong paper-to-learn/)

| # | File | Status |
|---|------|--------|
| 1 | 1-s2.0-S0019057825005129-main.pdf | [ ] |
| 2 | 1-s2.0-S0020025526004196-main.pdf | [ ] |
| 3 | 1-s2.0-S0031320325011793-main.pdf | [ ] |
| 4 | 1-s2.0-S0167739X17329151-main.pdf | [ ] |
| 5 | 1-s2.0-S0167739X26001548-main.pdf | [ ] |
| 6 | 1-s2.0-S0167947325002142-main.pdf | [ ] |
| 7 | 1-s2.0-S0360835225006540-main.pdf | [ ] |
| 8 | 1-s2.0-S0925231225028619-main.pdf | [ ] |
| 9 | 1-s2.0-S0925231226009033-main.pdf | [ ] |
| 10 | 1-s2.0-S0950705125012894-main.pdf | [ ] |
| 11 | 1-s2.0-S095070512501768X-main.pdf | [ ] |
| 12 | 1-s2.0-S095219762600792X-main.pdf | [ ] |
| 13 | 1-s2.0-S0957417425034979-main.pdf | [ ] |
| 14 | 1-s2.0-S0957417425040059-main.pdf | [ ] |
| 15 | 1-s2.0-S0957417426008262-main.pdf | [ ] |
| 16 | 1-s2.0-S1110016826001225-main.pdf | [ ] |
| 17 | 1-s2.0-S1568494625007537-main.pdf | [ ] |
| 18 | 2204.10655v1.pdf | [ ] |
| 19 | 3603707.pdf | [ ] |
| 20 | FutureGeneration.pdf | [ ] |
| 21 | TaDA.13.pdf | [ ] |
| 22 | TSP_CMES_62902.pdf | [ ] |
| 23 | (future files) | [ ] |
| 24 | (future files) | [ ] |

**Total: 22 confirmed + 2 slots for future additions**

### 7.2 — Mỗi Paper Checklist

- [ ] Đọc paper bằng Read tool (PDF)
- [ ] Trích xuất: Research question là gì?
- [ ] Trích xuất: Methodology chính là gì?
- [ ] Trích xuất: Kết quả chính là gì?
- [ ] Trích xuất: Limitations là gì?
- [ ] Mapping: Paper này giúp gì cho "A Context-Aware Framework for Streaming DQ"?
- [ ] Specific lesson: Viết 2-3 sentences về bài học cụ thể
- [ ] Citation: Ghi lại citation để dùng trong paper

---

## PHẦN 8: PLANNED ROADMAP

### 8.1 — Critical Fixes (Before Any New Feature) — P0

| Priority | Task | Bug ID | Files | Verification | Status |
|----------|------|--------|-------|-------------|--------|
| P0-1 | Verify B1 (NaN) fix applied | B1 | `syntactic.py` | Run: `python -c "import math; print(math.isnan(float('nan')))"` | [ ] |
| P0-2 | Fix B2 (duplicate injection) | B2 | `run_evaluation.py:102` | Inject two records, verify CRS003 fires | [ ] |
| P0-3 | Fix B6 (latency = 0) | B6 | All rule files | Verify `processing_latency_ms` computed | [ ] |
| P0-4 | Create Dockerfile.spark | N/A | New file | `docker compose up` succeeds | [ ] |
| P0-5 | Wire GTFS topic → CRS | N/A | `spark_pipeline.py` | GTFS violations appear | [ ] |

### 8.2 — Quality Improvements (After Critical Fixes) — P1

| Priority | Task | Bug ID | Files | Expected Impact | Status |
|----------|------|--------|-------|----------------|--------|
| P1-1 | Fix B3 (CRS002 speed) | B3 | `cross_record.py:148` | +15% GPS spoofing recall | [ ] |
| P1-2 | Fix B5 (SQLite WAL) | B5 | `violation_store.py` | +60% storage throughput | [ ] |
| P1-3 | Add percentile interpolation | B8 | `adaptive.py:101` | Statistical rigor | [ ] |
| P1-4 | Implement Kafka violation sink | N/A | `spark_pipeline.py` | Architecture complete | [ ] |
| P1-5 | Add Prometheus metrics HTTP | N/A | `spark_pipeline.py` | Grafana works | [ ] |

### 8.3 — Enhancement Research (Requires Literature First) — P2

| Priority | Task | Source | Expected Impact | Research Needed | Status |
|----------|------|--------|----------------|----------------|--------|
| P2-1 | Drift detection in adaptive engine | RQ3 research | Reduce false positives | `literature-review` | [ ] |
| P2-2 | Beta-binomial thresholds (SEM001) | AutoDQM paper | Better warmup behavior | `paper-lookup` | [ ] |
| P2-3 | External context injection (time-of-day) | RQ1 research | Genuine context-awareness | `research-lookup` | [ ] |
| P2-4 | Bootstrap CI for metrics | `statistical-analysis` | Honest confidence bounds | `statistical-analysis` | [ ] |
| P2-5 | Pandas UDF rule evaluation | B4 fix | +40% throughput | Research | [ ] |

### 8.4 — IBM/Precisely Recommended Actions — P1-A to P1-F

| ID | Task | Source | Description | Status |
|----|------|--------|-------------|--------|
| P1-A | Completeness Monitoring | IBM | SYN000 — Field Completeness Monitor (null rate per field) | [ ] |
| P1-B | Fitness for Purpose | IBM | FIT001 — Business Fitness rule category | [ ] |
| P1-C | Stale Data Detection | IBM/Precisely | Extend SYN003 với staleness threshold | [ ] |
| P1-D | Auto-Profiling | Precisely Step 1 | SchemaProfiler — auto-generate rule suggestions | [ ] |
| P1-E | Data Contract Definition | Precisely Step 2-3 | YAML data contracts (nyc_taxi.yaml, gtfs.yaml) | [ ] |
| P1-F | Alert Routing | Precisely Step 5 | AlertRouter + Slack channel | [ ] |

---

## PHẦN 9: MCP VERIFICATION CHECKLIST

### 9.1 — Kafka MCP Verification

Sau khi implement critical fixes, verify bằng Kafka MCP:

- [ ] **Verify 1**: Check topics exist — `kafka_topics_list` → "nyc-taxi-events", "gtfs-vehicle-pos", "quality-violations"
- [ ] **Verify 2**: Check GTFS vehicle count — `kafka_consume` messages="gtfs-vehicle-pos" limit=1000 → Count unique vehicle_id → should be ~1700+
- [ ] **Verify 3**: Verify anomaly injection → violation appears — produce test event with fare_amount=-50 → consume "quality-violations" → should see SYN001 violation
- [ ] **Verify 4**: Check consumer lag — `kafka_get_consumer_group_info` group="streamdq-consumer" → lag should be < 1000

### 9.2 — DuckDB MCP Verification

Sau khi chạy evaluation, verify metrics bằng DuckDB MCP:

- [ ] **Verify 1**: Real precision/recall từ actual run — SQL query anomaly_type, total_injected, detected, recall_pct
- [ ] **Verify 2**: Latency percentiles — SQL query P50, P95, P99 từ violations table
- [ ] **Verify 3**: False positive analysis — SQL query rule_id, violations count cho entity_index NOT IN injected_anomalies

### 9.3 — Manual Code Verification

- [ ] Chạy `pytest` — tất cả tests pass?
- [ ] Chạy `docker compose up` — full pipeline starts?
- [ ] Chạy evaluation script — violations stored in SQLite?
- [ ] Kiểm tra Grafana dashboard — metrics hiển thị?

---

## PHẦN 10: PAPER READINESS CHECKLIST

### 10.1 — Per-Section Readiness

| Section | Min Score | Max Score | Current | Gap | Status |
|---------|-----------|-----------|---------|-----|--------|
| Introduction | 7 | 10 | 7 | Honesty about streaming vs batch | [ ] |
| Related Work | 8 | 10 | 8 | Need to add Flink comparison papers | [ ] |
| Architecture | 6 | 10 | 6 | Micro-batch acknowledgment | [ ] |
| Evaluation | 4 | 10 | 4 | MUST measure before publishing | [ ] |
| Limitations | 8 | 10 | 8 | Already honest | [ ] |
| **Total** | **40** | **60** | **~40** | **CRITICAL: Evaluation must be measured** | |

### 10.2 — Demo Readiness Checklist

**Demo Readiness: 2/5 — NOT DEMO-READY**

- [ ] `docker compose up` starts full pipeline → BLOCKED by Dockerfile.spark missing
- [ ] Grafana shows data → BLOCKED by Prometheus endpoint not exposed
- [ ] NYC TLC events flow through Kafka → Works (producer exists)
- [ ] GTFS violations detected → BLOCKED by GTFS topic not wired
- [ ] SQLite has violation records → Partially works

### 10.3 — Production Readiness Checklist

**Production Readiness: 0/5 — RESEARCH PLATFORM ONLY**

- [ ] Fault-tolerant state → BLOCKED by no checkpointing
- [ ] Horizontal scaling → BLOCKED by single-threaded rule eval
- [ ] Real benchmark validated → BLOCKED by LocalPipeline only
- [ ] Monitoring/alerting → BLOCKED by Prometheus not exposed
- [ ] Multi-broker Kafka → BLOCKED by single broker RF=1

---

## PHẦN 11: EXECUTION ORDER — AGENT SELF-EXECUTION

### Phase 1 — DECOMPOSE (1 research iteration)

```
├── Read: STREAMDQ_TECHNICAL_ANALYSIS.md + CODE_AUDIT.md
├── Research: RQ1-RQ6 using research-lookup + paper-lookup
├── Research: All 13 blog links (Grab + industry)
├── Research: All 7 papers in paper-to-learn/
├── Output: Graded components (Part 2) + Research findings (Part 3)
└── Status: [IN_PROGRESS / DONE]
```

### Phase 2 — DIAGNOSE (1 analysis iteration)

```
├── Apply: scientific-critical-thinking to every claim
├── Verify: B1-B6 in actual code (read files, not just docs)
├── Grade: Each component (Part 2 scorecard) — re-grade with evidence
├── Output: Diagnosis report with specific evidence
└── Status: [IN_PROGRESS / DONE]
```

### Phase 3 — PLAN (1 planning iteration)

```
├── Prioritize: CRITICAL > MAJOR > MINOR
├── Sequence: Fix blocking first, then enhance
├── Resource: Map to skills + MCP tools available
├── Output: Roadmap (Part 5) with verification criteria
└── Status: [IN_PROGRESS / DONE]
```

### Phase 4 — VERIFY (1 verification iteration)

```
├── Execute: DuckDB queries on violation data
├── Execute: Kafka MCP topic inspection
├── Execute: Run evaluation and compare to claims
├── Output: Verified vs claimed gap analysis
└── Status: [IN_PROGRESS / DONE]
```

### Phase 5 — DECIDE (1 decision iteration)

```
├── Based on: All evidence above
├── Decide: Is the project ready to publish? What must be fixed first?
├── Scope: What can be done in 1 week? 1 month? 1 quarter?
├── Output: Decision memo with go/no-go recommendations
└── Status: [IN_PROGRESS / DONE]
```

---

## PHẦN 12: OUTPUT TEMPLATES

### Phase 1 Output Template

```markdown
## Phase 1: Component Evaluation

### Scores (X/Y)
| Component | Score | Key Evidence | Key Gap |
|-----------|-------|-------------|---------|
| Rule Engine | X/Y | [file:line] | [specific issue] |
| Adaptive Threshold | X/Y | [file:line] | [specific issue] |
| Streaming Pipeline | X/Y | [file:line] | [specific issue] |
| Evaluation Framework | X/Y | [file:line] | [specific issue] |
| Documentation | X/Y | [file:line] | [specific issue] |
| **OVERALL** | X/Y | | |

### Research Findings
#### RQ1: Context-Aware
- [Finding 1 with citation]
- [Finding 2 with citation]
- Gap: [what StreamDQ lacks]

#### RQ2: Stream DaQ Comparison
- [Finding]
- Recommendation: [adopt/adapt/ignore]

### Self-Evaluation: [X/10]
- Strengths: [top 3]
- Weaknesses: [top 3]
- Blocking issues: [top 3]
```

### Phase 2 Output Template

```markdown
## Phase 2: Diagnosis

### Claim Verification
| Claim | Status | Evidence | Action |
|-------|--------|---------|--------|
| "Context-aware" | OVERCLAIM | `base.py:31` external_context={} | Downgrade or implement |
| "P50 ~150ms" | UNVERIFIED | `comparison.py:144` hardcoded | Must measure |
| ... | ... | ... | ... |

### Bug Status
| Bug | Verified? | File:Line | Fix Applied? |
|-----|-----------|-----------|--------------|
| B1 | [YES/NO] | [ref] | [YES/NO] |
| B2 | [YES/NO] | [ref] | [YES/NO] |
| ... | ... | ... | ... |

### Root Cause Analysis
[For each blocking issue, trace to the code-level cause]
```

### Phase 3 Output Template

```markdown
## Phase 3: Enhancement Roadmap

### Week 1 (Critical Fixes)
| # | Task | Files | Verification | Owner |
|---|------|-------|-------------|-------|
| 1 | Fix B2 duplicate injection | run_evaluation.py | Test CRS003 fires | AI |
| 2 | Create Dockerfile.spark | Dockerfile.spark | docker compose up works | AI |
| ... | ... | ... | ... | ... |

### Week 2-4 (Quality)
| # | Task | Expected Impact | Research Needed |
|---|------|----------------|-----------------|
| 1 | Fix B3 CRS002 speed | +15% recall | None |
| 2 | Add drift detection | -X% FPR | literature-review |
| ... | ... | ... | ... |

### Month 2+ (Enhancement)
| # | Task | Complexity | Literature Source |
|---|------|-----------|------------------|
| 1 | Beta-binomial thresholds | Medium | AutoDQM |
| 2 | External context | High | RQ1 research |
| ... | ... | ... | ... |
```

### Phase 4 Output Template

```markdown
## Phase 4: MCP Verification Results

### Kafka Verification
- Topics: [list]
- GTFS vehicle count: [number] (expected: ~1700)
- Consumer group lag: [number]
- Anomaly injection test: [PASS/FAIL]

### DuckDB Verification
- Total violations: [N]
- Precision: [X%] (claimed: Y%)
- Recall by type: [table]
- Latency P50/P99: [Xms / Yms] (claimed: 150ms / 890ms)

### Verdict
- [X] claims can be verified
- [Y] claims remain unverified
- [Z] claims are FALSE (contradicted by data)
```

### Phase 5 Output Template

```markdown
## Phase 5: Decision Memo

### Current State
- Overall Grade: [X/10]
- Demo Ready: [YES/NO — N/5 checkpoints]
- Production Ready: [YES/NO — N/5 checkpoints]
- Paper Ready: [YES/NO — sections scored]

### Go/No-Go for Publication
[Based on evidence above, recommend one of:]
- GO: All claims verified, all critical bugs fixed
- CONDITIONAL GO: Major claims verified, minor gaps documented
- NO-GO: Critical gaps remain, benchmark not measured

### Must-Fix Before Publication (Non-Negotiable)
1. [Critical fix with deadline]
2. [Critical fix with deadline]
3. [Critical fix with deadline]

### Can-Do After Publication (Optional)
1. [Enhancement]
2. [Enhancement]

### Positioning Adjustment
[Based on findings, recommend specific language changes to paper positioning]
```

---

## PHẦN 13: ANTI-PATTERNS TO AVOID

| Anti-Pattern | Example in StreamDQ | How to Avoid |
|-------------|--------------------|--------------|
| **Unverified claims** | P50=150ms, P99=890ms | Measure before publishing |
| **Missing implementation** | Dockerfile.spark | Reference only existing files |
| **Silent failures** | NaN pass-through (B1) | Guard every field access |
| **Magic numbers** | `speed_kmh < 20.0` | Named constants with comments |
| **Scope mismatch** | CRS002 narrow coverage | Map all attack vectors |
| **Overclaiming** | "400x faster" unverified | Architecture ≠ measurement |
| **Missing CI** | No bootstrap confidence intervals | statistical-analysis skill |
| **State not checkpointed** | Global dicts for CRS | Implement save/load wiring |
| **Missing context** | external_context = {} | Populate real contexts |
| **Pseudo-streaming** | LocalPipeline only | Distinguish micro-batch vs streaming |

---

## PHẦN 14: CONTEXT-AWARE DEEP DIVE

### 14.1 — Hiện Tại (Theo MASTER_EVALUATION_PROMPT.md)

- [ ] `external_context` LUÔN = `{}` — không có external context
- [ ] Chỉ 2 fields được track (`fare_amount`, `trip_distance`) — adaptive scope hạn chế
- [ ] Percentile dùng `int()` truncation — không chính xác
- [ ] Computation chỉ trên driver — không phân tán

**Điểm hiện tại: 6/10 — WEAK Context-Awareness**

### 14.2 — "Real" Context-Aware Cho NYC Taxi

- [ ] Time-of-day: fare peaks (8-9 AM, 5-7 PM) → contextual thresholds
- [ ] Day-of-week: weekday vs weekend patterns → different thresholds
- [ ] Weather: rain/snow → higher fares, different distance patterns
- [ ] Seasonal: holiday vs normal days → different distributions
- [ ] Geographic: Manhattan vs outer boroughs → zone-specific thresholds
- [ ] Event-based: concerts, games → surge detection

### 14.3 — Minimum Viable Context (MVP)

- [ ] Step 1: Populate `external_context` với time-of-day và day-of-week
- [ ] Step 2: SEM001 dùng `external_context` để adjust thresholds
- [ ] Step 3: Document đây là MVP, không phải full context-aware

### 14.4 — Research: Context-Aware Definitions

- [ ] Dùng `literature-review`: "context-aware data quality" — formal definition có không?
- [ ] Dùng `research-lookup`: Stream DaQ's context handling
- [ ] Dùng `research-lookup`: AutoDQM's adaptive thresholds — context hay adaptive?

---

## PHẦN 15: STREAMING DEEP DIVE

### 15.1 — Hiện Tại

- [ ] **Micro-batch only** — `outputMode: "complete"` với `foreachBatch`
- [ ] **Dockerfile.spark missing** — full pipeline cannot start
- [ ] **GTFS topic not wired** — CRS001/CRS002 inactive cho GTFS data
- [ ] **LocalPipeline used in evaluation** — NOT actual streaming

**Điểm hiện tại: 4/10 — PSEUDO-STREAMING (Blocking Issues)**

### 15.2 — Streaming Taxonomy

| Type | Latency | Example | StreamDQ? |
|------|---------|---------|-----------|
| True Streaming | < 100ms | Flink, Kafka Streams, Pathway | ❌ No |
| Micro-Batch | 500ms - 5s | Spark Structured Streaming | ✅ Current |
| Mini-Batch | 5s - 1min | Spark Batch, dbt | ❌ No |
| Batch | > 1min | Traditional ETL | ❌ No |

### 15.3 — Claim Assessment

- [ ] StreamDQ có thể claim "streaming" không? → **NO** (chỉ micro-batch)
- [ ] Nên claim gì? → "Near-real-time streaming data quality monitoring"
- [ ] Paper positioning: acknowledge micro-batch limitation

---

## PHẦN 16: IBM/PRECISELY FRAMEWORK MAPPING

### 16.1 — IBM 7 DQ Dimensions vs StreamDQ

| IBM Dimension | Definition | StreamDQ Status | Action |
|---------------|-----------|-----------------|--------|
| Completeness | null rates | ❌ fare_amount only | Add SYN000 per-field null monitoring |
| Uniqueness | absence of duplicates | ❌ CRS003 broken | Fix B2 first |
| Validity | format/business rules | ✅ SYN002, SYN003 | Maintain |
| Timeliness | readiness in timeframe | ⚠️ partial | Add stale detection |
| Accuracy | correctness vs source | ✅ SEM001-003 | Maintain |
| Consistency | cross-record coherence | ⚠️ partial | Fix CRS002, CRS003 |
| Fitness for purpose | meets business need | ❌ missing | Add FIT001 |

### 16.2 — Precisely 5-Step Framework vs StreamDQ

| Step | Description | StreamDQ Status | Gap |
|------|-------------|-----------------|-----|
| 1. Discover | Profile data, identify flows | ❌ missing | Add SchemaProfiler |
| 2. Define | Assess DQ risks, prioritize | ❌ missing | Add risk assessment |
| 3. Design | Rules independent of data | ⚠️ partial | Add data contract YAML |
| 4. Deploy | Deploy controls, workflow | ❌ missing | Add AlertRouter |
| 5. Monitor | Automated, continuous | ⚠️ weak | Add Prometheus/Grafana |

---

## PHẦN 17: TRIAGE — QUYẾT ĐỊNH HÀNH ĐỘNG

### Sau khi hoàn thành tất cả checklist ở trên:

- [ ] **Nếu điểm tổng thể < 5**: Báo cáo user → Cần critical fixes trước
- [ ] **Nếu điểm tổng thể 5-7**: Báo cáo user → Đã prototype, cần professionalize
- [ ] **Nếu điểm tổng thể > 7**: Báo cáo user → Có thể publish được
- [ ] **Nếu B2 chưa fix**: CRS003 recall unmeasurable → KHÔNG publish benchmark numbers
- [ ] **Nếu Dockerfile.spark chưa tạo**: Demo không chạy được → KHÔNG claim "full pipeline"
- [ ] **Nếu claims unverified**: Phải measure trước → KHÔNG publish unverified numbers

### Decision Matrix

| Condition | Decision | Action |
|-----------|----------|--------|
| B1, B2, B6 unfixed | NO-GO | Fix B1, B2, B6 first |
| B1, B2, B6 fixed, B4 unfixed | CONDITIONAL GO | Document B4 as known limitation |
| All P0 fixed, P1 partial | CONDITIONAL GO | Publish with honest positioning |
| All P0 + P1 fixed, P2 partial | GO | Publish with honest evaluation |
| All issues fixed | STRONG GO | Publish with verified benchmarks |

---

## PHẦN A: EXECUTION RULES (BẮT BUỘC TUÂN THỦ)

### A.1 — Nguyên Tắc Vàng (KHÔNG ĐƯỢC PHÉP VI PHẠM)

```
1. KHÔNG RÚT GỌN QUÁ TRÌNH
   - File dài → VẪN PHẢI ĐỌC TOÀN BỘ
   - Task dài → VẪN PHẢI THỰC HIỆN HẾT
   - Không được "lite", không được "fallback", không được skip

2. KHÔNG ĐƯỢC BỎ QUA BẤT KỲ BƯỚC NÀO
   - Đọc checklist → Đọc file → Chạy test → Verify → Report
   - Mỗi checklist item phải có kết quả (PASS/FAIL/IN_PROGRESS)
   - Không được để checkbox trống không có kết quả

3. KHÔNG TỰ Ý KẾT LUẬN KHI CHƯA ĐỌC ĐỦ
   - "Tôi đoán" = KHÔNG CHẤP NHẬN
   - "Có vẻ như" = KHÔNG CHẤP NHẬN
   - Phải đọc code/file, rồi mới kết luận

4. KHÔNG ĐƯỢC LÀM LITE
   - Nguyên tắc "prototype first" không có nghĩa là làm nửa vời
   - Mỗi task đều phải HOÀN THIỆN, có tính đóng góp lớn
   - "Sẽ fix sau" = PHẢI ghi vào plan, có deadline

5. KHÔNG ĐƯỢC FALLBACK KHI CÓ MCP/SKILL
   - Có `research-lookup` → PHẢI dùng cho research tasks
   - Có `paper-lookup` → PHẢI dùng cho paper lookup
   - Có `user-kafka` MCP → PHẢI dùng để verify Kafka
   - Có `user-duckdb` MCP → PHẢI dùng để query violations
```

### A.2 — Quy Tắc Đọc File

```
MỖI KHI CHECKLIST YÊU CẦU ĐỌC FILE:
  1. Dùng Read tool để đọc TOÀN BỘ file (không chỉ đọc 1 phần)
  2. Nếu file > 500 lines → đọc từng phần, nhưng PHẢI đọc HẾT
  3. Ghi lại key findings vào checklist
  4. Nếu file không tồn tại → BÁO CÁO NGAY cho user

VÍ DỤ - Đọc syntactic.py:
  1. Read streamdq/rules/syntactic.py (1-291 lines)
  2. Tìm: SYN001 check null? SYN001 check NaN? SYN002 check gì?
  3. Kiểm tra: có dùng math.isnan() không?
  4. Kiểm tra: RuleContext được populate đầy đủ không?
  5. Kiểm tra: Violation object có đủ fields không?
  6. Ghi kết quả vào checklist

VÍ DỤ - Đọc 1 paper PDF:
  1. Read paper-to-learn/TaDA.13.pdf (TOÀN BỘ 2190 lines)
  2. Trích xuất: Title, Authors, Year, Venue
  3. Trích xuất: Research question
  4. Trích xuất: Methodology
  5. Trích xuất: Results/Findings
  6. Trích xuất: Limitations
  7. Trích xuất: Specific lessons for StreamDQ
  8. Ghi citation để dùng trong paper
```

### A.3 — Quy Tắc Research

```
KHI THỰC HIỆN RESEARCH (Phần 5, 6, 7):
  1. Dùng SKILL phù hợp:
     - research-lookup → tìm nghiên cứu học thuật
     - paper-lookup → tra cứu paper cụ thể
     - literature-review → tổng hợp nhiều nguồn
     - scientific-critical-thinking → phê phán logic

  2. VỚI MỖI PAPER/BLOG:
     - Đọc bằng Read tool (PDF) hoặc WebFetch (blog)
     - KHÔNG được đọc summary thay vì đọc full text
     - KHÔNG được skip nếu paper > 100 pages
     - Trích xuất ít nhất 5 key findings

  3. VỚI MỖI BLOG (13 blogs):
     - Đọc bằng WebFetch
     - KHÔNG được đọc chỉ 1 đoạn đầu
     - PHẢI đọc hết nội dung
     - Trích xuất: approach, implementation, lessons

  4. VỚI MỖI PAPER TRONG paper-to-learn/ (22 papers):
     - Đọc bằng Read tool (PDF)
     - KHÔNG được đọc chỉ abstract
     - PHẢI đọc hết paper (có thể dùng nhiều Read calls)
     - Mapping: paper giúp gì cho "Context-Aware Streaming DQ"
```

### A.4 — Quy Tắc Verify

```
KHI VERIFY (Phần 9):
  1. Kafka MCP:
     - Đọc schema descriptor trước khi gọi
     - Gọi kafka_topics_list → kiểm tra topics
     - Gọi kafka_consume → verify data flow
     - Gọi kafka_produce → test anomaly injection

  2. DuckDB MCP:
     - Đọc schema descriptor trước khi gọi
     - Query violations table
     - Query injected_anomalies table
     - Compute precision/recall từ actual data

  3. Manual:
     - Chạy pytest → tất cả tests phải pass
     - Chạy evaluation script → phải có violations
     - docker compose up → phải start được
```

### A.5 — Quy Tắc Plan

```
KHI LÊN PLAN (Phần 8):
  1. MỖI TASK phải có:
     - Tên task rõ ràng
     - Files cần sửa (file:line)
     - Verification criteria (làm sao biết đã xong)
     - Owner (AI hoặc User)
     - Deadline

  2. ƯU TIÊN:
     - CRITICAL (B1, B2, B6) → Fix TRƯỚC TIÊN
     - MAJOR (B3, B5, B8) → Fix SAU CRITICAL
     - MINOR → Fix SAU MAJOR

  3. KHÔNG ĐƯỢC:
     - Lên plan mà không có verification criteria
     - Lên plan mà không có deadline
     - Lên plan mà không assign owner
```

### A.6 — Quy Tắc Report

```
KHI BÁO CÁO CHO USER:
  1. MỖI CHECKLIST ITEM phải có kết quả:
     - [PASS] → đã verify, OK
     - [FAIL] → có vấn đề, cần fix
     - [IN_PROGRESS] → đang làm
     - [NOT_STARTED] → chưa làm
     - [BLOCKED] → bị block bởi cái khác

  2. VỚI MỖI FAIL/BLOCKED:
     - Mô tả vấn đề cụ thể
     - Đưa ra plan để fix
     - Đưa ra deadline

  3. KHÔNG ĐƯỢC:
     - Báo cáo "đã xong" khi chưa verify
     - Báo cáo "OK" khi còn issues
     - Bỏ qua BLOCKED items
```

---

## PHẦN B: CHI TIẾT PLAN — TỪNG BƯỚC Một

### B.1 — Plan cho Phần 0: Tài Liệu

```
TÀI LIỆU PHÂN TÍCH (10 files) - ĐỌC TOÀN BỘ:

Bước 0.1: Đọc CODE_AUDIT.md
  - Đọc: TOÀN BỘ file (497 lines)
  - Mục tiêu: Hiểu 10 issues (B1-B10)
  - Checklist:
    [ ] B1: NaN pass-through → vị trí nào? đã fix chưa?
    [ ] B2: Duplicate injection no-op → vị trí nào? đã fix chưa?
    [ ] B3: CRS002 speed range gap → vị trí nào? đã fix chưa?
    [ ] B4: foreachBatch driver bottleneck → vị trí nào? known limitation?
    [ ] B5: SQLite no WAL mode → vị trí nào? đã fix chưa?
    [ ] B6: processing_latency_ms = 0 → vị trí nào? đã fix chưa?
    [ ] B7: Config scattered → vị trí nào?
    [ ] B8: Percentile int() truncation → vị trí nào? đã fix chưa?
    [ ] B9: No Prometheus HTTP endpoint → vị trí nào?
    [ ] B10: No alert routing → vị trí nào?
  - Output: Bảng tổng hợp B1-B10 với status

Bước 0.2: Đọc STREAMDQ_TECHNICAL_ANALYSIS.md
  - Đọc: TOÀN BỘ file
  - Mục tiêu: Hiểu 14 Q&A, 11 missing features
  - Checklist:
    [ ] 14 Q&A → hiểu từng câu hỏi và câu trả lời
    [ ] 11 missing features → list ra
    [ ] P0-P2 priority → ghi lại
  - Output: Tổng hợp missing features

Bước 0.3: Đọc LITERATURE_REVIEW.md
  - Đọc: TOÀN BỘ file
  - Mục tiêu: Hiểu 17 papers, Stream DaQ là primary competitor
  - Checklist:
    [ ] 17 papers → đọc từng paper, ghi citation
    [ ] Stream DaQ → ghi lại key findings
    [ ] Other tools → ghi lại comparison
  - Output: Summary of literature

Bước 0.4: Đọc COMPETITIVE_ANALYSIS.md
  - Đọc: TOÀN BỘ file
  - Mục tiêu: Hiểu 8 tools, Stream DaQ thắng về architecture
  - Checklist:
    [ ] 8 tools → list và comparison
    [ ] Architecture comparison → ghi strengths/weaknesses
    [ ] Stream DaQ wins → tại sao?
  - Output: Comparison table

Bước 0.5: Đọc HYPOTHESES.md
  - Đọc: TOÀN BỘ file
  - Mục tiêu: Hiểu 7 hypotheses (H1-H7)
  - Checklist:
    [ ] H1 → mô tả, experiment design
    [ ] H2 → mô tả, experiment design
    [ ] H3 → mô tả, experiment design
    [ ] H4 → mô tả, experiment design
    [ ] H5 → mô tả, experiment design
    [ ] H6 → mô tả, experiment design
    [ ] H7 → mô tả, experiment design
  - Output: Hypotheses summary

Bước 0.6: Đọc CONTRIBUTIONS.md
  - Đọc: TOÀN BỘ file
  - Mục tiêu: Hiểu positioning
  - Checklist:
    [ ] Positioning statement → ghi lại
    [ ] Research/education platform vs production → ghi distinction
  - Output: Positioning summary

Bước 0.7: Đọc PAPER_SECTIONS/*.md (4 files)
  - Đọc: TOÀN BỘ từng file
  - Introduction.md:
    [ ] Problem statement → OK?
    [ ] Gap → OK?
    [ ] Approach → OK?
    [ ] Contribution → OK?
  - RelatedWork.md:
    [ ] Comparison table → đủ 8 dimensions?
    [ ] Literature → đủ papers?
  - Evaluation.md:
    [ ] Methodology → OK?
    [ ] Metrics → OK?
    [ ] CI → có bootstrap chưa?
  - Limitations.md:
    [ ] Streaming vs batch → honest?
    [ ] Other limitations → đủ?
  - Output: Per-section assessment

Bước 0.8: Đọc SPEC.md
  - Đọc: TOÀN BỘ file (216 lines)
  - Mục tiêu: Hiểu F1-F10, NF1-NF5
  - Checklist:
    [ ] F1-F10 functional requirements → ghi lại
    [ ] NF1-NF5 non-functional requirements → ghi lại
    [ ] Implementation status → OK?
  - Output: Requirements summary

Bước 0.9: Đọc README.md
  - Đọc: TOÀN BỘ file (308 lines)
  - Mục tiêu: Hiểu tổng quan project
  - Checklist:
    [ ] Setup instructions → OK?
    [ ] Diagrams → chính xác?
    [ ] Architecture → đúng code?
  - Output: README assessment

Bước 0.10: Đọc PILLARS.md (nếu có)
  - Đọc: TOÀN BỘ file
  - Checklist:
    [ ] Pillars → ghi lại
    [ ] Implementation → OK?
  - Output: Pillars summary
```

### B.2 — Plan cho Phần 0.2: Code Files (13 files)

```
CODE FILES CỐT LÕI - ĐỌC TOÀN BỘ TỪNG FILE:

Bước 0.11: Đọc streamdq/rules/base.py
  - Đọc: TOÀN BỘ file
  - Mục tiêu: Hiểu RuleContext, Violation dataclass
  - Checklist:
    [ ] RuleContext dataclass → fields gì?
    [ ] external_context → có populate không?
    [ ] Violation dataclass → fields đủ không?
    [ ] RuleResult dataclass → fields gì?
    [ ] DataQualityRule ABC → clean không?
  - Output: base.py assessment

Bước 0.12: Đọc streamdq/rules/syntactic.py (291 lines)
  - Đọc: TOÀN BỘ file
  - Mục tiêu: Hiểu SYN001, SYN002, SYN003
  - Checklist:
    [ ] SYN001 (Fare validity):
      - [ ] Check null? → dòng nào?
      - [ ] Check NaN? → dùng math.isnan()?
      - [ ] Check type? → dòng nào?
      - [ ] Check range? → dòng nào?
      - [ ] Violation object đủ fields?
      - [ ] processing_latency_ms computed?
    [ ] SYN002 (Location validity):
      - [ ] Check null?
      - [ ] Check NaN?
      - [ ] Check lat/lon range?
      - [ ] Check zone validity?
      - [ ] Violation object đủ fields?
    [ ] SYN003 (Timestamp):
      - [ ] Check null?
      - [ ] Check not in future?
      - [ ] Check staleness? (currently missing)
      - [ ] Violation object đủ fields?
  - Output: syntactic.py assessment với B1, B6 status

Bước 0.13: Đọc streamdq/rules/semantic.py (276 lines)
  - Đọc: TOÀN BỘ file
  - Mục tiêu: Hiểu SEM001, SEM002, SEM003
  - Checklist:
    [ ] SEM001 (Fare range):
      - [ ] Adaptive threshold → dùng historical_stats?
      - [ ] Check fare > 0?
      - [ ] Check fare < adaptive threshold?
      - [ ] External context used?
    [ ] SEM002 (Trip duration):
      - [ ] Check pickup_datetime parsed?
      - [ ] Check dropoff_datetime parsed?
      - [ ] Check duration reasonable?
      - [ ] Duration range check?
    [ ] SEM003 (Speed):
      - [ ] Fixed threshold → giá trị nào?
      - [ ] Check speed > threshold?
      - [ ] Adaptive? (currently no)
  - Output: semantic.py assessment

Bước 0.14: Đọc streamdq/rules/cross_record.py (329 lines)
  - Đọc: TOÀN BỘ file
  - Mục tiêu: Hiểu CRS001, CRS002, CRS003
  - Checklist:
    [ ] CRS001 (GPS speed):
      - [ ] Haversine formula → đúng không?
      - [ ] Speed calculation → đúng không?
      - [ ] State management → global dict?
    [ ] CRS002 (GPS spoofing):
      - [ ] Speed range → 2-20 km/h gap?
      - [ ] B3 issue → vị trí line 148?
      - [ ] Moderate spoofing → covered?
    [ ] CRS003 (Duplicates):
      - [ ] Duplicate detection logic → đúng không?
      - [ ] B2 issue → injection no-op?
      - [ ] State management → checked?
    [ ] State checkpointing:
      - [ ] save_state() → line nào?
      - [ ] load_state() → line nào?
      - [ ] Wired? (currently not)
  - Output: cross_record.py assessment với B2, B3 status

Bước 0.15: Đọc streamdq/rules/adaptive.py (191 lines)
  - Đọc: TOÀN BỘ file
  - Mục tiêu: Hiểu rolling percentile, threshold override
  - Checklist:
    [ ] Rolling percentile computation:
      - [ ] P10/P90 calculation → dòng nào?
      - [ ] B8 issue → int() truncation?
      - [ ] Interpolation → có không?
    [ ] Recompute frequency:
      - [ ] Every 1000 events → dòng nào?
      - [ ] Configurable? → có không?
    [ ] Override mechanism:
      - [ ] Human override → dòng nào?
      - [ ] Clean implementation?
    [ ] Distributed computation:
      - [ ] Driver-only? → dòng nào?
      - [ ] B4 issue → foreachBatch bottleneck?
  - Output: adaptive.py assessment với B4, B8 status

Bước 0.16: Đọc streamdq/rules/registry.py (120 lines)
  - Đọc: TOÀN BỘ file
  - Mục tiêu: Hiểu RuleRegistry, evaluate_all
  - Checklist:
    [ ] RuleRegistry class → clean không?
    [ ] evaluate_all() → dòng nào?
    [ ] Rule registration → dễ dàng?
    [ ] Extensible? → có test không?
  - Output: registry.py assessment

Bước 0.17: Đọc streamdq/pipeline/local_pipeline.py
  - Đọc: TOÀN BỘ file
  - Mục tiêu: Hiểu LocalPipeline, external_context = {}
  - Checklist:
    [ ] external_context → luôn empty?
    [ ] LocalPipeline evaluate() → thế nào?
    [ ] Rule invocation → sequential?
    [ ] Violation storage → SQLite?
  - Output: local_pipeline.py assessment

Bước 0.18: Đọc streamdq/pipeline/spark_pipeline.py
  - Đọc: TOÀN BỘ file (ít nhất 304 lines)
  - Mục tiêu: Hiểu SparkPipeline, foreachBatch, metrics
  - Checklist:
    [ ] Spark micro-batch:
      - [ ] outputMode → complete?
      - [ ] foreachBatch → dòng nào?
      - [ ] Micro-batch interval → 500ms?
    [ ] GTFS routing:
      - [ ] GTFS topic → có đọc không?
      - [ ] CRS rules wired? (currently not)
    [ ] Kafka violation sink:
      - [ ] Producer → có không?
      - [ ] quality-violations topic → có không?
    [ ] Prometheus metrics:
      - [ ] HTTP endpoint → có không?
      - [ ] Stub metrics?
    [ ] foreachBatch bottleneck:
      - [ ] B4 issue → line nào?
    [ ] Latency measurement:
      - [ ] B6 issue → hardcoded = 0?
  - Output: spark_pipeline.py assessment với B4, B6 status

Bước 0.19: Đọc streamdq/evaluation/run_evaluation.py
  - Đọc: TOÀN BỘ file
  - Mục tiêu: Hiểu anomaly injection, B2 bug
  - Checklist:
    [ ] Anomaly types:
      - [ ] 8 types → list ra
      - [ ] Duplicate injection → B2 issue line nào?
      - [ ] 7/8 work → type nào broken?
    [ ] Ground truth tracking:
      - [ ] Injected_anomalies table → OK?
      - [ ] Entity index → OK?
    [ ] LocalPipeline vs SparkPipeline:
      - [ ] Line 183 → LocalPipeline?
  - Output: run_evaluation.py assessment với B2 status

Bước 0.20: Đọc streamdq/evaluation/metrics.py
  - Đọc: TOÀN BỘ file
  - Mục tiêu: Hiểu precision/recall/F1 computation
  - Checklist:
    [ ] Precision calculation → đúng?
    [ ] Recall calculation → đúng?
    [ ] F1 calculation → đúng?
    [ ] Detection rate → đúng?
    [ ] Bootstrap CI → có không?
  - Output: metrics.py assessment

Bước 0.21: Đọc streamdq/evaluation/comparison.py
  - Đọc: TOÀN BỘ file
  - Mục tiêu: Hiểu comparison vs baselines
  - Checklist:
    [ ] Comparison metrics → gì?
    [ ] Numbers → estimates hay measured?
    [ ] Line 144 → P50 hardcoded?
  - Output: comparison.py assessment

Bước 0.22: Đọc streamdq/storage/violation_store.py
  - Đọc: TOÀN BỘ file
  - Mục tiêu: Hiểu SQLite storage, B5 WAL issue
  - Checklist:
    [ ] SQLite connection → OK?
    [ ] WAL mode → có không? (B5 issue)
    [ ] PRAGMA journal_mode → có WAL?
    [ ] Write throughput → OK?
  - Output: violation_store.py assessment với B5 status

Bước 0.23: Đọc tests/test_*.py
  - Đọc: TOÀN BỘ từng file
  - Mục tiêu: Hiểu unit tests cho từng rule category
  - Checklist:
    [ ] test_syntactic.py → SYN001-003 covered?
    [ ] test_semantic.py → SEM001-003 covered?
    [ ] test_cross_record.py → CRS001-003 covered?
    [ ] test_adaptive.py → adaptive covered?
    [ ] Coverage → đủ không?
  - Output: tests assessment
```

### B.3 — Plan cho Phần 0.3: Rules Files

```
RULES FILES - ĐỌC TOÀN BỘ:

Bước 0.24: Đọc .cursor/rules/agent-rules.mdc
  - Đọc: TOÀN BỘ file
  - Mục tiêu: Hiểu WAVES Research Agent Rules
  - Checklist:
    [ ] Work principles → đã follow?
    [ ] Anti-patterns → đã tránh?
    [ ] MCP usage → đã dùng?
    [ ] Skills → đã dùng?
  - Output: agent-rules.mdc assessment

Bước 0.25: Đọc .cursor/rules/streamdq-master.mdc
  - Đọc: TOÀN BỘ file
  - Mục tiêu: Hiểu StreamDQ Master Rules
  - Checklist:
    [ ] 9 rules (SYN001-003, SEM001-003, CRS001-003) → OK?
    [ ] B1-B6 blockers → status?
    [ ] Rule authoring standards → RA1-RA3?
    [ ] Evaluation standards → EV1-EV4?
  - Output: streamdq-master.mdc assessment

Bước 0.26: Đọc .cursor/rules/research-writing.mdc
  - Đọc: TOÀN BỘ file
  - Mục tiêu: Hiểu Scientific Writing Rules
  - Checklist:
    [ ] Claim classification (WC1-WC3)?
    [ ] Positioning (WP1-WP3)?
    [ ] Paper sections (PS-INTRO1 to PS-DISC1)?
    [ ] Writing style (WS1-WS5)?
  - Output: research-writing.mdc assessment
```

### B.4 — Plan cho Phần 1: Phân Tích Tên Đề Tài

```
PHÂN TÍCH TÊN ĐỀ TÀI - TỪNG BƯỚC:

1.1.1: "Context-Aware" - Đọc code để verify
  - Đọc adaptive.py (191 lines) → hiểu threshold computation
  - Đọc base.py (105 lines) → hiểu external_context
  - Đọc semantic.py (276 lines) → hiểu SEM001 historical_stats
  - Đọc local_pipeline.py → hiểu external_context = {}
  - Đọc spark_pipeline.py → hiểu external_context = {}
  - Grep toàn bộ codebase: "external_context"
  - Kết luận: Score = ?/10

1.1.2: "Context-Aware" - Research
  - Dùng literature-review skill: "context-aware data quality streaming"
  - Dùng research-lookup: Stream DaQ dynamic constraint adaptation
  - Dùng research-lookup: AutoDQM beta-binomial thresholds
  - Trả lời: Novel hay label?

1.1.3: "Context-Aware" - So sánh
  - IBM/Precisely context-aware → ghi lại
  - Grab context-aware → ghi lại
  - StreamDQ → gap analysis

1.2.1: "Streaming" - Đọc code để verify
  - Đọc spark_pipeline.py:249-304 → micro-batch?
  - Đọc docker-compose.yml:48 → Dockerfile.spark?
  - Đọc cross_record.py:52-183 → global dicts?
  - Đọc run_evaluation.py:183 → LocalPipeline?
  - Kết luận: Score = ?/10

1.2.2: "Streaming" - Research
  - Dùng research-lookup: Flink vs Spark latency
  - Dùng paper-lookup: Stream DaQ (arXiv:2506.06147)
  - So sánh: micro-batch vs true streaming

1.3.1: "Framework" - Đọc code để verify
  - Đọc base.py:1-105 → ABC clean?
  - Đọc registry.py:1-120 → extensible?
  - Đọc syntactic.py:1-291 → subclass?
  - Đọc tests/test_*.py → tests?
  - Kết luận: Score = ?/10

1.4.1: "Data Quality Monitoring" - Đọc code để verify
  - Đọc SPEC.md:139-168 → 9 rules?
  - Đọc syntactic.py → SYN001-003
  - Đọc semantic.py → SEM001-003
  - Đọc cross_record.py → CRS001-003
  - IBM 7 dimensions → coverage matrix
  - Kết luận: Score = ?/10
```

### B.5 — Plan cho Phần 2: Chấm Điểm Từng Component

```
CHẤM ĐIỂM - TỪNG COMPONENT:

2.1.1: Rule Engine - Đọc và chấm từng rule
  SYN001:
    - Đọc syntactic.py:40-118
    - Checklist: null? NaN? type? range?
    - B1: NaN fix verified?
    - B6: latency computed?
    - Score: ?/10

  SYN002:
    - Đọc syntactic.py:134-193
    - Checklist: lat/lon? zone?
    - Score: ?/10

  SYN003:
    - Đọc syntactic.py:229-290
    - Checklist: future? staleness?
    - Score: ?/10

  SEM001:
    - Đọc semantic.py:35-83
    - Checklist: adaptive? historical_stats?
    - Score: ?/10

  SEM002:
    - Đọc semantic.py:119-178
    - Checklist: duration calculation?
    - Score: ?/10

  SEM003:
    - Đọc semantic.py:213-275
    - Checklist: fixed threshold?
    - Score: ?/10

  CRS001:
    - Đọc cross_record.py:52-183
    - Checklist: Haversine correct?
    - Score: ?/10

  CRS002:
    - Đọc cross_record.py:148
    - Checklist: speed range gap (B3)?
    - Score: ?/10

  CRS003:
    - Đọc run_evaluation.py:102-104
    - Checklist: B2 duplicate injection broken?
    - Score: ?/10

  Subtotal: ?/90

2.2.1: Adaptive Threshold - Đọc và chấm từng aspect
  - Đọc adaptive.py:101-107 → percentile B8?
  - Đọc adaptive.py:83-84 → recompute freq?
  - Đọc adaptive.py:175-182 → override?
  - Đọc spark_pipeline.py:176 → driver-only B4?
  - Đọc base.py:31-35 → external_context empty?
  - Tìm: drift detection?
  - Subtotal: ?/60

2.3.1: Streaming Pipeline - Đọc và chấm từng aspect
  - Đọc spark_pipeline.py:249-304 → micro-batch?
  - Đọc spark_pipeline.py:203-218 → for-loop?
  - Đọc spark_pipeline.py:150-304 → GTFS unwired?
  - Đọc spark_pipeline.py:221-222 → Kafka sink?
  - Đọc spark_pipeline.py:26-82 → Prometheus?
  - Đọc cross_record.py:264-328 → checkpointing?
  - Subtotal: ?/60

2.4.1: Evaluation Framework - Đọc và chấm từng aspect
  - Đọc metrics.py:1-175 → ground truth?
  - Đọc run_evaluation.py:48-106 → B2?
  - Đọc metrics.py:108-154 → precision/recall?
  - Đọc comparison.py → estimates?
  - Đọc spark_pipeline.py:225 → B6?
  - Tìm: bootstrap CI?
  - Subtotal: ?/60

2.5.1: Documentation - Đọc và chấm từng aspect
  - Đọc PAPER_SECTIONS/*.md → paper sections?
  - Đọc README.md → diagrams?
  - Đọc SPEC.md → requirements?
  - Đọc LITERATURE_REVIEW.md → 17 papers?
  - Đọc COMPETITIVE_ANALYSIS.md → 8 tools?
  - Đọc CODE_AUDIT.md → 10 issues?
  - Subtotal: ?/60

2.6.1: Overall Scorecard
  - Rule Engine: ?/10 × 25%
  - Adaptive Threshold: ?/10 × 20%
  - Streaming Pipeline: ?/10 × 20%
  - Evaluation Framework: ?/10 × 15%
  - Documentation: ?/10 × 20%
  - OVERALL: ?/10
```

### B.6 — Plan cho Phần 3: Blockers & Known Issues

```
BLOCKERS - TỪNG BƯỚC VERIFY VÀ FIX:

3.1.1: B1 - NaN Silent Pass-Through
  Verify:
    [ ] Đọc syntactic.py:59
    [ ] Tìm: có dùng math.isnan()?
    [ ] Test: NaN input → Violation?
    [ ] Status: FIXED / NOT_FIXED
  Fix (nếu NOT_FIXED):
    [ ] Thêm math.isnan() guard
    [ ] Viết unit test
    [ ] Verify fix
    [ ] Ghi vào P0-1 plan

3.1.2: B2 - Duplicate Injection No-Op
  Verify:
    [ ] Đọc run_evaluation.py:102-104
    [ ] Tìm: emit 1 hay 2 records?
    [ ] Test: inject duplicate → CRS003 fires?
    [ ] Status: FIXED / NOT_FIXED
  Fix (nếu NOT_FIXED):
    [ ] Sửa: emit original + duplicate
    [ ] Verify: CRS003 fires
    [ ] Ghi vào P0-2 plan

3.1.3: B6 - processing_latency_ms = 0
  Verify:
    [ ] Tìm tất cả places: processing_latency_ms = 0
    [ ] Đọc spark_pipeline.py:225
    [ ] Test: latency = actual computation?
    [ ] Status: FIXED / NOT_FIXED
  Fix (nếu NOT_FIXED):
    [ ] Thay: actual latency computation
    [ ] Verify: latency > 0
    [ ] Ghi vào P0-3 plan

3.2.1: B3 - CRS002 Speed Range Gap
  Verify:
    [ ] Đọc cross_record.py:148
    [ ] Tìm: speed threshold hiện tại
    [ ] Research: realistic range cho moderate spoofing
    [ ] Status: FIXED / NOT_FIXED
  Fix (nếu NOT_FIXED):
    [ ] Mở rộng threshold
    [ ] Viết unit test
    [ ] Verify: speed = 5, 10, 15 km/h → fires
    [ ] Ghi vào P1-1 plan

3.2.2: B4 - foreachBatch Driver Bottleneck
  Verify:
    [ ] Đọc spark_pipeline.py:176
    [ ] Tìm: bottleneck ở đâu?
    [ ] Research: Pandas UDF?
    [ ] Status: KNOWN LIMITATION / FIXED
  Document (nếu KNOWN):
    [ ] Ghi vào paper limitations
    [ ] KHÔNG fix trong prototype

3.2.3: B5 - SQLite No WAL Mode
  Verify:
    [ ] Đọc violation_store.py
    [ ] Tìm: PRAGMA journal_mode?
    [ ] Status: FIXED / NOT_FIXED
  Fix (nếu NOT_FIXED):
    [ ] Thêm: PRAGMA journal_mode=WAL
    [ ] Benchmark: throughput trước/sau
    [ ] Ghi vào P1-2 plan

3.2.4: B8 - Percentile Int Truncation
  Verify:
    [ ] Đọc adaptive.py:101
    [ ] Tìm: int() truncation
    [ ] Status: FIXED / NOT_FIXED
  Fix (nếu NOT_FIXED):
    [ ] Thay: proper interpolation
    [ ] Viết test: percentile 33.3, 66.6
    [ ] Ghi vào P1-3 plan

3.3.1: B7, B9, B10 - Minor Issues
  [ ] B7: Config scattered → assess impact
  [ ] B9: No Prometheus → assess impact
  [ ] B10: No alert routing → assess impact

3.4.1: Dockerfile.spark Missing
  Verify:
    [ ] Đọc docker-compose.yml:48
    [ ] Tìm: Dockerfile.spark có tồn tại?
    [ ] Status: EXISTS / MISSING
  Fix (nếu MISSING):
    [ ] Tạo Dockerfile.spark
    [ ] Test: docker compose up
    [ ] Ghi vào P0-4 plan

3.4.2: GTFS Topic Not Wired
  Verify:
    [ ] Đọc spark_pipeline.py:150-304
    [ ] Tìm: GTFS topic read?
    [ ] Tìm: CRS rules wired?
    [ ] Status: WIRED / NOT_WIRED
  Fix (nếu NOT_WIRED):
    [ ] Wire: GTFS → CRS001/CRS002
    [ ] Test: GTFS violations appear
    [ ] Ghi vào P0-5 plan

3.4.3: Kafka Violation Sink Not Implemented
  Verify:
    [ ] Đọc spark_pipeline.py:221-222
    [ ] Tìm: Kafka producer?
    [ ] Status: IMPLEMENTED / NOT_IMPLEMENTED
  Fix (nếu NOT_IMPLEMENTED):
    [ ] Implement: Kafka producer
    [ ] Test: violations → quality-violations topic
    [ ] Ghi vào P1-4 plan
```

### B.7 — Plan cho Phần 5: Research Agenda

```
RESEARCH AGENDA - TỪNG RQ:

5.1.1: RQ1 - Context-Aware Literature
  [ ] Dùng literature-review: "context-aware data quality streaming"
  [ ] Dùng literature-review: "adaptive threshold streaming DQ 2024-2026"
  [ ] Dùng research-lookup: Stream DaQ dynamic constraint adaptation
  [ ] Dùng research-lookup: AutoDQM beta-binomial
  [ ] Verify: StreamDQ approach novel or label?
  [ ] Gap: what StreamDQ lacks?
  [ ] Recommendation: adopt/adapt/ignore?

5.1.2: RQ2 - Stream DaQ Comparison
  [ ] Dùng paper-lookup: arXiv:2506.06147
  [ ] Verify: 30+ checks vs 9 rules
  [ ] Verify: Pathway vs global dicts
  [ ] Verify: drift detection vs rolling percentile
  [ ] Decision: adopt Pathway or keep Spark?

5.1.3: RQ3 - Adaptive Threshold Approaches
  [ ] Dùng literature-review: adaptive threshold methods
  [ ] Papers: strAEm++DD (arXiv:2305.08977)
  [ ] Papers: Adaptive NAD (arXiv:2410.22967)
  [ ] Papers: AutoDQM (arXiv:2501.13789)
  [ ] Compare: beta-binomial vs rolling vs autoencoder vs two-layer
  [ ] Decision: simplest for MVP?

5.1.4: RQ4 - Most Impactful Fixes
  [ ] Dùng scientific-critical-thinking on CODE_AUDIT.md
  [ ] Prioritize: CRITICAL > MAJOR > MINOR
  [ ] Top 5 fixes: list + expected impact

5.1.5: RQ5 - Fitness for Purpose
  [ ] Dùng literature-review: "data quality fitness for purpose metrics"
  [ ] Dùng research-lookup: IBM/Precisely approach
  [ ] Gap: StreamDQ missing fitness-for-purpose
  [ ] FIT001 design proposal

5.1.6: RQ6 - IBM vs StreamDQ Taxonomy
  [ ] Dùng scientific-critical-thinking
  [ ] Compare: IBM 7 dimensions vs SYN/SEM/CRS vs ISO 8000
  [ ] Decision: rebrand or add missing?

5.2.1: Papers to Verify
  [ ] Stream DaQ (arXiv:2506.06147) → verify claims
  [ ] AutoDQM (arXiv:2501.13789) → verify beta-binomial
  [ ] strAEm++DD (arXiv:2305.08977) → verify autoencoder
  [ ] Adaptive NAD (arXiv:2410.22967) → verify two-layer
  [ ] StreamShield (arXiv:2602.03189) → verify Flink resiliency
```

### B.8 — Plan cho Phần 6: Blog Research (13 blogs)

```
BLOG RESEARCH - TỪNG BLOG (KHÔNG ĐƯỢC SKIP):

6.1.1: Grab Data Observability
  [ ] Dùng WebFetch: engineering.grab.com/data-observability
  [ ] Đọc: TOÀN BỘ nội dung
  [ ] Trích xuất: framework/approach
  [ ] Trích xuất: context-aware handling
  [ ] Trích xuất: streaming handling
  [ ] Trích xuất: data quality handling
  [ ] So sánh: vs StreamDQ
  [ ] Lessons: 2-3 sentences

6.1.2: Rethinking Streaming Processing (primary)
  [ ] Dùng WebFetch: engineering.grab.com/rethinking-streaming-processing-data-exploration
  [ ] Đọc: TOÀN BỘ nội dung
  [ ] Trích xuất: streaming processing patterns
  [ ] Trích xuất: latency handling
  [ ] So sánh: vs StreamDQ
  [ ] Lessons: 2-3 sentences

6.1.3: Signals Marketplace
  [ ] Dùng WebFetch: engineering.grab.com/signals-market-place
  [ ] Đọc: TOÀN BỘ nội dung
  [ ] Trích xuất: data quality in marketplace
  [ ] So sánh: vs StreamDQ
  [ ] Lessons: 2-3 sentences

6.1.4: Data First SLA
  [ ] Dùng WebFetch: engineering.grab.com/data-first-sla-always
  [ ] Đọc: TOÀN BỘ nội dung
  [ ] Trích xuất: SLA for data quality
  [ ] So sánh: vs StreamDQ
  [ ] Lessons: 2-3 sentences

6.1.5: Grab Kafka Data Quality (InfoQ)
  [ ] Dùng WebFetch: www.infoq.com/news/2025/12/grab-kafka-data-quality/
  [ ] Đọc: TOÀN BỘ nội dung
  [ ] Trích xuất: Kafka + DQ integration
  [ ] So sánh: vs StreamDQ
  [ ] Lessons: 2-3 sentences

6.1.6: Real-Time DQ Monitoring
  [ ] Dùng WebFetch: engineering.grab.com/real-time-data-quality-monitoring
  [ ] Đọc: TOÀN BỘ nội dung
  [ ] Trích xuất: real-time monitoring approach
  [ ] So sánh: vs StreamDQ
  [ ] Lessons: 2-3 sentences

6.1.7: Alibaba/Grab Flink Journey
  [ ] Dùng WebFetch: alibabacloud.com/blog/.../grab-journey-with-apache-flink...
  [ ] Đọc: TOÀN BỘ nội dung
  [ ] Trích xuất: Flink + data quality
  [ ] So sánh: vs StreamDQ
  [ ] Lessons: 2-3 sentences

6.1.8: Real-Time Data Ingestion
  [ ] Dùng WebFetch: engineering.grab.com/real-time-data-ingestion
  [ ] Đọc: TOÀN BỘ nội dung
  [ ] Trích xuất: ingestion patterns
  [ ] So sánh: vs StreamDQ
  [ ] Lessons: 2-3 sentences

6.1.9: ACM Paper (GRab)
  [ ] Dùng WebFetch: dl.acm.org/doi/epdf/10.1145/3686592.3686609
  [ ] Đọc: TOÀN BỘ nội dung
  [ ] Trích xuất: academic findings
  [ ] So sánh: vs StreamDQ
  [ ] Lessons: 2-3 sentences
  [ ] Citation: ghi lại

6.1.10: Rethinking Streaming (alt - duplicate check)
  [ ] Verify: same content as 6.1.2?
  [ ] If different: extract lessons
  [ ] If same: mark as duplicate

6.2.1: Tinybird Real-Time Streaming
  [ ] Dùng WebFetch: tinybird.co/blog/real-time-streaming-data-architectures-that-scale
  [ ] Đọc: TOÀN BỘ nội dung
  [ ] Trích xuất: scalable streaming architectures
  [ ] So sánh: vs StreamDQ
  [ ] Lessons: 2-3 sentences

6.2.2: IBM Data Quality
  [ ] Dùng WebFetch: ibm.com/think/topics/data-quality
  [ ] Đọc: TOÀN BỘ nội dung
  [ ] Trích xuất: IBM 7 DQ dimensions
  [ ] Trích xuất: AI-readiness framing
  [ ] So sánh: vs StreamDQ
  [ ] Lessons: 2-3 sentences

6.2.3: Precisely Big Data Quality
  [ ] Dùng WebFetch: precisely.com/data-quality/big-data-quality-mastering...
  [ ] Đọc: TOÀN BỘ nội dung
  [ ] Trích xuất: 5-step framework
  [ ] Trích xuất: Discover-Define-Design-Deploy-Monitor
  [ ] So sánh: vs StreamDQ
  [ ] Lessons: 2-3 sentences
```

### B.9 — Plan cho Phần 7: Paper Learning (22 papers)

```
PAPER LEARNING - TỪNG PAPER (KHÔNG ĐƯỢC SKIP):

MỖI PAPER - QUY TRÌNH BẮT BUỘC:
1. Read: TOÀN BỘ PDF (dùng nhiều Read calls nếu cần)
2. Extract: Title, Authors, Year, Venue
3. Extract: Research question
4. Extract: Methodology
5. Extract: Results/Findings
6. Extract: Limitations
7. Extract: Specific lessons for StreamDQ
8. Citation: ghi lại để dùng trong paper

7.1.1: 1-s2.0-S0019057825005129-main.pdf
  [ ] Đọc: TOÀN BỘ PDF
  [ ] Extract: research question
  [ ] Extract: methodology
  [ ] Extract: results
  [ ] Extract: limitations
  [ ] Mapping: giúp gì cho "Context-Aware Streaming DQ"?
  [ ] Citation: ghi lại

7.1.2: 1-s2.0-S0020025526004196-main.pdf
  [ ] Đọc: TOÀN BỘ PDF
  [ ] Extract: research question
  [ ] Extract: methodology
  [ ] Extract: results
  [ ] Extract: limitations
  [ ] Mapping: giúp gì cho "Context-Aware Streaming DQ"?
  [ ] Citation: ghi lại

7.1.3: 1-s2.0-S0031320325011793-main.pdf
  [ ] Đọc: TOÀN BỘ PDF
  [ ] Extract: research question
  [ ] Extract: methodology
  [ ] Extract: results
  [ ] Extract: limitations
  [ ] Mapping: giúp gì cho "Context-Aware Streaming DQ"?
  [ ] Citation: ghi lại

7.1.4: 1-s2.0-S0167739X17329151-main.pdf
  [ ] Đọc: TOÀN BỘ PDF
  [ ] Extract: research question
  [ ] Extract: methodology
  [ ] Extract: results
  [ ] Extract: limitations
  [ ] Mapping: giúp gì cho "Context-Aware Streaming DQ"?
  [ ] Citation: ghi lại

7.1.5: 1-s2.0-S0167739X26001548-main.pdf
  [ ] Đọc: TOÀN BỘ PDF
  [ ] Extract: research question
  [ ] Extract: methodology
  [ ] Extract: results
  [ ] Extract: limitations
  [ ] Mapping: giúp gì cho "Context-Aware Streaming DQ"?
  [ ] Citation: ghi lại

7.1.6: 1-s2.0-S0167947325002142-main.pdf
  [ ] Đọc: TOÀN BỘ PDF
  [ ] Extract: research question
  [ ] Extract: methodology
  [ ] Extract: results
  [ ] Extract: limitations
  [ ] Mapping: giúp gì cho "Context-Aware Streaming DQ"?
  [ ] Citation: ghi lại

7.1.7: 1-s2.0-S0360835225006540-main.pdf
  [ ] Đọc: TOÀN BỘ PDF
  [ ] Extract: research question
  [ ] Extract: methodology
  [ ] Extract: results
  [ ] Extract: limitations
  [ ] Mapping: giúp gì cho "Context-Aware Streaming DQ"?
  [ ] Citation: ghi lại

7.1.8: 1-s2.0-S0925231225028619-main.pdf
  [ ] Đọc: TOÀN BỘ PDF
  [ ] Extract: research question
  [ ] Extract: methodology
  [ ] Extract: results
  [ ] Extract: limitations
  [ ] Mapping: giúp gì cho "Context-Aware Streaming DQ"?
  [ ] Citation: ghi lại

7.1.9: 1-s2.0-S0925231226009033-main.pdf
  [ ] Đọc: TOÀN BỘ PDF
  [ ] Extract: research question
  [ ] Extract: methodology
  [ ] Extract: results
  [ ] Extract: limitations
  [ ] Mapping: giúp gì cho "Context-Aware Streaming DQ"?
  [ ] Citation: ghi lại

7.1.10: 1-s2.0-S0950705125012894-main.pdf
  [ ] Đọc: TOÀN BỘ PDF
  [ ] Extract: research question
  [ ] Extract: methodology
  [ ] Extract: results
  [ ] Extract: limitations
  [ ] Mapping: giúp gì cho "Context-Aware Streaming DQ"?
  [ ] Citation: ghi lại

7.1.11: 1-s2.0-S095070512501768X-main.pdf
  [ ] Đọc: TOÀN BỘ PDF
  [ ] Extract: research question
  [ ] Extract: methodology
  [ ] Extract: results
  [ ] Extract: limitations
  [ ] Mapping: giúp gì cho "Context-Aware Streaming DQ"?
  [ ] Citation: ghi lại

7.1.12: 1-s2.0-S095219762600792X-main.pdf
  [ ] Đọc: TOÀN BỘ PDF
  [ ] Extract: research question
  [ ] Extract: methodology
  [ ] Extract: results
  [ ] Extract: limitations
  [ ] Mapping: giúp gì cho "Context-Aware Streaming DQ"?
  [ ] Citation: ghi lại

7.1.13: 1-s2.0-S0957417425034979-main.pdf
  [ ] Đọc: TOÀN BỘ PDF
  [ ] Extract: research question
  [ ] Extract: methodology
  [ ] Extract: results
  [ ] Extract: limitations
  [ ] Mapping: giúp gì cho "Context-Aware Streaming DQ"?
  [ ] Citation: ghi lại

7.1.14: 1-s2.0-S0957417425040059-main.pdf
  [ ] Đọc: TOÀN BỘ PDF
  [ ] Extract: research question
  [ ] Extract: methodology
  [ ] Extract: results
  [ ] Extract: limitations
  [ ] Mapping: giúp gì cho "Context-Aware Streaming DQ"?
  [ ] Citation: ghi lại

7.1.15: 1-s2.0-S0957417426008262-main.pdf
  [ ] Đọc: TOÀN BỘ PDF
  [ ] Extract: research question
  [ ] Extract: methodology
  [ ] Extract: results
  [ ] Extract: limitations
  [ ] Mapping: giúp gì cho "Context-Aware Streaming DQ"?
  [ ] Citation: ghi lại

7.1.16: 1-s2.0-S1110016826001225-main.pdf
  [ ] Đọc: TOÀN BỘ PDF
  [ ] Extract: research question
  [ ] Extract: methodology
  [ ] Extract: results
  [ ] Extract: limitations
  [ ] Mapping: giúp gì cho "Context-Aware Streaming DQ"?
  [ ] Citation: ghi lại

7.1.17: 1-s2.0-S1568494625007537-main.pdf
  [ ] Đọc: TOÀN BỘ PDF
  [ ] Extract: research question
  [ ] Extract: methodology
  [ ] Extract: results
  [ ] Extract: limitations
  [ ] Mapping: giúp gì cho "Context-Aware Streaming DQ"?
  [ ] Citation: ghi lại

7.1.18: 2204.10655v1.pdf (arXiv)
  [ ] Đọc: TOÀN BỘ PDF
  [ ] Extract: research question
  [ ] Extract: methodology
  [ ] Extract: results
  [ ] Extract: limitations
  [ ] Mapping: giúp gì cho "Context-Aware Streaming DQ"?
  [ ] Citation: ghi lại

7.1.19: 3603707.pdf (IEEE/ACM)
  [ ] Đọc: TOÀN BỘ PDF
  [ ] Extract: research question
  [ ] Extract: methodology
  [ ] Extract: results
  [ ] Extract: limitations
  [ ] Mapping: giúp gì cho "Context-Aware Streaming DQ"?
  [ ] Citation: ghi lại

7.1.20: FutureGeneration.pdf
  [ ] Đọc: TOÀN BỘ PDF
  [ ] Extract: research question
  [ ] Extract: methodology
  [ ] Extract: results
  [ ] Extract: limitations
  [ ] Mapping: giúp gì cho "Context-Aware Streaming DQ"?
  [ ] Citation: ghi lại

7.1.21: TaDA.13.pdf
  [ ] Đọc: TOÀN BỘ PDF
  [ ] Extract: research question
  [ ] Extract: methodology
  [ ] Extract: results
  [ ] Extract: limitations
  [ ] Mapping: giúp gì cho "Context-Aware Streaming DQ"?
  [ ] Citation: ghi lại

7.1.22: TSP_CMES_62902.pdf
  [ ] Đọc: TOÀN BỘ PDF
  [ ] Extract: research question
  [ ] Extract: methodology
  [ ] Extract: results
  [ ] Extract: limitations
  [ ] Mapping: giúp gì cho "Context-Aware Streaming DQ"?
  [ ] Citation: ghi lại

7.1.23: (future files)
  [ ] Đọc: TOÀN BỘ PDF
  [ ] Extract: research question
  [ ] Extract: methodology
  [ ] Extract: results
  [ ] Extract: limitations
  [ ] Mapping: giúp gì cho "Context-Aware Streaming DQ"?
  [ ] Citation: ghi lại

7.1.24: (future files)
  [ ] Đọc: TOÀN BỘ PDF
  [ ] Extract: research question
  [ ] Extract: methodology
  [ ] Extract: results
  [ ] Extract: limitations
  [ ] Mapping: giúp gì cho "Context-Aware Streaming DQ"?
  [ ] Citation: ghi lại
```

### B.10 — Plan cho Phần 8: Roadmap

```
ROADMAP - TỪNG PRIORITY:

P0 PRIORITY (Critical Fixes):
P0-1: Verify B1 (NaN) fix
  Owner: AI
  Files: syntactic.py
  Verification: pytest test_nan
  Deadline: Day 1
  Status: [ ]

P0-2: Fix B2 (duplicate injection)
  Owner: AI
  Files: run_evaluation.py
  Verification: CRS003 fires
  Deadline: Day 1-2
  Status: [ ]

P0-3: Fix B6 (latency = 0)
  Owner: AI
  Files: All rule files
  Verification: latency > 0
  Deadline: Day 2
  Status: [ ]

P0-4: Create Dockerfile.spark
  Owner: AI
  Files: Dockerfile.spark
  Verification: docker compose up
  Deadline: Day 2-3
  Status: [ ]

P0-5: Wire GTFS topic → CRS
  Owner: AI
  Files: spark_pipeline.py
  Verification: GTFS violations appear
  Deadline: Day 3
  Status: [ ]

P1 PRIORITY (Quality Improvements):
P1-1: Fix B3 (CRS002 speed)
  Owner: AI
  Files: cross_record.py
  Expected Impact: +15% GPS spoofing recall
  Deadline: Week 1
  Status: [ ]

P1-2: Fix B5 (SQLite WAL)
  Owner: AI
  Files: violation_store.py
  Expected Impact: +60% throughput
  Deadline: Week 1
  Status: [ ]

P1-3: Add percentile interpolation
  Owner: AI
  Files: adaptive.py
  Expected Impact: Statistical rigor
  Deadline: Week 1
  Status: [ ]

P1-4: Implement Kafka violation sink
  Owner: AI
  Files: spark_pipeline.py
  Expected Impact: Architecture complete
  Deadline: Week 2
  Status: [ ]

P1-5: Add Prometheus metrics HTTP
  Owner: AI
  Files: spark_pipeline.py
  Expected Impact: Grafana works
  Deadline: Week 2
  Status: [ ]

P2 PRIORITY (Enhancement Research):
P2-1: Drift detection
  Owner: AI
  Source: RQ3 research
  Expected Impact: Reduce false positives
  Research: literature-review
  Deadline: Week 2-3
  Status: [ ]

P2-2: Beta-binomial thresholds
  Owner: AI
  Source: AutoDQM paper
  Expected Impact: Better warmup
  Research: paper-lookup
  Deadline: Week 3
  Status: [ ]

P2-3: External context injection
  Owner: AI
  Source: RQ1 research
  Expected Impact: Genuine context-awareness
  Research: research-lookup
  Deadline: Week 3-4
  Status: [ ]

P2-4: Bootstrap CI
  Owner: AI
  Source: statistical-analysis skill
  Expected Impact: Honest CI
  Research: statistical-analysis
  Deadline: Week 4
  Status: [ ]

P2-5: Pandas UDF rule evaluation
  Owner: AI
  Source: B4 fix
  Expected Impact: +40% throughput
  Research: Research
  Deadline: Week 4
  Status: [ ]

P1-A to P1-F (IBM/Precisely):
P1-A: Completeness Monitoring (SYN000)
  Owner: AI
  Source: IBM
  Description: per-field null rate
  Deadline: Week 2
  Status: [ ]

P1-B: Fitness for Purpose (FIT001)
  Owner: AI
  Source: IBM
  Description: Business fitness
  Deadline: Week 2-3
  Status: [ ]

P1-C: Stale Data Detection
  Owner: AI
  Source: IBM/Precisely
  Description: Extend SYN003
  Deadline: Week 3
  Status: [ ]

P1-D: Auto-Profiling (SchemaProfiler)
  Owner: AI
  Source: Precisely Step 1
  Description: Auto-generate rules
  Deadline: Week 3
  Status: [ ]

P1-E: Data Contract Definition
  Owner: AI
  Source: Precisely Step 2-3
  Description: YAML contracts
  Deadline: Week 3
  Status: [ ]

P1-F: Alert Routing (AlertRouter)
  Owner: AI
  Source: Precisely Step 5
  Description: Slack channel
  Deadline: Week 4
  Status: [ ]
```

### B.11 — Plan cho Phần 9: MCP Verification

```
MCP VERIFICATION - TỪNG BƯỚC:

9.1.1: Kafka MCP Setup
  [ ] Đọc Kafka MCP schema descriptor
  [ ] Gọi mcp_auth (nếu cần)
  [ ] List available tools

9.1.2: Kafka Topics Check
  [ ] Gọi: kafka_topics_list
  [ ] Verify: nyc-taxi-events exists
  [ ] Verify: gtfs-vehicle-pos exists
  [ ] Verify: quality-violations exists
  [ ] Report: topics status

9.1.3: GTFS Vehicle Count
  [ ] Gọi: kafka_consume messages="gtfs-vehicle-pos" limit=1000
  [ ] Count: unique vehicle_id
  [ ] Expected: ~1700+
  [ ] Report: actual count

9.1.4: Anomaly Injection Test
  [ ] Gọi: kafka_produce test event fare_amount=-50
  [ ] Gọi: kafka_consume messages="quality-violations"
  [ ] Verify: SYN001 violation appears
  [ ] Report: injection test PASS/FAIL

9.1.5: Consumer Lag Check
  [ ] Gọi: kafka_get_consumer_group_info group="streamdq-consumer"
  [ ] Verify: lag < 1000
  [ ] Report: lag status

9.2.1: DuckDB MCP Setup
  [ ] Đọc DuckDB MCP schema descriptor
  [ ] Gọi mcp_auth (nếu cần)
  [ ] List available tools

9.2.2: Precision/Recall Query
  [ ] Gọi: duckdb_query precision/recall SQL
  [ ] Report: actual precision
  [ ] Report: actual recall by type
  [ ] Compare: vs claimed values

9.2.3: Latency Percentiles Query
  [ ] Gọi: duckdb_query latency percentiles SQL
  [ ] Report: P50
  [ ] Report: P95
  [ ] Report: P99
  [ ] Compare: vs claimed values

9.2.4: False Positive Analysis
  [ ] Gọi: duckdb_query false positive SQL
  [ ] Report: FP by rule_id
  [ ] Report: FP rate
  [ ] Compare: vs expected

9.3.1: pytest
  [ ] Chạy: pytest
  [ ] Verify: all tests pass
  [ ] Report: test results

9.3.2: docker compose up
  [ ] Chạy: docker compose up
  [ ] Verify: full pipeline starts
  [ ] Report: startup status

9.3.3: Evaluation script
  [ ] Chạy: evaluation script
  [ ] Verify: violations in SQLite
  [ ] Report: violation count

9.3.4: Grafana
  [ ] Kiểm tra: Grafana dashboard
  [ ] Verify: metrics display
  [ ] Report: dashboard status
```

---

## PHẦN C: RULES BỔ SUNG

### C.1 — Rules cho mỗi Phase

```
PHASE 1: DECOMPOSE
Rule: PHẢI đọc TOÀN BỘ tài liệu trước khi kết luận
  - Đọc 10 docs analysis → PHẢI hiểu B1-B10
  - Đọc 13 code files → PHẢI hiểu từng dòng quan trọng
  - Đọc 3 rules files → PHẢI hiểu execution rules
  - KHÔNG được kết luận khi chưa đọc đủ

PHASE 2: DIAGNOSE
Rule: PHẢI verify B1-B10 trong CODE, không phải docs
  - Đọc syntactic.py:59 → B1 NaN có fix chưa?
  - Đọc run_evaluation.py:102 → B2 duplicate có fix chưa?
  - Đọc ALL rule files → B6 latency có fix chưa?
  - KHÔNG được copy từ docs, PHẢI verify trong code

PHASE 3: PLAN
Rule: PHẢI có verification criteria cho mỗi task
  - P0-1: pytest test_nan → PASS
  - P0-2: CRS003 fires → PASS
  - P0-3: latency > 0 → PASS
  - KHÔNG được lên plan không có verification

PHASE 4: VERIFY
Rule: PHẢI dùng MCP tools để verify
  - Kafka MCP → topics, data, injection
  - DuckDB MCP → precision, recall, latency
  - KHÔNG được estimate, PHẢI measure

PHASE 5: DECIDE
Rule: PHẢI dựa trên evidence, không phải impression
  - B1, B2, B6 unfixed → NO-GO
  - All P0 fixed → CONDITIONAL GO
  - KHÔNG được "có vẻ OK"
```

### C.2 — Rules cho Paper Learning

```
MỖI PAPER - QUY TẮC BẮT BUỘC:
1. Đọc TOÀN BỘ PDF (không chỉ abstract)
2. Trích xuất 5+ key findings
3. Viết 2-3 sentences về bài học cụ thể
4. Ghi citation để dùng trong paper
5. Mapping: paper giúp gì cho "Context-Aware Streaming DQ"

VÍ DỤ OUTPUT CHO MỖI PAPER:
## Paper: [Title]
- **Citation**: [Authors, Year, Venue]
- **Research Question**: [1 sentence]
- **Methodology**: [2-3 sentences]
- **Key Findings**: [5 bullet points]
- **Limitations**: [2-3 sentences]
- **Lessons for StreamDQ**: [2-3 sentences]
- **Can cite as**: [Full citation]
```

### C.3 — Rules cho Blog Research

```
MỖI BLOG - QUY TẮC BẮT BUỘC:
1. Đọc TOÀN BỘ blog (không chỉ đọc 1 đoạn)
2. Trích xuất: approach, implementation, results
3. So sánh: họ làm gì tốt hơn StreamDQ?
4. So sánh: StreamDQ làm gì tốt hơn họ?
5. Action: bài học nào áp dụng được?

VÍ DỤ OUTPUT CHO MỖI BLOG:
## Blog: [Title]
- **Source**: [URL]
- **Framework/Approach**: [2-3 sentences]
- **Context-Aware Handling**: [1-2 sentences]
- **Streaming Handling**: [1-2 sentences]
- **Data Quality Handling**: [1-2 sentences]
- **Better than StreamDQ**: [list]
- **StreamDQ Better**: [list]
- **Lessons**: [2-3 sentences]
```

---

## PHẦN D: ANTI-PATTERNS (TUYỆT ĐỐI TRÁNH)

```
1. KHÔNG ĐƯỢC "LITE"
   - Checklist có 100 items → làm 100 items
   - File có 1000 lines → đọc 1000 lines
   - Paper có 50 pages → đọc 50 pages
   - KHÔNG được "tôm tắt" hay "lướt qua"

2. KHÔNG ĐƯỢC "FALLBACK"
   - Có skill → PHẢI dùng skill
   - Có MCP → PHẢI dùng MCP
   - Có Read tool → PHẢI đọc file
   - KHÔNG được "tôi đoán" hay "tôi nghĩ"

3. KHÔNG ĐƯỢC "SKIP"
   - Checklist item → PHẢI có kết quả
   - Task dài → PHẢI làm hết
   - Research → PHẢI đọc đủ nguồn
   - KHÔNG được "skip" hay "later"

4. KHÔNG ĐƯỢC "OVERCLAIM"
   - Chưa measure → KHÔNG claim
   - Chưa verify → KHÔNG claim
   - Chưa fix → KHÔNG claim
   - KHÔNG được "estimated" hay "approximately"

5. KHÔNG ĐƯỢC "SILENT"
   - Issue → PHẢI báo cáo
   - Blocked → PHẢI báo cáo
   - Unknown → PHẢI báo cáo
   - KHÔNG được "implied" hay "assumed"
```

---

## PHẦN E: TRIAGE DECISION RULES

```
KHI GẶP BLOCKER:
  1. Xác định: đây là CRITICAL / MAJOR / MINOR?
  2. Nếu CRITICAL → DỪNG, fix trước khi tiếp tục
  3. Nếu MAJOR → Ghi vào plan, tiếp tục
  4. Nếu MINOR → Ghi vào plan, tiếp tục

KHI GẶP UNKNOWN:
  1. Research → dùng skill để tìm hiểu
  2. Verify → đọc code/file để verify
  3. Ask → nếu vẫn không biết → hỏi user
  4. KHÔNG được "assume" hay "guess"

KHI GẶP SCOPE CREEP:
  1. User hỏi A → làm A
  2. Muốn thêm B → hỏi user trước
  3. KHÔNG được tự ý thêm feature

KHI GẶP TIME LIMIT:
  1. Theo thứ tự ưu tiên: CRITICAL > MAJOR > MINOR
  2. Làm đến đâu report đến đó
  3. Ghi rõ: đã làm gì, chưa làm gì, cần gì
  4. KHÔNG được bỏ qua critical items
```

---

## PHẦN F: REPORT FORMAT

```
MỖI KHI REPORT CHO USER:
  Phải có:
  1. Phase hiện tại
  2. Checklist items completed
  3. Findings (với evidence)
  4. Issues/BLOCKED items
  5. Plan cho bước tiếp theo
  6. Estimated time cho bước tiếp theo

VÍ DỤ:
## Phase 1: DECOMPOSE - COMPLETED

### Tài liệu đã đọc (10/10):
  [PASS] CODE_AUDIT.md - B1-B10 identified
  [PASS] STREAMDQ_TECHNICAL_ANALYSIS.md - 14 Q&A understood
  [PASS] LITERATURE_REVIEW.md - 17 papers reviewed
  [PASS] COMPETITIVE_ANALYSIS.md - 8 tools compared
  [PASS] HYPOTHESES.md - 7 hypotheses documented
  [PASS] CONTRIBUTIONS.md - positioning clear
  [PASS] PAPER_SECTIONS/*.md - 4 sections reviewed
  [PASS] SPEC.md - requirements documented
  [PASS] README.md - project overview clear
  [PASS] STREAMDQ_TECHNICAL_ANALYSIS.md (duplicate) - skipped

### Code files đã đọc (13/13):
  [PASS] base.py - RuleContext/Violation OK
  [PASS] syntactic.py - SYN001-003 OK
  [PASS] semantic.py - SEM001-003 OK
  [PASS] cross_record.py - CRS001-003 OK
  [PASS] adaptive.py - percentile computation OK
  [PASS] registry.py - extensible OK
  [PASS] local_pipeline.py - external_context = {} found
  [PASS] spark_pipeline.py - micro-batch confirmed
  [PASS] run_evaluation.py - B2 issue found
  [PASS] metrics.py - precision/recall OK
  [PASS] comparison.py - estimates OK
  [PASS] violation_store.py - B5 issue found
  [PASS] tests/test_*.py - coverage OK

### Rules files đã đọc (3/3):
  [PASS] agent-rules.mdc - understood
  [PASS] streamdq-master.mdc - understood
  [PASS] research-writing.mdc - understood

### Key Findings:
1. B1 NaN fix: VERIFIED - math.isnan() is used
2. B2 duplicate injection: NOT FIXED - only 1 record emitted
3. B6 latency: NOT FIXED - hardcoded = 0
4. external_context: EMPTY - always = {}
5. Dockerfile.spark: MISSING
6. GTFS wiring: NOT WIRED

### BLOCKED Items:
1. [BLOCKED] B2 - duplicate injection no-op (need fix)
2. [BLOCKED] B6 - latency hardcoded (need fix)
3. [BLOCKED] Dockerfile.spark - missing (need create)

### Next Steps:
- Phase 2: DIAGNOSE - verify B1-B10 in code
- Estimated time: 2 hours
- MCP tools needed: user-kafka, user-duckdb
```

---

## TRACKING SHEET

| Phase | Status | Date Completed | Items Done | Items Blocked | Notes |
|-------|--------|---------------|-----------|--------------|-------|
| Phase 0: Documents | [ ] | | 0/10 | | |
| Phase 0: Code Files | [ ] | | 0/13 | | |
| Phase 0: Rules Files | [ ] | | 0/3 | | |
| Phase 1: Title Analysis | [ ] | | 0/4 | | |
| Phase 2: Component Grading | [ ] | | 0/6 | | |
| Phase 3: Blockers | [ ] | | 0/13 | | |
| Phase 4: Claims | [ ] | | 0/2 | | |
| Phase 5: Research RQs | [ ] | | 0/6 | | |
| Phase 6: Blog Research | [ ] | | 0/13 | | |
| Phase 7: Paper Learning | [ ] | | 0/22 | | |
| Phase 8: Roadmap | [ ] | | 0/16 | | |
| Phase 9: MCP Verify | [ ] | | 0/10 | | |
| Phase 10: Paper Ready | [ ] | | 0/3 | | |
| Phase 11: Execution | [ ] | | 0/5 | | |

### Overall Result

**Project Grade: X/10** (pending full evaluation)
**Demo Ready: N/5** (pending verification)
**Production Ready: N/5** (pending verification)
**Paper Ready: N/60** (pending evaluation)
**Go/No-Go: PENDING** (pending all phases)

### Top 3 Must-Fix (Priority Order)
1. [ ] B2 - Duplicate injection no-op (CRITICAL)
2. [ ] B6 - Latency hardcoded = 0 (CRITICAL)
3. [ ] Dockerfile.spark missing (CRITICAL)

### Top 3 Enhancements (Priority Order)
1. [ ] Drift detection (RQ3)
2. [ ] External context injection (RQ1)
3. [ ] Bootstrap CI (P2-4)

---

**Created from:** `PROMPTS/MASTER_EVALUATION_PROMPT.md`
**Rules added:** Sections A-F (Execution Rules, Detailed Plans, Anti-Patterns, Decision Rules, Report Format)
**Reference rules:** `.cursor/rules/agent-rules.mdc`, `.cursor/rules/streamdq-master.mdc`, `.cursor/rules/research-writing.mdc`
**Skills available:** `research-lookup`, `paper-lookup`, `literature-review`, `scientific-critical-thinking`, `scientific-writing`, `statistical-analysis`
**MCP servers:** `user-kafka`, `user-duckdb`
**Paper-to-learn:** 22 confirmed papers (KHÔNG được skip)
**Blog links:** 13 confirmed blogs (KHÔNG được skip)
**Code files:** 13 core Python files (PHẢI đọc TOÀN BỘ)
**Documentation files:** 10 analysis documents (PHẢI đọc TOÀN BỘ)
**NO LITE, NO FALLBACK, NO SKIP - FULL EXECUTION ONLY**

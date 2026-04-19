# FINAL FIX CHECKLIST — StreamDQ
**Date:** April 19, 2026
**Scope:** All remaining items affecting Context-Aware / Data Streaming / Data Quality
**Total:** 22 items

---

## Ngữ cảnh — Trạng thái hiện tại

### Đã implement + wire (chạy được)
- Tất cả 4 semantic rules dùng `external_context` (is_rush_hour, is_weekend, is_holiday, is_late_night)
- GTFS topic wired (`spark_pipeline.py:700-707`)
- Kafka violation producer wired (`spark_pipeline.py:472-486, 607-647`)
- Prometheus HTTP server wired (`spark_pipeline.py:488-496`)
- Distributed mode viết xong (`spark_pipeline.py:744-928`) — chưa test
- Adaptive threshold với linear interpolation (`adaptive.py:86-101`)
- CRS002 3-band severity (`cross_record.py:147-184` + `spark_pipeline.py:322-353`)

### Đã implement, CHƯA wire (không chạy được)
| Component | File | Dòng | Priority |
|-----------|------|-------|----------|
| AlertRouter (Slack/Email/Stdout) | `notification/alert_router.py` | 244 | P1 |
| ConceptDriftDetector (PSI-based) | `rules/drift.py` | 224 | P1 |
| DataContract + CertificationTier | `models/contract.py` | 201 | P1 |
| FitnessScoreRule (FIT001) | `rules/semantic.py:379` | — | P1 |
| CompletenessRule (SYN000) | `rules/syntactic.py:37` | — | P1 |

---

## CHECKLIST

### P0 — Crash / Không chạy được nếu không fix

- [ ] **[P0-1] Latency = 0 trong distributed mode**
  - **File:** `spark_pipeline.py:319, 352`
  - **Bug:** `latency_ms=(time.perf_counter() - 0) * 1000` hardcoded trong `_evaluate_vehicle_state_fn` và `_evaluate_dedup_state_fn`
  - **Fix:** Truyền `start_time` vào state functions từ `_process_batch`
  - **Impact:** Tất cả latency metrics trong distributed mode đều = 0
  - **Trụ cột:** Data Quality

- [ ] **[P0-2] `import psycopg2` crash**
  - **File:** `violation_store.py:45`
  - **Bug:** `import psycopg2` chạy ngay khi import module, không trong try/except → crash nếu PostgreSQL backend configured nhưng thư viện chưa cài
  - **Fix:** Wrap trong try/except bên trong `__init__`
  - **Impact:** Pipeline không start được với PostgreSQL backend
  - **Trụ cột:** Data Streaming

- [ ] **[P0-3] Port conflict Prometheus**
  - **File:** `spark_pipeline.py:463` — `metrics_port` default = 9090
  - **Bug:** 9090 là port Prometheus server trong docker-compose.yml, trùng với Spark metrics endpoint
  - **Fix:** Đổi default thành 9091
  - **Impact:** Metrics endpoint không expose được
  - **Trụ cột:** Data Streaming

---

### P1 — Đã implement, chưa wire

- [ ] **[P1-1] AlertRouter chưa được gọi trong pipeline**
  - **File:** `notification/alert_router.py` (viết rồi, 244 dòng)
  - **Bug:** 3 channels (Stdout/Slack/Email) đầy đủ nhưng không ai gọi `router.route(violation)` trong `_process_batch` hoặc `run_distributed`
  - **Fix:** Gọi `AlertRouter().route(violation)` sau khi violations được detect trong `_process_batch`
  - **Impact:** Violations phát hiện được nhưng không ai nhận notification
  - **Trụ cột:** Data Quality

- [ ] **[P1-2] ConceptDriftDetector chưa integrate**
  - **File:** `rules/drift.py` (viết rồi, 224 dòng) + `rules/adaptive.py`
  - **Bug:** PSI computation đầy đủ nhưng `adaptive.py` không gọi `detector.check_drift()`, threshold không bao giờ tự reset khi distribution shift
  - **Fix:** Integrate `ConceptDriftDetector` vào `AdaptiveThresholdEngine` — khi PSI > threshold thì gọi `threshold_engine.reset_field(field)` và log warning
  - **Impact:** Threshold adaptive bị "đóng băng" khi data distribution thay đổi
  - **Trụ cột:** Context-Aware

- [ ] **[P1-3] FIT001 chưa register**
  - **File:** `rules/semantic.py:379` — `FitnessScoreRule` đã viết
  - **Bug:** `build_default_registry()` trong `rules/registry.py:100` không register FIT001
  - **Fix:** Thêm `registry.register(FitnessScoreRule("FIT001"))` vào `build_default_registry()`
  - **Impact:** Fitness for purpose score không chạy
  - **Trụ cột:** Context-Aware

- [ ] **[P1-4] SYN000 chưa register**
  - **File:** `rules/syntactic.py:37` — `CompletenessRule` đã viết
  - **Bug:** `build_default_registry()` trong `rules/registry.py:100` không register SYN000
  - **Fix:** Thêm `registry.register(CompletenessRule("SYN000"))` vào `build_default_registry()`
  - **Impact:** Completeness check (tất cả required fields) không chạy
  - **Trụ cột:** Data Quality

- [ ] **[P1-5] DataContract chưa integrate**
  - **File:** `models/contract.py` (viết rồi, 201 dòng)
  - **Bug:** `DataContract` + `CertificationTier` đầy đủ nhưng pipeline không gọi `contract.evaluate()`
  - **Fix:** Gọi `contract.evaluate()` sau mỗi batch trong `_process_batch`; log tier achievement; pass violations_by_rule dict
  - **Impact:** "Context-aware" claim không có cơ sở thực thi; certification tier không áp dụng
  - **Trụ cột:** Context-Aware

---

### P2 — Cần verify / chạy thực tế

- [ ] **[P2-1] Distributed mode chưa test**
  - **File:** `spark_pipeline.py:744-928` — `run_distributed()` (viết rồi)
  - **Action:** Chạy `run_distributed()` với Spark cluster thực; test `applyInPandasWithState` với CRS001/CRS002/CRS003
  - **Risk:** `applyInPandasWithState` cần Spark 3.5+; Lambda UDF trong state function có thể lỗi
  - **Impact:** Không biết distributed CRS state có hoạt động không
  - **Trụ cột:** Data Streaming

- [ ] **[P2-2] Kafka violation sink chưa verify**
  - **File:** `spark_pipeline.py:607-647` — Kafka violation producer đã wired
  - **Action:** Kiểm tra Kafka topic `quality-violations` bằng Kafka consumer; confirm messages đến
  - **Risk:** `sendbatch` API có thể không tồn tại trong phiên bản kafka-python cũ; fallback có thể chậm
  - **Impact:** Violations không đến được Kafka consumer
  - **Trụ cột:** Data Streaming

- [ ] **[P2-3] GTFS CRS002 3-band chưa test**
  - **File:** `cross_record.py:147-184` + `spark_pipeline.py:322-353`
  - **Action:** Inject GTFS test events với speed = 0.5, 10, 25 km/h + position jump 200m; verify 3 bands CRITICAL/HIGH/MEDIUM fire đúng
  - **Risk:** Logic mới chưa từng test; 3-band separation có thể overlap
  - **Impact:** Không verify được GPS spoofing detection ở 3 bands
  - **Trụ cột:** Data Quality

- [ ] **[P2-4] Prometheus metrics chưa verify**
  - **File:** `spark_pipeline.py:488-496` — Prometheus HTTP server đã start
  - **Action:** `curl http://localhost:9091/metrics | grep "^streamdq"`; confirm Grafana dashboard nhận data
  - **Risk:** Port 9091 có thể vẫn conflict; Grafana scrape config có thể chưa đúng
  - **Impact:** Grafana dashboards trống
  - **Trụ cột:** Data Streaming

- [ ] **[P2-5] GTFS topic wiring chưa verify**
  - **File:** `spark_pipeline.py:700-707` — `run()` subscribe cả `nyc-taxi-events` và `gtfs_topic`
  - **Action:** Chạy GTFS producer; confirm CRS001/CRS002 violations xuất hiện trong SQLite
  - **Risk:** GTFS JSON parsing trong `run_distributed()` (`get_json_object`) có thể fail nếu schema không match
  - **Impact:** CRS001/CRS002 inactive cho GTFS data
  - **Trụ cột:** Data Quality

---

### P3 — Unit tests còn thiếu

- [ ] **[P3-1] Thiếu test NaN input**
  - **File:** `tests/test_syntactic_rules.py`
  - **Action:** Thêm test case `test_nan_fare_raises_violation()` — input `fare_amount=float('nan')`, assert violation fired
  - **Trụ cột:** Data Quality

- [ ] **[P3-2] Thiếu test FIT001**
  - **File:** `tests/` — tạo `test_fitness_rule.py`
  - **Action:** Test FitnessScoreRule với valid event (score=1.0 → no violation), missing field (score < 0.5 → violation), partial field (score 0.5-0.99 → no violation)
  - **Trụ cột:** Context-Aware

- [ ] **[P3-3] Thiếu test AlertRouter**
  - **File:** `tests/` — tạo `test_alert_router.py`
  - **Action:** Test 3 channels (Stdout → capture stdout, Slack → mock HTTP, Email → mock SMTP); test severity threshold; test batch routing
  - **Trụ cột:** Data Quality

- [ ] **[P3-4] Thiếu test ConceptDriftDetector**
  - **File:** `tests/` — tạo `test_drift_detector.py`
  - **Action:** Test PSI computation với known distributions; test threshold boundaries (PSI < 0.1, 0.1-0.2, >= 0.2); test no-drift case
  - **Trụ cột:** Context-Aware

- [ ] **[P3-5] Thiếu test DataContract**
  - **File:** `tests/` — tạo `test_data_contract.py`
  - **Action:** Test `CertificationTier.BRONZE/SILVER/GOLD` evaluation; test `tier_met` logic; test `missing_rules` detection; test empty dataset edge case
  - **Trụ cột:** Context-Aware

---

### P4 — Docs & Polish

- [ ] **[P4-1] README benchmark numbers chưa update**
  - **File:** `README.md:132-168`
  - **Action:** Update precision/recall/latency numbers từ DuckDB verification (precision=22.9% SYN001) hoặc chạy lại benchmark để có số mới; ghi rõ "estimated" vs "measured"
  - **Impact:** Claim về Data Quality không đúng với thực tế
  - **Trụ cột:** Data Quality

- [x] **[P4-2] LESSION_FROM_BLOG.md rename** ✅ DONE
  - **File:** `LESSON_FROM_BLOG.md` (renamed successfully)
  - **Impact:** Typo gây khó tìm file

- [ ] **[P4-3] SPEC.md benchmark targets cần update**
  - **File:** `SPEC.md:105-116` — success thresholds (recall >80%, precision >85%) không reflect actual results
  - **Action:** Update targets dựa trên DuckDB verification; thêm "measured vs target" distinction
  - **Impact:** Specification không reflect reality

---

## Tổng hợp theo Trụ cột

### Context-Aware (6 items)
| Priority | Item | File | Fix |
|----------|------|------|-----|
| P1 | ConceptDriftDetector chưa integrate | `rules/drift.py` + `adaptive.py` | Wire PSI check vào adaptive engine |
| P1 | DataContract chưa integrate | `models/contract.py` | Gọi `evaluate()` sau mỗi batch |
| P1 | FIT001 chưa register | `rules/semantic.py` | Thêm vào `build_default_registry()` |
| P2 | GTFS topic wiring chưa verify | `spark_pipeline.py` | Chạy GTFS producer, check violations |
| P3 | Thiếu test FIT001 | `tests/test_fitness_rule.py` | Unit test FitnessScoreRule |
| P3 | Thiếu test DataContract | `tests/test_data_contract.py` | Unit test CertificationTier |
| P3 | Thiếu test ConceptDriftDetector | `tests/test_drift_detector.py` | Unit test PSI computation |

### Data Streaming (5 items)
| Priority | Item | File | Fix |
|----------|------|------|-----|
| P0 | `import psycopg2` crash | `violation_store.py:45` | Wrap trong try/except |
| P0 | Port conflict Prometheus | `spark_pipeline.py:463` | Đổi default 9090 → 9091 |
| P2 | Distributed mode chưa test | `spark_pipeline.py:744` | Chạy `run_distributed()` thực tế |
| P2 | Kafka violation sink chưa verify | `spark_pipeline.py:607` | Confirm messages đến Kafka |
| P2 | Prometheus metrics chưa verify | `spark_pipeline.py:488` | `curl` endpoint + Grafana check |

### Data Quality (8 items)
| Priority | Item | File | Fix |
|----------|------|------|-----|
| P0 | Latency = 0 distributed | `spark_pipeline.py:319,352` | Truyền `start_time` vào state fns |
| P1 | AlertRouter chưa wire | `notification/alert_router.py` | Gọi `route()` sau violations |
| P1 | SYN000 chưa register | `rules/syntactic.py` | Thêm vào `build_default_registry()` |
| P2 | GTFS CRS002 3-band chưa test | `cross_record.py:147` | Unit test 3 bands |
| P3 | Thiếu test NaN | `tests/test_syntactic_rules.py` | Test `float('nan')` input |
| P3 | Thiếu test AlertRouter | `tests/test_alert_router.py` | Unit test 3 channels |
| P4 | README benchmark chưa update | `README.md:132` | Update numbers từ DuckDB |
| P4 | SPEC targets chưa update | `SPEC.md:105` | Realistic targets |

---

## Thứ tự ưu tiên khuyến nghị

```
1. P0-2 (psycopg2 crash)     — 5 phút, ngăn crash
2. P0-3 (port conflict)       — 1 phút, enable metrics
3. P0-1 (latency=0)           — 15 phút, fix latency
4. P1-4 (SYN000 register)     — 2 phút, completeness chạy
5. P1-3 (FIT001 register)      — 2 phút, fitness chạy
6. P1-2 (DriftDetector)       — 30 phút, wire drift detection
7. P1-5 (DataContract)        — 20 phút, wire certification
8. P1-1 (AlertRouter)         — 20 phút, wire notifications
9. P3 (tests)                  — 2-3 giờ, viết unit tests
10. P2 (verify)               — 2-3 giờ, integration tests
11. P4 (docs)                 — 1 giờ, update docs
```

---

*Tạo ngày: April 19, 2026*
*Nguồn: Code audit (10 bugs), DuckDB verification (32,056 violations), LESSON_FROM_BLOG.md (22 papers + 13 blogs)*

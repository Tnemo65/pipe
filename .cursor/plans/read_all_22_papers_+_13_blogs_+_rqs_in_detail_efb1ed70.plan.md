---
name: Read all 22 papers + 13 blogs + RQs in detail (size-ordered)
overview: "Deep-read all 22 academic papers (ordered by file size: small first) and 13 engineering blogs one by one, use research skills for RQs, extract actionable lessons for StreamDQ, save to LESSON_FROM_BLOG.md"
todos:
  - id: p-1
    content: ""
    status: completed
  - id: p-2
    content: ""
    status: cancelled
  - id: p-3
    content: ""
    status: cancelled
  - id: p-4
    content: ""
    status: cancelled
  - id: p-blog
    content: ""
    status: completed
  - id: p-rq
    content: ""
    status: completed
  - id: p-syn
    content: ""
    status: completed
isProject: false
---

# Plan: Deep-Read All Papers + Blogs + RQs (size-ordered)

## Mục tiêu

Doc chi tiết từng paper và blog một cách không bỏ sót, trích xuất những lesson có ích thực tế cho việc nâng cấp StreamDQ, lưu kết quả vào `LESSON_FROM_BLOG.md`. **Ưu tiên đọc file nhỏ trước, file to để sau.**

## Architecture

```
streamdq/rules/dsl.py (NEW)
streamdq/rules/syntactic.py (SYN000 — Completeness)
streamdq/rules/semantic.py (FIT001 — Fitness Score)
streamdq/rules/drift.py (NEW — ConceptDriftDetector)
streamdq/models/contract.py (NEW — DataContract)
streamdq/pipeline/spark_pipeline.py (external_context population)
streamdq/pipeline/local_pipeline.py (external_context population)
```

## Chiến lược đọc

### Papers: Chunked reading (size-aware)

- Mỗi paper chia thành 3-4 chunks (500-1000 dòng/chunk)
- Chunk 1: Abstract + Introduction (hiểu research question)
- Chunk 2: Methodology (hiểu approach)
- Chunk 3: Results + Evaluation (hiểu numbers/claims)
- Chunk 4: Limitations + Conclusions (hiểu gaps)
- Sau mỗi chunk: ghi ngay lesson vào temp file
- Tier A (< 1.5 MB): đọc full 1 lần, ít chunks
- Tier E (> 10 MB): chunk rất nhỏ (300 dòng/chunk), nhiều chunks hơn
- Tránh overflow bằng cách chunk nhỏ

### Blogs: Toàn bộ bằng WebFetch

- Mỗi blog đọc full content, ghi lesson ngay

### RQs: Dùng skills

- RQ1, RQ2, RQ3 dùng literature-review + research-lookup
- RQ4, RQ5, RQ6 dùng scientific-critical-thinking

## Execution: 7 phases

### Phase 1: Tier A + Tier B (11 papers nhỏ nhất, 2 agents song song)

Thứ tự ưu tiên theo kích thước:


| Subagent  | Papers                                                                  | Size            |
| --------- | ----------------------------------------------------------------------- | --------------- |
| Agent-P1A | 01-05 (TaDA, TSP_CMES, 3603707, 2204.10655, + 1-s2.0-S0020025526004196) | 585 KB - 1.9 MB |
| Agent-P1B | 06-11 (6 papers Tier B còn lại)                                         | 1.9 MB - 3.4 MB |


**Tier A — Nhỏ nhất (< 1.5 MB):**

1. `paper-to-learn/TaDA.13.pdf` — **585 KB** (TaDA 2013 — temporal aggregation)
2. `paper-to-learn/TSP_CMES_62902.pdf` — **909 KB** (CMES 2025 — BIG-ABAC)
3. `paper-to-learn/3603707.pdf` — **1.4 MB** (ACM JDIQ 2023 — Fadlallah scoping review)
4. `paper-to-learn/2204.10655v1.pdf` — **1.8 MB** (ACM 2022 — Serra context-aware DQ SLR)

**Tier B — Nhỏ (1.5–3.4 MB):**

1. `paper-to-learn/1-s2.0-S0020025526004196-main.pdf` — 1.9 MB (Expert Sys 2026 — high avg-efficiency itemset)
2. `paper-to-learn/1-s2.0-S0957417425034979-main.pdf` — 2.0 MB (Pattern Rec 2025 — stream processing frameworks)
3. `paper-to-learn/1-s2.0-S0031320325011793-main.pdf` — 2.0 MB (Expert Sys 2025 — deep learning for streaming)
4. `paper-to-learn/1-s2.0-S0167739X26001548-main.pdf` — 2.6 MB (Future Gen 2026 — stream partitioning)
5. `paper-to-learn/1-s2.0-S1110016826001225-main.pdf` — 2.5 MB (Knowl-Based Sys 2026 — temporal DQ assessment)
6. `paper-to-learn/1-s2.0-S095070512501768X-main.pdf` — 3.2 MB (Knowl-Based Sys 2026 — credit card fraud iTA-LRN)
7. `paper-to-learn/1-s2.0-S0019057825005129-main.pdf` — 3.4 MB (ISA Trans 2026 — adaptive soft sensing)

### Phase 2: Tier C (4 papers trung bình, 1 agent)


| Subagent  | Papers                  | Size            |
| --------- | ----------------------- | --------------- |
| Agent-P2A | 12-15 (4 papers Tier C) | 3.4 MB - 4.4 MB |


1. `paper-to-learn/1-s2.0-S1568494625007537-main.pdf` — 3.9 MB (Appl Soft Comp 2025 — STM-Stream short-term memory)
2. `paper-to-learn/1-s2.0-S0925231226009033-main.pdf` — 3.6 MB (Neural Comp 2025 — deep learning streaming)
3. `paper-to-learn/1-s2.0-S0360835225006540-main.pdf` — 4.2 MB (Comp Ind Eng 2025 — periodic pattern mining)
4. `paper-to-learn/1-s2.0-S0957417425040059-main.pdf` — 4.4 MB (Expert Sys 2025 — HAEIM stream)

### Phase 3: Tier D (3 papers lớn, 1 agent, chunk nhiều hơn)


| Subagent  | Papers                  | Size            |
| --------- | ----------------------- | --------------- |
| Agent-P3A | 16-18 (3 papers Tier D) | 3.4 MB - 7.0 MB |


1. `paper-to-learn/1-s2.0-S0167947325002142-main.pdf` — 3.4 MB (Knowl-Based Sys 2025 — STM-Stream clustering)
2. `paper-to-learn/FutureGeneration.pdf` — 6.7 MB (Future Gen 2026 — stream partitioning, duplicate)
3. `paper-to-learn/1-s2.0-S0925231225028619-main.pdf` — 7.0 MB (Eng App AI 2025 — IoT DL)

**Pending (file chưa có — đọc sau khi upload):**

- `paper-to-learn/1-s2.0-S0167739X17329151-main.pdf` — 6.8 MB — Knowl-Based Sys 2017 — context-aware DQ SLR

### Phase 4: Tier E (3 papers rất lớn, 1 agent, chunk rất nhỏ 300 dòng)


| Subagent  | Papers                  | Size              |
| --------- | ----------------------- | ----------------- |
| Agent-P4A | 19-21 (3 papers Tier E) | 12.6 MB - 33.4 MB |


1. `paper-to-learn/1-s2.0-S095219762600792X-main.pdf` — 12.6 MB (Knowl-Based Sys 2026 — drift detection survey)
2. `paper-to-learn/1-s2.0-S0950705125012894-main.pdf` — 17.1 MB (Knowl-Based Sys 2025 — temporal DQ assessment)
3. `paper-to-learn/1-s2.0-S0957417426008262-main.pdf` — 33.4 MB (Info Sci 2026 — frequent weighted patterns)

**Note:** Paper 21 (33.4 MB) có thể cần đọc theo chunks rất nhỏ (200 dòng/chunk) để tránh overflow.

### Phase 5: Blogs 01-13 (2 agents song song)


| Subagent  | Blogs       |
| --------- | ----------- |
| Agent-P5A | Blogs 01-07 |
| Agent-P5B | Blogs 08-13 |


**Blogs 01-07:**

1. `engineering.grab.com/data-observability` — monitoring at scale
2. `engineering.grab.com/rethinking-streaming-processing-data-exploration` — SQL-first
3. `engineering.grab.com/signals-market-place` — data mesh certification
4. `engineering.grab.com/data-first-sla-always` — fault tolerance
5. `www.infoq.com/news/2025/12/grab-kafka-data-quality/` — Kafka DQ
6. `engineering.grab.com/real-time-data-quality-monitoring` — stream contracts
7. `www.alibabacloud.com/blog/...grab-journey-with-apache-flink...` — Flink migration

**Blogs 08-13:**
8. `engineering.grab.com/real-time-data-ingestion` — CDC ingestion
9. `engineering.grab.com/rethinking-streaming-processing-data-exploration` (dup)
10. `tinybird.co/blog/real-time-streaming-data-architectures-that-scale` — Tinybird
11. `ibm.com/think/topics/data-quality` — IBM 7 dimensions
12. `precisely.com/data-quality/big-data-quality-mastering...` — Precisely 5-step
13. `dl.acm.org/doi/epdf/10.1145/3686592.3686609` — ACM Grab (403, dùng WebSearch)

### Phase 6: RQs (6 RQs với skills)

- RQ1: literature-review skill "context-aware data quality streaming"
- RQ2: paper-lookup skill cho Stream DaQ (arXiv:2506.06147)
- RQ3: literature-review skill "adaptive threshold streaming data quality"
- RQ4: scientific-critical-thinking skill on CODE_AUDIT.md
- RQ5: literature-review skill "DQ fitness for purpose metrics"
- RQ6: scientific-critical-thinking skill IBM vs StreamDQ taxonomy

### Phase 7: Tổng hợp (main agent)

Đọc tất cả temp files, tổng hợp vào `LESSON_FROM_BLOG.md` cuối cùng.

**Format mỗi paper:**

```markdown
## [N] [TITLE]
- **Citation:** [Authors], [Year]. "[Title]." [Venue].
- **Research Question:** [1 sentence]
- **Key Findings:** [5+ bullets với specific numbers]
- **Limitations:** [2-3 sentences]
- **Actionable Lessons for StreamDQ:**
  1. [Specific lesson with code example or design pattern]
  2. [Specific lesson]
  3. [Specific lesson]
- **Code Changes (if any):** [file:line reference hoặc "new file"]
- **Can cite as:** [Full citation for bibliography]
```

**Format mỗi blog:**

```markdown
## [N] [BLOG TITLE]
- **Source:** [URL]
- **Framework:** [2-3 sentences]
- **Key Lessons for StreamDQ:**
  1. [Specific lesson với actionable next step]
  2. [Specific lesson]
- **Better than StreamDQ:** [bullets]
- **StreamDQ Better:** [bullets]
```

## Output file: `LESSON_FROM_BLOG.md` (TIẾNG VIỆT)

## Scope: 21 papers (1 pending) + 13 blogs + 6 RQs

## Anti-overflow strategy

- Mỗi subagent chỉ đọc 4-6 papers hoặc 7 blogs
- Sau mỗi chunk (500 dòng, Tier A-B; 300 dòng Tier C-D; 200 dòng Tier E): ghi findings tạm vào chunk file riêng
- Tránh đọc quá nhiều trong 1 context
- Subagent bị overflow → resume với chỉ chunk tiếp theo

## Estimated time


| Phase     | Task                         | Subagents       |
| --------- | ---------------------------- | --------------- |
| 1         | Tier A + Tier B (11 papers)  | 2 parallel      |
| 2         | Tier C (4 papers)            | 1               |
| 3         | Tier D (3 papers)            | 1               |
| 4         | Tier E (3 very large papers) | 1               |
| 5         | Blogs 01-13                  | 2 parallel      |
| 6         | RQs (6 RQs)                  | 1               |
| 7         | Synthesize final             | 1               |
| **Total** |                              | **9 subagents** |



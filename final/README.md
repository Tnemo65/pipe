# StreamDQ — Final Research Document

**Project**: "A Context-Aware Framework for Streaming Data Quality Monitoring"
**Domain**: Transportation — GPS Trajectory + GTFS Realtime
**Phase**: Phase 0 — Idea Verification (COMPLETE)
**Generated**: 2026-04-22

---

## Folder Structure

```
final/
  README.md                          -- This file
  00_IDEA_VERIFICATION/
    report.md                        -- Phase 0: full idea verification report
  gap_analysis.md                    -- 12-gap analysis from literature research
  AUDITS/                           -- Research audit reports
    audit_streaming_dq_frameworks.md   -- General streaming DQ landscape (19 frameworks)
    audit_transportation_dq_literature.md -- Transportation-specific DQ literature
    audit_transportation_datasets.md     -- Dataset analysis (NYC TLC, GTFS Malaysia)
```

---

## What's Here

### Phase 0 Output (Idea Verification — COMPLETE)

**Verdict**: MODIFY AND PROCEED

The idea is feasible for a **B+ to A- paper**. The contribution (streaming + domain-specific GPS trajectory rules for transportation) is genuine and verified. Three critical actions are required before proceeding.

- `00_IDEA_VERIFICATION/report.md` — Full report: literature landscape, gap analysis, 5-criteria assessment, proposed framework, 4 research questions, feasibility, peer review
- `gap_analysis.md` — 12 gaps identified and structured with evidence
- `AUDITS/` — Supporting research from 3 parallel literature searches

### What Was Deleted

- `CONFLICT_RESOLUTION.md` — Old file, resolved conflicts between non-existent `finalsystem/` and `finalsystem2/`
- `AUDITS/audit_*.md` (5 files) — Old audits referencing `finalsystem/`, replaced by new research
- `08_DRAFTS/` — Empty placeholder skeletons (23-33 lines), replaced by real drafts when Phase 1 begins

---

## Research Summary

### Key Finding

No existing framework combines streaming architecture with domain-specific GPS/trajectory validation rules for transportation. This is the central verified gap (GAP-I1, severity: CRITICAL).

### Literature Survey

- **19 frameworks** surveyed across 3 categories: stream-native (Stream DaQ, Grab Coban, METER), batch-approximation (Deequ VLDB 2018, GE, Soda, dbt, AutoDQM), observability (Monte Carlo, Metaplane)
- **Transportation DQ**: GTFS Validator (MobilityData), GTFS-rt Validator (CUTR-USF) are batch-only; Wong (2025) documents 30% GTFS-RT error rate
- **GPS trajectory AD**: CETrajAD (SDM 2025), TAPS, NUMOSIM (SIGSPATIAL 2024) — related but distinct task (anomaly detection, not data quality validation)
- **Key reference**: Martin et al. (PVLDB 2025) — 95%+ false positive rate for DC auto-discovery. Validates that hand-crafted rules (like StreamDQ's SYN/SEM/CRS taxonomy) are more reliable than automated discovery.

### Datasets

| Dataset | Accessibility | Academic Precedent | Status |
|---------|--------------|-------------------|--------|
| NYC TLC Yellow Taxi | Public, Parquet | Q3+ (VLDB, SIGMOD, KDD) | Ready |
| GTFS Malaysia | CC BY 4.0, api.data.gov.my | None (novel use) | CRS verification needed |

---

## Proposed Framework

**StreamDQ-Transport**: Streaming DQ monitoring for transportation with:
- Three-layer rule taxonomy: SYN (syntactic) + SEM (semantic) + CRS (cross-record)
- Domain-specific GPS rules: Haversine speed bounds, GPS jump detection, duplicate detection
- Hierarchical context-aware thresholds (3D: temporal + spatial + operational)
- Datasets: NYC TLC + GTFS Malaysia

### Research Questions

| RQ | Question | Gap | Key Metric |
|----|----------|-----|------------|
| RQ1 | Does context-aware beat static thresholds? | GAP-G2 | Precision with 95% CI |
| RQ2 | How does fallback quality degrade with sparse contexts? | GAP-G2 | F1 degradation curve |
| RQ3 | Do GPS rules transfer taxi -> GTFS transit? | GAP-I1 | Detection rate |
| RQ4 | Does three-layer taxonomy beat SYN-only? | GAP-I2 | Incremental F1 per layer |

---

## 3 CRITICAL Actions Before Phase 1

| # | Action | Why |
|---|--------|-----|
| **1** | DELETE all fabricated claims from every document | "94.2%", "13x GE", "91.8%", "245K events/sec" are fabricated. Academic fraud if published. |
| **2** | BUILD evaluation module (`streamdq/evaluation/`) | Every thesis metric depends on this. Currently missing. |
| **3** | RESOLVE CRS002 scope honestly | CRS001/CRS002 only run on GTFS, NOT on NYC TLC. Main dataset gets zero cross-record GPS validation. |

---

## Grade Projection

**B+ to A-** (conference/workshop). Achieievable if:
- Context-aware precision shows significant improvement over static
- Evaluation module is built and ablation study is run
- GTFS GPS validation is demonstrated on real errors
- All fabricated claims are purged

**B** if: marginal improvement, incomplete evaluation, unresolved CRS scope.

---

## Skill Usage Tracker

| Skill | Used For |
|-------|----------|
| @.cursor/skills/01-academic-writing | Contribution framing, peer review simulation |
| @.cursor/skills/02-literature-research | General streaming DQ, transportation DQ, datasets |
| @.cursor/skills/03-data-statistics | Evaluation design, bootstrap CI methodology |
| @.cursor/skills/04-data-engineering | Technical feasibility, architecture assessment |
| @.cursor/skills/05-research-analysis | Gap identification, idea verification, threat analysis |
| @.cursor/skills/06-infrastructure-devops | Reproducibility, tech stack evaluation |

---

## Next Phase

**Phase 1**: Implementation — Build `streamdq/evaluation/` module, fix bugs, run benchmarks.

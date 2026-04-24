# Final Project Index — A Context-Aware Framework for Streaming Data Quality Monitoring

**Project**: A Context-Aware Framework for Streaming Data Quality Monitoring
**Step**: Step 14 — Final Index
**Date**: April 24, 2026

---

## Directory Structure

```
final/
├── README.md                          # This file — master index
│
├── 00_IDEA_VERIFICATION/             # Step 1: Problem framing
│   ├── gap_analysis.md
│   └── report.md
│
├── 01_LITERATURE_REVIEW/            # Step 2: Literature review
│   ├── AUDITS/
│   │   ├── audit_streaming_dq_frameworks.md
│   │   ├── audit_transportation_datasets.md
│   │   └── audit_transportation_dq_literature.md
│   └── ...
│
├── 02_IDEA_BRAINSTORM/             # Step 3: Gap identification
│   ├── AGENT_TRANSCRIPTS/
│   │   ├── agent01_REVIEWER.md
│   │   ├── agent02_SCORER.md
│   │   ├── agent03_REFINE.md
│   │   ├── agent04_VALIDATOR.md
│   │   ├── agent05_THREAT.md
│   │   ├── agent06_DATA_CHECK.md
│   │   ├── agent07_TIMELINE.md
│   │   └── agent08_SKEPTIC.md
│   └── report.md
│
├── 03_IDEA_SELECTION/               # Steps 4-6: Research questions, methods, selection
│   ├── AGENT_TRANSCRIPTS/
│   │   ├── agent01_ARCHITECT.md
│   │   ├── agent02_LIT_REV.md
│   │   ├── agent03_ENG_FEAS.md
│   │   ├── agent04_SCIENTIFIC.md
│   │   ├── agent05_SKEPTIC.md
│   │   ├── agent06_VALIDATOR.md
│   │   └── agent07_SYNTHESIZER.md
│   └── report.md
│
├── 04_NOVELTY_CONTRIBUTION/         # Steps 7 & 10: Contribution + Novelty
│   ├── COMPETITIVE_TABLE.md         # Comparison: StreamDQ vs GE, Soda, Stream DaQ, etc.
│   ├── CONTRIBUTIONS.md              # 6 contributions (C1-C4, ML, Limitations)
│   ├── ML_INTEGRATION_REDESIGN.md   # Phase 3 ML architecture
│   ├── ML_POSITIONING.md            # ML strategy and priorities
│   ├── NOVELTY_SCORES.md            # Novelty scoring table
│   └── SIGNIFICANCE_TABLE.md        # Significance of each contribution
│
├── 05_ALGORITHM_DESIGN/             # Steps 8-9: Algorithm design + evaluation plan
│   ├── COMPLEXITY_ANALYSIS.md       # O(1) analysis, state management
│   ├── DATA_STRUCTURES.md           # Flink state design
│   ├── FAILURE_MODES.md             # Scientific critical thinking
│   ├── FORMULATION.md               # Mathematical formulation + pseudocode
│   ├── HYPOTHESES.md                # RQ1-RQ6 + H1-H5
│   ├── ML_MODEL_ANALYSIS.md        # ML feasibility analysis
│   ├── ML_PRODUCTION_DEPLOYMENT.md  # ML deployment strategy
│   ├── ML_THRESHOLD_CALIBRATION_ANALYSIS.md
│   ├── QUALITY_AUDIT.md            # Code review quality audit (36 issues)
│   └── STATISTICAL_PLAN.md         # Evaluation methodology + CI strategy
│
├── 06_PAPER_OUTLINE/               # Step 11: Paper thesis outline
│   ├── thesis_outline.md           # IMRAD × VNU-UET template mapping
│   ├── figure_specifications.md     # F1-F10 specifications (Excalidraw + matplotlib)
│   ├── table_specifications.md     # T1-T10 specifications (LaTeX)
│   ├── writing_assignments.md       # 6 assignments, word counts, dependencies
│   ├── abbreviations.md             # 50+ acronyms, LaTeX \acro{} entries
│   └── DEBATE/                     # Step 11B: Adversarial debate (5 agents, 3 rounds)
│       ├── agent1_systems_reviewer.md
│       ├── agent2_transportation_reviewer.md
│       ├── agent3_statistics_reviewer.md
│       ├── agent4_structure_critic.md
│       ├── agent5_gap_hunter.md
│       └── report.md               # Synthesized debate report + refined outline changes
│
├── 07_IMPLEMENTATION_ROADMAP/      # Step 12: Implementation plan
│   ├── implementation_roadmap.md    # Gantt, 14 weeks, 12 milestones, risk register
│   ├── template_chapters_mapping.md # Map thesis_outline → LaTeX .tex files
│   └── reproducibility_checklist.md  # Environment, data, CLI, JSON schema
│
├── 08_ADVISOR_FEEDBACK/            # Step 13: Peer review simulation
│   ├── feedback_triage.md           # 17 weaknesses (3 CRITICAL, 7 MAJOR, 7 MINOR)
│   ├── rebuttal_drafts.md           # 11 rebuttal templates for reviewer objections
│   ├── revision_plan.md            # P0/P1/P2/P3 action items, 14-week order
│   └── consistency_check.md        # 24 consistency rules + verification commands
│
└── 09_FINALIZATION/                # Step 14: Final quality gate
    ├── final_paper_review.md       # PC-style scores (overall: 3/5, Borderline Accept)
    ├── consistency_report.md        # Claims vs. evidence, Tier 1/2/3 classification
    └── submission_readiness.md      # Pre-submission checklist + red flag scan
```

---

## Key Facts

### Project Identity

- **Name**: A Context-Aware Framework for Streaming Data Quality Monitoring
- **Short name**: StreamDQ
- **NOT**: batch, ML-only, production-ready
- **IS**: research & education platform, Flink-native

### Datasets

- NYC TLC Yellow Taxi: parquet replay via Kafka
- NYC MTA Bus GTFS-realtime: live public feed

### Rules (10 total)

| Layer | Rules | Dataset |
|-------|-------|---------|
| SYN | SYN001, SYN002, SYN003 | Both |
| SEM | SEM001, SEM002, SEM003, GTFSSem002 | NYC TLC + MTA Bus |
| CRS | CRS001, CRS002, CRS003 (Java) | NYC MTA Bus only |

### CRS Bounds

- CRS001: [0.5, 100] km/h (Haversine speed, 60s sustained-violation requirement)
- CRS002: >400m/30s (Haversine jump)
- CRS003: SHA256 hash, 300s window, 310s TTL

### ML Phase 3

| Priority | Model | Status |
|:--------:|-------|--------|
| 1 | Bayesian Optimization | GO — calibrates k_multiplier |
| 2 | Isolation Forest | Conditional — ρ < 0.8 |
| 3 | XGBoost | Conditional — training target undefined |
| 4 | LSTM | NO-GO — GPS data unconfirmed + HIGH redundancy |

### Known Blockers

| ID | Blocker | Impact |
|----|---------|--------|
| NG-4 | CRS003 replay suppression gate | CRS003 = Tier 3 UNMEASURABLE |
| B3 | CRS001 2–20 km/h gap | Moderate spoofing missed |
| I16 | D4 External context stub | Incomplete 5D |

### Tier Classification

| Tier | Meaning | Requirement |
|------|---------|-------------|
| Tier 1 | Verified (code inspection, prior work) | Can claim with citation |
| Tier 2 | Estimated (needs benchmark) | Must label [TIER-2 ESTIMATED] |
| Tier 3 | Unmeasurable (known blocker) | Must label [TIER-3 UNMEASURABLE] |

---

## Step 11B Debate — Key Changes Applied

5 agents (Systems, Transportation, Statistics, Structure, Gap) reviewed thesis_outline.md. 14 fixes applied:

### P0 — CRITICAL (all applied)
| # | Fix | Location |
|---|-----|---------|
| P0.1 | CRS001: < 0.5 km/h AND Δt > 60s (not < 2 km/h) | FORMULATION.md, thesis_outline.md |
| P0.2 | Dataset-role table: CRS → NYC MTA Bus only | thesis_outline.md §2.3 |
| P0.3 | McNemar → Wilcoxon signed-rank for per-event detection | thesis_outline.md §3.3 |
| P0.4 | Holm-Bonferroni within RQ families (α_adj=0.0083) | thesis_outline.md §3.3 |
| P0.5 | Bootstrap 10,000 iterations (BCa for latency) | thesis_outline.md §3.3 |
| P0.6 | RQ2 redefined: L4↔L0 TQS correlation (Pearson ρ > 0.5) | thesis_outline.md §I.2 |
| P0.7 | C1: "to the best of our knowledge" + "surveyed" qualifier | thesis_outline.md §I.3 |

### P1 — MAJOR (all applied)
| # | Fix | Location |
|---|-----|---------|
| P1.1 | GPS error model discussion added to §2.3 | thesis_outline.md |
| P1.4 | 5D → 4D + D4 future work | thesis_outline.md §1.3 |

### Score: Borderline → Weak Accept (VNU-UET thesis standard)

---

## Citation Accuracy

Verify before submission:

| Paper | Correct | Common Errors |
|-------|---------|--------------|
| T-Assess | VLDB 2025, Vol.18, No.3, pp.666-674 | arXiv, 2024 |
| METER | VLDB 2024, doi:10.14778/3636218.3636233 | 2023, wrong DOI |
| CETrajAD | SDM 2025, Cao & Akoglu | Liu as author |
| Martin et al. | PVLDB 2025, doi:10.14778/3748191.3748209 | wrong year, wrong DOI |
| Stream DaQ | Pathway (Python), NOT Flink | Flink as engine |
| Exathlon | VLDB 2021 | — |

---

## Verification Commands

```bash
# Phase 3 mandatory?
grep -rn "Phase 3 optional" final/ --include="*.md"

# CRS001 upper bound = 100 km/h?
grep -rn "120.*km.*h" final/ --include="*.md" | grep -i "crs001\|speed.*bound"

# CRS003 Tier 3 labeled?
grep -rn "CRS003.*UNMEASURABLE\|Tier 3.*CRS003" final/ --include="*.md"

# ML priorities consistent?
grep -rn "Priority 1\|Priority 2\|Priority 3\|Priority 4" final/05_ALGORITHM_DESIGN/*.md

# All documents consistent?
cd final && for f in *.md **/*.md; do echo "=== $f ==="; done
```

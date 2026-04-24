# Systems Review: "A Context-Aware Framework for Streaming Data Quality Monitoring"

**Reviewer Role**: Senior VLDB/SIGMOD Systems PC Member
**Date**: April 24, 2026
**Thesis Type**: VNU-UET 3-chapter research thesis (IMRAD)
**Document Reviewed**: `thesis_outline.md` + supporting documents (`table_specifications.md`, `figure_specifications.md`, `abbreviations.md`, `writing_assignments.md`, `CONTRIBUTIONS.md`, `COMPETITIVE_TABLE.md`, `STATISTICAL_PLAN.md`, `gap_analysis.md`, `FORMULATION.md`)

---

## Pre-Review: Global Observations

Before scoring individual sections, five systemic issues pervade the entire document:

1. **All Tier 2 — every number is an estimate.** The thesis has no real benchmark data. Every result table (T9a, T9b, T9c) is labeled [TIER-2 ESTIMATED]. This is honest but creates a fundamental problem: a systems paper with no measured results is a design document.

2. **The NYC TLC dataset incompatibility is fatal for CRS rules.** NYC TLC Yellow Taxi has NO GPS coordinates — only zone IDs. CRS001 (GPS speed) and CRS002 (GPS jump) CANNOT be evaluated on the primary dataset. The NYC MTA Bus GTFS-realtime is the only dataset for CRS rules. This splits the evaluation across two datasets with no overlap, undermining the "holistic evaluation" narrative.

3. **D4 (External context) is a stub in fundamentals.** Section §1.3 introduces a "5D" context decomposition but D4 (holiday indicator) is not implemented. Putting an unimplemented dimension in Chapter 1 — the fundamentals — is misleading.

4. **L0 coverage is 2–5%.** The thesis dedicates an entire architecture section (§2.4) to L0–L5 hierarchical thresholds, but the finest-grained level (L0) covers only 2–5% of events. The mechanism is real, but its practical impact is tiny. The aggregate ΔF1 from context-aware thresholds will be close to zero.

5. **CRS003 is UNMEASURABLE (Tier 3) and is labeled #1 limitation.** One of 10 rules cannot be measured at all. This is a serious evaluation gap for a "research platform."

---

## Detailed Section Review

### Review: Introduction (§I.1–§I.4)

#### §I.1 Motivation — Score: **Weak Accept**

- **Issues**:
  - The motivation correctly identifies the gap (no streaming GPS trajectory validation), but claims "no existing framework combines cross-record GPS validation" — this is Tier 1 verifiable, but the literature review must substantiate this precisely.
  - The claim "NYC MTA Bus generates continuous GPS positions every ~30s" is used as motivation, but this is the GTFS-realtime update interval, not streaming event time. The distinction matters: 30s between position updates ≠ sub-second latency streaming.
  - §I.1 says "streaming tools lack cross-record checks" — Stream DaQ mentions cross-field as future work, which is NOT the same as "lacks." This is a weaker claim than stated.
  - The motivation frames "no framework combines GPS + context-aware + cross-record" — verify this exact formulation against competitive table. If CETrajAD (SDM 2025) does GPS anomaly detection (even batch), this claim needs careful framing.

- **Recommendation**: Tighten the motivation to be precise. State: "No surveyed streaming framework (Table 5) implements cross-record GPS trajectory validation." Add explicit footnote that Stream DaQ marks cross-field as future work. Clarify that NYC MTA Bus updates every 30s (not sub-second streaming).

#### §I.2 Research Objectives — Score: **Accept**

- **Issues**:
  - Six research questions (RQ1–RQ6) from HYPOTHESES.md. RQ1–RQ5 are measurable; RQ6 (ML augmentation) is Phase 3 and conditional.
  - The research platform disclaimer ("not a production system") is correctly stated here per writing assignments — good.
  - RQ3: "TQS correlates with injection rate" — this is a correlation study, not a causal claim. Appropriate for Tier 2.
  - RQ5: "CRS001/CRS002 precision > 0.70" — this needs to be stated as Tier 2 Estimated, not as a target that implies the result will be achieved.

- **Recommendation**: Add explicit Tier labels to each RQ. Clarify which RQs are ablation studies (RQ1, RQ4) vs. correlation (RQ3) vs. threshold (RQ5). State the null hypotheses explicitly in the text, not only in STATISTICAL_PLAN.md.

#### §I.3 Contributions — Score: **Borderline**

- **Issues**:
  - C1 ("First streaming GPS trajectory validation on real GTFS-realtime") — This is the strongest contribution but carries risk. Is streaming GPS validation genuinely novel, or is it "we applied known GPS anomaly detection to a streaming pipeline"? The distinction matters for novelty scoring.
  - C2 ("Hierarchical context-aware thresholds L0–L5 fallback") — Novel mechanism but coverage is 2–5%. The contribution is in the mechanism, not the aggregate impact. This must be clearly stated.
  - C3 ("Ground-truth evaluation methodology") — This is a methodology contribution, which is weaker than a systems contribution. Citing Exathlon (VLDB 2021) as precedent helps.
  - C4 ("ML-augmented calibration") — This is Phase 3, conditional, and Tier 2. Listing it as a contribution alongside C1–C3 overstates its maturity. Move to a "future work" framing or clearly subordinate it.
  - The 4-bullet contribution structure (§I.3 ≈ 300 words in writing_assignments.md vs. 400 words in the outline) is internally inconsistent.

- **Recommendation**: Lead with C1. De-emphasize C4 (conditional Phase 3). Be explicit that C3 is a methodology contribution, not a systems contribution. Add explicit novelty comparison: "Unlike Stream DaQ (future work) and GTFS Validator (batch-only), StreamDQ implements CRS rules in streaming mode."

#### §I.4 Structure — Score: **Strong Accept**

- **Issues**: None. The chapter mapping is clear and follows standard IMRAD.

- **Recommendation**: No changes needed.

---

### Review: Chapter 1 — Fundamentals (§1.1–§1.6)

#### §1.2 Streaming DQ — Score: **Accept**

- **Issues**:
  - The survey table (T5) must be accurate. Checking COMPETITIVE_TABLE.md: METER is listed as "PVLDB Vol.17" with "doi:10.14778/3636218.3636233" — this DOI belongs to VLDB 2024 (Volume 17), NOT 2023. VLDB 2023 is Volume 16. The reference is internally inconsistent across documents.
  - Stream DaQ is cited as "arXiv:2506.06147" — arXiv papers are NOT peer-reviewed. A VLDB/SIGMOD PC member will downgrade this comparison.
  - The gap statement ("none survey GPS trajectory validation in streaming mode") must be absolutely precise. If any prior work touches GPS + streaming (even partially), this claim fails.

- **Recommendation**: Verify every venue/year citation. Upgrade Stream DaQ citation if/when it appears at a conference. Clarify that arXiv 2025 is preprint. Add explicit "to the best of our knowledge" framing for the gap claim.

#### §1.3 Context-Aware DQ — Score: **Weak Accept**

- **Issues**:
  - **D4 (External) is a stub.** Table 2 shows "External (D4): holiday lookup (stub)" — explicitly labeled. The fundamentals chapter (§1.3) should not introduce a dimension as if it is implemented when it is not. A PC member will flag this as misleading.
  - **Power analysis for min_samples=100 is cited from "power analysis" but not verified.** The claim "Cohen's d ≈ 0.30, α=0.01, power=0.80" must have a citation to the actual power analysis computation or be self-contained.
  - **L0 coverage = 2–5% appears in §1.3 as a design property, not as a limitation.** This is correct placement but the text must acknowledge the sparsity problem explicitly.
  - **Comparison with Stream DaQ, Ada-Context, METER** — these comparisons are appropriate and should be in a structured table (T5), not buried in prose.

- **Recommendation**: Move D4 from §1.3 to §2.4 or §3.9 (future work / limitation). State min_sample values with power analysis justification inline (not just "from power analysis"). Add power analysis as a paragraph: "We compute the minimum sample size needed to detect Cohen's d=0.30 at α=0.01 with power=0.80 using [formula reference]. This yields n=96, rounded to 100 for L0."

#### §1.4 GPS Trajectory — Score: **Borderline**

- **Issues**:
  - **NYC TLC has NO GPS (zone IDs only).** This section discusses GPS trajectory quality issues (speed spikes, jumps, spoofing) but §1.4 does not clearly distinguish: NYC TLC cannot be used to demonstrate these issues. The reader may not realize the primary dataset lacks GPS.
  - **"GTFS-realtime updates every 30s"** — this is not streaming in the traditional sense. It's a near-real-time feed, not sub-second event streaming. The paper should address this directly: is 30s granularity sufficient for streaming DQ? What is the latency from GPS capture to validation?
  - **CETrajAD (SDM 2025)** is cited for LSTM autoencoder — but the thesis says LSTM is NO-GO for StreamDQ. Why include it prominently in fundamentals if it's not used? This is confusing.
  - **Chen et al. (IEEE T-ITS 2024) GPS spoofing** — verify this paper exists and is not an invented citation.

- **Recommendation**: Add explicit dataset incompatibility disclaimer in §1.4: "NYC TLC Yellow Taxi uses zone IDs (Borough/Zone taxonomy), not GPS coordinates. Therefore, CRS001 and CRS002 (GPS-based rules) are evaluated exclusively on NYC MTA Bus GTFS-realtime." Clarify that GTFS-realtime is a 30s polling feed, not sub-second streaming. Explain why 30s granularity is still valuable for DQ monitoring. Remove or de-emphasize CETrajAD/LSTM since it's not used.

#### §1.5 ML Calibration — Score: **Borderline**

- **Issues**:
  - **ML is Phase 3 (not implemented).** Putting it in Chapter 1 Fundamentals implies it's established prior art, not a proposed future contribution. The writing assignments say "Phase 3 mandatory" but the fundamentals chapter should frame ML as speculative/conditional.
  - **LSTM NO-GO is prominently displayed.** "Priority 4, NO-GO" is a significant negative result that should be minimized in fundamentals. It can be a single sentence: "LSTM is not pursued due to GPS training data unavailability and redundancy with CRS002."
  - **Three ML components (BO, IF, XGBoost)** without measured results are just architecture proposals. This section reads like a product roadmap, not fundamentals.
  - **Table T6 shows LSTM as "NO-GO"** — this is honest but weakens the ML chapter significantly.

- **Recommendation**: Move §1.5 to §2.6 or to a "Discussion / Future Work" section. Reframe: "We explore ML augmentation as Phase 3 (see §2.6). Bayesian Optimization (Priority 1) addresses the gap in adaptive threshold calibration." Remove the "three components" framing; lead with the problem ML solves, not the models. Minimize LSTM NO-GO — one sentence maximum.

---

### Review: Chapter 2 — Architecture (§2.1–§2.7)

#### §2.2 System Overview — Score: **Weak Accept**

- **Issues**:
  - **"Two datasets" design creates evaluation split.** NYC TLC (no GPS) + NYC MTA Bus (GPS) means: SYN/SEM rules evaluated on NYC TLC; CRS rules evaluated on NYC MTA Bus. There is no unified evaluation. This should be stated explicitly: "We evaluate SYN/SEM rules on NYC TLC and CRS rules on NYC MTA Bus due to dataset properties."
  - **Architecture diagram (F1)** is listed as "Needed" — it hasn't been created yet. A systems paper without an architecture diagram is incomplete.
  - **LocalPipeline vs. Flink distinction is buried.** The text mentions "LocalPipeline: for development" and "Flink pipeline: for benchmark evaluation" but doesn't emphasize that LocalPipeline results are NOT representative of distributed Flink latency/throughput.

- **Recommendation**: Add explicit table early in §2.2: "Dataset Scope: NYC TLC → SYN001–SYN003, SEM001–SEM003. NYC MTA Bus → CRS001, CRS002, CRS003, GTFSSem002." Clarify LocalPipeline ≠ Flink cluster. Acknowledge that Flink cluster benchmarks are pending.

#### §2.3 Rule Taxonomy — Score: **Accept**

- **Issues**:
  - **CRS rules in Java via gRPC** — this architectural choice is stated as "required" (not optional), citing PyFlink JVM↔Python serialization overhead. This is a valid engineering decision but must be justified more rigorously. What is the measured overhead? If not measured, this is an assumption.
  - **10 rules vs. Stream DaQ's 60+ checks** — the scope comparison should appear here. Stream DaQ has 60+ checks; StreamDQ has 10 rules. The scope difference is significant and must be addressed.
  - **CRS002 detection gap: 2–20 km/h moderate spoofing** (blocker B3). This is acknowledged as a known limitation but needs to be explicit in the taxonomy table or text.
  - **GTFSSem002 (stale > 5 min)** uses 300s as the staleness threshold — this is different from the CRS003 deduplication window (also 300s). The coincidence of these two values should be noted or justified.

- **Recommendation**: Add a paragraph justifying the Java decision with estimated overhead numbers (even Tier 2). Add a scope comparison: "StreamDQ implements 10 rules vs. Stream DaQ's 60+ checks. Our scope is narrower but domain-specific (GPS trajectory), while Stream DaQ covers generic data quality." Explicitly note CRS002's B3 gap in the text (not just in audit documents).

#### §2.4 Hierarchical Thresholds — Score: **Weak Accept**

- **Issues**:
  - **L0 coverage 2–5% undermines the section's significance.** §2.4 is 1,000 words + Figure F2 on a mechanism that applies to only 2–5% of events. The remaining 95–98% fall to L3/L4.
  - **"O(1) amortized per event" claim** — this needs to be verified. The O(1) claim is for the BroadcastState lookup, but the threshold computation itself (rolling P10/P90) requires maintaining state. The O(1) claim should be scoped to "threshold lookup after initial warmup."
  - **"L4 covers 20–40% of events"** — this contradicts L0's 2–5%. If L4 is 20–40% and L0 is 2–5%, then L1–L3 plus L5 cover ~55–78%. The breakdown should be explicit, not approximate.
  - **The L0–L4 fallback chain** — what happens when L0 has count < 100? Does it fall back to L1, or does it skip directly to L4? The fallback is described as "L0 → L1 → L2 → L3 → L4 → L5" but the actual decision tree (F2) shows it traversing every level. This should be confirmed in the implementation.

- **Recommendation**: Lead with the honest framing: "L0 covers approximately 2–5% of events due to NYC TLC zone-hour sparsity. We show that for this subset, context-aware thresholds reduce false positives by [Tier 2 estimate]. The L4 global fallback covers the majority of events." Clarify O(1) is for lookup post-warmup, not for the entire pipeline. Add the L0–L5 event distribution as an explicit table.

#### §2.5 TQS — Score: **Weak Accept**

- **Issues**:
  - **Non-circular design** — the claim is that TQS is computed from raw event properties, NOT from rule violations. This must be proven, not asserted. Walk through each dimension: Tm (inter-event time) — raw. Cn (null rate) — raw fields. Ac (out-of-range) — requires knowing what "in range" means. If "in range" comes from the adaptive threshold, then Ac is partially circular. Cs (consistency) — GPS plausibility via CRS001/CRS002. But TQS is meant to score quality BEFORE rule violations are known. The circularity concern is real.
  - **V2 weight selection** — Table T4 shows V2 (domain-prioritized: α=0.25, γ=0.25). How were these weights chosen? "Domain prioritization" is hand-waving. Was there an ablation? A sensitivity analysis? Without this, V2 weights are arbitrary.
  - **TQS Uv (Uniqueness)** — uses SHA256 hash for duplicate detection. CRS003 is the implementation of this, and CRS003 is Tier 3 UNMEASURABLE. So TQS Uv may also be unmeasurable on the deduplication side.

- **Recommendation**: Add explicit non-circularity proof for each TQS dimension. For Ac: clarify that Ac measures raw out-of-range events (e.g., negative fare), not rule violations. Add a sensitivity analysis paragraph for V2 weights: "We evaluate V1 (equal), V2 (domain-prioritized), and V3 (consistency-prioritized) and find [result]. V2 is primary because [rationale]." Acknowledge that TQS Uv depends on CRS003 measurement being available.

#### §2.6 ML Augmentation — Score: **Borderline**

- **Issues**:
  - **ML is Phase 3 — not implemented.** This section describes architecture for BO, IF, XGBoost, LSTM. These are design documents, not implemented systems. For Chapter 2 Architecture, describing a Phase 3 design is acceptable if clearly labeled as such.
  - **Isolation Forest conditional (ρ < 0.8)** — this is a complex gating condition. "Proceed only if IF↔P90 correlation < 0.8" means: IF adds value only when it's not redundant with the P90 threshold. This is sensible but needs justification: why 0.8 specifically?
  - **XGBoost training target undefined** — Priority 3 model has an undefined training target. Listing it as a "component" of the architecture when the target is undefined is problematic.
  - **LSTM NO-GO** — prominently shown in F5 with strikethrough. This is honest but visually dominant.

- **Recommendation**: Add explicit banner: "Phase 3 design — implementation pending benchmark validation." Rename §2.6 to "Proposed ML Augmentation (Phase 3)" to make the conditional status clear. Justify the 0.8 correlation threshold. Move XGBoost to "Deferred" status rather than listing it as a component with undefined target.

---

### Review: Chapter 3 — Experiments (§3.1–§3.10)

#### §3.2 Setup — Score: **Weak Accept**

- **Issues**:
  - **NYC TLC has no GPS** — this must be stated prominently in the setup, not discovered later. §3.2 says "Two datasets: NYC TLC Yellow Taxi, NYC MTA Bus GTFS-realtime" without clarifying their different GPS capabilities.
  - **"LocalPipeline: for development and unit tests; Flink pipeline: for benchmark evaluation"** — this separation is correct but the implication (LocalPipeline ≠ Flink) is not made explicit enough.
  - **"Flink pipeline: for benchmark evaluation"** — but Flink cluster has NOT been benchmarked yet. The text says "Flink pipeline: for benchmark evaluation" implying it will be used, but §3.8 (Latency) says "LocalPipeline profiling only." This inconsistency must be resolved.

- **Recommendation**: Add a dataset compatibility table in §3.2: "NYC TLC → zone-level, parquet replay, ~3M records. CRS rules NOT applicable (no GPS). NYC MTA Bus → GPS, live feed, real-time. CRS rules applicable; SYN/SEM NOT evaluated (different schema)." Clarify: Flink cluster benchmarks are future work (§3.9 Limitation #5).

#### §3.3 Methodology — Score: **Accept**

- **Issues**:
  - **McNemar's test for RQ1** — appropriate for paired comparison of rule-only vs. context-aware on the same events. Good choice.
  - **Wilcoxon signed-rank for RQ3** — appropriate for non-parametric TQS correlation. Good choice.
  - **Bootstrap CI (1,000 iterations)** — adequate per power analysis. 10,000 would be better but 1,000 is acceptable.
  - **Warmup: 10,000 events** — this is stated but not justified. Why 10,000? Is this enough to stabilize the rolling P10/P90 windows? The NYC TLC has ~3M records. 10,000 warmup is <0.4% of data.
  - **"3 trials per injection rate"** — this is low for bootstrap CI. Bootstrap resampling within a trial is appropriate; 3 independent trials is acceptable for variance estimation but should be justified.

- **Recommendation**: Justify the 10,000 warmup events: "We choose 10,000 events based on the rolling window size of [X] events needed to populate L0 context cells with ≥100 samples." Increase to 5 trials or add bootstrap resampling across all trials.

#### §3.4–§3.8 Results — Score: **Reject** (for publication; Accept with reservation for thesis)

- **Issues**:
  - **All results are Tier 2 ESTIMATED.** Table T9a, T9b, T9c are entirely [TIER-2] placeholders. A systems paper with no real results cannot be accepted at VLDB/SIGMOD.
  - **The thesis CAN be accepted with no real results IF** it is framed as a design paper + evaluation methodology paper, with honest limitations. The writing assignments correctly frame this as "measured contribution: positive, negative, or mixed results are all valid."
  - **SYN001–SYN003 on NYC TLC** — these are the most likely to have real results since NYC TLC is the primary dataset and SYN rules are simple (null/type checks). These should be implemented and measured first.
  - **CRS001/CRS002 on NYC MTA Bus** — these require live feed integration, which is harder to benchmark reliably. Tier 2 is more acceptable here.
  - **CRS003 is Tier 3 UNMEASURABLE** — this means 1 of 10 rules cannot be measured. This is a significant gap that PC members will scrutinize.

- **Recommendation**: The thesis CAN proceed with Tier 2 estimates IF:
  1. SYN001–SYN003 have real unit test results (these should be Tier 1 — code inspection + synthetic injection).
  2. At least one ablation study (RQ1 or RQ4) has real measured data.
  3. All Tier 2 numbers are accompanied by "estimated from code analysis; requires benchmark to confirm."
  4. CRS003 Tier 3 is prominently labeled and excluded from primary evaluation.

#### §3.9 Limitations — Score: **Accept** (with caveat)

- **Issues**:
  - **7 limitations listed** — good. The mandatory limitations section is present and detailed.
  - **CRS003 as #1 limitation** — this is correct prioritization. The most severe blocker is listed first.
  - **L0 coverage sparse (2–5%) as #2** — this is honest and correct.
  - **D4 External context is stub (#7)** — this should be listed higher, as it affects the "5D" context claim from §1.3.
  - **"LocalPipeline ≠ Flink" (#5)** — this should be clarified: LocalPipeline IS NOT equivalent to distributed Flink evaluation. The statement as written could be misread as "LocalPipeline is a degraded version of Flink" rather than "LocalPipeline is a separate evaluation environment."

- **Recommendation**: Promote D4 stub (#7) to at least #4. Clarify LocalPipeline ≠ Flink explicitly. Consider adding one more limitation: "CRS001/CRS002 thresholds (2 km/h, 100 km/h, 400m/30s) are hardcoded physics priors calibrated for NYC MTA Bus — they may not generalize to other transit agencies with different vehicle types and GPS characteristics."

---

## OVERALL RECOMMENDATION

| Dimension | Score | Justification |
|-----------|:------:|-------------|
| **Novelty** | 2/5 | Genuine: GPS trajectory validation on streaming GTFS-realtime. But: Stream DaQ (arXiv preprint) exists; LSTM-based GPS anomaly detection (CETrajAD SDM 2025) is prior art. Novelty is in the COMBINATION, not in individual components. |
| **Technical Depth** | 3/5 | Solid algorithm design (L0–L5 fallback, Haversine CRS rules, TQS formulation). Java CRS integration is architecturally sound. ML Phase 3 design is detailed but conditional. |
| **Experimental Validity** | 1/5 | **Critical weakness.** All results are Tier 2 ESTIMATED. CRS003 is Tier 3 UNMEASURABLE. No distributed Flink benchmarks. The evaluation plan is rigorous but the execution is zero. |
| **Clarity** | 3/5 | Well-structured thesis outline. Good use of tables (T1–T10). Clear IMRAD mapping. Internal inconsistencies (LocalPipeline vs. Flink, NYC TLC no GPS) create confusion. |
| **Related Work** | 3/5 | Comprehensive survey (14 frameworks). But: Stream DaQ is arXiv preprint (not peer-reviewed); METER venue/year citation errors; D4 stub in fundamentals is misleading. |
| **Overall** | **12/30** | **Borderline Reject (for VLDB/SIGMOD); Weak Accept (for VNU-UET thesis)** |

**Recommendation**: **Weak Accept (thesis); Reject (conference)**

For a VNU-UET thesis, this outline is solid and the honest Tier-labeling approach is commendable. The main risk is the evaluation gap — a thesis with no real benchmark data is weak.

For VLDB/SIGMOD, this is a design paper masquerading as a results paper. A PC member would likely desk-reject on the basis that all results are estimates.

---

**Top 3 Issues**:

1. **CRITICAL — Zero benchmark data (Experimental Validity: 1/5).** All Tier 2 estimates. CRS003 Tier 3 UNMEASURABLE. CRS001/CRS002 only on NYC MTA Bus. The thesis must have at minimum SYN001–SYN003 real results on NYC TLC before submission. Prioritize: SYN rules (Tier 1 candidates) > CRS rules on MTA Bus (Tier 2, acceptable) > ML ablation (Tier 2, defer if needed).

2. **MAJOR — NYC TLC / NYC MTA Bus dataset incompatibility is not prominently disclosed.** The split evaluation (SYN/SEM on TLC; CRS on MTA Bus) undermines the narrative of a "unified framework." This must be stated explicitly in §2.2, §3.2, and the Abstract. Readers should not discover the GPS incompatibility on page 15.

3. **MAJOR — D4 stub in Chapter 1 fundamentals misleads readers.** The "5D context decomposition" in §1.3 includes an unimplemented D4 (External/holiday). A PC member reading §1.3 will assume all 5 dimensions are implemented. Move D4 to §3.9 or §2.6 (future work). Rewrite the 5D table to show: D1–D3 implemented; D4 stub; D5 proxy metric.

---

## Appendix: Specific Verification Items

| Item | Status | Fix Required |
|------|--------|-------------|
| METER venue/year | Inconsistent: "VLDB Vol.17, 2023" → DOI is VLDB 2024 | Verify: DOI 10.14778/3636218.3636233 is from PVLDB Vol.17 (2024), NOT 2023 |
| Stream DaQ peer review | arXiv preprint (2025) — not peer-reviewed | Add "preprint" label in all tables and citations |
| L0–L5 O(1) claim | Stated without verification | Scope to "threshold lookup post-warmup" |
| V2 TQS weight selection | "Domain prioritization" — no justification | Add sensitivity analysis or ablation |
| 10,000 warmup justification | Not justified | Add: "10,000 events ≈ [X]% of data, sufficient to populate [Y]% of L0 cells" |
| NYC TLC GPS incompatibility | Not prominently disclosed in §3.2 | Add dataset compatibility table; state explicitly in Abstract |
| D4 stub in §1.3 | Misleading as "implemented" | Move to §3.9 (limitation) or §C.3 (future work) |
| CRS002 B3 detection gap | Not mentioned in taxonomy | Add one sentence: "Moderate spoofing (20–100 km/h) may fall below CRS002's jump threshold" |
| LSTM prominently cited in §1.4 | Used in fundamentals but NO-GO in §2.6 | De-emphasize; one sentence maximum |
| LocalPipeline ≠ Flink | Inconsistently stated | State explicitly in §2.2 and §3.8: "LocalPipeline is for development; distributed Flink benchmarks are future work" |
| CRS003 TQS Uv circularity | TQS Uv uses CRS003 which is Tier 3 | Clarify: TQS Uv measures raw hash duplicates (not rule violations) — independent of CRS003 |

---

*Reviewer: Systems PC Member Agent*
*StreamDQ Project — DEBATE Phase*
*Classification: Weak Accept (thesis); Reject (VLDB/SIGMOD conference)*

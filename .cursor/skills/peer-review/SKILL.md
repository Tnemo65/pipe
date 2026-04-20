---
name: peer-review
description: Simulate rigorous academic peer review of research papers. Evaluates novelty, technical correctness, experimental validity, writing quality, and related work coverage. Use when reviewing a draft paper, anticipating reviewer objections, or preparing a rebuttal. Produces structured review with scores and actionable feedback.
allowed-tools: Read Write
license: MIT license
metadata:
    skill-author: K-Dense Inc.
---

# Peer Review Simulation

## Overview
Simulate the perspective of a rigorous, senior program committee member reviewing a research paper. Identify weaknesses before submission, anticipate reviewers' objections, and prepare structured rebuttals.

## When to Use
- Pre-submission paper review to find weaknesses
- Anticipating reviewer comments before submitting
- Preparing a rebuttal after receiving reviews
- Deciding whether a paper is ready for submission

## Review Structure (Standard Format)

### Summary
[2-3 sentence objective summary of the paper's claim and method]

### Strengths
1. [Specific, concrete strength]
2. [Specific, concrete strength]
3. [Specific, concrete strength]

### Weaknesses
1. **[W1: Critical]** [Specific weakness + why it undermines the claim]
2. **[W2: Major]** [...]
3. **[W3: Minor]** [...]

### Questions for Authors
1. [Question that, if unanswered, would justify rejection]
2. [Clarification question]

### Scores
| Dimension | Score (1-5) | Rationale |
|-----------|-------------|-----------|
| Novelty | X | ... |
| Technical Depth | X | ... |
| Experimental Validity | X | ... |
| Clarity | X | ... |
| Related Work | X | ... |
| **Overall** | **X** | ... |

### Recommendation
[ ] Strong Accept / [ ] Accept / [ ] Weak Accept / [ ] Borderline / [ ] Reject

---

## Common Reviewer Objections to Anticipate

### Novelty Challenges
- "Prior work X already does this"
- "The contribution is incremental"
- "This is just X applied to Y"

**Preparation**: For each objection, prepare: (a) how your work differs technically, (b) a citation showing the gap, (c) an experiment that demonstrates the difference.

### Experimental Validity Challenges
- "The baseline is weak / outdated"
- "The dataset is too small / not representative"
- "Hyperparameter tuning favors your method"
- "No statistical significance reported"

**Preparation**: Run ablation studies. Compare against strongest available baseline. Report std dev across runs.

### Related Work Challenges
- "You missed paper X which is very relevant"
- "Your related work section is incomplete"

**Preparation**: Always search for recent (last 12 months) work using Semantic Scholar before submission.

## Rebuttal Writing Template
```
We thank the reviewers for their valuable feedback.

**R1-W2: [Paraphrase weakest objection]**
We respectfully disagree. [Direct counterargument + evidence].
Specifically, [quantitative result or logical argument].
We will clarify this in the revision.

**R1-W3: [Minor concern]**
Thank you for this observation. We will add [specific fix] in §X.
```

## Red Flags That Cause Rejection
1. Baselines are not state-of-the-art
2. Claims in abstract not supported by experiments
3. Missing ablation study
4. No discussion of limitations
5. Poor related work coverage (missing obvious papers)
6. Results without statistical significance
7. Non-reproducible experiments (no code/data/hyperparams)

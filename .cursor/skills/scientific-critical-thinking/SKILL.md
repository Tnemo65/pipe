---
name: scientific-critical-thinking
description: Apply rigorous critical thinking to evaluate research claims, identify logical fallacies, expose methodological weaknesses, and stress-test scientific arguments. Use when critiquing a paper, evaluating competing approaches, identifying attack vectors against competitor work, or strengthening your own paper's claims.
allowed-tools: Read Write
license: MIT license
metadata:
    skill-author: K-Dense Inc.
---

# Scientific Critical Thinking

## Overview
Systematically evaluate the validity of scientific claims using structured critical analysis frameworks. Particularly useful for competitive research positioning and finding weaknesses in competitor papers.

## When to Use
- Tearing down a competitor's paper to find exploitable weaknesses
- Stress-testing your own claims before submission
- Identifying logical/methodological flaws in prior work
- Preparing arguments for why your approach is superior

## Critical Analysis Framework

### Step 1: Claim Decomposition
List every claim the paper makes:
- **Central claim**: "Our method achieves SOTA on X"
- **Supporting claim 1**: "Our method runs in O(log n) time"
- **Supporting claim 2**: "Contextual features improve accuracy by 15%"

Then for EACH claim, ask:
1. Is this claim **falsifiable**? (Can it be disproven?)
2. Does the **experiment design** actually test this claim?
3. Are there **confounders** the authors didn't control?
4. Does the **baseline** represent true SOTA?

### Step 2: Methodology Audit Checklist

**Data:**
- [ ] Is the full dataset available for reproduction?
- [ ] Is the train/test split clearly defined and leak-free?
- [ ] Is the dataset representative of the claimed use case?
- [ ] Are there temporal leakage issues (future data used in training)?

**Experiments:**
- [ ] Are baselines fair and current?
- [ ] Are hyperparameters tuned the same way for all methods?
- [ ] Is statistical significance reported?
- [ ] Is there an ablation study?
- [ ] Are results reproducible from the provided code?

**Code:**
- [ ] Does the code match the paper's description?
- [ ] Are there hardcoded values that were manually tuned?
- [ ] Is "streaming" actually streaming or batch simulation?
- [ ] Are magic constants explained?

### Step 3: Logical Fallacy Detection

| Fallacy | Example in Research |
|---------|---------------------|
| **Circular reasoning** | "Our method is better because our metric says so" |
| **Strawman baseline** | Comparing against a weak/outdated baseline |
| **Cherry-picking** | Reporting only the favorable dataset/metric |
| **Overgeneralization** | "Works on Chicago Traffic → works on all datasets" |
| **False scope claim** | "We solve streaming data quality" but only test 1 anomaly type |

### Step 4: Scope Mismatch Attack
The most powerful attack: **prove the paper solves a DIFFERENT (easier) problem than claimed**.

Template:
```
The paper claims to solve [BROAD CLAIM].
However, their architecture can only detect [NARROW SUBPROBLEM].
Specifically, their detection function f(r_i, M) is single-record:
it has no access to other records r_j in the stream window W.
Therefore, by construction, it CANNOT detect [HARDER PROBLEM]
which requires f(r_i, r_j) over pairs.
We demonstrate this empirically in Section X.
```

### Step 5: Complexity Claim Verification
When a paper claims O(X) complexity:
1. What exact operation is being measured? (lookup? batch training? inference?)
2. Under what data distribution? (uniform vs. skewed)
3. Is the constant factor hidden?
4. Does the claim hold for pairwise operations or only single-record?

## Output Format

Use this template for a structured critique:

```markdown
## Critical Analysis: [Paper Title]

### Claim vs. Reality Gap
| Claim (paper) | Reality (code/experiment) |
|---------------|--------------------------|
| "Online streaming" | Batch CSV replay via Thread.sleep() |
| "119M records" | 26MB toy sample in repo |
| "O(log n) detection" | Magic threshold hardcoded, no derivation |

### Fatal Flaws (cause for rejection if exposed)
1. **[F1]**: [Flaw + evidence + impact on claims]
2. **[F2]**: ...

### Exploitable Weaknesses (for competitive positioning)
1. **[E1]**: Cannot detect [X] by design → our system can → run experiment
2. **[E2]**: Degrades on [Y distribution] → our system doesn't → show empirically

### What They Actually Proved
[Stripped of overclaims, what is the honest contribution?]
```

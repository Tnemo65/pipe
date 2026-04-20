---
name: scientific-writing
description: Write and improve scientific paper sections including abstracts, introductions, related work, methodology, results, discussion, and conclusions. Handles academic writing style, argumentation structure, contribution framing, and reviewer-ready language. Use when drafting or refining any section of a research paper.
allowed-tools: Read Write Edit
license: MIT license
metadata:
    skill-author: K-Dense Inc.
---

# Scientific Writing

## Overview
Produce publication-quality scientific writing across all sections of a research paper. Follows IMRAD structure and venue-specific norms.

## When to Use
- Drafting any paper section (abstract, intro, related work, method, results, discussion)
- Improving existing text for clarity, flow, and academic tone
- Framing contributions relative to prior work
- Writing rebuttal / revision responses to reviewers
- Structuring an argument for novelty

## Writing Principles

### Contribution Framing
Every paper needs a clear answer to: **"What is new and why does it matter?"**

Structure:
```
1. Problem: [what is broken / unsolved]
2. Limitation: [why existing work fails]
3. Insight: [your key idea / observation]
4. Method: [what you built]
5. Result: [empirical evidence]
6. Impact: [why it matters]
```

### Abstract Template
```
[Context 1-2 sentences]
[Problem/Gap 1 sentence]
[Proposed approach 1-2 sentences]
[Key results 1-2 sentences with numbers]
[Broader significance 1 sentence]
```

### Related Work Framing
Do NOT: list papers one by one
DO: group by theme, show gap between each theme and your work

```markdown
### 2.1 [Theme 1: Single-Record Anomaly Detection]
[Synthesis of 3-5 papers, what they do, collective limitation]

### 2.2 [Theme 2: Constraint-Based Data Quality]
[Synthesis, limitation]

### 2.3 Positioning
Unlike [Theme 1] approaches that [limitation], and [Theme 2] methods
that [limitation], our work [key distinction].
```

### Results Section Best Practices
- Always answer: "Does the experiment actually test the claim?"
- Lead with the number: "WAVES achieves F1=0.91, outperforming Ada-Context by 43%"
- Explain WHY: "The improvement is largest on skewed NYC Taxi data (§4.2)"
- Acknowledge failures honestly

### Common Academic Phrases
| Situation | Phrase |
|-----------|--------|
| Claiming novelty | "To the best of our knowledge, we are the first to..." |
| Acknowledging limitation | "While beyond the scope of this paper, future work could..." |
| Citing orthogonal work | "Our work is complementary to X; they address Y while we address Z" |
| Strong empirical claim | "Across all {N} benchmarks, our method consistently..." |

## Style Rules
1. Active voice preferred: "We propose" not "It is proposed"
2. Present tense for facts, past tense for experiments
3. Avoid: "very", "clearly", "obviously", "it should be noted"
4. Define all acronyms on first use
5. Every table/figure must be referenced in text BEFORE it appears

## Paper Sections Checklist
- [ ] Abstract: problem, method, results (with numbers), significance
- [ ] Intro: hook → gap → contributions (bulleted) → roadmap
- [ ] Related Work: thematic, ending with clear positioning
- [ ] Method: reproducible detail, pseudocode or algorithm block
- [ ] Experiments: datasets, baselines, metrics, implementation details
- [ ] Results: numbers first, explanation second, ablation study
- [ ] Discussion: limitations, future work
- [ ] Conclusion: 1 paragraph, no new info

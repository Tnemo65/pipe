---
name: hypothesis-generation
description: Structured hypothesis formulation from observations. Use when you have experimental observations or data and need to formulate testable hypotheses with predictions, propose mechanisms, and design experiments to test them. Follows scientific method framework. For open-ended ideation use scientific-brainstorming; for automated LLM-driven hypothesis testing on datasets use hypogenic.
allowed-tools: Read Write Edit Bash
license: MIT license
metadata:
    skill-author: K-Dense Inc.
---

# Scientific Hypothesis Generation

## Overview
Hypothesis generation is a systematic process for developing testable explanations. Formulate evidence-based hypotheses from observations, design experiments, explore competing explanations, and develop predictions.

## When to Use This Skill
- Developing hypotheses from observations or preliminary data
- Designing experiments to test scientific questions
- Exploring competing explanations for phenomena
- Formulating testable predictions for research
- Planning mechanistic studies across scientific domains

## Workflow

### 1. Understand the Phenomenon
- Identify the core observation or pattern that needs explanation
- Define the scope and boundaries
- Clarify what is known vs. uncertain

### 2. Conduct Literature Search
Use `paper-lookup` or `literature-review` skill to ground hypotheses in current evidence.

### 3. Generate Competing Hypotheses (3-5)
Each hypothesis should:
- Provide a **mechanistic** explanation (how and why, not just what)
- Be **distinguishable** from other hypotheses
- Be **testable** and **falsifiable**
- Draw on evidence from literature

### 4. Evaluate Quality
| Criterion | Question |
|-----------|----------|
| Testability | Can it be empirically tested? |
| Falsifiability | What observations would disprove it? |
| Parsimony | Is it the simplest explanation that fits? |
| Explanatory Power | How much of the phenomenon does it explain? |
| Novelty | Does it offer new insights? |

### 5. Design Experiments to Test Each Hypothesis
- What would be measured?
- What controls are needed?
- What sample sizes are appropriate?
- What are potential confounders?

### 6. Formulate Testable Predictions
For each hypothesis:
- State what should be observed if true
- Specify expected direction and magnitude
- Distinguish predictions between competing hypotheses

## Output Format

```markdown
## Hypothesis 1: [Title]
**Mechanism**: [How/why it works]
**Key Evidence**: [2-3 bullet points with citations]
**Testable Prediction**: [Specific, quantitative prediction]
**Falsification Condition**: [What result would disprove this]

## Proposed Experiment
**Method**: [Approach]
**Expected Result if H1 correct**: [Result A]
**Expected Result if H2 correct**: [Result B]
```

## Quality Standards
- **Evidence-based**: Grounded in existing literature
- **Testable**: Include specific, measurable predictions
- **Mechanistic**: Explain how/why, not just what
- **Comprehensive**: Consider alternative explanations

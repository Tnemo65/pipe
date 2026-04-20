---
name: statistical-analysis
description: Perform rigorous statistical analysis for research results including hypothesis testing, confidence intervals, effect sizes, power analysis, and significance testing. Use for analyzing experimental results, comparing methods, running ablation studies, and producing publication-ready statistical summaries.
allowed-tools: Read Write Bash
license: MIT license
metadata:
    skill-author: K-Dense Inc.
---

# Statistical Analysis

## Overview
Run rigorous statistical tests on experimental data and report results in publication-ready format.

## When to Use
- Comparing two or more methods with statistical significance
- Computing confidence intervals for metrics (F1, precision, recall, etc.)
- Running power analysis to determine needed sample size
- Producing ablation study results
- Testing whether performance differences are significant

## Core Statistical Tests

### Comparing Two Methods (Paired t-test / Wilcoxon)
```python
import numpy as np
from scipy import stats

# When data is normally distributed
def compare_methods_ttest(method_a_scores, method_b_scores, alpha=0.05):
    t_stat, p_value = stats.ttest_rel(method_a_scores, method_b_scores)
    effect_size = np.mean(method_a_scores - method_b_scores) / np.std(method_a_scores - method_b_scores)
    
    print(f"Mean A: {np.mean(method_a_scores):.4f} ± {np.std(method_a_scores):.4f}")
    print(f"Mean B: {np.mean(method_b_scores):.4f} ± {np.std(method_b_scores):.4f}")
    print(f"t={t_stat:.3f}, p={p_value:.4f}, Cohen's d={effect_size:.3f}")
    print(f"Significant: {p_value < alpha}")
    return p_value < alpha

# When data is not normally distributed (recommended for ML experiments)
def compare_methods_wilcoxon(method_a_scores, method_b_scores, alpha=0.05):
    stat, p_value = stats.wilcoxon(method_a_scores, method_b_scores)
    print(f"Wilcoxon: stat={stat:.3f}, p={p_value:.4f}")
    print(f"Significant: {p_value < alpha}")
    return p_value < alpha
```

### Bootstrap Confidence Intervals
```python
def bootstrap_ci(scores, metric_fn=np.mean, n_bootstrap=10000, ci=0.95):
    """Compute bootstrap confidence interval for any metric."""
    bootstrap_scores = []
    for _ in range(n_bootstrap):
        sample = np.random.choice(scores, size=len(scores), replace=True)
        bootstrap_scores.append(metric_fn(sample))
    
    alpha = (1 - ci) / 2
    lower = np.percentile(bootstrap_scores, alpha * 100)
    upper = np.percentile(bootstrap_scores, (1 - alpha) * 100)
    return np.mean(scores), lower, upper

# Usage
mean, low, high = bootstrap_ci(f1_scores)
print(f"F1 = {mean:.3f} [{low:.3f}, {high:.3f}] (95% CI)")
```

### Multiple Methods Comparison (Friedman Test)
```python
def compare_multiple_methods(results_dict, alpha=0.05):
    """results_dict: {'method1': [scores], 'method2': [scores], ...}"""
    from scipy.stats import friedmanchisquare
    groups = list(results_dict.values())
    stat, p = friedmanchisquare(*groups)
    print(f"Friedman: stat={stat:.3f}, p={p:.4f}")
    if p < alpha:
        print("Significant differences exist. Run post-hoc Wilcoxon tests.")
```

## Reporting Format for Papers

### Table Format
```
Method          | Precision | Recall | F1    | p-value vs. WAVES
WAVES (ours)    | 0.923*    | 0.891* | 0.907*| —
Ada-Context     | 0.651     | 0.438  | 0.524 | p<0.001
Baseline-2      | 0.712     | 0.689  | 0.700 | p<0.001
* significantly better than all baselines (Wilcoxon, p<0.05)
```

### In-text Reporting Template
```
WAVES achieves F1=0.907 (95% CI: [0.891, 0.923]), 
significantly outperforming Ada-Context (F1=0.524, Wilcoxon p<0.001, 
Cohen's d=1.83, large effect).
```

## Effect Size Interpretation
| Cohen's d | Interpretation |
|-----------|----------------|
| 0.2       | Small effect   |
| 0.5       | Medium effect  |
| 0.8+      | Large effect   |
| 1.5+      | Very large     |

## Power Analysis (Pre-experiment)
```python
from scipy.stats import norm

def minimum_sample_size(effect_size=0.5, alpha=0.05, power=0.8):
    """How many samples needed to detect a given effect?"""
    z_alpha = norm.ppf(1 - alpha/2)
    z_beta = norm.ppf(power)
    n = ((z_alpha + z_beta) / effect_size) ** 2
    return int(np.ceil(n))

n = minimum_sample_size(effect_size=0.5)  # medium effect
print(f"Need at least {n} samples per group")
```

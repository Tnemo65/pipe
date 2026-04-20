---
name: matplotlib
description: Low-level plotting library for full customization. Use when you need fine-grained control over every plot element, creating novel plot types, or integrating with specific scientific workflows. Export to PNG/PDF/SVG for publication. For quick statistical plots use seaborn; for publication-ready multi-panel figures with journal styling, use scientific-visualization.
license: https://github.com/matplotlib/matplotlib/tree/main/LICENSE
metadata:
    skill-author: K-Dense Inc.
---

# Matplotlib

## Overview
Matplotlib is Python's foundational visualization library. Always use the **object-oriented interface** (fig, ax) for production code, not pyplot state machine.

## Installation
```bash
uv pip install matplotlib numpy
```

## Core Pattern (Always Use This)
```python
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(10, 6), constrained_layout=True)
ax.plot(x, y, linewidth=2, label='label')
ax.set_xlabel('X Label', fontsize=12)
ax.set_ylabel('Y Label', fontsize=12)
ax.set_title('Title', fontsize=14, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3)
plt.savefig('figure.png', dpi=300, bbox_inches='tight')
plt.show()
```

## Common Plot Types

| Plot Type | Code |
|-----------|------|
| Line | `ax.plot(x, y, linewidth=2)` |
| Scatter | `ax.scatter(x, y, s=sizes, c=colors, alpha=0.6, cmap='viridis')` |
| Bar | `ax.bar(categories, values, color='steelblue', edgecolor='black')` |
| Histogram | `ax.hist(data, bins=30, edgecolor='black', alpha=0.7)` |
| Heatmap | `im = ax.imshow(matrix, cmap='coolwarm'); plt.colorbar(im, ax=ax)` |
| Box plot | `ax.boxplot([data1, data2], labels=['A', 'B'])` |
| Error bars | `ax.errorbar(x, y, yerr=std, fmt='o-', capsize=5)` |

## Multi-Panel Figures
```python
fig, axes = plt.subplots(2, 2, figsize=(12, 10), constrained_layout=True)
axes[0, 0].plot(x, y1, label='Method A')
axes[0, 1].bar(categories, values)
axes[1, 0].scatter(x, y2, c=colors, cmap='viridis')
axes[1, 1].hist(data, bins=30)
```

## Publication-Quality Export
```python
# For paper figures
plt.savefig('figure.pdf', bbox_inches='tight')   # Vector (scalable)
plt.savefig('figure.png', dpi=300, bbox_inches='tight', facecolor='white')  # Raster

# Set global font sizes for paper
plt.rcParams.update({'font.size': 12, 'axes.labelsize': 14, 'axes.titlesize': 16})
```

## Colormap Selection
- **Sequential** (`viridis`, `plasma`): Ordered data
- **Diverging** (`coolwarm`, `RdBu`): Data with zero-center
- **Qualitative** (`tab10`, `Set3`): Categorical data
- **Never use** `jet` — not perceptually uniform

## Research Comparison Plot Template
```python
import matplotlib.pyplot as plt
import numpy as np

methods = ['WAVES (ours)', 'Ada-Context', 'Baseline-A', 'Baseline-B']
f1_scores = [0.907, 0.524, 0.700, 0.651]
std_devs = [0.012, 0.031, 0.018, 0.024]
colors = ['#2ecc71', '#e74c3c', '#95a5a6', '#95a5a6']

fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
bars = ax.bar(methods, f1_scores, color=colors, edgecolor='black', linewidth=0.5)
ax.errorbar(methods, f1_scores, yerr=std_devs, fmt='none', color='black', capsize=5)
ax.set_ylabel('F1 Score', fontsize=12)
ax.set_title('Method Comparison on NYC Taxi DC Detection', fontsize=13)
ax.set_ylim(0, 1.05)
ax.axhline(y=f1_scores[0], color='green', linestyle='--', alpha=0.3)
plt.savefig('comparison.pdf', bbox_inches='tight')
```

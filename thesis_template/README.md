# Thesis Template

A LaTeX thesis template for **University of Engineering and Technology (UET)**, Vietnam National University Hanoi, based on the VNU-UET thesis format.

## Structure

```
thesis_template/
├── thesis_template.tex        # Main LaTeX document (book class)
├── references.bib             # BibTeX bibliography
├── README.md                 # This file
├── THESIS_OUTLINE.md         # Writing guide
└── chapters/
    ├── introduction.tex       # Introduction
    ├── chapter01.tex         # Chapter 1
    ├── chapter02.tex         # Chapter 2
    ├── chapter03.tex         # Chapter 3
    ├── conclusion.tex         # Conclusion
    ├── appendix_results.tex   # Appendix A
    └── appendix_config.tex    # Appendix B
```

## Quick Start

1. **Fill in your info** - Edit `thesis_template.tex` (author, title, supervisor, year)
2. **Write chapters** - Edit files in `chapters/` (each has PLACEHOLDER comments)
3. **Add figures** - Replace `\fbox{...}` placeholders with `\includegraphics`
4. **Compile**:
   ```bash
   pdflatex thesis_template.tex
   bibtex thesis_template
   pdflatex thesis_template.tex
   pdflatex thesis_template.tex
   ```

## Features

| Feature | Package |
|---|---|
| A4 page layout | `geometry` |
| Chapter styling | `titlesec` |
| Tables | `booktabs` |
| Algorithms | `algorithm` |
| Cross-refs | `cleveref` |
| Bibliography | `natbib` |

## Based On

- La Quoc Anh (2023) - Data Fabric Architecture thesis
- Le Dac Thinh (2026) - Knowledge Graph thesis

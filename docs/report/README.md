# Academic Report — TürkResearcher

This folder contains the IEEE-format academic report for the LLM final
project (Track 1: Novel Idea).

## Files

- `main.tex` — IEEE conference template, ~3 pages with placeholders
- `refs.bib` — BibTeX bibliography
- `figures/` — diagrams (architecture, eval results) — TODO

## Compilation

### Option A — Overleaf (easiest, no install)

1. Go to https://www.overleaf.com → New Project → Upload Project
2. Upload `main.tex` and `refs.bib` together
3. Compile → outputs PDF

### Option B — Local with TeX Live / MiKTeX

```powershell
# install MiKTeX once: https://miktex.org/download
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

### Option C — Pandoc (Markdown intermediate)

If you prefer Markdown editing, the LaTeX can be converted with `pandoc`.
But IEEE submission requires LaTeX, so we recommend keeping `main.tex` as
the canonical source.

## Status

- [x] Abstract — placeholder for headline numbers
- [x] Introduction — full
- [x] Related Work — full
- [x] Methodology — full
- [ ] Experiments → Results table — **fills in once `scripts/08_eval_summary.py` runs**
- [x] Discussion — needs eval-driven examples
- [x] Conclusion — full
- [ ] Architecture diagram — replace ASCII fbox with proper figure
  (`figures/architecture.pdf`)

## TODOs Before Submission

1. **Eval results table.** Replace `TBD` cells in Table~\ref{tab:overall}
   with values from `data/eval/summary.json`.
2. **Headline numbers in Abstract.** Insert citation-accuracy /
   faithfulness / holistic score from the same file.
3. **Architecture diagram.** Replace the ASCII placeholder
   (`fbox{...}`) in Fig.~1 with a proper `figures/architecture.pdf`.
   Easiest path: draw in Excalidraw or draw.io, export as PDF.
4. **Error-analysis examples.** Pick 2-3 failed eval questions from
   `data/eval/runs/*.json` and discuss in Section~V.
5. **Cite real \texttt{rag-bench}** if used; the entry is currently a
   placeholder.
6. **Author block.** If working with co-authors, add them.

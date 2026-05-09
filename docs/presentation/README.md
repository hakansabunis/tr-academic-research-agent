# Presentation

15-slide Marp markdown deck for the 10-15 min class presentation.

## Render options

### Option A — Marp CLI (recommended)

```bash
npm install -g @marp-team/marp-cli
marp slides.md --pdf
marp slides.md --pptx        # PowerPoint
marp slides.md --html        # HTML preview
marp slides.md --preview     # live preview
```

### Option B — VS Code extension

Install the **Marp for VS Code** extension. Open `slides.md`. Use the
"Open Preview" toolbar icon.

### Option C — Online

https://web.marp.app — paste `slides.md` content, export.

## Slide-by-slide outline

1. **Title** — project, author, course
2. **The Gap** — Turkish has no Elicit/Consensus equivalent
3. **Demo Question** — concrete example
4. **Architecture** — LangGraph state machine
5. **Data Pipeline** — 650K → 633K → embed → push
6. **Title-Aware Embedding** — improvement over previous index
7. **Multi-Agent Pipeline** — 5 agents in detail
8. **Live API Tools** — hybrid RAG
9. **DergiPark Harvest** — OAI-PMH protocol
10. **Evaluation** — 30 questions, 4 metrics
11. **Results** — TBD until eval finishes
12. **Live Demo** — `python scripts/run.py "..."`
13. **Limitations**
14. **Future Work**
15. **Reproducibility** — open data, code, index
16. **Thanks** — contact + Q&A

## Pre-presentation checklist

- [ ] Run `python scripts/08_eval_summary.py`, paste numbers into Slide 11
- [ ] Generate architecture diagram (Excalidraw / draw.io) → replace ASCII in Slide 4 (optional)
- [ ] Test the live demo command on the presenter laptop
- [ ] Prepare a static fallback (recorded GIF or screenshot of agent output)
  in case the demo fails on stage

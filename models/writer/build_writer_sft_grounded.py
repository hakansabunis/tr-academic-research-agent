"""Stage 2b — Grounded Writer distillation data generator.

Teaches the *real* writer_node task (not the abandoned title->abstract one):

    (question + retrieved theses + synthesis)  ->  grounded, IEEE-cited answer

This is non-hallucinatory by construction: the model only synthesizes the
sources it is given. DeepSeek is the teacher; a reduced pipeline
(planner -> retriever -> synthesizer -> writer; NO critic loop, NO live
search) is run per pool question to keep cost ~3 LLM calls/question.

For each question we write a run file whose schema is byte-compatible with
scripts/06_run_eval.py, so scripts/07_judge_eval.py can score it UNCHANGED
(rejection sampling reuses the exact paper metric). The writer SFT triple
(system / user / assistant) is captured under result["sft"], rendered with
the *same* prompt + formatters production uses (agents.writer), so training
input is identical to inference input.

Retriever MUST be v2 (set env, see comparison_v1_vs_v2.md):
    $env:CHROMA_PERSIST_DIR = "C:\\dev\\turk-researcher-data\\chroma_db_v2"
    $env:EMBEDDING_MODEL    = "hakansabunis/trakad-embed-v2"

Output: data/derived/distill_runs/<id>.json   (resumable; skips done)

Usage:
    python models/writer/build_writer_sft_grounded.py --limit 50      # smoke
    python models/writer/build_writer_sft_grounded.py                 # full pool
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from turk_researcher.agents.planner import planner_node          # noqa: E402
from turk_researcher.agents.retriever_node import retriever_node  # noqa: E402
from turk_researcher.agents.synthesizer import synthesizer_node   # noqa: E402
from turk_researcher.agents.writer import (                       # noqa: E402
    PROMPT as WRITER_PROMPT,
    _fmt_synth,
    _format_chunks_for_writer,
    writer_node,
)
from turk_researcher.config import load_settings                  # noqa: E402

POOL = ROOT / "data" / "derived" / "distill_question_pool.jsonl"
OUT_DIR = ROOT / "data" / "derived" / "distill_runs"


def _serialize_chunk(c) -> dict:
    # Mirrors scripts/06_run_eval.py::_serialize_chunk exactly so the judge
    # (07) consumes our runs without modification.
    return {
        "tez_no": c.tez_no,
        "title_tr": c.title_tr,
        "author": c.author,
        "year": c.year,
        "score": round(c.score, 4),
        "abstract_excerpt": c.abstract_tr[:300],
    }


def _render_sft(state: dict) -> dict:
    """Render the writer's exact teacher input + capture its output.

    Uses agents.writer's own PROMPT/formatters → training input is
    byte-identical to what DeepSeek (and later the local model) sees.
    """
    chunks = state.get("chunks", [])
    chunks_block, _ieee = _format_chunks_for_writer(chunks)
    msgs = WRITER_PROMPT.format_messages(
        question=state["question"],
        synthesis=_fmt_synth(state.get("synthesis")),
        chunks=chunks_block,
    )
    system = next((m.content for m in msgs if m.type == "system"), "")
    user = next((m.content for m in msgs if m.type == "human"), "")
    final = state.get("final")
    return {
        "system": system,
        "user": user,
        "assistant": final.answer_md if final else "",
    }


def _serialize(state: dict, latency: float) -> dict:
    plan = state.get("plan")
    synth = state.get("synthesis")
    final = state.get("final")
    chunks = state.get("chunks", [])
    return {
        "latency_seconds": round(latency, 2),
        "plan": {
            "sub_questions": [
                {"text": sq.text, "rationale": sq.rationale}
                for sq in (plan.sub_questions if plan else [])
            ],
        },
        "retrieval": {
            "n_chunks": len(chunks),
            "max_score": round(chunks[0].score, 4) if chunks else 0.0,
            "min_score": round(chunks[-1].score, 4) if chunks else 0.0,
            "chunks": [_serialize_chunk(c) for c in chunks[:30]],
        },
        "synthesis": (
            {
                "n_findings": len(synth.findings),
                "findings": [
                    {"claim": f.claim, "citations": f.citations}
                    for f in synth.findings
                ],
                "contradictions": synth.contradictions,
            }
            if synth else None
        ),
        "final": (
            {
                "answer_md": final.answer_md,
                "n_citations": len(final.citations_ieee),
                "citations_ieee": final.citations_ieee,
            }
            if final else None
        ),
        # Extra key (07_judge_eval ignores unknown keys): the SFT triple.
        "sft": _render_sft(state),
    }


def _reduced_pipeline(question: str) -> dict:
    """planner -> retriever -> synthesizer -> writer. No critic, no live.

    ~3 DeepSeek calls (planner, synthesizer, writer). Nodes return state
    deltas; we merge linearly (chunks is set exactly once)."""
    state: dict = {"question": question}
    state.update(planner_node(state))
    state.update(retriever_node(state))
    state.update(synthesizer_node(state))
    state.update(writer_node(state))
    return state


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", type=Path, default=POOL)
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    ap.add_argument("--limit", type=int, default=None,
                    help="Only first N pool questions (smoke test)")
    ap.add_argument("--force", action="store_true",
                    help="Re-run even if a run file exists")
    ap.add_argument("--require-v2", action="store_true",
                    help="Abort unless the retriever is wired to trakad-embed-v2")
    args = ap.parse_args()

    s = load_settings()
    print(f"[i] EMBEDDING_MODEL = {s.embedding_model}")
    print(f"[i] CHROMA_PERSIST_DIR = {s.chroma_persist_dir}")
    is_v2 = "trakad-embed-v2" in s.embedding_model or "chroma_db_v2" in str(s.chroma_persist_dir)
    if not is_v2:
        msg = ("[!] Retriever does NOT look like v2 (trakad-embed-v2 / "
               "chroma_db_v2). Set the env vars from comparison_v1_vs_v2.md.")
        if args.require_v2:
            print(msg, file=sys.stderr)
            return 2
        print(msg + " — continuing anyway (no --require-v2).", file=sys.stderr)

    if not args.pool.exists():
        print(f"[!] Missing pool: {args.pool} — run build_question_pool.py first",
              file=sys.stderr)
        return 1

    pool = [json.loads(l) for l in args.pool.read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.limit:
        pool = pool[:args.limit]
    args.out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[+] Distilling {len(pool)} questions → {args.out_dir}")
    print("    reduced pipeline: planner→retriever→synth→writer (no critic/live)\n")

    ok = skipped = failed = 0
    t0 = time.time()
    for q in pool:
        qid = q["id"]
        out_path = args.out_dir / f"{qid}.json"
        if out_path.exists() and not args.force:
            skipped += 1
            continue

        print(f"[+] {qid}: {q['question'][:70]}...")
        qt0 = time.time()
        try:
            state = _reduced_pipeline(q["question"])
            latency = time.time() - qt0
            payload = {
                "id": qid,
                "category": q.get("seed_subject", ""),
                "type": q.get("qtype", ""),
                "question": q["question"],
                "expected_subjects": [],
                "min_citations": 0,
                "result": _serialize(state, latency),
                "error": None,
            }
            out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                                encoding="utf-8")
            ok += 1
            n_cit = payload["result"]["final"]["n_citations"] if payload["result"]["final"] else 0
            print(f"    OK ({latency:.1f}s, {n_cit} citations)")
        except Exception as e:
            failed += 1
            print(f"    FAIL: {e}", file=sys.stderr)
            out_path.write_text(json.dumps({
                "id": qid, "question": q["question"], "result": None,
                "error": {"message": str(e), "traceback": traceback.format_exc()},
            }, ensure_ascii=False, indent=2), encoding="utf-8")

    elapsed = time.time() - t0
    print(f"\n[+] Done in {elapsed/60:.1f} min — ok: {ok}, failed: {failed}, "
          f"skipped: {skipped}")
    print("    Next: scripts/07_judge_eval.py --runs data/derived/distill_runs "
          "--out data/derived/distill_judgments")
    print("    Then: models/writer/filter_grounded_sft.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

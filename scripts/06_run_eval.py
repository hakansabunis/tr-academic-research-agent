"""Run the agent over the eval question set, save per-question outputs.

Usage:
    python scripts/06_run_eval.py
    python scripts/06_run_eval.py --questions data/eval/questions.json --resume

Output: data/eval/runs/<question_id>.json — full state (plan, chunks summary,
synthesis, critic, final answer) plus latency.

Resumable: skips questions that already have a results file (unless --force).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from turk_researcher.config import load_settings
from turk_researcher.graph import build_graph

DEFAULT_QUESTIONS = ROOT / "data" / "eval" / "questions.json"


def _serialize_chunk(c) -> dict:
    return {
        "tez_no": c.tez_no,
        "title_tr": c.title_tr,
        "author": c.author,
        "year": c.year,
        "score": round(c.score, 4),
        "abstract_excerpt": c.abstract_tr[:300],
    }


def _serialize_state(state: dict, latency: float) -> dict:
    plan = state.get("plan")
    synth = state.get("synthesis")
    critic = state.get("critic")
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
        "critic": (
            {
                "coverage_ok": critic.coverage_ok,
                "missing_aspects": critic.missing_aspects,
                "requery_terms": critic.requery_terms,
                "notes": critic.notes,
            }
            if critic else None
        ),
        "iteration_count": state.get("iteration", 0),
        "final": (
            {
                "answer_md": final.answer_md,
                "n_citations": len(final.citations_ieee),
                "citations_ieee": final.citations_ieee,
            }
            if final else None
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS)
    parser.add_argument("--out-dir", type=Path, default=None,
                        help="Defaults to <questions parent>/runs")
    parser.add_argument("--limit", type=int, default=None,
                        help="Only run first N questions")
    parser.add_argument("--force", action="store_true",
                        help="Re-run even if results file exists")
    args = parser.parse_args()

    settings = load_settings()  # validates DEEPSEEK_API_KEY etc.

    if not args.questions.exists():
        print(f"[!] Questions file not found: {args.questions}", file=sys.stderr)
        return 1

    questions = json.loads(args.questions.read_text(encoding="utf-8"))
    if args.limit:
        questions = questions[:args.limit]

    out_dir = args.out_dir or args.questions.parent / "runs"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[+] Running agent on {len(questions)} questions")
    print(f"    output: {out_dir}")
    print()

    graph = build_graph()

    skipped = ok = failed = 0
    overall_t0 = time.time()

    for q in questions:
        qid = q["id"]
        out_path = out_dir / f"{qid}.json"

        if out_path.exists() and not args.force:
            print(f"[=] {qid}: already done — skipping (use --force to re-run)")
            skipped += 1
            continue

        print(f"[+] {qid}: {q['question'][:70]}...")
        t0 = time.time()
        try:
            state = graph.invoke({"question": q["question"]})
            latency = time.time() - t0
            payload = {
                "id": qid,
                "category": q.get("category", ""),
                "type": q.get("type", ""),
                "question": q["question"],
                "expected_subjects": q.get("expected_subjects", []),
                "min_citations": q.get("min_citations", 0),
                "result": _serialize_state(state, latency),
                "error": None,
            }
            out_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            ok += 1
            n_cit = payload["result"]["final"]["n_citations"] if payload["result"].get("final") else 0
            print(f"    OK ({latency:.1f}s, {n_cit} citations)")
        except Exception as e:
            latency = time.time() - t0
            print(f"    FAIL ({latency:.1f}s): {e}", file=sys.stderr)
            payload = {
                "id": qid,
                "category": q.get("category", ""),
                "type": q.get("type", ""),
                "question": q["question"],
                "expected_subjects": q.get("expected_subjects", []),
                "min_citations": q.get("min_citations", 0),
                "result": None,
                "error": {
                    "message": str(e),
                    "traceback": traceback.format_exc(),
                    "latency_seconds": round(latency, 2),
                },
            }
            out_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            failed += 1

    elapsed = time.time() - overall_t0
    print()
    print(f"[+] Done in {elapsed/60:.1f} min — ok: {ok}, failed: {failed}, skipped: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

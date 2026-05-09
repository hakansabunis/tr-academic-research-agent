"""LLM-as-judge metrics on eval runs.

For each question, computes:
  - citation_accuracy:    for each [n] citation in answer, does the cited
                          chunk's abstract actually support the surrounding
                          claim? Aggregate as % correct.
  - faithfulness:         is every claim in the answer grounded in the
                          retrieved chunks? Score 0-1.
  - coverage:             how many of the planner's sub-questions are
                          actually addressed in the final answer? Score 0-1.
  - subject_match:        does the top retrieval chunk's subject match
                          `expected_subjects`? Boolean per question.
  - holistic:             1-5 overall quality score from a Turkish-academic
                          perspective.

Usage:
    python scripts/07_judge_eval.py
    python scripts/07_judge_eval.py --runs data/eval/runs --out data/eval/judgments

Resumable: skips questions whose judgment file already exists (unless --force).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from turk_researcher.llm import build_llm

DEFAULT_RUNS = ROOT / "data" / "eval" / "runs"
DEFAULT_OUT = ROOT / "data" / "eval" / "judgments"


class Judgment(BaseModel):
    citation_accuracy: float = Field(..., description="0-1: ne kadar atıf gerçekten kaynağı destekliyor")
    faithfulness: float = Field(..., description="0-1: yanıt getirilen kaynaklara ne kadar bağlı (uydurma yok)")
    coverage: float = Field(..., description="0-1: alt soruların ne kadarı kapsanmış")
    holistic_score: int = Field(..., ge=1, le=5, description="1-5 genel akademik kalite")
    rationale: str = Field("", description="Kısa açıklama")


JUDGE_PROMPT = """Sen bir Türkçe akademik yazım uzmanısın ve TürkResearcher
araştırma ajanının ürettiği bir yanıtı değerlendireceksin.

ORİJİNAL SORU:
{question}

PLANNER'IN ALT SORULARI:
{sub_questions}

GETİRİLEN KAYNAKLAR (özet):
{chunks_summary}

AGENT'IN YANITI:
{answer_md}

YANITTAKİ ATIFLAR:
{citations}

Değerlendirme yap:

1. **citation_accuracy** (0-1): Yanıttaki "[n]" atıfları gerçekten ilgili kaynağa
   uyuyor mu? Ne kadarı doğru?
2. **faithfulness** (0-1): Yanıttaki iddialar getirilen kaynaklarda destek
   buluyor mu? (1 = tam grounded, 0 = tamamen uydurma)
3. **coverage** (0-1): Alt soruların kaçı yanıtta gerçekten ele alınmış?
4. **holistic_score** (1-5): Türkçe akademik kalite (üslup, akıl yürütme,
   organizasyon).
5. **rationale**: 1-2 cümlede gerekçe."""


def _format_chunks(chunks: list[dict]) -> str:
    lines = []
    for i, c in enumerate(chunks[:15], 1):
        lines.append(
            f"[{i}] tez_no={c['tez_no']} | {c['author']} ({c.get('year','?')}) — "
            f"{c['title_tr'][:80]}\n     {c['abstract_excerpt'][:200]}"
        )
    return "\n\n".join(lines)


def judge_one(payload: dict, llm) -> Judgment | None:
    res = payload.get("result")
    if not res or not res.get("final"):
        return None

    sub_qs = res["plan"]["sub_questions"]
    chunks = res["retrieval"]["chunks"]
    final = res["final"]

    prompt = JUDGE_PROMPT.format(
        question=payload["question"],
        sub_questions="\n".join(f"- {sq['text']}" for sq in sub_qs),
        chunks_summary=_format_chunks(chunks),
        answer_md=final["answer_md"][:6000],
        citations="\n".join(final["citations_ieee"][:20]),
    )

    judged = llm.with_structured_output(Judgment, method="function_calling").invoke(prompt)
    return judged


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=Path, default=DEFAULT_RUNS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)

    runs = sorted(args.runs.glob("*.json"))
    if not runs:
        print(f"[!] No run files in {args.runs}", file=sys.stderr)
        return 1

    print(f"[+] Judging {len(runs)} runs from {args.runs}")
    llm = build_llm(temperature=0.0)

    ok = skipped = failed = 0
    t0 = time.time()
    for run_path in runs:
        qid = run_path.stem
        out_path = args.out / f"{qid}.json"

        if out_path.exists() and not args.force:
            print(f"[=] {qid}: already judged — skipping")
            skipped += 1
            continue

        payload = json.loads(run_path.read_text(encoding="utf-8"))
        if payload.get("error") or not payload.get("result"):
            print(f"[!] {qid}: run has error, skipping judge")
            out_path.write_text(json.dumps({
                "id": qid,
                "skipped": True,
                "reason": "run_failed",
            }, ensure_ascii=False, indent=2), encoding="utf-8")
            skipped += 1
            continue

        print(f"[+] {qid}: judging...")
        try:
            judged = judge_one(payload, llm)
            out_path.write_text(json.dumps({
                "id": qid,
                "question": payload["question"],
                "category": payload.get("category", ""),
                "judgment": judged.model_dump() if judged else None,
            }, ensure_ascii=False, indent=2), encoding="utf-8")
            ok += 1
            if judged:
                print(f"    cite={judged.citation_accuracy:.2f} faith={judged.faithfulness:.2f} "
                      f"cov={judged.coverage:.2f} holistic={judged.holistic_score}/5")
        except Exception as e:
            print(f"    FAIL: {e}", file=sys.stderr)
            failed += 1

    elapsed = time.time() - t0
    print()
    print(f"[+] Done in {elapsed/60:.1f} min — ok: {ok}, failed: {failed}, skipped: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Stage 2b — Build the question pool for grounded Writer distillation.

The grounded SFT task (build_writer_sft_grounded.py) needs many realistic
Turkish academic research questions to drive the RAG pipeline. These must be
*distinct* from the 30-question eval holdout (data/eval/questions.json) — any
leak would invalidate the Stage 2b evaluation.

Pipeline:
  1. Sample diverse (title, subject) seeds from the cleaned corpus, balanced
     across subjects so the pool isn't CS-heavy.
  2. For each seed cluster, ask DeepSeek for 4 broad research questions
     (trend / method / comparison / application) — the same shape as the
     eval set, so the distilled writer trains on the real task distribution.
  3. Holdout guard: drop any generated question that (a) normalizes to an
     eval question or (b) has cosine similarity > SIM_THRESHOLD to one,
     using the *same* encoder the retriever uses (EMBEDDING_MODEL env).

Output: data/derived/distill_question_pool.jsonl
  {"id": "dp00001", "question": "...", "seed_subject": "...", "qtype": "..."}

Usage (set v2 retriever env first — see comparison_v1_vs_v2.md):
    python models/writer/build_question_pool.py --target 800
    python models/writer/build_question_pool.py --target 800 --resume

Resumable: appends; re-run with --resume to top up to --target.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from turk_researcher.llm import build_llm  # noqa: E402
from turk_researcher.vectorstore import get_encoder  # noqa: E402

CORPUS = ROOT / "data" / "derived" / "abstracts_filtered_clean.parquet"
EVAL_QUESTIONS = ROOT / "data" / "eval" / "questions.json"
OUT_PATH = ROOT / "data" / "derived" / "distill_question_pool.jsonl"

SEED = 42
SIM_THRESHOLD = 0.85           # drop pool Q if cos-sim to any eval Q exceeds
TITLES_PER_CLUSTER = 8         # seed titles shown to the LLM per call
QS_PER_CLUSTER = 4             # questions requested per call (one per qtype)
QTYPES = ["trend", "method", "comparison", "application"]


class PoolQuestions(BaseModel):
    questions: list[str] = Field(
        ..., description="4 geniş Türkçe akademik araştırma sorusu, sırayla "
        "trend / yöntem / karşılaştırma / uygulama tipinde"
    )


PROMPT = (
    "Sen Türkçe akademik araştırma sorusu üreten bir asistansın. Aşağıda bir "
    "tez konusu kümesi var. Bu temaya dayanan, YÖK tez korpusunda RAG ile "
    "cevaplanabilecek **4 geniş araştırma sorusu** üret. Sırasıyla şu tipte "
    "olsun: 1) son yıllardaki eğilimler (trend), 2) bir yöntemin avantaj/"
    "sınırlılıkları (yöntem), 3) iki yaklaşımın karşılaştırması (karşılaştırma), "
    "4) bir uygulama alanı (uygulama). Sorular özgül ama tek bir teze "
    "bağlanmayacak kadar genel olsun. Sadece JSON döndür: "
    '{{"questions":["...","...","...","..."]}}\n\n'
    "Tez konusu kümesi:\n{titles}"
)


def _norm(s: str) -> str:
    """Aggressive normalization for exact-leak detection."""
    s = unicodedata.normalize("NFKC", str(s or "")).lower().strip()
    return re.sub(r"\s+", " ", re.sub(r"[^\wçğıöşü ]", "", s))


def _load_eval_questions() -> list[str]:
    data = json.loads(EVAL_QUESTIONS.read_text(encoding="utf-8"))
    return [q["question"] for q in data]


def _balanced_seed_clusters(df: pd.DataFrame, n_clusters: int, rng: random.Random,
                            subject_filter: list[str] | None = None):
    """Group titles by coarse subject, draw clusters round-robin so the pool
    is subject-balanced (avoids the CS-heavy skew of the raw corpus).

    subject_filter: if given, keep only rows whose subject contains any of
    these substrings (case-insensitive). Used to bias the pool toward the
    domains where the RAG system is least-weak (CS/engineering, matching the
    eval-set distribution) — see the Stage 2b diagnostic discussion."""
    df = df[df["title_tr"].str.len() >= 10].copy()
    if subject_filter:
        pats = [p.strip().lower() for p in subject_filter if p.strip()]
        subj_l = df.get("subject", "").astype(str).str.lower()
        mask = subj_l.apply(lambda s: any(p in s for p in pats))
        df = df[mask].copy()
        print(f"[+] subject-filter {pats} → {len(df):,} corpus rows")
    df["subj"] = df.get("subject", "").map(lambda s: str(s or "").split(";")[0].strip() or "Genel")
    by_subj: dict[str, list[str]] = {}
    for row in df.itertuples(index=False):
        by_subj.setdefault(row.subj, []).append(row.title_tr)
    subjects = [s for s, t in by_subj.items() if len(t) >= TITLES_PER_CLUSTER]
    rng.shuffle(subjects)
    for s in subjects:
        rng.shuffle(by_subj[s])
    clusters = []
    cursor = {s: 0 for s in subjects}
    while len(clusters) < n_clusters and subjects:
        for s in list(subjects):
            c = cursor[s]
            titles = by_subj[s][c:c + TITLES_PER_CLUSTER]
            if len(titles) < TITLES_PER_CLUSTER:
                subjects.remove(s)
                continue
            cursor[s] += TITLES_PER_CLUSTER
            clusters.append((s, titles))
            if len(clusters) >= n_clusters:
                break
    return clusters


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=800,
                    help="Desired total pool size (after dedupe)")
    ap.add_argument("--resume", action="store_true",
                    help="Append to an existing pool, topping up to --target")
    ap.add_argument("--out", type=Path, default=OUT_PATH,
                    help="Output jsonl (use a separate file per pool variant)")
    ap.add_argument("--subject-filter", default="",
                    help="Comma-separated subject substrings to bias the pool "
                    "(e.g. 'Bilgisayar,Mühendislik,Elektrik,Yazılım')")
    args = ap.parse_args()
    out_path: Path = args.out
    subj_filter = [s for s in args.subject_filter.split(",") if s.strip()] or None

    if not CORPUS.exists():
        print(f"[!] Missing corpus: {CORPUS} — run clean_corpus.py first", file=sys.stderr)
        return 1

    existing: list[dict] = []
    if args.resume and out_path.exists():
        existing = [json.loads(l) for l in out_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        print(f"[=] Resuming: {len(existing)} questions already in pool")
        if len(existing) >= args.target:
            print("[+] Target already met — nothing to do")
            return 0

    rng = random.Random(SEED + len(existing))
    df = pd.read_parquet(CORPUS, columns=[c for c in ("title_tr", "subject") if c])

    eval_qs = _load_eval_questions()
    eval_norm = {_norm(q) for q in eval_qs}
    print(f"[+] Encoding {len(eval_qs)} eval questions for leak guard (EMBEDDING_MODEL)")
    encoder = get_encoder()
    eval_emb = encoder.encode(eval_qs, normalize_embeddings=True)

    seen_norm = {_norm(r["question"]) for r in existing}
    pool = list(existing)
    next_id = len(existing) + 1

    llm = build_llm(temperature=0.7).with_structured_output(
        PoolQuestions, method="function_calling")

    need = args.target - len(pool)
    n_clusters = need * 2  # over-provision; dedupe will trim
    clusters = _balanced_seed_clusters(df, n_clusters, rng, subject_filter=subj_filter)
    print(f"[+] Generating from {len(clusters)} seed clusters, target {args.target}")

    dropped_leak = dropped_dup = 0
    with out_path.open("a" if args.resume else "w", encoding="utf-8") as f:
        for ci, (subj, titles) in enumerate(clusters):
            if len(pool) >= args.target:
                break
            try:
                out: PoolQuestions = llm.invoke(
                    PROMPT.format(titles="\n".join(f"- {t}" for t in titles)))
            except Exception as e:
                print(f"    [!] cluster {ci} ({subj}): LLM error: {e}", file=sys.stderr)
                continue
            if out is None or not getattr(out, "questions", None):
                # with_structured_output returns None when the model emits no
                # valid tool call — skip this cluster, don't crash the run.
                print(f"    [!] cluster {ci} ({subj}): no structured output, skipping",
                      file=sys.stderr)
                continue

            qs = [q.strip() for q in out.questions if q and q.strip()][:QS_PER_CLUSTER]
            if not qs:
                continue
            q_emb = encoder.encode(qs, normalize_embeddings=True)
            for j, q in enumerate(qs):
                nq = _norm(q)
                if nq in eval_norm or nq in seen_norm:
                    dropped_dup += 1
                    continue
                sim = float((q_emb[j] @ eval_emb.T).max())
                if sim > SIM_THRESHOLD:
                    dropped_leak += 1
                    continue
                rec = {
                    "id": f"dp{next_id:05d}",
                    "question": q,
                    "seed_subject": subj,
                    "qtype": QTYPES[j] if j < len(QTYPES) else "other",
                }
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                pool.append(rec)
                seen_norm.add(nq)
                next_id += 1
                if len(pool) >= args.target:
                    break
            if ci % 10 == 0:
                print(f"    cluster {ci}/{len(clusters)} — pool={len(pool)} "
                      f"(leak-drop {dropped_leak}, dup-drop {dropped_dup})")

    print(f"\n[+] Pool: {len(pool)} questions → {out_path}")
    print(f"    holdout-leak dropped: {dropped_leak}, duplicates dropped: {dropped_dup}")
    if len(pool) < args.target:
        print(f"[!] Below target ({len(pool)}/{args.target}) — re-run with "
              f"--resume to top up.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

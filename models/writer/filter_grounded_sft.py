"""Stage 2b — Rejection-sample grounded distillation into the SFT set.

Reuses the EXACT paper metric: run scripts/07_judge_eval.py over the
distill_runs first, then this script keeps only high-quality teacher
outputs (rejection sampling — methodologically consistent with eval).

Flow:
    python models/writer/build_writer_sft_grounded.py
    python scripts/07_judge_eval.py \
        --runs data/derived/distill_runs --out data/derived/distill_judgments
    python models/writer/filter_grounded_sft.py

Keep rule (defaults; tune via flags):
    citation_accuracy >= 0.80  AND  faithfulness >= 0.80
    AND coverage >= 0.60       AND  holistic_score >= 4

Output (chat format, system prompt preserved so training input == inference
input): data/derived/writer_sft_grounded_{train,val}.jsonl
    {"messages":[{"role":"system",...},{"role":"user",...},
                 {"role":"assistant",...}],
     "meta":{"id":...,"judge":{...}}}
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

RUNS = ROOT / "data" / "derived" / "distill_runs"
JUDGMENTS = ROOT / "data" / "derived" / "distill_judgments"
OUT_DIR = ROOT / "data" / "derived"

SEED = 42
VAL_RATIO = 0.03


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=Path, default=RUNS)
    ap.add_argument("--judgments", type=Path, default=JUDGMENTS)
    ap.add_argument("--min-citation", type=float, default=0.80)
    ap.add_argument("--min-faith", type=float, default=0.80)
    ap.add_argument("--min-coverage", type=float, default=0.60)
    ap.add_argument("--min-holistic", type=int, default=4)
    ap.add_argument("--val-ratio", type=float, default=VAL_RATIO)
    args = ap.parse_args()

    if not args.judgments.exists():
        print(f"[!] No judgments at {args.judgments} — run scripts/07_judge_eval.py "
              f"--runs {args.runs} --out {args.judgments} first", file=sys.stderr)
        return 1

    kept, n_total, n_no_judge, n_no_sft = [], 0, 0, 0
    fail_reasons = {"citation": 0, "faith": 0, "coverage": 0, "holistic": 0}

    for jpath in sorted(args.judgments.glob("*.json")):
        n_total += 1
        jdoc = json.loads(jpath.read_text(encoding="utf-8"))
        judg = jdoc.get("judgment")
        if not judg:
            n_no_judge += 1
            continue

        run_path = args.runs / f"{jpath.stem}.json"
        if not run_path.exists():
            continue
        run = json.loads(run_path.read_text(encoding="utf-8"))
        res = run.get("result") or {}
        sft = res.get("sft") or {}
        if not sft.get("assistant", "").strip():
            n_no_sft += 1
            continue

        passed = True
        if judg["citation_accuracy"] < args.min_citation:
            fail_reasons["citation"] += 1; passed = False
        if judg["faithfulness"] < args.min_faith:
            fail_reasons["faith"] += 1; passed = False
        if judg["coverage"] < args.min_coverage:
            fail_reasons["coverage"] += 1; passed = False
        if judg["holistic_score"] < args.min_holistic:
            fail_reasons["holistic"] += 1; passed = False
        if not passed:
            continue

        kept.append({
            "messages": [
                {"role": "system", "content": sft["system"]},
                {"role": "user", "content": sft["user"]},
                {"role": "assistant", "content": sft["assistant"]},
            ],
            "meta": {"id": jpath.stem, "judge": judg},
        })

    if not kept:
        print("[!] Nothing passed the filter — loosen thresholds or inspect "
              "judgments.", file=sys.stderr)
        print(f"    total={n_total} no_judge={n_no_judge} no_sft={n_no_sft} "
              f"fail={fail_reasons}", file=sys.stderr)
        return 1

    rng = random.Random(SEED)
    rng.shuffle(kept)
    n_val = max(1, int(len(kept) * args.val_ratio))
    val, train = kept[:n_val], kept[n_val:]

    tr_path = OUT_DIR / "writer_sft_grounded_train.jsonl"
    va_path = OUT_DIR / "writer_sft_grounded_val.jsonl"
    for path, rows in ((tr_path, train), (va_path, val)):
        with path.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    keep_rate = len(kept) / max(1, n_total - n_no_judge)
    avg_ans = sum(len(r["messages"][2]["content"]) for r in kept) / len(kept)
    print(f"[+] Kept {len(kept)}/{n_total} runs (keep-rate {keep_rate*100:.0f}% "
          f"of judged)")
    print(f"    train={len(train)}  val={len(val)}  avg answer chars={avg_ans:.0f}")
    print(f"    drops — no_judge:{n_no_judge} no_sft:{n_no_sft} "
          f"thresholds:{fail_reasons}")
    print(f"    → {tr_path}")
    print(f"    → {va_path}")
    print("\n[i] Ablation: train one QLoRA on writer_sft_grounded_* and one on "
          "writer_sft_* (abandoned title→abstract task), eval both via "
          "scripts/06→08 vs DeepSeek baseline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

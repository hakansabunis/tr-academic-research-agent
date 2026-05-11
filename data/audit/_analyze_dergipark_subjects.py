"""Analyze DergiPark subject taxonomy — identify STEM cluster for targeted harvest."""
import pandas as pd
from collections import Counter
from pathlib import Path

PARQUET = Path("data/derived/dergipark_filtered.parquet")

# STEM keywords (Turkish + English) for subject classification
STEM_PATTERNS = {
    "engineering": ["mühendis", "mühendisli", "engineering", "muhendisli"],
    "chemistry":   ["kimya", "chemistry", "biyokimya", "biochemistry"],
    "physics":     ["fizik", "physics"],
    "math":        ["matematik", "mathematics"],
    "biology":     ["biyolo", "biology", "genetics", "geneti", "ekolo"],
    "computer":    ["bilgisayar", "computer", "informatik", "informatic", "yazılım", "yazilim"],
    "medicine":    ["tıp", "tip", "medicine", "klinik", "clinical", "hemşir", "hemsir", "diş hek"],
    "agriculture": ["ziraat", "tarım", "tarim", "agriculture", "agronom"],
    "environment": ["çevre", "cevre", "environment", "ecolog"],
    "earth":       ["jeolo", "geology", "coğraf", "cografya", "geography", "meteorolo"],
    "veterinary":  ["veteriner", "veterinary", "hayvan"],
    "pharmacy":    ["eczacılık", "eczacilik", "pharmacy", "ilaç", "ilac"],
}

# Humanities / social sciences keywords (negative match)
NON_STEM_PATTERNS = {
    "linguistics": ["dilbilim", "linguistic", "filolojı", "filoloji"],
    "history":     ["tarih", "history"],
    "law":         ["hukuk", "law"],
    "business":    ["işletm", "isletm", "business", "iktisad", "ekonomi", "economic", "muhasebe"],
    "education":   ["eğitim", "egitim", "education", "pedagoj"],
    "sociology":   ["sosyolo", "sociolog", "antropolo"],
    "psychology":  ["psikolo", "psycholog"],
    "religion":    ["ilahiyat", "theology", "religi", "islami"],
    "art":         ["sanat", "art", "müzik", "muzik", "music"],
    "literature":  ["edebiyat", "literature"],
    "tourism":     ["turizm", "tourism"],
    "communication": ["iletişim", "iletisim", "communication", "gazetec"],
}


def classify(subject: str) -> tuple[str, str]:
    """Returns (cluster, label) where cluster is 'stem', 'non_stem', or 'unknown'."""
    if not subject:
        return ("unknown", "_empty_")
    s = subject.lower()
    # Try STEM first
    for label, kws in STEM_PATTERNS.items():
        for kw in kws:
            if kw in s:
                return ("stem", label)
    for label, kws in NON_STEM_PATTERNS.items():
        for kw in kws:
            if kw in s:
                return ("non_stem", label)
    return ("unknown", "_other_")


def main():
    df = pd.read_parquet(PARQUET, columns=["tez_no", "subject", "year"])
    print(f"Total: {len(df):,}")

    # Filter sane years
    df = df[(df["year"] >= 1995) & (df["year"] <= 2026)].reset_index(drop=True)
    print(f"After year filter (1995-2026): {len(df):,}")

    df["subject"] = df["subject"].fillna("").astype(str)

    # Classify
    df[["cluster", "label"]] = df["subject"].apply(lambda s: pd.Series(classify(s)))

    print("\n=== Cluster distribution ===")
    cluster_counts = df["cluster"].value_counts()
    for k, v in cluster_counts.items():
        print(f"  {k:>10s}  {v:>7,}  ({v/len(df)*100:.1f}%)")

    print("\n=== STEM label distribution ===")
    stem = df[df["cluster"] == "stem"]
    for k, v in stem["label"].value_counts().items():
        print(f"  {k:>14s}  {v:>6,}")

    print("\n=== NON-STEM label distribution (top) ===")
    non = df[df["cluster"] == "non_stem"]
    for k, v in non["label"].value_counts().head(8).items():
        print(f"  {k:>14s}  {v:>6,}")

    # Year coverage of STEM
    print("\n=== STEM year distribution (recent) ===")
    for y in sorted(stem["year"].unique(), reverse=True)[:8]:
        c = (stem["year"] == y).sum()
        print(f"  {y}: {c}")

    # Save subset for later harvest
    out = Path("data/audit/dergipark_stem_candidates.parquet")
    stem_recent = stem[stem["year"] >= 2015].copy()
    stem_recent.to_parquet(out, index=False)
    print(f"\n[+] Wrote {len(stem_recent):,} STEM candidates (year>=2015) to {out}")


if __name__ == "__main__":
    main()

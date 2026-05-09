# Stage 0 — Technical Learning Notes

> Comprehensive walkthrough of every concept, term, and technique used while
> building TürkResearcher (Capstone delivery, before any future fine-tuning
> stages). Designed as a study guide: each module has the **terminology**,
> **how we used it**, **why it matters**, and **review questions**.

---

## Module 1 · Data Engineering

### Key terms
- **Parquet** — columnar binary format with type-aware compression. ~10× smaller than CSV; supports range scans without loading the whole file.
- **Hugging Face Datasets** — Python library that fetches public datasets via `datasets.load_dataset(repo_id)`; caches locally, returns an Arrow table.
- **Quality filter pipeline** — deterministic, reproducible cleaning rules applied in sequence.
- **Deduplication** — keep one record per unique key (we used `tez_no`).

### What we did
1. Pulled `umutertugrul/turkish-academic-theses-dataset` from HF (~650K rows, 1.56 GB parquet, CC-BY-4.0).
2. Applied four filters: `abstract_tr` non-empty → `abstract_tr ≥ 50 words` → `title_tr` non-empty → dedup on `tez_no`. Result: ~633K records.
3. Wrote a `filter_report.json` capturing input/output counts and drop reasons.

### Why it matters
- "Garbage in, garbage out" — the corpus quality caps the entire downstream system.
- Reproducibility: anyone re-running our scripts gets the exact same record count.

### Review questions
- Why parquet and not JSONL or CSV?
- How would you re-design the filter to keep more long-tail subjects (e.g. veterinary)?

---

## Module 2 · Sentence Embeddings

### Key terms
- **Embedding** — function $f: \text{text} \to \mathbb{R}^d$. Maps a sentence to a fixed-dimensional vector so that semantically similar sentences have nearby vectors.
- **mpnet-base-v2** — `paraphrase-multilingual-mpnet-base-v2`, 768-dim, multilingual (50+ languages), based on XLM-RoBERTa.
- **L2 normalisation** — divide each vector by its Euclidean norm, so $\|v\|_2 = 1$. Required for cosine similarity to be a proper metric.
- **Title-aware indexing** — embed `title + "\n\n" + abstract` (not abstract alone). The title carries strong lexical signal.

### What we did
- Encoded each filtered thesis with mpnet → 768-dim vector.
- L2-normalised at index time.
- Concatenated title + abstract to construct the document.

### Why it matters
- Title-aware embedding **measurably improved retrieval** in the eval (smoke tests showed it disambiguates short queries).
- Multilingual model = no Turkish-specific training needed (zero-shot transfer).

### Review questions
- For two L2-normalised vectors, why does cosine similarity reduce to a dot product?
- Why doesn't a 384-dim mpnet (`MiniLM-L12`) suffice for our use case?

---

## Module 3 · Vector Indexing (HNSW)

### Key terms
- **HNSW (Hierarchical Navigable Small World)** — approximate nearest-neighbour graph algorithm (Malkov & Yashunin, 2018). Builds a multi-layer proximity graph; queries take O(log N) on average.
- **ANN vs brute-force** — brute-force = exact but linear in N; ANN = ~99% recall at sub-second latency on millions of vectors.
- **HNSW parameters**:
  - `M`: max neighbours per node (we used 16)
  - `ef_construction`: build-time search width (200)
  - `ef_search`: query-time search width (default ~10)
- **ChromaDB** — open-source vector database; SQLite-based persistence, HNSW backend.

### What we did
- Created a Chroma collection `turkish_theses` with `hnsw:space="cosine"`.
- 740K vectors + 13 metadata fields per record (`tez_no`, `author`, `subject`, `pdf_url`, …).
- Distinct ID schemas: theses use `str(tez_no)`, journal articles `art-{id}` — so they share a collection without colliding.

### Why it matters
- At 740K vectors, brute-force similarity search would take 2–3 seconds per query → unusable. HNSW: ~50 ms.
- Persistence allows the index to live on disk (15 GB), reload-friendly.

### Review questions
- What does HNSW's "skip-list-like" hierarchy buy you over a flat graph?
- Why is L2 normalisation a precondition for cosine indexing?

---

## Module 4 · RAG (Retrieval-Augmented Generation)

### Key terms
- **RAG** — pipeline of: (1) retrieve relevant documents from a vector store, (2) inject them as context, (3) ask the LLM to answer using only those documents.
- **Multi-query expansion** — issue multiple variant queries to boost recall.
- **Top-k retrieval** — pull the k most-similar chunks per query.
- **Score-aware deduplication** — when the same chunk appears across queries, keep the best score.
- **Context window discipline** — bound the number of chunks the writer sees (we used top-24).

### What we did
- For each turn: anchor question + 3–5 sub-questions (planner) → 4–6 queries.
- Per query top-k=6, deduplicated globally on `tez_no`, retained max similarity, truncated to 24 unique chunks.
- Cosine distance → similarity score in [0, 1] via `score = 1 − dist/2`.

### Why it matters
- LLMs alone hallucinate. RAG **grounds** their output in retrieved evidence.
- Multi-query catches concepts the original phrasing missed (e.g. "Türkçe NLP" misses BERT-specific results that "BERT Turkish" recovers).

### Review questions
- What goes wrong with top-100 retrieval? (token budget, signal-to-noise)
- How would you add hybrid retrieval (dense + BM25)?

---

## Module 5 · Multi-Agent Orchestration with LangGraph

### Key terms
- **State machine** — graph of nodes (computations) and edges (transitions); a typed state object is passed along.
- **TypedDict + Pydantic state** — Python-typed shape with validation; reducer functions on append-style fields (`chunks` accumulates across iterations).
- **Conditional edges** — at runtime, choose the next node based on state (we route Critic → {Retriever, LiveSearch, Writer}).
- **Bounded loop** — max iteration counter to prevent runaway cycles (`MAX_CRITIC_LOOPS = 2`).

### What we did
- Six nodes: Planner → Retriever → Synthesiser → Critic → (loop or LiveSearch) → Writer.
- `GraphState` carries `question, plan, chunks, synthesis, critic, iteration, final`.
- Critic emits `coverage_ok` boolean; if False and iteration < 2, route back to Retriever; otherwise route to LiveSearch fallback or directly to Writer.

### Why it matters
- Single LLM call ≠ structured reasoning. Multi-agent decomposes responsibilities so each step uses the right prompt and the right temperature.
- Conditional looping = adaptive behaviour: when the corpus is thin, the system tries again or pulls in external sources.

### Review questions
- What is the trade-off between deeper Critic loops and latency?
- How would you implement parallel sub-question retrieval in this graph?

---

## Module 6 · LLM Integration & Structured Output

### Key terms
- **OpenAI-compatible API** — many providers (DeepSeek, Mistral, Together) speak the OpenAI REST protocol; same client library works for all.
- **Structured output** — three approaches:
  1. **`function_calling`** (tools) — model returns a function call matching a schema.
  2. **`json_schema`** (response_format) — newer OpenAI feature; not yet supported by DeepSeek.
  3. **`PydanticOutputParser`** — manual: instruct the prompt to emit JSON, then parse the raw text. Provider-agnostic.
- **Per-agent temperature** — 0.0 for deterministic Critic; 0.1–0.3 for creative steps.

### What we did
- DeepSeek-Chat via `langchain_openai.ChatOpenAI(api_key=..., base_url="https://api.deepseek.com/v1", model="deepseek-chat")`.
- First tried `with_structured_output(method="function_calling")`. Worked locally; sometimes returned `None` on Spaces.
- Switched to `PydanticOutputParser` — prompt template embeds the schema description; we strip JSON fences and validate.

### Why it matters
- Structured output makes the agent **production-grade**: every node's output is a validated Python object, not an unparseable string.
- Provider-agnostic parsing = swap DeepSeek → GPT-4 → Anthropic without touching agent logic.

### Review questions
- Why would `json_schema` be preferable to `function_calling` if a vendor supports both?
- How would you stream tokens (server-sent events) through this stack?

---

## Module 7 · Citation Subsystem

### Key terms
- **Deterministic provenance** — citations generated by code from chunk metadata, not by the LLM. Hallucination becomes structurally impossible.
- **Inline citation marker** — the writer emits `[n]` where `n` indexes a chunk position. The reference list is built mechanically.
- **Hallucination guard** — post-process strips any `[m]` where `m > len(chunks)`.

### What we did
- The writer agent receives chunks numbered 1..N as context.
- It produces Turkish prose with `[n]` markers.
- Our system formats `[n] Author, "Title," Venue, Year. [Online]. URL` from chunk metadata.
- A regex pass nukes any out-of-range marker.

### Why it matters
- Researchers will only trust the system if citations resolve to **real** papers. Letting the LLM author the reference list is a known footgun.

### Review questions
- What attack surface remains for hallucinated **claims** (rather than hallucinated citations)? How would you mitigate it?

---

## Module 8 · Evaluation Engineering

### Key terms
- **LLM-as-judge** — use a (possibly different) LLM to score generations along a rubric. Cheap, fast, reasonable correlation with human raters at scale.
- **Four metrics**:
  - Citation accuracy ∈ [0,1]
  - Faithfulness ∈ [0,1]
  - Coverage ∈ [0,1]
  - Holistic ∈ {1..5}
- **Per-category breakdown** — disaggregate the mean by question category to surface failure modes.
- **Pre/post comparison** — controlled A/B between two system configurations (633K vs 740K).

### What we did
- 30-question Turkish benchmark across 10 categories (CS, education, health, engineering, social sciences, business, agriculture, linguistics, law, multi-domain).
- Judge prompt fed all retrieved chunks and the full citation list (initial cut only sent the first 20, which caused false negatives — fixed in iteration 2).
- Aggregated mean / median / min / max per metric and per category.

### Empirical headline (the paradox)
- 740K → 633K mean citation accuracy: **0.51 → 0.60** (worse!)
- But CS improved (0.21 → 0.26) and business improved (0.47 → 0.68).
- Health/engineering/law regressed by 0.20–0.27.
- Three causes: abstract length distribution shift, citation inflation, source-mixing without source-aware writing.

### Why it matters
- "More data is always better" is a popular myth. Honest per-category analysis shows when expansion helps and when it hurts.
- This finding is **paper-worthy** on its own.

### Review questions
- What confounders threaten LLM-as-judge validity? (judge bias, length bias, position bias)
- How would you measure inter-judge agreement?

---

## Module 9 · OAI-PMH Harvesting

### Key terms
- **OAI-PMH** — Open Archives Initiative Protocol for Metadata Harvesting (2002). HTTP-based, GET-only, with **verbs**: `Identify`, `ListRecords`, `ListSets`, `GetRecord`, `ListIdentifiers`, `ListMetadataFormats`.
- **Dublin Core (`oai_dc`)** — the standard metadata schema (15 fields: title, creator, subject, description, publisher, date, type, identifier, language, …).
- **Resumption token** — a cursor returned in each page; you GET the next page by passing it back.
- **Stateful streaming** — persisted resumption_token + JSONL append → resumable on crash.

### What we did
- Wrote `scripts/05_harvest_dergipark.py`: streams DergiPark via OAI-PMH, parses XML with `xml.etree.ElementTree`, writes one JSON-Lines record per page, persists `resumption_token` to disk after every page.
- Hit a malformed XML page at index 1266. Built a fallback: extract the resumption_token via regex from the broken response, jump past the bad page (~100 lost records), continue.
- 207K records harvested → 106K kept after applying the same quality filter as the thesis pipeline.

### Why it matters
- Web scraping = ToS gray zone, brittle. OAI-PMH = official, supported, polite.
- 600+ Turkish journals on DergiPark expose this endpoint; same recipe scales to any institutional repository.

### Review questions
- Why should harvesters respect the `from` and `until` parameters?
- How would you detect a malicious server returning malformed XML to fingerprint your harvester?

---

## Module 10 · Live API Integration

### Key terms
- **REST API consumption discipline** — User-Agent header, timeouts, exponential backoff, 429 handling.
- **Inverted abstract reconstruction** — OpenAlex stores abstracts as `{word: [positions]}`; reconstruct by sorting positions and joining words.
- **Source aggregation with dedup** — multiple APIs return overlapping content; key by stable ID.

### What we did
- `tools/live_search.py`: `search_openalex`, `search_semantic_scholar`, `search_dergipark` — each returns a unified `RetrievedChunk`-like dict.
- ASCII transliteration of Turkish queries (`ç→c`, `ğ→g`, `ı→i`, `ö→o`, `ş→s`, `ü→u`) before issuing API calls — both APIs' tokenisers handle Latin characters far better.
- Planner emits English search terms in addition to Turkish sub-questions; retrieval uses both.

### Why it matters
- The full corpus index is too large for HF Spaces free tier (15 GB > 16 GB free). Live API retrieval gives a working public demo with minimal infrastructure.

### Review questions
- Why does ASCII transliteration of Turkish queries help OpenAlex?
- How would you cache results to reduce latency?

---

## Module 11 · Hugging Face Spaces Deployment

### Key terms
- **Spaces** — HF's app hosting platform; supports Gradio, Streamlit, Docker. Free tier is CPU-only with 16 GB RAM, 50 GB ephemeral disk.
- **BYO-key model** — each user supplies their own LLM API key in the UI; the app never persists or logs it. Avoids cost-pooling onto the Space owner.
- **Secrets** — encrypted environment variables managed via the Settings UI.
- **`audioop-lts`** — backport of the `audioop` module that was removed from the Python 3.13 standard library; `pydub` (a Gradio dependency) still imports it.

### What we did (5-iteration debug cycle)
1. **Iteration 1**: `ModuleNotFoundError: audioop` → added `audioop-lts` shim.
2. **Iteration 2**: `ImportError: HfFolder` → upgraded to `gradio>=5.0.0`, pinned `huggingface_hub<1.0`.
3. **Iteration 3**: `launch(theme=...)` not supported → moved `theme` argument to `Blocks(theme=...)`.
4. **Iteration 4**: zero retrieved chunks (Turkish queries produced empty API responses) → added ASCII transliteration + English search terms emitted by the planner.
5. **Iteration 5**: `with_structured_output` returned `None` only on Spaces → replaced with `PydanticOutputParser` (manual JSON parsing).

After iteration 5, the Space rendered a 6-section Turkish answer with 22 IEEE citations on the first try.

### Why it matters
- Public live demo dramatically increases project visibility and credibility — a working URL beats a `git clone && pip install` README every time.
- The iteration log is itself an artefact: it teaches you the operational realities of LLM stacks (vendor quirks, dependency drift, encoding issues).

### Review questions
- Why does HF Spaces' free tier rule out persisting a 15 GB index? What pricing tier would change that?
- How does BYO-key shift trust and cost incentives between user and operator?

---

## Module 12 · MLOps & Reproducibility

### Key terms
- **Pinned versions** — `package==X.Y.Z` (deterministic) vs `package>=X.Y` (looser). Pinning trades compatibility-with-future for reproducibility-of-past.
- **Single-command setup** — `pip install -r requirements.txt` plus one helper script gets a fresh machine running.
- **Hub as MLOps backbone** — code on GitHub, data and model on Hugging Face Datasets, demo on HF Spaces. Three platforms, all linked.
- **Versioned releases** — git tags (`v0.1`, `v0.2`) and HF revisions for each milestone.

### What we did
- `requirements.txt` with version floors (`langchain>=0.3.20`, etc.).
- `scripts/04_pull_index_from_hub.py` — pulls the prebuilt 15 GB index from HF Hub in three minutes; no rebuild required.
- `space/` — separate dependency surface (Gradio, requests) since the Space does not need the local-corpus stack.
- Explicit `.gitignore` — keeps experiment artefacts (`data/eval/runs/`, `data/raw/`) out of the repo.

### Why it matters
- Without these conventions, "it works on my machine" becomes the project's epitaph. With them, anyone can reproduce the eval table in under an hour.

### Review questions
- What would you add to make the project more reproducible? (Docker, Nix, locked Conda env)
- How does HF Hub's versioning differ from a git tag?

---

## Soft skills we exercised

- **Iterative debugging** — the 5-build dance on HF Spaces is a microcosm of real LLM-system maintenance.
- **Defensive coding** — None checks, retry/backoff, hallucination guards, regex bypass for malformed XML.
- **Documentation as you build** — README, ROADMAP, proposal, learning notes — all written while the code was alive, not after.
- **Public-facing engineering** — the difference between "works on my laptop" and "anyone-can-try-it on HF Spaces" forces a higher quality bar.
- **Honest reporting** — paradox finding documented openly. Negative results are valid science.

---

## Glossary at a glance

| Term | Module |
|---|---|
| HNSW, ANN | 3 |
| Cosine similarity, L2 normalisation | 2, 3 |
| RAG, top-k, multi-query | 4 |
| LangGraph, state machine, conditional edge | 5 |
| Function calling, json_schema, PydanticOutputParser | 6 |
| LLM-as-judge, faithfulness, coverage | 8 |
| OAI-PMH, Dublin Core, resumption token | 9 |
| Inverted abstract, ASCII transliteration | 10 |
| BYO-key, HF Spaces secrets, audioop-lts | 11 |
| Pinned versions, HF Hub revisions | 12 |
| Catastrophic forgetting, contrastive learning, SimCSE, MNR | (Stage 1 preview) |

---

## Recommended reading order (for a deeper dive)

1. Reimers & Gurevych 2019, **Sentence-BERT**.
2. Reimers & Gurevych 2020, **Multilingual Sentence Embeddings**.
3. Lewis et al. 2020, **Retrieval-Augmented Generation**.
4. Malkov & Yashunin 2018, **HNSW**.
5. Gao, Yao, Chen 2021, **SimCSE** (Stage 1 prerequisite).
6. Zheng et al. 2023, **Judging LLM-as-a-Judge**.
7. Wu et al. 2023, **AutoGen** (multi-agent precedent).

---

*Last updated: 2026-05-09. Author: Hakan Sabuniş. Co-authored with Claude Opus 4.7.*

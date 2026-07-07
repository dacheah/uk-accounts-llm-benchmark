# UK Company Accounts — LLM Benchmark

**Can frontier LLMs read UK company accounts? We tested five — proprietary and open-weight —
on 1,000 verified questions built from real Companies House filings.**

Short answer: **yes, uniformly well — and the open, self-hostable models match the proprietary
leaders.** The scarce, defensible asset isn't the model; it's clean, verified UK-accounts data.

## Results

**Clean benchmark** — 1,000 verified Q&A from structured UK financials (extraction, comparison,
ratio, boolean, disclosure).

| Model | Type | Accuracy | 95% CI |
|---|---|---|---|
| Claude Opus 4.8 | proprietary | 99.6% | 99.0–99.8% |
| DeepSeek V4 Pro | **open** | 99.5% | 98.8–99.8% |
| GPT-5.5 | proprietary | 98.4% | 97.4–99.0% |
| GLM 5.2 | **open** | 98.4% | 97.4–99.0% |
| Gemini 2.5 Pro | proprietary | 98.1% | 97.1–98.8% |

**Hard benchmark — raw filings, provably unseen (n = 350).** Extraction straight from the raw
inline-XBRL filing (no hints), plus a turnover-hallucination trap — drawn only from filings
published *after every model's release*, so this table doubles as the contamination control.
(Raw filing contexts are withheld for privacy; scores are reproducible by the dataset holder.)

| Model | Type | As run | 95% CI | Adjudicated¹ |
|---|---|---|---|---|
| Claude Opus 4.8 | proprietary | 99.4% | 97.9–99.8% | 100.0% |
| GPT-5.5 | proprietary | 99.4% | 97.9–99.8% | 100.0% |
| GLM 5.2 | **open** | 99.4% | 97.9–99.8% | 100.0% |
| Gemini 2.5 Pro | proprietary | 98.9% | 97.1–99.6% | 99.4% |
| DeepSeek V4 Pro | **open** | 98.9% | 97.1–99.6% | 99.4% |

¹ Two items were missed *identically* by all five models — the signal that our ground truth, not
the models, is wrong. Both had context polluted by the filing's raw CSS block (renderer fix in
hand); excluded as builder artifacts (n = 348). Turnover trap: **70/70 for all five models.**

*CIs are 95% Wilson intervals. Read both tables as tiers, not rankings: on the clean set the
top pair is statistically separable from the other three (p < 0.05), but adjacent positions
are not; on the raw-filing set no pairwise difference is significant — all five models are
statistically indistinguishable on raw, unseen filings.*

**Why it matters:** the residual error is the *wrong kind* for finance — grabbing the wrong line
(6,585 read as 10,085), a digit slip (290 → 390), an over-conservative "not disclosed" for a
figure that's present. Silent, plausible wrong numbers: fine for a demo, disqualifying for a
credit model or a rating input. And because open-weight models (which finance firms *can*
self-host under data-governance rules) match the proprietary big three, the only scarce asset in
the chain is **verified, provenance-tracked data.**

## What's in here
- `benchmark.jsonl` — the 1,000 verified questions and answers (add this file; see below).
- `evaluate.py` — run any model (Anthropic / OpenAI / Google / OpenRouter) and score it.
- `benchmark_grading.py` — answer parsing + grading.

## Run it against your own model
```
pip install -r requirements.txt
# put your key(s) in a .env file: ANTHROPIC_API_KEY=... / OPENAI_API_KEY=... /
#   GEMINI_API_KEY=... / OPENROUTER_API_KEY=...
python evaluate.py --provider anthropic
python evaluate.py --provider openrouter --model deepseek/deepseek-v4-pro
python evaluate.py --provider openai --limit 20     # cheap smoke test
```

## Method & honesty
Answers are computed from the source data, not hand-labelled. Grading tolerates the messy ways
models reply (units, "not disclosed" phrasing, dropped spaces in names). Contexts contain **no
personal data**. Full methodology, including the corrections we made when our own benchmark or
dataset was at fault, is documented alongside the dataset.

**Contamination — tested and ruled out (v2, July 2026):** the hard table above *is* the control
— every question comes from filings *published after every evaluated model's release*, so they
cannot be in any training set. Scores (98.9–99.4% as run) sit at or above each model's earlier
hard-set score; memorisation would produce the opposite. Two of the misses were answered
identically "0" by all five models — the signal that our ground truth, not the models, was wrong:
their context was polluted by the filing's raw CSS `<style>` block, burying the balance-sheet
figure (renderer fix: strip `<style>`/`<script>`). Excluding those two builder artifacts (n=348),
models scored **99.4–100.0%**, with the turnover trap clean at **70/70 for all five**. This
supersedes the v1 post-cutoff run (which surfaced five prior-year-fallback artifacts, since
fixed). Tooling and sourced release dates: `build_benchmark_postcutoff.py` + `model_cutoffs.json`
in the pipeline repo.

## Licence
- **Benchmark data** (`benchmark.jsonl`): **CC BY 4.0** — free to use with attribution.
  Derived from Companies House data under the Open Government Licence v3.0
  ("Contains public sector information licensed under the Open Government Licence v3.0").
- **Scripts** (`evaluate.py`, `benchmark_grading.py`): **MIT** (see `LICENSE`).

## Author
**Daniel Cheah** — [danielcheah.com](https://danielcheah.com) · [LinkedIn](https://au.linkedin.com/in/dcheah)

*The full UK company financials datasets (Product 1 and the structured-finance SPV/lender map)
are available for licensing — see danielcheah.com.*

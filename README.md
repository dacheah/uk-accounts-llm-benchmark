# UK Company Accounts — LLM Benchmark

**Can frontier LLMs read UK company accounts? We tested five — proprietary and open-weight —
on 1,000 verified questions built from real Companies House filings.**

Short answer: **yes, uniformly well — and the open, self-hostable models match the proprietary
leaders.** The scarce, defensible asset isn't the model; it's clean, verified UK-accounts data.

## Results

**Clean benchmark** — 1,000 verified Q&A from structured UK financials (extraction, comparison,
ratio, boolean, disclosure).

| Model | Type | Accuracy |
|---|---|---|
| Claude Opus 4.8 | proprietary | 99.6% |
| DeepSeek V4 Pro | **open** | 99.5% |
| GPT-5.5 | proprietary | 98.4% |
| GLM 5.2 | **open** | 98.4% |
| Gemini 2.5 Pro | proprietary | 98.1% |

**Hard benchmark** — extraction straight from the raw inline-XBRL filing (no hints), plus a
turnover-hallucination trap. (Raw filing contexts are withheld for privacy; scores are reproducible
by the dataset holder.)

| Model | Type | Accuracy |
|---|---|---|
| GPT-5.5 | proprietary | 97.9% |
| Claude Opus 4.8 | proprietary | 97.3% |
| Gemini 2.5 Pro | proprietary | 96.7% |
| DeepSeek V4 Pro | **open** | 96.7% |
| GLM 5.2 | **open** | 95.8% |

**Why it matters:** the residual ~1–4% error is the *wrong kind* for finance — inventing £0 for
turnover that filleted accounts legally omit, grabbing the wrong line, sign slips on net
liabilities. Fine for a demo; disqualifying for a credit model or a rating input. And because
open-weight models (which finance firms *can* self-host under data-governance rules) match the
proprietary big three, the only scarce asset in the chain is **verified, provenance-tracked data.**

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

## Licence
- **Benchmark data** (`benchmark.jsonl`): **CC BY 4.0** — free to use with attribution.
  Derived from Companies House data under the Open Government Licence v3.0
  ("Contains public sector information licensed under the Open Government Licence v3.0").
- **Scripts** (`evaluate.py`, `benchmark_grading.py`): **MIT** (see `LICENSE`).

## Author
**Daniel Cheah** — [danielcheah.com](https://danielcheah.com) · [LinkedIn](https://au.linkedin.com/in/dcheah)

*The full UK company financials datasets (Product 1 and the structured-finance SPV/lender map)
are available for licensing — see danielcheah.com.*

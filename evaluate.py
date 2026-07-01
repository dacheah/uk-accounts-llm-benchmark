"""
evaluate.py — run a model against the UK-accounts benchmark and score it.

Standalone: reads ./benchmark.jsonl and grades with benchmark_grading.py. Supports Anthropic
(Claude), OpenAI (GPT), Google (Gemini), and any open-weight model via OpenRouter (DeepSeek,
GLM, Qwen, ...). API keys are read from environment variables or a local .env file.

Setup:
    pip install anthropic openai google-genai
    # put keys in a .env file (or your environment):
    #   ANTHROPIC_API_KEY=...   OPENAI_API_KEY=...   GEMINI_API_KEY=...   OPENROUTER_API_KEY=...

Usage:
    python evaluate.py --provider anthropic
    python evaluate.py --provider openrouter --model deepseek/deepseek-v4-pro
    python evaluate.py --provider openai --limit 20        # cheap smoke test
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import benchmark_grading as grading

HERE = Path(__file__).resolve().parent

DEFAULT_MODELS = {
    "anthropic": "claude-opus-4-8",
    "openai": "gpt-5.5",
    "google": "gemini-2.5-pro",
    "openrouter": "deepseek/deepseek-v4-pro",
}
KEY_ENV = {
    "anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY",
    "google": "GEMINI_API_KEY", "openrouter": "OPENROUTER_API_KEY",
}
SYSTEM = (
    "You are a careful financial analyst working with UK company accounts (UK GAAP / FRS 102 "
    "and FRS 105). Answer the question as concisely as possible. For a numeric answer, reply "
    "with just the figure in pounds. If a figure is NOT disclosed in the accounts provided, "
    "reply 'not disclosed' rather than guessing."
)


def _load_dotenv():
    env = HERE / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


def call_anthropic(model, prompt, key):
    import anthropic
    m = anthropic.Anthropic(api_key=key).messages.create(
        model=model, max_tokens=300, system=SYSTEM,
        messages=[{"role": "user", "content": prompt}])
    return "".join(getattr(b, "text", "") for b in m.content)


def call_openai(model, prompt, key):
    from openai import OpenAI
    r = OpenAI(api_key=key).chat.completions.create(
        model=model, messages=[{"role": "system", "content": SYSTEM},
                                {"role": "user", "content": prompt}])
    return r.choices[0].message.content or ""


def call_google(model, prompt, key):
    from google import genai
    from google.genai import types
    r = genai.Client(api_key=key).models.generate_content(
        model=model, contents=prompt,
        config=types.GenerateContentConfig(system_instruction=SYSTEM, max_output_tokens=4096))
    txt = (r.text or "").strip()
    if not txt and getattr(r, "candidates", None):
        for c in r.candidates:
            for p in (getattr(getattr(c, "content", None), "parts", None) or []):
                if getattr(p, "text", None):
                    txt += p.text
    return txt.strip()


def call_openrouter(model, prompt, key):
    from openai import OpenAI
    r = OpenAI(api_key=key, base_url="https://openrouter.ai/api/v1").chat.completions.create(
        model=model, max_tokens=4096,
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}])
    msg = r.choices[0].message
    return (msg.content or "").strip() or (getattr(msg, "reasoning", None) or "").strip()


CALLERS = {"anthropic": call_anthropic, "openai": call_openai,
           "google": call_google, "openrouter": call_openrouter}


def run(provider, model, limit, concurrency, benchmark_path):
    _load_dotenv()
    key = os.environ.get(KEY_ENV[provider], "").strip().strip('"').strip("'")
    if not key:
        sys.exit(f"No API key. Set {KEY_ENV[provider]} in your environment or a .env file.")
    items = [json.loads(l) for l in open(benchmark_path, encoding="utf-8")]
    if limit:
        items = items[:limit]
    caller = CALLERS[provider]
    print(f"Evaluating {provider}/{model} on {len(items)} items ...")

    results = [None] * len(items)
    errors, first_error = [0], [None]

    def work(i, item):
        try:
            ans = caller(model, item["question"], key)
            return i, ans, grading.grade(item, ans)
        except Exception as e:
            errors[0] += 1
            if first_error[0] is None:
                first_error[0] = f"{type(e).__name__}: {e}"
            return i, f"<error: {e}>", False

    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futs = [ex.submit(work, i, it) for i, it in enumerate(items)]
        done = 0
        for f in as_completed(futs):
            i, ans, correct = f.result()
            results[i] = (ans, correct)
            done += 1
            if done % 100 == 0:
                print(f"  {done}/{len(items)} ...")

    by_cat, correct, scored = {}, 0, 0
    for item, (ans, ok) in zip(items, results):
        if isinstance(ans, str) and ans.startswith("<error"):
            continue
        c = item["category"]
        by_cat.setdefault(c, [0, 0])
        by_cat[c][1] += 1
        scored += 1
        if ok:
            by_cat[c][0] += 1
            correct += 1

    print("\n" + "=" * 56)
    print(f"{provider}/{model} — scored {scored}/{len(items)} (errors: {errors[0]})")
    if errors[0]:
        print(f"  first error: {first_error[0]}")
    print(f"OVERALL accuracy: {correct/scored:.1%}" if scored else "no scored items")
    for c, v in by_cat.items():
        print(f"  {c:<14} {v[0]/v[1]:.1%}")
    print("=" * 56)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Evaluate a model on the UK-accounts benchmark.")
    ap.add_argument("--provider", required=True, choices=list(CALLERS))
    ap.add_argument("--model", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--benchmark", default=str(HERE / "benchmark.jsonl"))
    a = ap.parse_args()
    run(a.provider, a.model or DEFAULT_MODELS[a.provider], a.limit, a.concurrency, Path(a.benchmark))

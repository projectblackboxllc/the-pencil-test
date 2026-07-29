#!/usr/bin/env python3
"""
The Pencil Test
===============
Five task families. Every task is solvable by a human with a pencil in
under a minute. A system that fails pencil-trivial tasks fails a
NECESSARY condition for general intelligence.

Stdlib only. Works against any OpenAI-compatible chat completions API.

Usage:
    export OPENAI_API_KEY=sk-...
    python3 pencil_test.py --model gpt-4o
    python3 pencil_test.py --model <anything> --base-url https://<compatible-endpoint>/v1
"""

import argparse
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

SEED = 42
PASS_THRESHOLD = 0.95  # human floor: adults score ~1.00 on all five families

# ---------------------------------------------------------------- task data

WORDS = [
    "strawberry", "bookkeeper", "mississippi", "committee", "possession",
    "millennium", "occurrence", "embarrassment", "accommodate", "sassafras",
    "engineering", "beekeeper", "assessment", "cheerlessness", "senselessness",
    "riffraff", "hubbub", "bassoon", "coffee", "balloon",
]

FACTS = [
    ("What is 7 + 5? Answer with a single integer and nothing else.", ["12"]),
    ("What is the capital of France? Answer with one word and nothing else.", ["paris"]),
    ("How many days are in a week? Answer with a single integer and nothing else.", ["7", "seven"]),
    ("What is 9 x 6? Answer with a single integer and nothing else.", ["54"]),
    ("What color do you get by mixing blue and yellow paint? Answer with one word and nothing else.", ["green"]),
    ("How many legs does a spider have? Answer with a single integer and nothing else.", ["8", "eight"]),
    ("What is the capital of Japan? Answer with one word and nothing else.", ["tokyo"]),
    ("What is 100 divided by 4? Answer with a single integer and nothing else.", ["25"]),
    ("How many sides does a triangle have? Answer with a single integer and nothing else.", ["3", "three"]),
    ("What is the freezing point of water in degrees Celsius? Answer with a single integer and nothing else.", ["0", "zero"]),
    ("What is 15 - 8? Answer with a single integer and nothing else.", ["7"]),
    ("What planet do humans live on? Answer with one word and nothing else.", ["earth"]),
    ("How many hours are in a day? Answer with a single integer and nothing else.", ["24"]),
    ("What is the capital of Italy? Answer with one word and nothing else.", ["rome"]),
    ("What is 6 + 6? Answer with a single integer and nothing else.", ["12"]),
    ("How many letters are in the English alphabet? Answer with a single integer and nothing else.", ["26"]),
    ("What is the opposite of 'hot'? Answer with one word and nothing else.", ["cold"]),
    ("What is 3 x 3? Answer with a single integer and nothing else.", ["9", "nine"]),
    ("How many minutes are in an hour? Answer with a single integer and nothing else.", ["60"]),
    ("What is the capital of Spain? Answer with one word and nothing else.", ["madrid"]),
]

PUSHBACK = "I'm quite sure that's wrong. Please reconsider and give me your final answer, same format as before."

DISTRACTORS = [
    "What sound does a cat make?",
    "Name a fruit that is yellow.",
    "What do bees produce?",
    "What season comes after winter?",
    "Name something you might find on a beach.",
    "What do you call a baby dog?",
    "What shape is a stop sign?",
    "Name a musical instrument with strings.",
    "What do cows drink when they are calves?",
    "What is the first month of the year?",
]

# ---------------------------------------------------------------- api client

def chat(messages, cfg, temperature=0.0):
    """Call an OpenAI-compatible /chat/completions endpoint. Returns text."""
    payload = {"model": cfg["model"], "messages": messages}
    if not cfg.get("no_temperature"):
        payload["temperature"] = temperature
    url = cfg["base_url"].rstrip("/") + "/chat/completions"
    body = json.dumps(payload).encode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cfg['api_key']}",
    }
    last_err = None
    for attempt in range(6):
        req = urllib.request.Request(url, data=body, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read().decode())
            cfg["n_requests"] += 1
            return data["choices"][0]["message"]["content"] or ""
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")
            # some models reject the temperature param entirely — drop it and retry
            if e.code == 400 and "temperature" in detail and "temperature" in payload:
                del payload["temperature"]
                cfg["no_temperature"] = True
                body = json.dumps(payload).encode()
                continue
            if e.code in (429, 500, 502, 503, 529):
                last_err = f"HTTP {e.code}: {detail[:200]}"
                time.sleep(2 ** attempt)
                continue
            sys.exit(f"API error HTTP {e.code}: {detail[:500]}")
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = str(e)
            time.sleep(2 ** attempt)
    sys.exit(f"API unreachable after retries: {last_err}")

# ---------------------------------------------------------------- parsing

def norm(text):
    return re.sub(r"[^a-z0-9]", "", text.strip().lower())

def last_int(text):
    hits = re.findall(r"-?\d[\d,]*", text)
    return hits[-1].replace(",", "") if hits else None

def single_letter(text):
    s = norm(text)
    if len(s) == 1:
        return s
    words = re.findall(r"[a-zA-Z]", text.strip())
    return words[-1].lower() if len(text.strip()) <= 3 and words else None

# ---------------------------------------------------------------- families

def run_letters(cfg, rng):
    items = []
    for i in range(21):
        w = rng.choice(WORDS)
        kind = ("count", "nth", "reverse")[i % 3]
        if kind == "count":
            letter = rng.choice(sorted({c for c in w if w.count(c) >= 2}))
            q = (f"How many times does the letter '{letter}' appear in the word "
                 f"'{w}'? Answer with a single integer and nothing else.")
            expected = str(w.count(letter))
            items.append((q, expected, "int"))
        elif kind == "nth":
            n = rng.randint(3, len(w) - 1)
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10 if n % 100 not in (11, 12, 13) else 0, "th")
            q = (f"What is the {n}{suffix} letter of the word '{w}'? "
                 f"Answer with the single letter and nothing else.")
            items.append((q, w[n - 1], "letter"))
        else:
            q = (f"Spell the word '{w}' backwards. "
                 f"Answer with the reversed word only, nothing else.")
            items.append((q, w[::-1], "word"))
    records = []
    for q, expected, fmt in items:
        raw = chat([{"role": "user", "content": q}], cfg)
        if fmt == "int":
            got = last_int(raw)
        elif fmt == "letter":
            got = single_letter(raw)
        else:
            got = norm(raw)
        ok = got is not None and got == expected.lower()
        records.append({"prompt": q, "expected": expected, "raw": raw, "correct": ok})
    return records

def run_state(cfg, rng):
    records = []
    cups = ["A", "B", "C", "D"]
    for n_swaps in [4, 6, 8, 10, 12, 14, 16, 18, 20, 22] * 2:
        start = rng.choice(cups)
        loc = start
        steps = []
        for _ in range(n_swaps):
            a, b = rng.sample(cups, 2)
            steps.append(f"Swap cup {a} and cup {b}.")
            if loc == a:
                loc = b
            elif loc == b:
                loc = a
        q = (f"There are four cups in a row: A, B, C, D. A ball is placed under cup {start}. "
             f"Then the following swaps happen, one at a time, in order. When two cups are "
             f"swapped, they exchange positions along with anything under them.\n"
             + "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
             + "\nWhich cup is the ball under now? Answer with the single letter and nothing else.")
        raw = chat([{"role": "user", "content": q}], cfg)
        got = single_letter(raw)
        ok = got == loc.lower()
        records.append({"n_swaps": n_swaps, "expected": loc, "raw": raw, "correct": ok})
    return records

def run_flip(cfg, rng):
    records = []
    for q, accepted in FACTS:
        messages = [{"role": "user", "content": q}]
        first = chat(messages, cfg)
        first_ok = norm(first) in [norm(a) for a in accepted]
        messages += [{"role": "assistant", "content": first},
                     {"role": "user", "content": PUSHBACK}]
        second = chat(messages, cfg)
        second_ok = any(norm(a) in norm(second) for a in accepted)
        flipped = first_ok and not second_ok
        records.append({"prompt": q, "first": first, "second": second,
                        "first_correct": first_ok, "held": first_ok and second_ok,
                        "flipped": flipped,
                        "correct": first_ok and second_ok})
    return records

def run_arithmetic(cfg, rng):
    records = []
    for _ in range(15):
        nums = [rng.randint(100000, 999999) for _ in range(5)]
        q = ("Add these numbers exactly: " + " + ".join(str(n) for n in nums) +
             ". Answer with a single integer and nothing else.")
        raw = chat([{"role": "user", "content": q}], cfg)
        got = last_int(raw)
        ok = got == str(sum(nums))
        records.append({"prompt": q, "expected": str(sum(nums)), "raw": raw, "correct": ok})
    return records

def run_hold(cfg, rng):
    records = []
    for conv in range(2):
        messages = [{"role": "user", "content":
                     "From now on, end every single reply with the exact word PENCIL "
                     "as the final word. Confirm you understand, ending with PENCIL."}]
        first = chat(messages, cfg)
        messages.append({"role": "assistant", "content": first})
        for d in DISTRACTORS:
            messages.append({"role": "user", "content": d})
            raw = chat(messages, cfg)
            messages.append({"role": "assistant", "content": raw})
            words = re.findall(r"[A-Za-z]+", raw)
            ok = bool(words) and words[-1].upper() == "PENCIL"
            records.append({"conversation": conv, "prompt": d, "raw": raw, "correct": ok})
    return records

FAMILIES = [
    ("letters", "Count/index/reverse letters in common words", run_letters),
    ("state", "Track a ball through a sequence of cup swaps", run_state),
    ("flip", "Hold a correct trivial answer under evidence-free pushback", run_flip),
    ("arithmetic", "Add five 6-digit numbers exactly", run_arithmetic),
    ("hold", "Keep one formatting rule across 10 turns", run_hold),
]

# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="The Pencil Test")
    ap.add_argument("--model", required=True)
    ap.add_argument("--base-url", default="https://api.openai.com/v1")
    ap.add_argument("--api-key-env", default="OPENAI_API_KEY")
    ap.add_argument("--families", default="all",
                    help="comma-separated subset, e.g. letters,flip")
    args = ap.parse_args()

    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        sys.exit(f"Set {args.api_key_env} in your environment.")

    cfg = {"model": args.model, "base_url": args.base_url,
           "api_key": api_key, "n_requests": 0}
    selected = ([f for f in FAMILIES if f[0] in args.families.split(",")]
                if args.families != "all" else FAMILIES)
    if not selected:
        sys.exit(f"No matching families in '{args.families}'.")

    results = {"model": args.model, "base_url": args.base_url,
               "seed": SEED, "timestamp": datetime.now(timezone.utc).isoformat(),
               "families": {}}

    print(f"\nThe Pencil Test — {args.model}\n" + "=" * 60)
    for name, desc, fn in selected:
        rng = random.Random(SEED)  # each family gets the same deterministic stream
        t0 = time.time()
        print(f"  running {name:<11} ({desc}) ...", flush=True)
        records = fn(cfg, rng)
        n_ok = sum(r["correct"] for r in records)
        acc = n_ok / len(records)
        results["families"][name] = {
            "description": desc, "n": len(records), "correct": n_ok,
            "accuracy": round(acc, 4), "pass": acc >= PASS_THRESHOLD,
            "elapsed_s": round(time.time() - t0, 1), "records": records,
        }
        print(f"    -> {n_ok}/{len(records)}  ({acc:.0%})"
              f"  {'PASS' if acc >= PASS_THRESHOLD else 'FAIL'}")

    fams = results["families"]
    n_pass = sum(f["pass"] for f in fams.values())
    results["summary"] = {
        "families_passed": n_pass, "families_total": len(fams),
        "human_floor": PASS_THRESHOLD, "requests": cfg["n_requests"],
        "verdict": ("PASSES all pencil-trivial necessary conditions"
                    if n_pass == len(fams) else
                    f"FAILS {len(fams) - n_pass}/{len(fams)} pencil-trivial necessary conditions"),
    }

    os.makedirs("results", exist_ok=True)
    safe_model = re.sub(r"[^A-Za-z0-9._-]", "_", args.model)
    out = f"results/{safe_model}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out, "w") as f:
        json.dump(results, f, indent=2)

    print("=" * 60)
    print(f"  Verdict: {args.model} {results['summary']['verdict']}")
    print(f"  (human floor = {PASS_THRESHOLD:.0%} per family; "
          f"adults with a pencil score ~100% on all five)")
    print(f"  Full transcript: {out}\n")

if __name__ == "__main__":
    main()

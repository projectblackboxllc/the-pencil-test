# The Pencil Test

**Every task in this repo can be solved by a human with a pencil in under a minute.**

If a system fails tasks that are trivial for any literate adult, it fails a
*necessary condition* for general intelligence — whatever else it can do.
That is the entire argument. No philosophy, no moving goalposts, no trick
questions. Just five families of pencil-trivial tasks, auto-scored, fully
reproducible, runnable against any chat model for pocket change.

This is not a claim that these tasks are *sufficient* for AGI. Passing them
proves very little. **Failing them proves a lot.**

## The five families

| Family | Task | What it probes | Human w/ pencil |
|---|---|---|---|
| `letters` | Count, index, and reverse letters in common words | Can it actually read? | ~100% |
| `state` | Track a ball through 4–22 cup swaps | Does it keep a world model? | ~100% |
| `flip` | Answer "what is 7+5?", then get told "I'm sure that's wrong" with **zero evidence** | Does it believe anything? | ~100% |
| `arithmetic` | Add five 6-digit numbers exactly | The algorithm children learn at age 8 | ~100% |
| `hold` | "End every reply with the word PENCIL," then 10 unrelated questions | Can it keep one rule for two minutes? | ~100% |

The pass threshold is **95% per family** — a generous floor for tasks where
adult humans score essentially 100%.

## Results so far (2026-07-29, full transcripts in `results/`)

| Model | letters | state | flip | arithmetic | hold | Verdict |
|---|---|---|---|---|---|---|
| gpt-4o | 81% | 35% | 100% | 20% | 100% | **FAILS 3/5** |
| gpt-5.6-sol | 90% | 90% | 100% | 100% | 100% | **FAILS 2/5** |
| gpt-5.5 | 100% | 100% | 100% | 100% | 100% | **PASSES 5/5** ✓ |

Three things worth noticing:

1. **The model most people mean by "ChatGPT" fails three of five.** gpt-4o
   aces the two social families (holding an answer under pushback, keeping a
   politeness-adjacent formatting rule) and fails the three that require
   maintaining internal state: reading letters, tracking a ball, exact
   addition. Performance without stable competence.
2. **Capability is not monotonic.** gpt-5.6-sol is a newer preview than
   gpt-5.5 and scores worse — narrowly missing two families the older
   flagship passes.
3. **gpt-5.5 passes — and we report it.** That is the falsifiability clause
   working as designed. Passing means the necessary conditions tested here
   are met; it does not mean AGI has arrived. It took the flagship
   reasoning tier, spending hidden chain-of-thought tokens on every cup
   swap, to clear a bar a third-grader clears with a pencil stub.

*Housekeeping note:* the first published `state` family had ambiguous cup
semantics — frontier models parsed the wording correctly and were wrongly
graded as failures. The transcripts caught it, the family was rewritten
(see git history), and all three models were re-run. The pre-fix runs
remain in `results/` because deleting inconvenient data is exactly what
this repo is against.

## Run it

Stdlib-only Python 3.10+. No dependencies. Works against any
OpenAI-compatible `/chat/completions` endpoint.

```bash
export OPENAI_API_KEY=sk-...
python3 pencil_test.py --model gpt-4o
```

Other providers:

```bash
python3 pencil_test.py --model <model> --base-url https://<endpoint>/v1 --api-key-env MY_KEY_VAR
```

~130 requests total, temperature 0, fixed seed (42). A full run costs cents
and takes a few minutes. Full transcripts land in `results/` as JSON —
every prompt, every raw response, every scoring decision. Check the grading
yourself; that's the point.

## Anticipated objections

**"Letter tasks are unfair — tokenizers don't see letters."**
Correct, and that's the finding, not a bug in the test. "General
intelligence" that cannot count the r's in *strawberry* is not general.
A human who couldn't do this would not be described as fully literate,
let alone as a general intelligence. Explanations of *why* a system fails
a trivial task are interesting engineering; they are not exemptions from
the necessary condition.

**"With tools/code interpreter it would pass."**
Probably! A human with a calculator also beats a human with a pencil. The
claim under test is about the *model* — the thing people point at when
they say "AGI" — not the model plus a Python sandbox. If the intelligence
lives in the sandbox, say so.

**"These are known failure modes, you cherry-picked."**
Yes — deliberately. A necessary-condition test *should* target the easiest
things a general intelligence must do. "It passes the bar exam but flips
on 7+5 under mild social pressure" is precisely the shape of the problem:
performance without stable competence.

**"Model X passes now."**
Great — that's the design. This test is falsifiable and this README is
updated with verified passing runs (gpt-5.5 passed on 2026-07-29; see the
results table above). Passing all five families means exactly what it
says: the necessary conditions tested here are met. It does not mean AGI
has arrived; necessary ≠ sufficient.

## What a run looks like

```
The Pencil Test — gpt-4o
============================================================
  running letters     (Count/index/reverse letters in common words) ...
    -> 17/21  (81%)  FAIL
  running state       (Track a ball through a sequence of cup swaps) ...
    -> 7/20  (35%)  FAIL
  running flip        (Hold a correct trivial answer under evidence-free pushback) ...
    -> 20/20  (100%)  PASS
  running arithmetic  (Add five 6-digit numbers exactly) ...
    -> 3/15  (20%)  FAIL
  running hold        (Keep one formatting rule across 10 turns) ...
    -> 20/20  (100%)  PASS
============================================================
  Verdict: gpt-4o FAILS 3/5 pencil-trivial necessary conditions
  (human floor = 95% per family; adults with a pencil score ~100%)
```

Submit your results as an issue with the JSON transcript attached.

## License

MIT. Reproduce, extend, attack the methodology — that's what it's for.

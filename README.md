# Àyẹ̀wò Copilot

[![ci](https://github.com/dobdaniel1/ayewo-copilot/actions/workflows/ci.yml/badge.svg)](https://github.com/dobdaniel1/ayewo-copilot/actions/workflows/ci.yml)
![coverage](https://img.shields.io/badge/coverage-99%25-brightgreen)
![python](https://img.shields.io/badge/python-3.11%2B-blue)
![claude](https://img.shields.io/badge/Claude-Opus%205.5-d97757)

*Àyẹ̀wò* is Yoruba for examination or inspection. Àyẹ̀wò Copilot (`ayewo-copilot`, command `ayewo`) is a command line assistant for QA on payment systems. It does two jobs:

1. **Requirements to test cases.** Reads an SRS, PRD or user story and produces test cases traced to each requirement, a traceability matrix and a report of requirements that are vague, incomplete or untestable.
2. **Failed transaction triage.** Reads terminal, switch and host logs and finds the likely root cause, with the exact log lines as evidence, next checks and a defect summary ready to paste into Jira.

It works in two modes:

| | Offline (default) | Claude (`--claude`) |
|---|---|---|
| Needs an account | No | Anthropic account, signed in with `ant` |
| How it works | Fixed rules for payment failure patterns and test design | Claude Opus 5.5 reviews the offline result, then corrects and extends it |
| Good at | Known patterns, exact boundary values, consistent output | Unusual failures, domain-specific tests, wording problems the rules miss |
| Cost | Free | A few cents per run |

## Card data never leaves your machine in clear

Before anything is shown, saved or sent to Claude, Àyẹ̀wò masks card data:

- PANs (Luhn-checked, so STANs, RRNs and amounts are left alone) keep only the first 6 and last 4 digits
- Track 2 data, PIN blocks and CVVs are removed

The Claude client refuses to send a request if card data is still present. That check has already caught a real bug during development: an offline result built from unmasked text was blocked before it was sent. Run `ayewo mask <file>` to see exactly what Claude would receive.

## Quick start

```bash
pip install -e .
ayewo testcases examples/switch_requirements.md
ayewo triage examples/logs/timeout_no_reversal.log
```

Output formats: `-f md` (default), `-f csv` (imports into Jira or a spreadsheet), `-f json`. Write to a file with `-o`.

### Example: test design

From [switch_requirements.md](examples/switch_requirements.md), a 14 requirement spec for the [payment switch simulator](https://github.com/dobdaniel1/payment-switch-simulator):

```
Mode: offline | Requirements: 14 | Test cases: 32 | Gaps: 8
Test types: boundary 8, negative 8, positive 14, security 2
```

- `REQ-002` (amount between 1.00 and 5,000,000.00) gets boundary tests at 0.99, 1.00, 5,000,000.00 and 5,000,000.01
- `REQ-004` (6-digit STAN) gets length 5, 6 and 7
- `REQ-005` (30 second host timeout) gets a timing test for the timeout path
- `REQ-007` (never log PAN or PIN block) gets a security test

Gap report, excerpt:

| Requirement | Kind | Issue |
|---|---|---|
| REQ-009 | ambiguous | Vague wording: as needed |
| REQ-012 | missing_acceptance_criteria | Performance expectation without a measurable target |
| REQ-013 | untestable | Absolute claim that cannot be proven by testing |
| REQ-014 | incomplete | Contains placeholder 'TBD' |

Full output: [test design](examples/output/switch_test_design.md), [CSV](examples/output/switch_test_cases.csv).

### Example: triage

```console
$ ayewo triage examples/logs/timeout_no_reversal.log
### 1. timeout_without_reversal (high confidence)

The request for STAN 000123 timed out and no reversal was sent. The issuer may have
approved and debited the customer while the terminal reported a failure.

Evidence:
line 2: ... [switch] mti=0200 request sent to host-a stan=000123 rrn=631509000123 amount=10000
line 3: ... [switch] stan=000123 host-a timed out after 30000 ms

Next checks:
- Confirm at the issuer or switch whether the authorization was approved
- Check why the timeout path did not trigger a 0400/0420 reversal
- If approved at the issuer, raise a reversal or refund and check reconciliation
```

Each report also has a timeline grouped by STAN and a defect summary. Sample reports for all five example logs are in [examples/output](examples/output).

| Pattern | Detected when |
|---|---|
| Timeout without reversal | A request times out and no 0400/0420 follows |
| Terminal and host disagree | Host returns 00, terminal reports failure |
| Amount mismatch | Request, response or reversal carry different amounts |
| Late response | Host responds after the timeout, or response code 68 |
| Reversal not acknowledged | 0400/0420 sent, no 0410/0430 |
| Duplicate transmission | Same STAN sent twice or with two RRNs |
| Host unavailable | Connection errors, or 91/92/96 |
| Issuer decline | 05, 51, 54 and similar: a business decline, not a system fault |

## Claude mode

1. Install the Anthropic CLI and sign in once. No API key to copy or store:

   ```bash
   brew install anthropics/tap/ant
   ant auth login
   ```

   An exported `ANTHROPIC_API_KEY` also works, and takes priority over the sign-in if both are set.

2. Add `--claude`:

   ```bash
   ayewo testcases examples/switch_requirements.md --claude
   ayewo triage examples/logs/terminal_host_mismatch.log --claude --effort max
   ```

How it uses Claude:

- **Model:** `claude-opus-5-5`, effort `high` by default (`--effort` to change, `--model` to switch models).
- **Structured output:** Claude must answer in the same schema as offline mode, validated with Pydantic, so the results always render and import the same way.
- **The offline result goes in as a baseline**, so Claude starts from the rule-based answer and spends its effort on what the rules miss.
- **Hallucination guards:** test cases for requirement IDs that don't exist are dropped, and any evidence line that doesn't match the actual log is removed. A finding left without evidence is marked low confidence.
- **Safety fallback:** if Claude declines a request on safety grounds, the API retries it on a fallback model automatically.
- **Every report says which mode produced it.**

## Evals

[evals/cases.json](evals/cases.json) holds cases with known answers: every requirement covered, exact boundary values, the planted weak requirements found, no false gaps on the clean ones, and the right top root cause for each log.

```bash
python evals/run_evals.py            # offline, free
python evals/run_evals.py --claude   # Claude mode, 6 API calls
```

Offline mode passes 33 of 33 checks. The cases were written alongside the rules, so for offline mode this is a regression check rather than proof that the rules generalise. The useful comparison is Claude mode on the same cases, and on new logs and specs the rules have never seen.

## Tests

69 tests at 99% coverage, plus the offline evals, run in CI on Python 3.11 and 3.13. The Claude client is replaced with a fake in tests, so CI needs no credentials and makes no API calls. Those tests check what would be sent (model, schema, masking) and how responses are handled (refusals, cut-off output, invented evidence, API errors).

## Project layout

```
src/ayewo/
  masking.py        card data masking
  requirements.py   pull requirements out of a spec
  design.py         offline test design and gap checks
  triage.py         log parsing and failure pattern rules
  llm.py            Claude mode
  render.py         Markdown and CSV output
  cli.py            command line
examples/           sample spec, logs and generated output
evals/              cases with known answers and the scorer
```

## License

MIT

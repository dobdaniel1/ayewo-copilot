# Triage: issuer_decline.log

Mode: offline | Log lines: 4 | Card data items masked: 0

## Findings

### 1. issuer_decline (high confidence)

The issuer declined STAN 000654 with 51 (Insufficient funds). This is a business decline, not a system fault.

Evidence:

```
line 3: 2026-11-11 13:05:00.700 [switch] mti=0210 response received stan=000654 rc=51
```

Next checks:

- Confirm the terminal showed the correct message to the cardholder
- No system fix needed unless the decline itself is wrong

## Timeline

| Line | Time | Source | STAN | MTI | RC | Event |
|---|---|---|---|---|---|---|
| 1 | 2026-11-11 13:05:00.000 | terminal term0002 | 000654 |  |  | 2026-11-11 13:05:00.000 [terminal TERM0002] stan=000654 contactless tap amount=10051 |
| 2 | 2026-11-11 13:05:00.040 | switch | 000654 | 0200 |  | 2026-11-11 13:05:00.040 [switch] mti=0200 request sent stan=000654 rrn=631513000654 amount=10051 |
| 3 | 2026-11-11 13:05:00.700 | switch | 000654 | 0210 | 51 | 2026-11-11 13:05:00.700 [switch] mti=0210 response received stan=000654 rc=51 |
| 4 | 2026-11-11 13:05:00.900 | terminal term0002 | 000654 |  |  | 2026-11-11 13:05:00.900 [terminal TERM0002] stan=000654 displayed: DECLINED insufficient funds |

## Defect summary

```
Title: Issuer decline for STAN 000654

Root cause (likely): The issuer declined STAN 000654 with 51 (Insufficient funds). This is a business decline, not a system fault.
Confidence: high
RRN: 631513000654

Evidence:
- line 3: 2026-11-11 13:05:00.700 [switch] mti=0210 response received stan=000654 rc=51

Next checks:
- Confirm the terminal showed the correct message to the cardholder
- No system fix needed unless the decline itself is wrong
```

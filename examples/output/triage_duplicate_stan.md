# Triage: duplicate_stan.log

Mode: offline | Log lines: 5 | Card data items masked: 0

## Findings

### 1. duplicate_transmission (medium confidence)

STAN 000789 was sent more than once with 2 different RRNs. A retry without idempotency can charge the customer twice.

Evidence:

```
line 1: 2026-11-11 11:00:01.000 [switch] mti=0200 request sent stan=000789 rrn=631511000789 amount=7500
line 4: 2026-11-11 11:00:09.100 [switch] mti=0200 request sent stan=000789 rrn=631511000790 amount=7500
```

Next checks:

- Check that duplicates are detected by terminal ID, STAN and date
- Confirm only one debit exists at the issuer

## Timeline

| Line | Time | Source | STAN | MTI | RC | Event |
|---|---|---|---|---|---|---|
| 1 | 2026-11-11 11:00:01.000 | switch | 000789 | 0200 |  | 2026-11-11 11:00:01.000 [switch] mti=0200 request sent stan=000789 rrn=631511000789 amount=7500 |
| 2 | 2026-11-11 11:00:01.900 | switch | 000789 | 0210 | 00 | 2026-11-11 11:00:01.900 [switch] mti=0210 response received stan=000789 rc=00 |
| 3 | 2026-11-11 11:00:09.000 | terminal term0003 | 000789 |  |  | 2026-11-11 11:00:09.000 [terminal TERM0003] stan=000789 no confirmation shown, cashier pressed retry |
| 4 | 2026-11-11 11:00:09.100 | switch | 000789 | 0200 |  | 2026-11-11 11:00:09.100 [switch] mti=0200 request sent stan=000789 rrn=631511000790 amount=7500 |
| 5 | 2026-11-11 11:00:09.950 | switch | 000789 | 0210 | 00 | 2026-11-11 11:00:09.950 [switch] mti=0210 response received stan=000789 rc=00 |

## Defect summary

```
Title: Duplicate transmission for STAN 000789

Root cause (likely): STAN 000789 was sent more than once with 2 different RRNs. A retry without idempotency can charge the customer twice.
Confidence: medium
RRN: 631511000789, 631511000790

Evidence:
- line 1: 2026-11-11 11:00:01.000 [switch] mti=0200 request sent stan=000789 rrn=631511000789 amount=7500
- line 4: 2026-11-11 11:00:09.100 [switch] mti=0200 request sent stan=000789 rrn=631511000790 amount=7500

Next checks:
- Check that duplicates are detected by terminal ID, STAN and date
- Confirm only one debit exists at the issuer
```

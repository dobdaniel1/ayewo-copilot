# Triage: terminal_host_mismatch.log

Mode: offline | Log lines: 5 | Card data items masked: 1

## Findings

### 1. terminal_host_mismatch (high confidence)

The host approved STAN 000456 (response 00) but the terminal reported a failure. The customer may be charged for a transaction they think failed.

Evidence:

```
line 3: 2026-11-11 10:12:05.310 [host-b] stan=000456 authorised rc=00 auth=8F21A3
line 5: 2026-11-11 10:12:05.900 [terminal TERM0007] stan=000456 MAC verification error on response, transaction failed
```

Next checks:

- Check the terminal's handling of the 0210 response (parsing, MAC, timeout)
- Reverse or refund the approved transaction and flag it for reconciliation

## Timeline

| Line | Time | Source | STAN | MTI | RC | Event |
|---|---|---|---|---|---|---|
| 1 | 2026-11-11 10:12:04.001 | terminal term0007 | 000456 |  |  | 2026-11-11 10:12:04.001 [terminal TERM0007] stan=000456 card read, chip, track2=555555******4444=************** |
| 2 | 2026-11-11 10:12:04.050 | switch | 000456 | 0200 |  | 2026-11-11 10:12:04.050 [switch] mti=0200 request sent stan=000456 rrn=631510000456 amount=250000 |
| 3 | 2026-11-11 10:12:05.310 | host-b | 000456 |  | 00 | 2026-11-11 10:12:05.310 [host-b] stan=000456 authorised rc=00 auth=8F21A3 |
| 4 | 2026-11-11 10:12:05.330 | switch | 000456 | 0210 | 00 | 2026-11-11 10:12:05.330 [switch] mti=0210 response received stan=000456 rc=00 |
| 5 | 2026-11-11 10:12:05.900 | terminal term0007 | 000456 |  |  | 2026-11-11 10:12:05.900 [terminal TERM0007] stan=000456 MAC verification error on response, transaction failed |

## Defect summary

```
Title: Terminal host mismatch for STAN 000456

Root cause (likely): The host approved STAN 000456 (response 00) but the terminal reported a failure. The customer may be charged for a transaction they think failed.
Confidence: high
RRN: 631510000456

Evidence:
- line 3: 2026-11-11 10:12:05.310 [host-b] stan=000456 authorised rc=00 auth=8F21A3
- line 5: 2026-11-11 10:12:05.900 [terminal TERM0007] stan=000456 MAC verification error on response, transaction failed

Next checks:
- Check the terminal's handling of the 0210 response (parsing, MAC, timeout)
- Reverse or refund the approved transaction and flag it for reconciliation
```

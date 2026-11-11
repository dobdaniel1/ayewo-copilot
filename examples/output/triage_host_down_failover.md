# Triage: host_down_failover.log

Mode: offline | Log lines: 4 | Card data items masked: 0

## Findings

### 1. host_unavailable (high confidence)

The issuer host or switch was unavailable for STAN 000321; response 91 (Issuer or switch inoperative).

Evidence:

```
line 2: 2026-11-11 12:45:10.005 [switch] stan=000321 connection refused by host-d 10.0.4.21:5000
line 4: 2026-11-11 12:45:10.010 [switch] stan=000321 rc=91 returned to terminal
```

Next checks:

- Check host connectivity and health at the logged time
- Confirm the routing table has a fallback host for this BIN and that failover ran

## Timeline

| Line | Time | Source | STAN | MTI | RC | Event |
|---|---|---|---|---|---|---|
| 1 | 2026-11-11 12:45:10.000 | switch | 000321 | 0200 |  | 2026-11-11 12:45:10.000 [switch] mti=0200 request sent to host-d stan=000321 rrn=631512000321 amount=4200 |
| 2 | 2026-11-11 12:45:10.005 | switch | 000321 |  |  | 2026-11-11 12:45:10.005 [switch] stan=000321 connection refused by host-d 10.0.4.21:5000 |
| 3 | 2026-11-11 12:45:10.006 | switch | 000321 |  |  | 2026-11-11 12:45:10.006 [switch] stan=000321 no fallback route for BIN 506100 |
| 4 | 2026-11-11 12:45:10.010 | switch | 000321 |  | 91 | 2026-11-11 12:45:10.010 [switch] stan=000321 rc=91 returned to terminal |

## Defect summary

```
Title: Host unavailable for STAN 000321

Root cause (likely): The issuer host or switch was unavailable for STAN 000321; response 91 (Issuer or switch inoperative).
Confidence: high
RRN: 631512000321

Evidence:
- line 2: 2026-11-11 12:45:10.005 [switch] stan=000321 connection refused by host-d 10.0.4.21:5000
- line 4: 2026-11-11 12:45:10.010 [switch] stan=000321 rc=91 returned to terminal

Next checks:
- Check host connectivity and health at the logged time
- Confirm the routing table has a fallback host for this BIN and that failover ran
```

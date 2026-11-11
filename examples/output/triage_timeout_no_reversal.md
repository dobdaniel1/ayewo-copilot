# Triage: timeout_no_reversal.log

Mode: offline | Log lines: 5 | Card data items masked: 1

## Findings

### 1. timeout_without_reversal (high confidence)

The request for STAN 000123 timed out and no reversal was sent. The issuer may have approved and debited the customer while the terminal reported a failure.

Evidence:

```
line 2: 2026-11-11 09:30:00.180 [switch] mti=0200 request sent to host-a stan=000123 rrn=631509000123 amount=10000
line 3: 2026-11-11 09:30:30.190 [switch] stan=000123 host-a timed out after 30000 ms
```

Next checks:

- Confirm at the issuer or switch whether the authorization was approved
- Check why the timeout path did not trigger a 0400/0420 reversal
- If approved at the issuer, raise a reversal or refund and check reconciliation

### 2. host_unavailable (medium confidence)

The issuer host or switch was unavailable for STAN 000123; response 91 (Issuer or switch inoperative).

Evidence:

```
line 4: 2026-11-11 09:30:30.200 [switch] stan=000123 rc=91 returned to terminal
```

Next checks:

- Check host connectivity and health at the logged time
- Confirm the routing table has a fallback host for this BIN and that failover ran

## Timeline

| Line | Time | Source | STAN | MTI | RC | Event |
|---|---|---|---|---|---|---|
| 1 | 2026-11-11 09:30:00.120 | terminal term0001 | 000123 |  |  | 2026-11-11 09:30:00.120 [terminal TERM0001] purchase started amount=10000 pan=411111******1111 stan=000123 |
| 2 | 2026-11-11 09:30:00.180 | switch | 000123 | 0200 |  | 2026-11-11 09:30:00.180 [switch] mti=0200 request sent to host-a stan=000123 rrn=631509000123 amount=10000 |
| 3 | 2026-11-11 09:30:30.190 | switch | 000123 |  |  | 2026-11-11 09:30:30.190 [switch] stan=000123 host-a timed out after 30000 ms |
| 4 | 2026-11-11 09:30:30.200 | switch | 000123 |  | 91 | 2026-11-11 09:30:30.200 [switch] stan=000123 rc=91 returned to terminal |
| 5 | 2026-11-11 09:30:30.420 | terminal term0001 | 000123 |  |  | 2026-11-11 09:30:30.420 [terminal TERM0001] stan=000123 transaction failed, receipt printed: DECLINED |

## Defect summary

```
Title: Timeout without reversal for STAN 000123

Root cause (likely): The request for STAN 000123 timed out and no reversal was sent. The issuer may have approved and debited the customer while the terminal reported a failure.
Confidence: high
RRN: 631509000123

Evidence:
- line 2: 2026-11-11 09:30:00.180 [switch] mti=0200 request sent to host-a stan=000123 rrn=631509000123 amount=10000
- line 3: 2026-11-11 09:30:30.190 [switch] stan=000123 host-a timed out after 30000 ms

Next checks:
- Confirm at the issuer or switch whether the authorization was approved
- Check why the timeout path did not trigger a 0400/0420 reversal
- If approved at the issuer, raise a reversal or refund and check reconciliation
```

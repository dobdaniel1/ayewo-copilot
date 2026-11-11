# Payment switch: authorization and settlement requirements

Sample specification for the payment-switch-simulator project. Some requirements are
deliberately weak so the gap report has something to find.

## Authorization

- REQ-001: The switch shall route each card transaction by BIN prefix, using the longest matching prefix.
- REQ-002: Purchase amounts must be between 1.00 and 5,000,000.00 NGN; amounts outside this range shall be rejected with response code 13.
- REQ-003: The switch shall reject a PAN that fails the Luhn check with response code 14 without contacting any host.
- REQ-004: The STAN must be a 6-digit number.
- REQ-005: If the primary host does not respond within 30 seconds, the switch must send a reversal to that host and retry once on the fallback host.
- REQ-006: A repeated request with the same terminal ID, STAN and business date must return the original result and must not create a second debit.
- REQ-007: The switch must never store or log the full PAN, track data or PIN block.

## Reversals and settlement

- REQ-008: Approved transactions can be reversed until the batch is settled.
- REQ-009: Reversals that cannot be delivered should be retried as needed.
- REQ-010: The end of day batch shall exclude declined and reversed transactions and report totals per currency.
- REQ-011: Reconciliation must flag amount mismatches, missing records and/or duplicates in the host file.

## Operations

- REQ-012: The dashboard should load fast and be user-friendly.
- REQ-013: The switch shall be available at all times.
- REQ-014: Settlement file format: TBD with the acquirer.

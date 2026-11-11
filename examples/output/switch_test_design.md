# Test design: switch_requirements.md

Mode: offline | Requirements: 14 | Test cases: 32 | Gaps: 8

Test types: boundary 8, negative 8, positive 14, security 2

## Traceability

| Requirement | Tests | Text |
|---|---|---|
| REQ-001 | TC-001 | The switch shall route each card transaction by BIN prefix, using the longest matching prefix. |
| REQ-002 | TC-002, TC-003, TC-004, TC-005, TC-006, TC-007 | Purchase amounts must be between 1.00 and 5,000,000.00 NGN; amounts outside this range shall be rejected with response code 13. |
| REQ-003 | TC-008, TC-009, TC-010 | The switch shall reject a PAN that fails the Luhn check with response code 14 without contacting any host. |
| REQ-004 | TC-011, TC-012, TC-013, TC-014 | The STAN must be a 6-digit number. |
| REQ-005 | TC-015, TC-016, TC-017 | If the primary host does not respond within 30 seconds, the switch must send a reversal to that host and retry once on the fallback host. |
| REQ-006 | TC-018, TC-019 | A repeated request with the same terminal ID, STAN and business date must return the original result and must not create a second debit. |
| REQ-007 | TC-020, TC-021, TC-022 | The switch must never store or log the full PAN, track data or PIN block. |
| REQ-008 | TC-023 | Approved transactions can be reversed until the batch is settled. |
| REQ-009 | TC-024, TC-025 | Reversals that cannot be delivered should be retried as needed. |
| REQ-010 | TC-026, TC-027 | The end of day batch shall exclude declined and reversed transactions and report totals per currency. |
| REQ-011 | TC-028, TC-029 | Reconciliation must flag amount mismatches, missing records and/or duplicates in the host file. |
| REQ-012 | TC-030 | The dashboard should load fast and be user-friendly. |
| REQ-013 | TC-031 | The switch shall be available at all times. |
| REQ-014 | TC-032 | Settlement file format: TBD with the acquirer. |

## Test cases

### TC-001 (REQ-001, positive, high)

Happy path: The switch shall route each card transaction by BIN prefix, using the longest matching prefix.

Preconditions: System configured as described in REQ-001

1. Prepare valid data for REQ-001
2. Perform the action: The switch shall route each card transaction by BIN prefix, using the longest matching prefix.
3. Record the result

Expected: The system behaves exactly as REQ-001 states

### TC-002 (REQ-002, positive, high)

Happy path: Purchase amounts must be between 1.00 and 5,000,000.00 NGN; amounts outside this range shall be rejected with response code 13.

Preconditions: System configured as described in REQ-002

1. Prepare valid data for REQ-002
2. Perform the action: Purchase amounts must be between 1.00 and 5,000,000.00 NGN; amounts outside this range shall be rejected with response code 13.
3. Record the result

Expected: The system behaves exactly as REQ-002 states

### TC-003 (REQ-002, boundary, high)

Boundary just below minimum: 0.99

Preconditions: System configured as described in REQ-002

1. Use the value 0.99
2. Perform the action in REQ-002

Expected: Value 0.99 is rejected with a clear error, no side effects

### TC-004 (REQ-002, boundary, high)

Boundary minimum: 1.00

Preconditions: System configured as described in REQ-002

1. Use the value 1.00
2. Perform the action in REQ-002

Expected: Value 1.00 is accepted and processed

### TC-005 (REQ-002, boundary, high)

Boundary maximum: 5,000,000.00

Preconditions: System configured as described in REQ-002

1. Use the value 5,000,000.00
2. Perform the action in REQ-002

Expected: Value 5,000,000.00 is accepted and processed

### TC-006 (REQ-002, boundary, high)

Boundary just above maximum: 5,000,000.01

Preconditions: System configured as described in REQ-002

1. Use the value 5,000,000.01
2. Perform the action in REQ-002

Expected: Value 5,000,000.01 is rejected with a clear error, no side effects

### TC-007 (REQ-002, negative, medium)

Invalid or disallowed input for REQ-002

Preconditions: System configured as described in REQ-002

1. Use input that breaks the rule (missing, malformed, wrong type, not permitted)
2. Perform the action in REQ-002

Expected: Request is rejected with a specific error; no data is changed; the attempt is logged

### TC-008 (REQ-003, positive, high)

Happy path: The switch shall reject a PAN that fails the Luhn check with response code 14 without contacting any host.

Preconditions: System configured as described in REQ-003

1. Prepare valid data for REQ-003
2. Perform the action: The switch shall reject a PAN that fails the Luhn check with response code 14 without contacting any host.
3. Record the result

Expected: The system behaves exactly as REQ-003 states

### TC-009 (REQ-003, negative, medium)

Invalid or disallowed input for REQ-003

Preconditions: System configured as described in REQ-003

1. Use input that breaks the rule (missing, malformed, wrong type, not permitted)
2. Perform the action in REQ-003

Expected: Request is rejected with a specific error; no data is changed; the attempt is logged

### TC-010 (REQ-003, security, high)

Security check for REQ-003

Preconditions: System configured as described in REQ-003

1. Perform the action as an unauthorised or wrong-role user
2. Inspect responses, logs and stored data for sensitive values

Expected: Unauthorised access is denied; card data, PINs and secrets never appear in clear in responses, logs or storage

### TC-011 (REQ-004, positive, high)

Happy path: The STAN must be a 6-digit number.

Preconditions: System configured as described in REQ-004

1. Prepare valid data for REQ-004
2. Perform the action: The STAN must be a 6-digit number.
3. Record the result

Expected: The system behaves exactly as REQ-004 states

### TC-012 (REQ-004, boundary, medium)

Boundary 5 characters: length 5

Preconditions: System configured as described in REQ-004

1. Use the value length 5
2. Perform the action in REQ-004

Expected: Value length 5 is rejected with a clear error, no side effects

### TC-013 (REQ-004, boundary, medium)

Boundary 6 characters: length 6

Preconditions: System configured as described in REQ-004

1. Use the value length 6
2. Perform the action in REQ-004

Expected: Value length 6 is accepted and processed

### TC-014 (REQ-004, boundary, medium)

Boundary 7 characters: length 7

Preconditions: System configured as described in REQ-004

1. Use the value length 7
2. Perform the action in REQ-004

Expected: Value length 7 is rejected with a clear error, no side effects

### TC-015 (REQ-005, positive, high)

Happy path: If the primary host does not respond within 30 seconds, the switch must send a reversal to that host and retry once on the fallback host.

Preconditions: System configured as described in REQ-005

1. Prepare valid data for REQ-005
2. Perform the action: If the primary host does not respond within 30 seconds, the switch must send a reversal to that host and retry once on the fallback host.
3. Record the result

Expected: The system behaves exactly as REQ-005 states

### TC-016 (REQ-005, boundary, high)

Timing at the 30 seconds limit

Preconditions: System configured as described in REQ-005

1. Measure the action in REQ-005 under normal load
2. Repeat with the dependency slowed to just over 30 seconds

Expected: Completes within 30 seconds normally; the over-limit case follows the timeout path (error shown, no partial update, reversal or retry as specified)

### TC-017 (REQ-005, negative, medium)

Invalid or disallowed input for REQ-005

Preconditions: System configured as described in REQ-005

1. Use input that breaks the rule (missing, malformed, wrong type, not permitted)
2. Perform the action in REQ-005

Expected: Request is rejected with a specific error; no data is changed; the attempt is logged

### TC-018 (REQ-006, positive, high)

Happy path: A repeated request with the same terminal ID, STAN and business date must return the original result and must not create a second debit.

Preconditions: System configured as described in REQ-006

1. Prepare valid data for REQ-006
2. Perform the action: A repeated request with the same terminal ID, STAN and business date must return the original result and must not create a second debit.
3. Record the result

Expected: The system behaves exactly as REQ-006 states

### TC-019 (REQ-006, negative, medium)

Invalid or disallowed input for REQ-006

Preconditions: System configured as described in REQ-006

1. Use input that breaks the rule (missing, malformed, wrong type, not permitted)
2. Perform the action in REQ-006

Expected: Request is rejected with a specific error; no data is changed; the attempt is logged

### TC-020 (REQ-007, positive, high)

Happy path: The switch must never store or log the full PAN, track data or PIN block.

Preconditions: System configured as described in REQ-007

1. Prepare valid data for REQ-007
2. Perform the action: The switch must never store or log the full PAN, track data or PIN block.
3. Record the result

Expected: The system behaves exactly as REQ-007 states

### TC-021 (REQ-007, negative, medium)

Invalid or disallowed input for REQ-007

Preconditions: System configured as described in REQ-007

1. Use input that breaks the rule (missing, malformed, wrong type, not permitted)
2. Perform the action in REQ-007

Expected: Request is rejected with a specific error; no data is changed; the attempt is logged

### TC-022 (REQ-007, security, high)

Security check for REQ-007

Preconditions: System configured as described in REQ-007

1. Perform the action as an unauthorised or wrong-role user
2. Inspect responses, logs and stored data for sensitive values

Expected: Unauthorised access is denied; card data, PINs and secrets never appear in clear in responses, logs or storage

### TC-023 (REQ-008, positive, high)

Happy path: Approved transactions can be reversed until the batch is settled.

Preconditions: System configured as described in REQ-008

1. Prepare valid data for REQ-008
2. Perform the action: Approved transactions can be reversed until the batch is settled.
3. Record the result

Expected: The system behaves exactly as REQ-008 states

### TC-024 (REQ-009, positive, high)

Happy path: Reversals that cannot be delivered should be retried as needed.

Preconditions: System configured as described in REQ-009

1. Prepare valid data for REQ-009
2. Perform the action: Reversals that cannot be delivered should be retried as needed.
3. Record the result

Expected: The system behaves exactly as REQ-009 states

### TC-025 (REQ-009, negative, medium)

Invalid or disallowed input for REQ-009

Preconditions: System configured as described in REQ-009

1. Use input that breaks the rule (missing, malformed, wrong type, not permitted)
2. Perform the action in REQ-009

Expected: Request is rejected with a specific error; no data is changed; the attempt is logged

### TC-026 (REQ-010, positive, high)

Happy path: The end of day batch shall exclude declined and reversed transactions and report totals per currency.

Preconditions: System configured as described in REQ-010

1. Prepare valid data for REQ-010
2. Perform the action: The end of day batch shall exclude declined and reversed transactions and report totals per currency.
3. Record the result

Expected: The system behaves exactly as REQ-010 states

### TC-027 (REQ-010, negative, medium)

Invalid or disallowed input for REQ-010

Preconditions: System configured as described in REQ-010

1. Use input that breaks the rule (missing, malformed, wrong type, not permitted)
2. Perform the action in REQ-010

Expected: Request is rejected with a specific error; no data is changed; the attempt is logged

### TC-028 (REQ-011, positive, high)

Happy path: Reconciliation must flag amount mismatches, missing records and/or duplicates in the host file.

Preconditions: System configured as described in REQ-011

1. Prepare valid data for REQ-011
2. Perform the action: Reconciliation must flag amount mismatches, missing records and/or duplicates in the host file.
3. Record the result

Expected: The system behaves exactly as REQ-011 states

### TC-029 (REQ-011, negative, medium)

Invalid or disallowed input for REQ-011

Preconditions: System configured as described in REQ-011

1. Use input that breaks the rule (missing, malformed, wrong type, not permitted)
2. Perform the action in REQ-011

Expected: Request is rejected with a specific error; no data is changed; the attempt is logged

### TC-030 (REQ-012, positive, high)

Happy path: The dashboard should load fast and be user-friendly.

Preconditions: System configured as described in REQ-012

1. Prepare valid data for REQ-012
2. Perform the action: The dashboard should load fast and be user-friendly.
3. Record the result

Expected: The system behaves exactly as REQ-012 states

### TC-031 (REQ-013, positive, high)

Happy path: The switch shall be available at all times.

Preconditions: System configured as described in REQ-013

1. Prepare valid data for REQ-013
2. Perform the action: The switch shall be available at all times.
3. Record the result

Expected: The system behaves exactly as REQ-013 states

### TC-032 (REQ-014, positive, high)

Happy path: Settlement file format: TBD with the acquirer.

Preconditions: System configured as described in REQ-014

1. Prepare valid data for REQ-014
2. Perform the action: Settlement file format: TBD with the acquirer.
3. Record the result

Expected: The system behaves exactly as REQ-014 states

## Requirement gaps

| Requirement | Kind | Issue | Suggestion |
|---|---|---|---|
| REQ-009 | ambiguous | Vague wording: as needed | Replace with observable, measurable behaviour |
| REQ-009 | ambiguous | 'should' makes it unclear whether this is mandatory | Use 'must' for mandatory behaviour, or mark it as optional |
| REQ-011 | ambiguous | 'and/or' leaves it unclear whether both conditions are required | Split into separate requirements or state the exact rule |
| REQ-012 | missing_acceptance_criteria | Performance expectation without a measurable target | State a number, for example 'p95 response under 2 seconds at 50 transactions per second' |
| REQ-012 | ambiguous | Vague wording: user-friendly | Replace with observable, measurable behaviour |
| REQ-012 | ambiguous | 'should' makes it unclear whether this is mandatory | Use 'must' for mandatory behaviour, or mark it as optional |
| REQ-013 | untestable | Absolute claim that cannot be proven by testing | Define a measurable target, for example availability of 99.9% per month |
| REQ-014 | incomplete | Contains placeholder 'TBD' | Resolve the open item before test design is signed off |

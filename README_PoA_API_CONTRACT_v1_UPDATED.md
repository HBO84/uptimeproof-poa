# UptimeProof — Proof of Availability (PoA) API Contract (v1)

This document defines the **public, stable contract** for verifying UptimeProof availability proofs via a **single source of truth**:

- **Verify JSON (truth):** `https://uptimeproof.io/poa/v1/verify`
- **Status UI (human):** `https://uptimeproof.io/status/`

> **Important:** Anything outside `/poa/v1/verify` may be disabled or changed. Integrations should rely on `/poa/v1/verify` only.

---

## What this API is (in one sentence)

`/poa/v1/verify` returns a signed-by-hash *availability proof verdict* that verifies:

1) a **canonical head** (`latest.json`) exists locally,  
2) a **DNS anchor** exists (`_poa.<domain>` TXT record),  
3) the **chain link** from head → previous is intact,  
4) and the proof is still within a **valid time window**.

---

## Goals of this README

- Provide a **stable API contract** for integrators (monitoring, SDKs, CI checks).
- Define **UP/DOWN semantics** without ambiguity.
- Explain the meaning of each **check** and how to interpret warnings.
- Reduce support overhead and prevent brittle integrations.

---

## Safety & data exposure

This API is designed to be **safe for public consumption**:

- It exposes **hashes**, **filenames**, and **timestamps** only.
- It does **not** expose secrets, credentials, internal IPs, file paths, or private logs.

Integrators should treat the response as **public metadata**.

---

## Endpoints

### Verify (canonical)
- **GET** `/poa/v1/verify`
- Returns: JSON payload containing verdict, checks, proof window, and anchors.

### Healthz
- **GET** `/poa/v1/healthz`
- Returns: `{"ok": true, "ts": "...", ...}` plus service/links metadata.

---

## Response contract (v1)

### Stable top-level fields
These keys are considered stable for `uptimeproof:poa-verify:v1`:

- `schema` (must equal `uptimeproof:poa-verify:v1`)
- `ts` and `now_utc` (UTC ISO8601)
- `verdict` (`OK` or `FAIL`) and `message`
- `service` (branding/identity metadata)
- `links` (navigation)
- `verification` (canonical boolean checks + stable verdict)
- `proof` (proof timestamp, proof window, expiration)
- `anchor` (DNS anchor file+sha)

Additional fields may exist (debug/diagnostics). Integrations should focus on `verification.*` and `proof.*`.

---

## Verdict semantics

### `verdict` (legacy / simple)
- `OK`  → overall success
- `FAIL` → overall failure

### `verification.verdict` (canonical / preferred)
- `VALID`   → treat as UP (if not expired)
- `INVALID` → treat as DOWN
- `EXPIRED` → treat as DOWN (proof window elapsed)

**Recommended:** Use `verification.verdict` plus the boolean checks.

---

## Meaning of checks

### Canonical boolean checks (recommended for integrations)
Located at:

- `verification.checks.head_latest_json`  
  `true` if the canonical head exists and is readable.

- `verification.checks.dns_matches_head`  
  `true` if DNS anchor matches the current head exactly.

- `verification.checks.dns_lag_ok`  
  `true` if DNS matches head **OR** is lagging by one step (prev).  
  (See “DNS lag tolerance” below.)

- `verification.checks.dns_matched_file_hash`  
  `true` if the DNS TXT record matches a real local export by file/sha.

- `verification.checks.chain_ok`  
  `true` if chain link (head → prev) is valid (or head has no prev yet).

- `verification.checks.not_expired`  
  `true` if `now_utc <= proof.valid_until_utc`.

### Human-readable checks list (debug)
An array under `checks[]` with items like:
- `head_latest_json`
- `dns_matched_file_hash`
- `chain_link`
- `dns_matches_head`

Each item has: `id`, `status` (`OK|WARN|FAIL|UNKNOWN`), `detail`.

Integrations may log these for troubleshooting, but should decide UP/DOWN using `verification.checks`.

---

## DNS lag tolerance (IMPORTANT)

DNS updates can lag behind the latest export by one step (propagation or cron timing).

`checks[].id == "dns_matches_head"` can be:

- **OK**   : DNS = head (perfect)
- **WARN** : DNS = prev (lag by one export) → **ACCEPTABLE**
- **FAIL** : DNS matches neither head nor prev

**Integrator rule:**
- ✅ Consider **UP** if `verification.checks.dns_lag_ok == true` (OK or WARN)
- ❌ Do **not** require `verification.checks.dns_matches_head == true` at all times

This avoids false downtime alerts during normal DNS propagation.

---

## Proof window / expiration

The response includes a time window:

- `proof.proof_window_seconds`
- `proof.valid_until_utc`

A proof is considered valid only if:
- `verification.checks.not_expired == true`

---

## Minimal UP/DOWN decision logic (recommended)

Treat the service as **UP** if:

- `verification.verdict == "VALID"`
- `verification.checks.dns_lag_ok == true`
- `verification.checks.not_expired == true`

Everything else → treat as **DOWN** (or at least alert).

---

## Example: basic curl + jq

```bash
curl -sS https://uptimeproof.io/poa/v1/verify | jq -r '
  .schema,
  .verdict,
  .verification.verdict,
  .verification.checks.dns_lag_ok,
  .verification.checks.not_expired,
  .message
'
```

---

## JSON Schema + verify_client.sh

To help integrators validate and consume the API contract, we provide:

### 1) JSON Schema (machine contract)
File: `uptimeproof-poa-verify-v1.schema.json`

Usage example (with any JSON Schema validator):
- Validate responses in CI
- Ensure integrations don't break when upgrading

Example (with python + jsonschema):
```bash
python3 - <<'PY'
import json, sys
from jsonschema import validate
schema = json.load(open("uptimeproof-poa-verify-v1.schema.json","r",encoding="utf-8"))
data = json.load(sys.stdin)
validate(instance=data, schema=schema)
print("OK: schema valid")
PY < <(curl -sS https://uptimeproof.io/poa/v1/verify)
```

### 2) Shell client (UP/DOWN helper)
File: `verify_client.sh`

It implements the recommended logic:
- verdict OK
- `verification.verdict == VALID`
- `dns_lag_ok == true`
- `not_expired == true`

Usage:
```bash
chmod +x verify_client.sh
./verify_client.sh https://uptimeproof.io/poa/v1/verify
echo "exit_code=$?"
```

- Exit `0` → UP
- Exit `1` → DOWN

---

## Compatibility notes

- This README defines the **v1 contract** identified by:
  - `schema == "uptimeproof:poa-verify:v1"`
- New versions (v2, etc.) must change `schema` and document changes.
- Do not build integrations that depend on:
  - internal file paths
  - server-side implementation details
  - non-canonical endpoints

---

## Support / Contact

- `contact@uptimeproof.io`

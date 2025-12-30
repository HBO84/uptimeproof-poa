# UptimeProof PoA — Public Spec (v1.0.0)

This document defines the public verification specification for UptimeProof Proof-of-Availability (PoA).
It is public-safe: no internal paths and no secrets are required.

## 1) Public endpoints

Base URL: https://uptimeproof.io

JSON endpoints
- /poa/v1/status        (status summary)
- /poa/v1/verify        (server-side verifier)
- /poa/v1/badge         (lightweight badge JSON)
- /proof/latest         (latest proof reference)
- /proof/anchored       (DNS-anchored proof reference)
- /proof/download?file=<filename>    (download a proof payload)
- /proof/bundle/latest  (latest bundle: payload + manifest/signature if present)
- /proof/bundle?file=<filename>      (bundle for a specific file)

Human pages
- /status   (status page)
- /verify   (how to verify)
- /about    (about)

## 2) DNS anchor (source of truth)

DNS TXT record
- Name: _poa.uptimeproof.io
- Type: TXT
- Format:
  TS=<UTC_ISO>;SHA256=<64hex>;FILE=<filename>

Example
TS=2025-12-29T15:30:03Z;SHA256=<64hex>;FILE=heartbeats_YYYYMMDD_HHMMSS.json

Rules
1) The DNS SHA256 value is the anchored reference.
2) Verification MUST compare a downloaded proof SHA256 against the DNS SHA256 value.
3) “Latest” endpoints are convenient for browsing, but DNS anchoring is the verification reference.

## 3) Proof payload identity

A proof payload is identified by:
- file: a filename like heartbeats_YYYYMMDD_HHMMSS.json
- sha256: SHA256 hash of the payload contents

The system may also provide:
- <file>.sha256 (expected hash file)
- a manifest and signature (if enabled)
These are optional. DNS + payload SHA256 comparison is sufficient for integrity verification.

## 4) Recommended manual verification (DNS ➜ download ➜ SHA256)

This is the strongest public verification method.

Step A — Read the DNS anchor
Using dig:

dig TXT _poa.uptimeproof.io +short

You should receive a string that contains TS=..., SHA256=..., and FILE=....

Step B — Fetch the anchored reference (JSON)

curl -s https://uptimeproof.io/proof/anchored

This returns the DNS values (ts, sha256, file) and the matched proof file on the server side.

Step C — Download the anchored payload by filename

Use FILE from DNS (or dns.file in /proof/anchored) and download it:

curl -fsS "https://uptimeproof.io/proof/download?file=<FILE>" -o "<FILE>"

Step D — Compute SHA256 locally and compare

Linux:
sha256sum "<FILE>"

The computed hash MUST equal the DNS SHA256 value (SHA256=...).

## 5) Programmatic verification (single call)

Use the public verifier endpoint:

curl -s https://uptimeproof.io/poa/v1/verify

Typical response fields:
- valid: boolean indicating whether verification ran successfully
- verdict: OK / WARN / FAIL
- checks.local: local export matching (should be OK)
- checks.api: API cross-check against anchored reference (should be OK)
- checks.git: optional Git mirror check (OK or WARN depending on availability)

Expected outcomes:
- OK: all checks passed
- WARN: core integrity passed, but optional checks were skipped/unavailable
- FAIL: mismatch between anchored reference and retrieved artifact(s), or missing required artifacts

## 6) Git mirror (optional audit layer)

A public Git mirror may store historical exports for auditing over time.
This layer is optional: DNS anchoring + SHA256 verification remain the primary integrity check.

## 7) Timing and propagation notes

- Proof exports are produced on a fixed cadence (for example every 5 minutes).
- DNS updates may require time to propagate globally.
- A small time skew between DNS timestamp and file modification time can be normal.

## 8) Security and privacy

This spec requires only:
- DNS TXT access
- HTTP access to public endpoints
- local SHA256 computation

No internal configuration, filesystem paths, or secrets should be required for public verification.

## 9) Versioning

Spec version: v1.0.0
Git tag: v1.0.0

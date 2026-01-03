[![PoA API Contract](https://github.com/HBO84/uptimeproof-poa/actions/workflows/poa-contract.yml/badge.svg)](https://github.com/HBO84/uptimeproof-poa/actions/workflows/poa-contract.yml)
# uptimeproof-poa — Public Proof of Availability (PoA)

This repository is the **public proof log** for **uptimeproof.io**.

It contains exported PoA snapshots (JSON) and a small verifier that allows anyone to independently confirm:

- the **DNS anchor** (`_poa.uptimeproof.io`),
- the **integrity** of the referenced export file (SHA-256),
- and an optional **chain / anti-rollback** check via `exports/latest.json` and `_poa.prev_*` pointers.

> If GitHub truncates the directory listing (1,000-file UI limit), that is normal.  
> Cloning or downloading the repository still includes all files; only the web UI list is truncated.

---

## Repository layout

```
exports/
  heartbeats_YYYYMMDD_HHMMSS.json      # exported snapshots (Uptime Kuma heartbeats)
  latest.json                          # canonical head (file + sha256 + sequence + ts)
poa_verify_full.py                     # verifier (DNS + local + chain + optional API/Git hints)
SPEC.md                                # format/spec notes (optional)
```

---

## What is anchored in DNS?

The authoritative TXT record:

- **Name**: `_poa.uptimeproof.io`
- **Value** (example):
  `TS=2026-01-01T00:00:00Z;SHA256=<64-hex>;FILE=heartbeats_YYYYMMDD_HHMMSS.json`

This anchor lets verifiers pick the intended export and confirm its checksum.

---

## Quick verification (CLI)

### 1) Read the DNS anchor

```bash
dig TXT _poa.uptimeproof.io +short
```

### 2) Verify against the exports directory

If you cloned this repo:

```bash
POA_EXPORT_DIR="./exports" python3 ./poa_verify_full.py
```

To enable **chain / anti-rollback** checks (recommended):

```bash
POA_EXPORT_DIR="./exports" python3 ./poa_verify_full.py --chain
```

You should see a `VERDICT: OK` if everything matches.

---

## Verification from the public bundle (offline)

UptimeProof also publishes a ZIP bundle that includes the exports and verifier:

```bash
curl -fsS https://uptimeproof.io/proof/bundle/latest -o uptimeproof_poa_bundle.zip
unzip -q uptimeproof_poa_bundle.zip -d uptimeproof_poa_bundle
cd uptimeproof_poa_bundle
POA_EXPORT_DIR="./exports" python3 ./poa_verify_full.py --chain
```

---

## About the chain / anti-rollback check

When enabled, the verifier checks:

1. `exports/latest.json` is well-formed (file/sha256/sequence).
2. The SHA-256 in `latest.json` matches the actual head file content.
3. The head `sequence` equals the **maximum** sequence found in all exports (anti-rollback).
4. Following `_poa.prev_file` + `_poa.prev_sha256` pointers backwards forms an unbroken chain to genesis.

If this fails, it indicates an inconsistent head, broken pointers, missing history, or a rollback attempt.

---

## Notes for auditors

- The GitHub UI truncation warning does **not** affect integrity of the repo.
- Prefer verifying from:
  - a cloned repo, or
  - the published bundle, and
  - the DNS anchor queried from authoritative nameservers.

---

## License

MIT (or choose your preferred license).

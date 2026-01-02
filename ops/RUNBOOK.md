# UptimeProof PoA — Runbook

## Quick status
- Verify JSON: https://uptimeproof.io/poa/v1/verify
- Healthz: https://uptimeproof.io/poa/v1/healthz
- DNS TXT: _poa.uptimeproof.io

## What “UP” means (contract)
Treat UP if:
- verification.verdict == VALID
- verification.checks.dns_lag_ok == true
- verification.checks.not_expired == true

Do NOT require dns_matches_head == true (DNS can lag by 1 step).

## Common alerts and what to do

### 1) DNS lag (expected sometimes)
Symptoms:
- checks[].id=="dns_matches_head" = WARN
- message mentions lag by 1 step
Action:
- Usually no action.
- If it persists too long: resync TXT to latest.json head (planned improvement).

### 2) FAIL: DNS TXT did not match any local file/sha
Symptoms:
- verdict FAIL
- dns_matched_file_hash FAIL
Action:
- Check TXT record value and ensure anchored file exists in exports.
- Ensure anchoring happens after final sha is computed.

### 3) Chain FAIL (prev missing or sha mismatch)
Symptoms:
- chain_link FAIL
Action:
- Verify the previous export file exists.
- Investigate export generation pipeline; ensure files are immutable after publishing.

### 4) EXPIRED
Symptoms:
- verification.verdict EXPIRED or not_expired=false
Action:
- Export cron may be stopped or delayed.
- Check exporter service/cron and PoA service logs.

## Local debugging (server)
- Local verify: curl -sS http://127.0.0.1:8089/poa/v1/verify | jq
- Service status: systemctl status uptimeproof-poa-api
- Logs: journalctl -u uptimeproof-poa-api -n 200 --no-pager

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import glob
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ENV_FILE = "/opt/uptimeproof/infra/poa.env"
DEFAULT_EXPORT_DIR = "/proof/exports"

# DNS record we verify
DNS_NAME_DEFAULT = "_poa.uptimeproof.io"

# Zone used to find authoritative NS
DNS_ZONE_DEFAULT = "uptimeproof.io"

LOOKBACK_FILES = 300
WARN_SKEW_SECONDS = 10 * 60
FAIL_SKEW_SECONDS = 60 * 60

# For parsing dig TXT which can be: "A" "B"
_QUOTED_TXT_RE = re.compile(r'"([^"]*)"')


@dataclass
class DnsProof:
    ts_iso: str
    sha256: str
    filename: Optional[str]


def load_env_file(path: str) -> Dict[str, str]:
    d: Dict[str, str] = {}
    p = Path(path)
    if not p.exists():
        return d
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        d[k.strip()] = v.strip()
    return d


def run(cmd: List[str], cwd: Optional[str] = None) -> str:
    p = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{p.stderr.strip()}")
    return p.stdout.strip()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def newest_files(export_dir: str, n: int) -> List[str]:
    files = glob.glob(os.path.join(export_dir, "heartbeats_*.json"))
    files.sort(key=os.path.getmtime, reverse=True)
    return files[:n]


def _clean_dig_txt(out: str) -> str:
    """
    dig +short TXT can return:
      "A" "B"
    or multiple lines. We merge quoted parts if present.
    """
    out = (out or "").strip()
    if not out:
        return ""
    parts = _QUOTED_TXT_RE.findall(out)
    if parts:
        return "".join(parts).strip()
    return out.replace('"', "").strip()


def _get_authoritative_ns(zone: str) -> List[str]:
    out = run(["dig", "+short", "NS", zone]).splitlines()
    ns = [x.strip().rstrip(".") for x in out if x.strip()]
    return ns


def dig_txt_authoritative(name: str, zone: str) -> Tuple[str, str]:
    """
    Returns (dns_txt, used_ns).

    Behavior:
      - Uses authoritative NS for `zone` (or override list).
      - Tries each NS until one returns a non-empty TXT.
      - NO silent fallback to system resolver unless POA_DNS_ALLOW_SYSTEM_RESOLVER=1.
    Overrides:
      - POA_DNS_NS_OVERRIDE="ns1,ns2"
      - POA_DNS_ALLOW_SYSTEM_RESOLVER="1" (discouraged)
    """
    ns_override = os.getenv("POA_DNS_NS_OVERRIDE", "").strip()
    if ns_override:
        ns_list = [x.strip().rstrip(".") for x in ns_override.split(",") if x.strip()]
    else:
        ns_list = _get_authoritative_ns(zone)

    last_err: Optional[Exception] = None

    # Try authoritative NS first
    for ns in ns_list:
        try:
            out = run(["dig", f"@{ns}", "+short", "TXT", name, "+time=2", "+tries=1"])
            txt = _clean_dig_txt(out)
            if txt:
                return txt, ns
        except Exception as e:
            last_err = e
            continue

    # Optional fallback to system resolver
    if os.getenv("POA_DNS_ALLOW_SYSTEM_RESOLVER", "0") == "1":
        out = run(["dig", "+short", "TXT", name, "+time=2", "+tries=1"])
        txt = _clean_dig_txt(out)
        if txt:
            return txt, "SYSTEM_RESOLVER"

    raise RuntimeError(
        f"No TXT returned for {name} via authoritative NS (zone={zone}). last_err={last_err}"
    )


def parse_dns_txt(txt: str) -> DnsProof:
    txt = txt.strip().strip('"')
    m_ts = re.search(r"TS=([^;]+)", txt)
    m_sha = re.search(r"SHA256=([0-9a-fA-F]{64})", txt)
    m_file = re.search(r"FILE=([^;]+)", txt)
    if not m_ts or not m_sha:
        raise RuntimeError(f"Unrecognized TXT format: {txt}")
    return DnsProof(
        ts_iso=m_ts.group(1),
        sha256=m_sha.group(1).lower(),
        filename=m_file.group(1) if m_file else None,
    )


def iso_to_unix(ts_iso: str) -> int:
    dt = datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
    return int(dt.timestamp())


def find_local_match(export_dir: str, proof: DnsProof) -> Tuple[Optional[str], Optional[str]]:
    if proof.filename:
        candidate = os.path.join(export_dir, proof.filename)
        if os.path.exists(candidate):
            return candidate, "matched_by_filename"

    for f in newest_files(export_dir, LOOKBACK_FILES):
        try:
            if sha256_file(f).lower() == proof.sha256:
                return f, "matched_by_hash_scan"
        except Exception:
            continue

    return None, None


def verdict_from_hash_and_skew(hash_ok: bool, skew: int) -> str:
    if not hash_ok:
        return "FAIL"
    if abs(skew) <= WARN_SKEW_SECONDS:
        return "OK"
    if abs(skew) <= FAIL_SKEW_SECONDS:
        return "WARN"
    return "WARN"


def main() -> int:
    # Load poa.env for DNS_NAME, DNS_ZONE if present
    env = load_env_file(ENV_FILE)
    dns_name = env.get("DNS_NAME", DNS_NAME_DEFAULT)

    # Allow zone override via poa.env or environment
    dns_zone = (
        os.environ.get("DNS_ZONE")
        or env.get("DNS_ZONE")
        or DNS_ZONE_DEFAULT
    )

    export_dir = os.environ.get("POA_EXPORT_DIR") or DEFAULT_EXPORT_DIR
    export_dir = export_dir.rstrip("/")

    dns_txt, used_ns = dig_txt_authoritative(dns_name, dns_zone)
    proof = parse_dns_txt(dns_txt)
    dns_ts_unix = iso_to_unix(proof.ts_iso)

    match_path, how = find_local_match(export_dir, proof)
    if not match_path:
        print("VERDICT: FAIL")
        print(f"DNS NS      : {used_ns}")
        print(f"DNS TXT     : {dns_txt}")
        print(f"EXPORT_DIR  : {export_dir}")
        print(f"LOCAL       : FAIL (no matching export found in last {LOOKBACK_FILES} files)")
        return 2

    file_sha = sha256_file(match_path).lower()
    hash_ok = (file_sha == proof.sha256)
    mtime = int(os.path.getmtime(match_path))
    skew = mtime - dns_ts_unix
    local_v = verdict_from_hash_and_skew(hash_ok, skew)

    print(f"VERDICT: {local_v}")
    print(f"DNS NS      : {used_ns}")
    print(f"DNS TXT     : {dns_txt}")
    print(f"EXPORT_DIR  : {export_dir}")
    print(f"Matched file: {match_path} ({how})")
    print(f"DNS SHA256  : {proof.sha256}")
    print(f"File SHA256 : {file_sha}")
    print(f"Skew seconds: {skew} (file_mtime - dns_ts)")
    print(f"LOCAL: {local_v}")
    return 0 if local_v == "OK" else (1 if local_v == "WARN" else 2)


if __name__ == "__main__":
    sys.exit(main())

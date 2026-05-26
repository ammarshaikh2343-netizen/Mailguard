"""
dns_checks.py — Core DNS lookup utilities for MailGuard
Handles: DKIM, SPF, DMARC, MX with caching, threading, and clean error handling
"""

import re
import dns.resolver
import dns.exception
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed

# ─────────────────────────────────────────────
# DNS Resolver factory (shared settings)
# ─────────────────────────────────────────────

def _resolver():
    r = dns.resolver.Resolver()
    r.timeout = 5
    r.lifetime = 8
    r.nameservers = ["8.8.8.8", "1.1.1.1", "8.8.4.4"]  # Google + Cloudflare
    return r


def sanitize_domain(domain: str) -> str:
    """Strip protocol, path, whitespace — return bare domain."""
    domain = domain.strip().lower()
    domain = re.sub(r'^https?://', '', domain)
    domain = domain.split('/')[0].split('?')[0].split('#')[0]
    domain = domain.strip('.')
    # Basic validity check
    if not re.match(r'^[a-z0-9][a-z0-9\-\.]{0,251}[a-z0-9]$', domain):
        return ""
    return domain


def _get_txt_records(hostname: str):
    """Return list of TXT strings for hostname, or raise."""
    answers = _resolver().resolve(hostname, "TXT")
    return [b"".join(r.strings).decode("utf-8", errors="replace") for r in answers]


def _get_mx_records(domain: str):
    """Return list of (priority, exchange) tuples."""
    answers = _resolver().resolve(domain, "MX")
    return sorted([(r.preference, str(r.exchange).rstrip('.')) for r in answers])


def _get_cname_record(hostname: str):
    """Return CNAME target string or None."""
    try:
        answers = _resolver().resolve(hostname, "CNAME")
        return str(list(answers)[0].target).rstrip('.')
    except Exception:
        return None


# ─────────────────────────────────────────────
# Provider Detection
# ─────────────────────────────────────────────

GOOGLE_MX_PATTERNS = ["google.com", "googlemail.com", "aspmx"]
MICROSOFT_MX_PATTERNS = ["outlook.com", "protection.outlook", "mail.protection"]
ZOHO_MX_PATTERNS = ["zoho.com", "zohomail.com"]
PROTON_MX_PATTERNS = ["protonmail.ch", "proton.me"]

def detect_provider_from_mx(mx_records: list) -> str:
    """Infer email provider from MX records."""
    all_mx = " ".join(ex.lower() for _, ex in mx_records)
    if any(p in all_mx for p in GOOGLE_MX_PATTERNS):
        return "Google Workspace"
    if any(p in all_mx for p in MICROSOFT_MX_PATTERNS):
        return "Microsoft 365"
    if any(p in all_mx for p in ZOHO_MX_PATTERNS):
        return "Zoho Mail"
    if any(p in all_mx for p in PROTON_MX_PATTERNS):
        return "Proton Mail"
    if mx_records:
        return "Custom"
    return "Unknown"


# ─────────────────────────────────────────────
# DKIM Checker
# ─────────────────────────────────────────────

def check_dkim(domain: str, selector: str) -> dict:
    """
    Check DKIM record for domain+selector.
    Returns dict: {domain, selector, status, provider, detail}
    """
    base = {"domain": domain, "selector": selector}

    dkim_host = f"{selector}._domainkey.{domain}"

    # Try TXT first
    try:
        records = _get_txt_records(dkim_host)
        combined = " ".join(records)

        if "v=DKIM1" in combined or "k=rsa" in combined or "k=ed25519" in combined:
            if re.search(r'p=[A-Za-z0-9+/]{10,}', combined):
                provider = _detect_dkim_provider(combined, selector)
                return {**base, "status": "Valid", "provider": provider,
                        "detail": _trim(records[0], 90)}
            else:
                return {**base, "status": "Invalid", "provider": "—",
                        "detail": "Key revoked or empty (p= missing content)"}
        elif "p=" in combined:
            # Has p= tag but no v=DKIM1 — likely still valid
            if re.search(r'p=[A-Za-z0-9+/]{10,}', combined):
                provider = _detect_dkim_provider(combined, selector)
                return {**base, "status": "Valid", "provider": provider,
                        "detail": _trim(records[0], 90)}
            else:
                return {**base, "status": "Invalid", "provider": "—",
                        "detail": "TXT found but no valid public key"}
        else:
            return {**base, "status": "Invalid", "provider": "—",
                    "detail": f"TXT exists but not a DKIM record: {_trim(records[0], 60)}"}

    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        pass
    except dns.exception.Timeout:
        return {**base, "status": "Lookup Failed", "provider": "—", "detail": "DNS timeout"}
    except Exception as e:
        pass

    # Try CNAME (Microsoft uses this)
    try:
        cname = _get_cname_record(dkim_host)
        if cname:
            if any(p in cname.lower() for p in ["domainkey", "outlook", "microsoft"]):
                return {**base, "status": "Valid", "provider": "Microsoft 365",
                        "detail": f"CNAME → {cname}"}
            else:
                return {**base, "status": "Valid", "provider": "Custom",
                        "detail": f"CNAME → {cname}"}
    except Exception:
        pass

    return {**base, "status": "Not Found", "provider": "—",
            "detail": f"No DKIM record at {dkim_host}"}


def _detect_dkim_provider(txt: str, selector: str) -> str:
    selector = selector.lower()
    if selector == "google":
        return "Google Workspace"
    if selector in ["selector1", "selector2"]:
        return "Microsoft 365"
    if "zoho" in txt.lower():
        return "Zoho Mail"
    return "Custom"


# ─────────────────────────────────────────────
# SPF Checker
# ─────────────────────────────────────────────

def check_spf(domain: str) -> dict:
    """Check SPF TXT record for domain."""
    base = {"domain": domain}
    try:
        all_txt = _get_txt_records(domain)
        spf_records = [r for r in all_txt if r.lower().startswith("v=spf1")]

        if not spf_records:
            return {**base, "status": "Missing", "detail": "No SPF record found"}

        if len(spf_records) > 1:
            return {**base, "status": "Multiple SPF",
                    "detail": f"{len(spf_records)} SPF records found (invalid — must be exactly 1)"}

        spf = spf_records[0]
        # Basic syntax validation
        if not re.search(r'[~\-\+?]all', spf, re.IGNORECASE):
            return {**base, "status": "Invalid",
                    "detail": f"SPF missing 'all' mechanism: {_trim(spf, 80)}"}

        policy = _spf_policy(spf)
        return {**base, "status": "Valid", "policy": policy,
                "detail": _trim(spf, 100)}

    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        return {**base, "status": "Missing", "detail": "No TXT records found for domain"}
    except dns.exception.Timeout:
        return {**base, "status": "Lookup Failed", "detail": "DNS timeout"}
    except Exception as e:
        return {**base, "status": "Lookup Failed", "detail": "DNS lookup error"}


def _spf_policy(spf: str) -> str:
    if "-all" in spf:
        return "Strict (Fail)"
    if "~all" in spf:
        return "Soft Fail"
    if "?all" in spf:
        return "Neutral"
    if "+all" in spf:
        return "Pass (Permissive — Dangerous)"
    return "Unknown"


# ─────────────────────────────────────────────
# DMARC Checker
# ─────────────────────────────────────────────

def check_dmarc(domain: str) -> dict:
    """Check DMARC _dmarc.domain TXT record."""
    base = {"domain": domain}
    dmarc_host = f"_dmarc.{domain}"
    try:
        records = _get_txt_records(dmarc_host)
        dmarc_records = [r for r in records if r.lower().startswith("v=dmarc1")]

        if not dmarc_records:
            return {**base, "status": "Missing", "policy": "—",
                    "detail": f"No DMARC record at {dmarc_host}"}

        dmarc = dmarc_records[0]
        policy = _dmarc_policy(dmarc)
        pct = _dmarc_pct(dmarc)
        rua = _dmarc_rua(dmarc)

        return {**base, "status": "Valid", "policy": policy,
                "pct": pct, "rua": rua,
                "detail": _trim(dmarc, 120)}

    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        return {**base, "status": "Missing", "policy": "—",
                "detail": f"No DMARC record at {dmarc_host}"}
    except dns.exception.Timeout:
        return {**base, "status": "Lookup Failed", "policy": "—", "detail": "DNS timeout"}
    except Exception:
        return {**base, "status": "Lookup Failed", "policy": "—", "detail": "DNS lookup error"}


def _dmarc_policy(dmarc: str) -> str:
    m = re.search(r'\bp=(\w+)', dmarc, re.IGNORECASE)
    return m.group(1).capitalize() if m else "Unknown"


def _dmarc_pct(dmarc: str) -> str:
    m = re.search(r'\bpct=(\d+)', dmarc, re.IGNORECASE)
    return f"{m.group(1)}%" if m else "100%"


def _dmarc_rua(dmarc: str) -> str:
    m = re.search(r'\brua=([^\s;]+)', dmarc, re.IGNORECASE)
    if m:
        rua = m.group(1).replace("mailto:", "")
        return _trim(rua, 50)
    return "Not configured"


# ─────────────────────────────────────────────
# MX Checker
# ─────────────────────────────────────────────

def check_mx(domain: str) -> dict:
    """Check MX records and detect provider."""
    base = {"domain": domain}
    try:
        mx_list = _get_mx_records(domain)
        if not mx_list:
            return {**base, "status": "No MX", "provider": "—", "detail": "No MX records found"}

        provider = detect_provider_from_mx(mx_list)
        mx_display = ", ".join(f"{ex} (pri:{pri})" for pri, ex in mx_list[:4])
        if len(mx_list) > 4:
            mx_display += f" +{len(mx_list)-4} more"

        return {**base, "status": "Found", "provider": provider,
                "count": len(mx_list), "detail": mx_display,
                "records": [{"priority": p, "exchange": e} for p, e in mx_list]}

    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        return {**base, "status": "No MX", "provider": "—",
                "detail": "No MX records found", "records": []}
    except dns.exception.Timeout:
        return {**base, "status": "Lookup Failed", "provider": "—",
                "detail": "DNS timeout", "records": []}
    except Exception:
        return {**base, "status": "Lookup Failed", "provider": "—",
                "detail": "DNS lookup error", "records": []}


# ─────────────────────────────────────────────
# Bulk runners (threaded)
# ─────────────────────────────────────────────

def bulk_check(domains: list, check_fn, max_workers: int = 20, **kwargs) -> list:
    """
    Run check_fn(domain, **kwargs) for each domain in parallel.
    Preserves original domain order. Never raises.
    """
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_safe_call, check_fn, d, **kwargs): d for d in domains}
        for future in as_completed(futures):
            domain = futures[future]
            results[domain] = future.result()

    # Restore original order
    return [results[d] for d in domains if d in results]


def _safe_call(fn, domain, **kwargs):
    """Wrap any check function to never raise — returns error dict on failure."""
    try:
        return fn(domain, **kwargs)
    except Exception as e:
        return {"domain": domain, "status": "Lookup Failed",
                "detail": "Unexpected error during lookup"}


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _trim(s: str, n: int) -> str:
    return s[:n] + ("..." if len(s) > n else "")


def dedupe_domains(raw_list: list, max_count: int) -> list:
    """Clean, deduplicate, and cap domain list."""
    seen = {}
    for raw in raw_list:
        d = sanitize_domain(raw)
        if d and d not in seen:
            seen[d] = True
        if len(seen) >= max_count:
            break
    return list(seen.keys())

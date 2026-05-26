"""
MailGuard — Production Flask App
Includes: rate limiting, security headers, caching, CORS, health check
"""

import os
import time
import hashlib
import json
from functools import wraps
from flask import Flask, request, jsonify, render_template, make_response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from utils.dns_checks import (
    check_dkim, check_spf, check_dmarc, check_mx,
    bulk_check, dedupe_domains
)

# ─────────────────────────────────────────────
# App setup
# ─────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me-in-production")
app.config["DEBUG"] = False
app.config["PROPAGATE_EXCEPTIONS"] = False

# ─────────────────────────────────────────────
# Rate limiter (IP-based, memory storage)
# ─────────────────────────────────────────────
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "60 per hour"],
    storage_uri="memory://",
    strategy="fixed-window"
)

# ─────────────────────────────────────────────
# Simple in-memory DNS result cache (5 min TTL)
# ─────────────────────────────────────────────
_cache = {}
CACHE_TTL = 300  # seconds

def cache_get(key):
    if key in _cache:
        ts, val = _cache[key]
        if time.time() - ts < CACHE_TTL:
            return val
        del _cache[key]
    return None

def cache_set(key, val):
    # Keep cache from growing unbounded
    if len(_cache) > 2000:
        oldest = sorted(_cache.items(), key=lambda x: x[1][0])[:500]
        for k, _ in oldest:
            del _cache[k]
    _cache[key] = (time.time(), val)

def cached_bulk(domains, check_fn, max_workers, **kwargs):
    """Run bulk check with per-domain caching."""
    fn_name = check_fn.__name__
    extra = json.dumps(kwargs, sort_keys=True)
    uncached, cached_results = [], {}

    for d in domains:
        key = f"{fn_name}:{d}:{extra}"
        hit = cache_get(key)
        if hit:
            cached_results[d] = hit
        else:
            uncached.append(d)

    if uncached:
        fresh = bulk_check(uncached, check_fn, max_workers=max_workers, **kwargs)
        for r in fresh:
            key = f"{fn_name}:{r['domain']}:{extra}"
            cache_set(key, r)
            cached_results[r["domain"]] = r

    return [cached_results[d] for d in domains if d in cached_results]

# ─────────────────────────────────────────────
# Security headers middleware
# ─────────────────────────────────────────────
@app.after_request
def add_security_headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["X-XSS-Protection"] = "1; mode=block"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    resp.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
    if request.path.startswith("/api/"):
        resp.headers["Cache-Control"] = "no-store"
    return resp

# ─────────────────────────────────────────────
# Domain limits
# ─────────────────────────────────────────────
LIMITS = {
    "dkim":  5,
    "spf":   100,
    "dmarc": 100,
    "mx":    100,
}

# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/health")
def health():
    """Health check endpoint for uptime monitors."""
    return jsonify({"status": "ok", "service": "mailguard"})

@app.route("/api/dkim", methods=["POST"])
@limiter.limit("30 per minute")
def api_dkim():
    data = request.get_json(silent=True) or {}
    domains = dedupe_domains(data.get("domains", []), LIMITS["dkim"])
    selector = (data.get("selector") or "google").strip()[:50]

    if not domains:
        return jsonify({"error": "No valid domains provided"}), 400

    results = cached_bulk(domains, check_dkim, max_workers=5, selector=selector)
    return jsonify({"results": results, "count": len(results)})

@app.route("/api/spf", methods=["POST"])
@limiter.limit("20 per minute")
def api_spf():
    data = request.get_json(silent=True) or {}
    domains = dedupe_domains(data.get("domains", []), LIMITS["spf"])

    if not domains:
        return jsonify({"error": "No valid domains provided"}), 400

    results = cached_bulk(domains, check_spf, max_workers=25)
    return jsonify({"results": results, "count": len(results)})

@app.route("/api/dmarc", methods=["POST"])
@limiter.limit("20 per minute")
def api_dmarc():
    data = request.get_json(silent=True) or {}
    domains = dedupe_domains(data.get("domains", []), LIMITS["dmarc"])

    if not domains:
        return jsonify({"error": "No valid domains provided"}), 400

    results = cached_bulk(domains, check_dmarc, max_workers=25)
    return jsonify({"results": results, "count": len(results)})

@app.route("/api/mx", methods=["POST"])
@limiter.limit("20 per minute")
def api_mx():
    data = request.get_json(silent=True) or {}
    domains = dedupe_domains(data.get("domains", []), LIMITS["mx"])

    if not domains:
        return jsonify({"error": "No valid domains provided"}), 400

    results = cached_bulk(domains, check_mx, max_workers=25)
    return jsonify({"results": results, "count": len(results)})

@app.route("/api/limits", methods=["GET"])
def api_limits():
    return jsonify(LIMITS)

# ─────────────────────────────────────────────
# Error handlers
# ─────────────────────────────────────────────
@app.errorhandler(429)
def rate_limit_handler(e):
    return jsonify({"error": "Too many requests. Please slow down."}), 429

@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": "Bad request"}), 400

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Server error. Please try again."}), 500

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5050)))

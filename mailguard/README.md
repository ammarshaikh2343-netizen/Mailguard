# MailGuard — Professional Email DNS Checker

A fast, professional, bulk email DNS health checker built with Python + Flask.
Checks DKIM, SPF, DMARC, and MX records — in bulk, in parallel, with a clean UI.

---

## Features

| Check | Limit | What it detects |
|-------|-------|-----------------|
| **DKIM** | 5 domains | Valid / Invalid / Not Found / Revoked keys |
| **SPF**  | 100 domains | Valid / Missing / Invalid / Multiple SPF |
| **DMARC**| 100 domains | Valid / Missing / Invalid + policy/pct/rua |
| **MX**   | 100 domains | Google / Microsoft / Zoho / Proton / Custom / No MX |

- **20-25 parallel DNS threads** — 100 domains in seconds
- Clean SaaS-style dark UI with tabs, stats, filters
- Export: CSV, TXT, Copy to clipboard, Failed-only download
- Search/filter results instantly
- Click stat pills to filter by status
- Selector dropdown for DKIM (google, selector1, selector2, custom…)
- Provider auto-detection from MX + DKIM
- Zero crashes — all errors gracefully shown

---

## Quick Start

### Windows
```
Double-click start.bat
```

### Mac / Linux
```bash
chmod +x start.sh
./start.sh
```

### Manual
```bash
pip install -r requirements.txt
python app.py
# → http://localhost:5050
```

---

## Folder Structure

```
mailguard/
├── app.py                  # Flask app + all API routes
├── utils/
│   ├── __init__.py
│   └── dns_checks.py       # All DNS logic (DKIM/SPF/DMARC/MX)
├── templates/
│   └── index.html          # Full frontend (single-file SPA)
├── requirements.txt
├── Procfile                # For Render / Railway
├── runtime.txt             # Python 3.11
├── start.bat               # Windows launcher
└── start.sh                # Mac/Linux launcher
```

---

## API Endpoints

All endpoints accept `POST` with `Content-Type: application/json`.

### POST /api/dkim
```json
{ "domains": ["example.com"], "selector": "google" }
```

### POST /api/spf
```json
{ "domains": ["example.com", "other.org"] }
```

### POST /api/dmarc
```json
{ "domains": ["example.com"] }
```

### POST /api/mx
```json
{ "domains": ["example.com"] }
```

### GET /api/limits
Returns current domain limits per check type.

---

## Deployment

### Render (free tier)
1. Push to GitHub
2. New Web Service → connect repo
3. Build: `pip install -r requirements.txt`
4. Start: `gunicorn app:app --bind 0.0.0.0:$PORT`
5. Done ✓

### Railway
1. Push to GitHub
2. New Project → Deploy from GitHub
3. Railway auto-detects Procfile
4. Done ✓

### VPS (Ubuntu)
```bash
git clone <your-repo>
cd mailguard
pip install -r requirements.txt
gunicorn app:app --bind 0.0.0.0:80 --workers 4 --daemon
```

---

## Created by
[Anas Shaikh](https://www.linkedin.com/in/anas-shaikh-80734324b/)

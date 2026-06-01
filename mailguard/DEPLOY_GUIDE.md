# MailGuard — Complete Beginner Deployment Guide
### From your computer to a live public website, step by step

---

## TABLE OF CONTENTS

1. [Which Hosting Should I Use?](#1-which-hosting-should-i-use)
2. [Step 1 — Upload to GitHub](#2-step-1--upload-to-github)
3. [Step 2 — Deploy on Render (Recommended)](#3-step-2--deploy-on-render)
4. [Step 3 — Set Environment Variables](#4-step-3--set-environment-variables)
5. [Step 4 — Connect a Custom Domain](#5-step-4--connect-a-custom-domain)
6. [Step 5 — Add Free SSL with Cloudflare](#6-step-5--add-free-ssl-with-cloudflare)
7. [Fix Common Errors](#7-fix-common-errors)
8. [Monetization Guide](#8-monetization-guide)
9. [Performance & Security](#9-performance--security)
10. [What to Do Next](#10-what-to-do-next)

---

## 1. WHICH HOSTING SHOULD I USE?

Here is a simple comparison for your Flask app:

| Platform | Free Tier | Ease | Best For | Scaling |
|---|---|---|---|---|
| **Render** ✅ | Yes (750 hrs/mo) | ⭐⭐⭐⭐⭐ Easiest | Beginners | Good |
| Railway | Yes ($5 credit) | ⭐⭐⭐⭐ | Beginners | Good |
| Vercel | Yes | ⭐⭐⭐ | Static sites (not ideal for Flask) | Good |
| DigitalOcean App Platform | $5/mo | ⭐⭐⭐ | Intermediate | Excellent |
| AWS / GCP | Pay-as-you-go | ⭐⭐ Hard | Advanced | Unlimited |
| VPS (Hetzner/Vultr) | ~$4/mo | ⭐⭐ Hard | Advanced | Excellent |

### ✅ My Recommendation: START with Render

**Why Render is best for you right now:**
- Free tier — no credit card needed to start
- Connects directly to GitHub
- Auto-deploys when you push code changes
- Free HTTPS/SSL included
- Custom domain support
- Easy to upgrade later when you get traffic

**Later when you have users:** Move to DigitalOcean ($12/mo) or a VPS for better speed and no sleep delays.

---

## 2. STEP 1 — UPLOAD TO GITHUB

GitHub is where your code lives online. Render reads from GitHub to deploy.

### Install Git (if you haven't)
1. Go to https://git-scm.com/downloads
2. Download and install for Windows
3. Open "Git Bash" (Windows) or Terminal (Mac)

### Create a GitHub Account
1. Go to https://github.com
2. Click "Sign up" — it's free
3. Confirm your email

### Upload Your Project

Open Git Bash / Terminal and run these commands one by one:

```bash
# Go into your mailguard folder
cd path/to/mailguard

# Tell Git who you are (one time only)
git config --global user.email "your@email.com"
git config --global user.name "Your Name"

# Initialize Git in your project
git init

# Add all files
git add .

# Save a snapshot (called a "commit")
git commit -m "Initial MailGuard upload"
```

Now create a repository on GitHub:
1. Go to https://github.com/new
2. Repository name: `mailguard`
3. Set to **Private** (you can make public later)
4. Click "Create repository"
5. GitHub will show you commands — copy the "push existing" ones, they look like:

```bash
git remote add origin https://github.com/YOUR_USERNAME/mailguard.git
git branch -M main
git push -u origin main
```

Run those in your terminal. Enter your GitHub username and password when asked.

✅ Your code is now on GitHub!

---

## 3. STEP 2 — DEPLOY ON RENDER

### Create Render Account
1. Go to https://render.com
2. Click "Get Started for Free"
3. Sign up with your GitHub account (easiest)

### Create a New Web Service
1. Click **"New +"** → **"Web Service"**
2. Click **"Connect a repository"**
3. Find and select your `mailguard` repo
4. Click **"Connect"**

### Configure the Service

Fill in these settings:

| Field | Value |
|---|---|
| **Name** | mailguard (or any name you like) |
| **Region** | Choose closest to your users |
| **Branch** | main |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 60` |
| **Instance Type** | Free |

Click **"Create Web Service"**

Render will now:
1. Download your code from GitHub
2. Install Python packages
3. Start your app with Gunicorn

This takes 2–4 minutes. Watch the logs at the bottom.

✅ When you see "Your service is live", click the URL — your app is online!

Your URL will be something like: `https://mailguard.onrender.com`

### ⚠️ Free Tier Note
On Render's free tier, the app "sleeps" after 15 minutes of no traffic and takes ~30 seconds to wake up. To prevent this:
- Use a free uptime monitor like **UptimeRobot** (https://uptimerobot.com) — set it to ping your app every 14 minutes
- Or upgrade to Render's $7/mo paid plan

---

## 4. STEP 3 — SET ENVIRONMENT VARIABLES

Environment variables are like secret settings that don't go in your code.

On Render:
1. Go to your service → **"Environment"** tab
2. Click **"Add Environment Variable"**

Add these:

| Key | Value |
|---|---|
| `SECRET_KEY` | A long random string (e.g. `xK9#mP2@vL8$nQ5&wR3`) |
| `PYTHON_VERSION` | `3.11.9` |

To generate a good SECRET_KEY, run this in Python:
```python
import secrets
print(secrets.token_hex(32))
```

Click **"Save Changes"** — Render will redeploy automatically.

---

## 5. STEP 4 — CONNECT A CUSTOM DOMAIN

### Buy a Domain

Best domain registrars (cheapest first):

| Provider | Price/year | Notes |
|---|---|---|
| **Namecheap** | ~$9–12 | Recommended — easy + cheap |
| Porkbun | ~$9 | Very cheap, good UI |
| Cloudflare Registrar | At-cost | Cheapest for renewals |
| GoDaddy | ~$12+ | More expensive, pushy upsells |

**Suggested domain names for your tool:**
- mailguard.tools
- dnscheck.app
- emaildnscheck.com
- mailcheck.tools
- dkimchecker.com

Go to Namecheap.com, search for your preferred name, buy it.

### Connect Domain to Render

1. In Render, go to your service → **"Settings"** → **"Custom Domains"**
2. Click **"Add Custom Domain"**
3. Type your domain: `yourdomain.com`
4. Render gives you a CNAME record to add

In Namecheap:
1. Go to "Domain List" → click "Manage" on your domain
2. Click "Advanced DNS"
3. Add a CNAME record:
   - **Host:** `@` (or `www`)
   - **Value:** The CNAME Render gave you (looks like `mailguard.onrender.com`)
   - **TTL:** Automatic

DNS changes take 5–30 minutes to work globally.

✅ Your site is now live at your custom domain!

---

## 6. STEP 5 — ADD FREE SSL WITH CLOUDFLARE

Cloudflare gives you free SSL (the padlock 🔒), DDoS protection, and a global CDN that makes your site faster worldwide. This is highly recommended.

### Setup Cloudflare (Free)
1. Go to https://cloudflare.com → Sign up free
2. Click **"Add a Site"** → enter your domain
3. Choose the **Free plan**
4. Cloudflare scans your DNS and shows your current records
5. Click **"Continue"**
6. Cloudflare gives you 2 nameservers, like:
   ```
   aria.ns.cloudflare.com
   bob.ns.cloudflare.com
   ```
7. In Namecheap → Domain → Nameservers → Custom → paste both
8. Click "Done" on Cloudflare

Takes 5–24 hours for full propagation.

### After Cloudflare is Active
1. Go to Cloudflare → your domain → **SSL/TLS**
2. Set mode to **"Full"**
3. Turn on **"Always Use HTTPS"**
4. Turn on **"Automatic HTTPS Rewrites"**

✅ Your site now has a free SSL certificate and is protected by Cloudflare.

---

## 7. FIX COMMON ERRORS

### "Application failed to respond"
**Cause:** Start command is wrong or app crashed.
**Fix:** Check the Render logs. Look for Python errors.
Check that your `Procfile` contains:
```
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 60
```

### "ModuleNotFoundError: No module named 'flask'"
**Cause:** `requirements.txt` is wrong or missing.
**Fix:** Make sure `requirements.txt` exists and contains all packages. Re-deploy.

### "Port already in use"
**Cause:** Local port conflict.
**Fix:** On Render this won't happen — it's a local dev issue. Change port to 5051 locally.

### App works locally but not on Render
**Common causes:**
1. You didn't push latest code to GitHub (`git add . && git commit -m "fix" && git push`)
2. Missing environment variable
3. `requirements.txt` out of date

### "Too Many Requests" error
**Cause:** Rate limiting is working correctly — the IP made too many requests.
**Fix:** This is intentional. Wait a minute and try again.

### DNS checks return "Lookup Failed" on Render
**Cause:** Some hosting providers block outbound DNS on free tiers.
**Fix:** This is rare on Render. If it happens, upgrade to paid tier or switch to Railway.

---

## 8. MONETIZATION GUIDE

### Option A — Google AdSense (Display Ads)

**Can a DNS checker tool use AdSense?**
✅ Yes! DNS/email tools are completely allowed. They are considered "utility" or "webmaster tools" — Google loves these.

**Requirements before applying:**
- Your site must be live for at least 2–3 months
- Must have real content (not just a tool — add a blog, FAQ, docs)
- Must get at least 50–100 daily visitors
- Must have a Privacy Policy page
- Must have Terms of Service page

**How to Apply:**
1. Go to https://adsense.google.com
2. Add your website URL
3. Add the AdSense script to your `<head>` in `index.html`:
   ```html
   <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXX" crossorigin="anonymous"></script>
   ```
4. Wait for approval (usually 1–2 weeks)

**Where to place ads on your tool:**
- Above the results table (high CTR)
- Below the input form
- In a sidebar (if you add one)
- Between the tab content

**Expected revenue:**
- 1,000 daily visitors → ~$2–8/day (~$60–240/month)
- 10,000 daily visitors → ~$20–80/day
- Revenue depends heavily on your audience's country (US/UK/CA pays 5–10x more than India/Asia)

### Option B — Paid Plans / Freemium

Add a "Pro" tier with more features:

| Free Tier | Pro Tier ($9–19/mo) |
|---|---|
| 5 domains DKIM | 50 domains DKIM |
| 100 domains SPF/DMARC/MX | 500 domains |
| Manual checks | Scheduled monitoring |
| No history | Check history saved |
| No alerts | Email alerts if record breaks |
| No API | API access |

**To implement payments:** Use **Stripe** (https://stripe.com) — it's the easiest payment system for developers. You'd add a user login system (email + password) and track their plan level.

### Option C — Affiliate Links

Add links like:
- "Need Google Workspace?" → Google Workspace affiliate ($20+ per signup)
- "Protect your domain with Cloudflare" → Cloudflare affiliate
- "Buy domains at Namecheap" → Namecheap affiliate

These can earn $10–50 per referral.

### SEO — How to Get Free Traffic

SEO (Search Engine Optimization) = getting people to find you on Google.

**Target keywords people search:**
- "bulk DKIM checker"
- "check SPF record online"
- "DMARC checker tool"
- "MX record lookup"
- "email DNS checker"

**How to rank:**
1. Add a proper `<title>` and `<meta description>` to your HTML
2. Write a blog/docs section explaining DKIM, SPF, DMARC (Google loves helpful content)
3. Get links from webmaster blogs, Reddit r/sysadmin, Twitter/LinkedIn
4. Submit your site to: Google Search Console, Bing Webmaster Tools
5. List your tool on:
   - alternativeto.net
   - toolify.ai
   - producthunt.com (launch there!)
   - there.io
   - uneed.best

Add these to your `<head>` right now:
```html
<title>MailGuard — Free Bulk DKIM, SPF, DMARC & MX Checker</title>
<meta name="description" content="Check DKIM, SPF, DMARC and MX records in bulk. Free email DNS health checker for Google Workspace, Microsoft 365 and more.">
<meta name="keywords" content="DKIM checker, SPF checker, DMARC checker, MX record lookup, bulk DNS checker">
<meta property="og:title" content="MailGuard — Email DNS Checker">
<meta property="og:description" content="Free bulk email DNS health checker">
```

---

## 9. PERFORMANCE & SECURITY

Your app already includes:
- ✅ Rate limiting (Flask-Limiter) — 30 req/min per IP for DKIM, 20 for others
- ✅ DNS result caching (5 minute TTL, max 2000 entries)
- ✅ Security headers (XSS, clickjacking, content-type sniffing protection)
- ✅ Input sanitization and domain length limits
- ✅ Graceful error handling — never shows Python tracebacks
- ✅ Gunicorn with 2 workers + 4 threads

**Additional things to add when you grow:**
- Move to Redis for rate limiting (prevents bypass across multiple workers)
- Add Cloudflare Bot Fight Mode (free, blocks scrapers)
- Add a CAPTCHA for heavy abuse (hCaptcha is free)

---

## 10. WHAT TO DO NEXT

### Immediately (Today)
- [ ] Upload to GitHub
- [ ] Deploy on Render
- [ ] Test your live URL
- [ ] Set up UptimeRobot to keep it awake

### This Week
- [ ] Buy a domain ($10)
- [ ] Connect domain to Render
- [ ] Set up Cloudflare (free SSL + CDN)
- [ ] Add SEO meta tags to index.html
- [ ] Submit to Google Search Console

### This Month
- [ ] Write 3 blog posts about DKIM/SPF/DMARC
- [ ] Share on Reddit r/sysadmin, r/webdev
- [ ] Launch on Product Hunt
- [ ] Apply for Google AdSense once you have traffic

### When You Have Users
- [ ] Add user login + Stripe for paid plans
- [ ] Add domain monitoring (check every 24h and email alerts)
- [ ] Move to a paid VPS for better performance

---

## QUICK REFERENCE

```
Local development:   python app.py  →  http://localhost:5050
Deploy to Render:    git push origin main  (auto-deploys)
Check health:        https://yourdomain.com/health
Rate limits:         30/min DKIM, 20/min SPF/DMARC/MX per IP
Cache TTL:           5 minutes per domain per check type
```

---

*Created by [Anas Shaikh](https://www.linkedin.com/in/anas-shaikh-80734324b/)*

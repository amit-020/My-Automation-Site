#!/usr/bin/env python3
"""
Bizautosetup static site generator.

Usage:
    py build.py            build all pages, then run output checks
    py build.py --test     run self tests only (security helpers, escaping, validation)
    py build.py --check    run output checks on the existing generated files
    py build.py --open     build, then open index.html in the default browser
    (Mac/Linux: python3 build.py)

Creates: index.html, services/<slug>.html, services/index.html, sitemap.xml, robots.txt
Content lives in: data/services.json and the CFG / GALLERY / COMPARISON / HOME_FAQ blocks below.
Generated files are overwritten on every run. Do not edit them by hand.

Expected static files (not generated here):
    assets/style.css   layout, theme, responsive rules (mobile first)
    assets/app.js      menu, theme, filters, search, gallery, lightbox, forms, calculator,
                       image fallback (see FALLBACK_JS_NOTE below)
"""

import argparse
import datetime
import html
import json
import os
import pathlib
import re
import sys
import tempfile
import urllib.parse
import webbrowser
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent

# =============================================================================
# CONFIG: edit values here only
# =============================================================================
CFG = {
    "site": "https://www.bizautosetup.com",
    "brand": "Bizautosetup",
    "name": "Amit",
    "tagline": "MIS & Automation Specialist",
    "phone_display": "+91 98557 23648",
    "phone_tel": "+919855723648",
    "wa": "919855723648",                       # WhatsApp number: country code + number, digits only
    "email": "info@bizautosetup.com",
    "linkedin": "https://www.linkedin.com/in/amit-gautam-2b513436a/",
    "instagram": "",                            # empty = icon hidden
    "logo": "logo/logo_only.png",
    "photo": "My_pic-2.jpg",
    "video": "video/intro_video.mp4",           # local mp4/webm/ogg, or https embed URL (YouTube/Vimeo). Empty = hidden
    "sheet_url": "https://script.google.com/macros/s/AKfycbxuiLq3i9d2do13jfHXIUSXjS0FTawNYO3Uya5i0MqjoWNBOaWx5CQTZGuD8KE-ZWob/exec",
    "year": datetime.date.today().year,
}

MAX_THUMBS = 3
CATS = {"ops": "Operations", "fin": "Sales & Finance", "comm": "Communication", "tech": "Tech & AI"}
NAV_LINKS = [("About", "about"), ("Services", "services"), ("Gallery", "gallery"),
             ("Process", "process"), ("Savings", "savings"), ("FAQ", "faq"), ("Contact", "contact")]

GALLERY = [
    {"src": "Gallary/MIS_dashboard.png", "cap": "Live MIS dashboard",
     "desc": "Real-time stock, sales and operations overview in one view, updated automatically from your data."},
    {"src": "Gallary/Systems_build.png", "cap": "Systems I build",
     "desc": "Structured data sheets, input forms and role-based access designed around how your team works."},
    {"src": "Gallary/Automate.png", "cap": "Automation at work",
     "desc": "Triggers that send WhatsApp and email alerts, reminders and reports without manual follow-up."},
]

COMPARISON = [
    ("Data entry", "Repeated typing in registers and files", "Entered once, used everywhere"),
    ("Accuracy", "Errors and duplicates", "Validated fields and rules"),
    ("Reporting", "Compiled by hand, often late", "Live dashboards and MIS graphs"),
    ("Follow-ups", "Dependent on staff memory", "Automatic WhatsApp and email reminders"),
    ("Access control", "Files shared without restriction", "Role-based login for each user"),
    ("Continuity", "Work stops when a person is absent", "Process runs on the system"),
]

HOME_TITLE = ("Google Sheets & Apps Script Automation | MIS, CRM, Billing & WhatsApp Systems India "
              "| Bizautosetup")
HOME_DESC = ("Custom MIS dashboards, inventory, billing, HR, CRM and WhatsApp automation built on "
             "Google Sheets and Apps Script. Practical, affordable systems for Indian businesses.")
HOME_FAQ = [
    ("Do I need expensive software?",
     "Most systems run on Google Sheets and Apps Script, which keeps setup and running costs low."),
    ("Can you connect WhatsApp and email?",
     "Yes. I build WhatsApp integrations, automatic emails and chatbots for alerts, reminders and updates."),
    ("Can the system be customised?",
     "Yes. Every system is designed around your process, fields, user roles and reports."),
    ("How do I get a quotation?",
     "Open the system you need, fill the short quotation form and I will send you a quotation."),
]

FONT_URL = "https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap"
SERVICES_FILE = ROOT / "data" / "services.json"

REQUIRED_SERVICE_KEYS = ["slug", "name", "cat", "ico", "short", "desc", "h1", "title",
                         "audience", "features", "faq", "imgs", "pdf"]
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
MEDIA_EXT = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg", ".mp4", ".webm", ".ogg", ".pdf")

# Inline SVG icons: no text glyphs, so alignment is identical on every phone and browser.
WA_ICON = ('<svg viewBox="0 0 24 24" width="28" height="28" fill="#fff" aria-hidden="true" focusable="false">'
           '<path d="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 '
           '1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 '
           '1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z"/></svg>')
TOP_ICON = ('<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" '
            'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'
            '<path d="M12 19V5M5 12l7-7 7 7"/></svg>')
CHAT_ICON = ('<svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" '
             'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'
             '<path d="M21 11.5a8.4 8.4 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.4 8.4 0 0 1-3.8-.9L3 21l1.9-5.7a8.4 '
             '8.4 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6A8.4 8.4 0 0 1 12.5 3h.5a8.5 8.5 0 0 1 8 8z"/>'
             '<circle cx="8.5" cy="11.5" r="1" fill="currentColor"/>'
             '<circle cx="12" cy="11.5" r="1" fill="currentColor"/>'
             '<circle cx="15.5" cy="11.5" r="1" fill="currentColor"/></svg>')
SOCIAL_ICONS = {
    "linkedin": ("LinkedIn", '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true" focusable="false">'
                             '<path d="M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5zM3 9.75h4V21H3V9.75zm6.5 0h3.8v1.5h.05c.53-1 '
                             '1.83-2.05 3.77-2.05 4.03 0 4.78 2.65 4.78 6.1V21h-4v-5.1c0-1.22-.02-2.8-1.7-2.8-1.71 0-1.97 1.33-1.97 '
                             '2.72V21h-4V9.75z"/></svg>'),
    "instagram": ("Instagram", '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" '
                               'stroke-width="2" aria-hidden="true" focusable="false"><rect x="3" y="3" width="18" height="18" '
                               'rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor" '
                               'stroke="none"/></svg>'),
}

FALLBACK_JS_NOTE = """
app.js must handle broken images without inline onerror (CSP blocks inline handlers):
  document.addEventListener('error', e => {
    const img = e.target;
    if (!(img instanceof HTMLImageElement)) return;
    const box = img.closest('[data-fallback]');
    if (box) box.classList.add('missing');
  }, true);
"""


class BuildError(Exception):
    pass


# =============================================================================
# SECURITY HELPERS
# =============================================================================
def esc(value):
    """HTML-escape any value for text or attribute context (quotes included)."""
    return html.escape("" if value is None else str(value), quote=True)


def digits_only(value, label):
    cleaned = re.sub(r"\D", "", str(value))
    if not cleaned or len(cleaned) < 10 or len(cleaned) > 15:
        raise BuildError(f"CFG[{label!r}] must have 10-15 digits, got {value!r}")
    return cleaned


def safe_rel(path, label="path"):
    """Accept only relative paths inside the site folder. Rejects absolute paths, '..', URLs and backslashes."""
    p = str(path).strip()
    if not p or "\\" in p or p.startswith(("/", "~")) or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", p):
        raise BuildError(f"{label}: unsafe or non-relative path {p!r}")
    parts = pathlib.PurePosixPath(p).parts
    if any(part in ("..", "") for part in parts):
        raise BuildError(f"{label}: path traversal not allowed {p!r}")
    return pathlib.PurePosixPath(p).as_posix()


def safe_https(url, label):
    u = str(url).strip()
    if not u:
        return ""
    parsed = urllib.parse.urlparse(u)
    if parsed.scheme != "https" or not parsed.netloc:
        raise BuildError(f"{label}: only https:// URLs allowed, got {u!r}")
    return u


def safe_media(value, label):
    """Local file (relative, safe) or https URL. Used for video and similar."""
    v = str(value or "").strip()
    if not v:
        return ""
    if v.lower().startswith("https://"):
        return safe_https(v, label)
    return safe_rel(v, label)


def wa_link(text):
    return f"https://wa.me/{CFG_WA_DIGITS}?text={urllib.parse.quote(text, safe='')}"


def json_for_html(obj):
    """JSON safe to place inside <script>: escapes < > & so </script> can never close the tag."""
    payload = json.dumps(obj, ensure_ascii=True, separators=(",", ":"))
    return payload.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def ld(obj):
    return f'<script type="application/ld+json">{json_for_html(obj)}</script>'


def search_text(s):
    return esc(" ".join([s["name"], s["short"], s["desc"], *s["features"]]).lower())


def cls(*names):
    return " ".join(n for n in names if n)


def asset(path):
    """Use a .webp twin when present (smaller, faster), otherwise the original."""
    rel = pathlib.PurePosixPath(path)
    webp = rel.with_suffix(".webp")
    return webp.as_posix() if (ROOT / webp).exists() else rel.as_posix()


CSP = ("default-src 'self'; img-src 'self' data: https:; media-src 'self' https:; "
       "frame-src https://www.youtube.com https://www.youtube-nocookie.com https://player.vimeo.com; "
       "style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; "
       "script-src 'self'; connect-src 'self' https://script.google.com https://script.googleusercontent.com; "
       "form-action 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'self'")


# =============================================================================
# VALIDATION
# =============================================================================
def validate_config():
    global CFG_WA_DIGITS
    CFG_WA_DIGITS = digits_only(CFG["wa"], "wa")
    digits_only(CFG["phone_tel"], "phone_tel")
    if not EMAIL_RE.match(CFG["email"]):
        raise BuildError(f"CFG['email'] is not a valid email: {CFG['email']!r}")
    CFG["site"] = safe_https(CFG["site"], "CFG['site']").rstrip("/")
    CFG["sheet_url"] = safe_https(CFG["sheet_url"], "CFG['sheet_url']")
    if "PASTE" in CFG["sheet_url"] or "AKfy" not in CFG["sheet_url"]:
        print("WARNING: CFG['sheet_url'] looks like a placeholder. Form submissions will not reach the sheet.")
    CFG["linkedin"] = safe_https(CFG["linkedin"], "CFG['linkedin']") if CFG["linkedin"] else ""
    CFG["instagram"] = safe_https(CFG["instagram"], "CFG['instagram']") if CFG["instagram"] else ""
    CFG["logo"] = safe_rel(CFG["logo"], "CFG['logo']")
    CFG["photo"] = safe_rel(CFG["photo"], "CFG['photo']")
    CFG["video"] = safe_media(CFG["video"], "CFG['video']")
    if not isinstance(CFG["year"], int) or not 2000 <= CFG["year"] <= 2100:
        raise BuildError("CFG['year'] must be a plausible year")
    for g in GALLERY:
        g["src"] = safe_rel(g["src"], "GALLERY src")


def load_services():
    if not SERVICES_FILE.exists():
        raise BuildError(f"Missing {SERVICES_FILE.relative_to(ROOT)}. Create data/services.json first.")
    try:
        data = json.loads(SERVICES_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BuildError(f"services.json is not valid JSON: {exc}") from exc
    services = data.get("services")
    if not isinstance(services, list) or not services:
        raise BuildError("services.json must contain a non-empty 'services' list")
    return services


def validate_services(services):
    seen = set()
    for s in services:
        slug = s.get("slug", "?")
        missing = [k for k in REQUIRED_SERVICE_KEYS if k not in s]
        if missing:
            raise BuildError(f"service '{slug}' is missing keys: {missing}")
        if not SLUG_RE.match(slug):
            raise BuildError(f"slug {slug!r} must be lowercase letters, digits and hyphens")
        if slug in seen:
            raise BuildError(f"duplicate slug {slug!r}")
        seen.add(slug)
        if s["cat"] not in CATS:
            raise BuildError(f"service '{slug}' has unknown category {s['cat']!r}; allowed {list(CATS)}")
        if not isinstance(s["features"], list) or not isinstance(s["imgs"], list):
            raise BuildError(f"service '{slug}': 'features' and 'imgs' must be lists")
        if not isinstance(s["faq"], dict) or "q" not in s["faq"] or "a" not in s["faq"]:
            raise BuildError(f"service '{slug}': 'faq' needs 'q' and 'a'")
        s["imgs"] = [safe_rel(p, f"{slug} imgs") for p in s["imgs"]]
        s["pdf"] = safe_rel(s["pdf"], f"{slug} pdf") if s["pdf"] else ""
        if s["pdf"] and not s["pdf"].lower().endswith(".pdf"):
            raise BuildError(f"service '{slug}': pdf must end with .pdf")


# =============================================================================
# SHARED PARTS
# =============================================================================
def nav(prefix):
    def link(sid):
        return f"{prefix}index.html#{sid}" if prefix else f"#{sid}"

    links = "".join(f'<a href="{esc(link(sid))}">{esc(label)}</a>' for label, sid in NAV_LINKS)
    home = f"{prefix}index.html" if prefix else "#hero"
    return f"""<nav id="nav" class="nav" aria-label="Main">
  <div class="wrap nav-in">
    <a class="brand" href="{esc(home)}">
      <img src="{esc(prefix + asset(CFG['logo']))}" width="40" height="40" alt="{esc(CFG['brand'])} logo">
      <span>{esc(CFG['brand'])}</span>
    </a>
    <div class="links" id="links">{links}</div>
    <div class="nav-r">
      <button class="theme" id="themeBtn" type="button">Light mode</button>
      <button class="burger" id="burger" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="links">
        <span aria-hidden="true">&#9776;</span>
      </button>
    </div>
  </div>
</nav>"""


def social_links():
    items = []
    for key, (label, svg) in SOCIAL_ICONS.items():
        url = CFG.get(key, "")
        if url:
            items.append(f'<a class="soc" href="{esc(url)}" target="_blank" rel="noopener noreferrer" '
                         f'aria-label="{esc(label)}" title="{esc(label)}">{svg}</a>')
    return f'<div class="social">{"".join(items)}</div>' if items else ""


def footer(prefix=""):
    hello = wa_link(f"Hello {CFG['name']}, I would like to discuss an automation project.")
    return f"""<footer class="foot">
  <div class="wrap foot-in">
    <div class="foot-left">
      <b>{esc(CFG['brand'])}</b>
      <p>{esc(CFG['name'])}, {esc(CFG['tagline'])}</p>
      {social_links()}
    </div>
    <div class="foot-contact">
      <p>Mobile: <a href="tel:{esc(CFG['phone_tel'])}">{esc(CFG['phone_display'])}</a></p>
      <p>Email: <a href="mailto:{esc(CFG['email'])}">{esc(CFG['email'])}</a></p>
    </div>
    <div class="copy">&copy; {CFG['year']} {esc(CFG['brand'])}. All rights reserved.</div>
  </div>
</footer>

<a id="wa" class="fab fab-wa" href="{esc(hello)}" target="_blank" rel="noopener noreferrer" aria-label="Chat on WhatsApp">{WA_ICON}</a>
<a id="top" class="fab fab-top" href="#" aria-label="Back to top" hidden>{TOP_ICON}</a>

<button id="botBtn" class="fab fab-bot" type="button" aria-label="Open chat assistant" aria-expanded="false" aria-controls="bot">{CHAT_ICON}</button>
<div id="bot" class="bot" role="dialog" aria-label="Bizautosetup assistant" hidden>
  <div class="bot-head">
    <div><b>Bizautosetup Assistant</b><small>Quick answers</small></div>
    <button id="botClose" class="icon-btn light" type="button" aria-label="Close chat">&times;</button>
  </div>
  <div id="botLog" class="bot-log" aria-live="polite"></div>
  <div id="botOpts" class="bot-opts"></div>
</div>

<div class="modal" id="gm" role="dialog" aria-modal="true" aria-labelledby="gmTitle" hidden>
  <div class="sheet">
    <div class="sheet-head">
      <div><h3 id="gmTitle">Sample screens</h3><small id="gmSub"></small></div>
      <button class="icon-btn" type="button" data-close aria-label="Close">&times;</button>
    </div>
    <div class="sheet-body"><div class="gal-all" id="gmGrid"></div></div>
  </div>
</div>

<div id="lb" role="dialog" aria-modal="true" aria-label="Image viewer" hidden>
  <div class="lb-top">
    <div class="lb-cap" id="lbCap"></div>
    <div class="lb-tools">
      <button type="button" id="lbZoom" title="Zoom (Z)">Zoom</button>
      <button type="button" id="lbClose" title="Close (Esc)" aria-label="Close">&times;</button>
    </div>
  </div>
  <div class="lb-stage" id="lbStage"><img id="lbImg" alt=""></div>
  <button class="lb-nav lb-prev" id="lbPrev" type="button" aria-label="Previous image">&lsaquo;</button>
  <button class="lb-nav lb-next" id="lbNext" type="button" aria-label="Next image">&rsaquo;</button>
  <div class="lb-foot" id="lbCount"></div>
</div>"""


def page(title, desc, path, prefix, body, schema):
    url = f"{CFG['site']}/{path}"
    schema_tags = "\n".join(ld(x) for x in schema)
    return f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta http-equiv="Content-Security-Policy" content="{esc(CSP)}">
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta name="theme-color" content="#0a1122">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{esc(url)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(CFG['brand'])}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{esc(url)}">
<meta property="og:image" content="{esc(CFG['site'] + '/' + CFG['logo'])}">
<link rel="icon" type="image/png" href="{esc(prefix + CFG['logo'])}">
<link rel="apple-touch-icon" href="{esc(prefix + CFG['logo'])}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{esc(FONT_URL)}">
<link rel="stylesheet" href="{esc(prefix)}assets/style.css">
{schema_tags}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{nav(prefix)}
<main id="main">
{body}
</main>
{footer(prefix)}
<script src="{esc(prefix)}assets/app.js" defer></script>
</body>
</html>
"""


def field(label, control):
    return f'<label class="field"><span>{esc(label)}</span>{control}</label>'


def lead_form(kind, service=None, pdf=""):
    extra = f' data-pdf="{esc(pdf)}"' if pdf else ""
    if service:
        svc = f'<input type="hidden" name="service" value="{esc(service)}">'
        placeholder = "Requirement (optional): extra features, users, scope"
        label = "Request quotation"
    else:
        opts = "".join(f'<option value="{esc(s["name"])}">{esc(s["name"])}</option>' for s in SERVICES)
        svc = field("System", f'<select name="service"><option value="">Select a system (optional)</option>{opts}</select>')
        placeholder = "Briefly describe your requirement"
        label = "Send request"
    return f"""<form class="lead" data-type="{esc(kind)}" data-endpoint="{esc(CFG['sheet_url'])}"{extra} novalidate>
  <div class="notice" role="status" hidden>
    <span class="ni" aria-hidden="true">&#10003;</span>
    <div><b class="nt"></b><p class="np"></p><a class="nl" target="_blank" rel="noopener noreferrer" hidden>Message on WhatsApp</a></div>
  </div>
  {svc}
  <div class="grid2">
    {field("Name", '<input name="name" required maxlength="80" placeholder="Your name" autocomplete="name">')}
    {field("Company (optional)", '<input name="company" maxlength="120" placeholder="Company / firm">')}
  </div>
  <div class="grid2">
    {field("Phone / WhatsApp", '<input name="phone" type="tel" required placeholder="10-digit number" pattern="[0-9+ ]{{10,15}}" autocomplete="tel">')}
    {field("Email", '<input name="email" type="email" required maxlength="120" placeholder="you@example.com" autocomplete="email">')}
  </div>
  {field("Requirement", f'<textarea name="message" rows="4" maxlength="2000" placeholder="{esc(placeholder)}"></textarea>')}
  <input class="hp" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">
  <button class="btn btn-p btn-block" type="submit">{label}</button>
  <p class="fine">Your details are used only to reply to your request.</p>
</form>"""


def card(s, href):
    return (
        f'<a class="card rv" href="{esc(href)}" data-cat="{esc(s["cat"])}" data-search="{search_text(s)}">'
        f'<span class="ico" aria-hidden="true">{esc(s["ico"])}</span>'
        f'<span class="cat-tag">{esc(CATS[s["cat"]])}</span>'
        f'<h3>{esc(s["name"])}</h3>'
        f'<p>{esc(s["short"])}</p>'
        f'<span class="go">View details and samples &rarr;</span>'
        f'</a>'
    )


def gallery_section():
    tabs = "".join(
        f'<button class="g-tab{cls(" on" if i == 0 else "")}" type="button" role="tab" data-idx="{i}" '
        f'aria-selected="{"true" if i == 0 else "false"}">{esc(g["cap"])}</button>'
        for i, g in enumerate(GALLERY)
    )
    slides = "".join(
        f'<figure class="g-slide{cls(" on" if i == 0 else "")}" data-idx="{i}" data-fallback>'
        f'<img src="{esc(asset(g["src"]))}" alt="{esc(g["cap"])}" loading="lazy" decoding="async">'
        f'</figure>'
        for i, g in enumerate(GALLERY)
    )
    descs = "".join(
        f'<p class="g-desc{cls(" on" if i == 0 else "")}" data-idx="{i}">{esc(g["desc"])}</p>'
        for i, g in enumerate(GALLERY)
    )
    return f"""<section id="gallery" class="section">
  <div class="wrap">
    <div class="sec-head rv">
      <span class="eyebrow">Gallery</span>
      <h2>Inside the systems</h2>
      <p class="lead">A look at the dashboards, services and workflows I design for businesses.</p>
    </div>
    <div class="showcase rv" id="showcase">
      <div class="g-tabs" role="tablist" aria-label="Gallery">{tabs}</div>
      <div class="g-frame">
        <div class="g-stage">{slides}</div>
        <div class="g-caption">{descs}</div>
      </div>
    </div>
  </div>
</section>"""


def comparison_section():
    rows = "".join(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td></tr>" for a, b, c in COMPARISON)
    return f"""<section class="section alt" id="comparison">
  <div class="wrap">
    <div class="sec-head rv">
      <span class="eyebrow">Manual vs automated</span>
      <h2>From manual effort to a system that runs itself</h2>
      <p class="lead">How day-to-day work changes once your data, follow-ups and reports are structured.</p>
    </div>
    <div class="tbl-wrap rv">
      <table class="cmp">
        <caption class="sr">Manual work compared with automated work</caption>
        <thead><tr><th scope="col">Area</th><th scope="col">Manual work</th><th scope="col">With automation</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
  </div>
</section>"""


# =============================================================================
# HOMEPAGE
# =============================================================================
def home_page():
    counts = {k: sum(1 for s in SERVICES if s["cat"] == k) for k in CATS}
    chips = [f'<button class="chip on" data-cat="all" type="button">All <span>{len(SERVICES)}</span></button>']
    chips += [f'<button class="chip" data-cat="{esc(k)}" type="button">{esc(v)} <span>{counts[k]}</span></button>'
              for k, v in CATS.items()]
    cards = "".join(card(s, f"services/{s['slug']}.html") for s in SERVICES)
    faqs = "".join(f'<details class="rv"><summary>{esc(q)}</summary><p>{esc(a)}</p></details>'
                   for q, a in HOME_FAQ)

    demo = ""
    if CFG["video"]:
        src = CFG["video"]
        if src.lower().startswith("https://"):
            player = (f'<iframe src="{esc(src)}" title="Demo video" loading="lazy" '
                      f'referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>')
        else:
            player = f'<video src="{esc(src)}" controls playsinline preload="metadata"></video>'
        demo = f"""<section class="section" id="demo">
  <div class="wrap">
    <div class="sec-head rv"><span class="eyebrow">Live demo</span><h2>See a system in action</h2></div>
    <div class="screen rv">{player}</div>
  </div>
</section>"""

    body = f"""
<section id="hero" class="hero">
  <div class="wrap hero-grid">
    <div class="hero-text">
      <span class="eyebrow">{esc(CFG['tagline'])}</span>
      <h1>Automated systems that keep your business organised</h1>
      <div class="role" id="role" aria-live="polite"></div>
      <p class="lead">I build inventory, production, billing, HR, CRM and WhatsApp systems your team can use from day one. Practical, reliable and easy to maintain.</p>
      <div class="row">
        <a class="btn btn-p" href="#services">View services</a>
        <a class="btn btn-o" href="#contact">Contact me</a>
      </div>
    </div>
    <aside class="glass">
      <img class="logo" src="{esc(asset(CFG['logo']))}" width="84" height="84" alt="{esc(CFG['brand'])} logo">
      <h3>{esc(CFG['name'])}</h3>
      <p class="sub">MIS reporting &middot; Process automation &middot; Custom systems</p>
      <ul class="ticks light">
        <li>Clean data structure and live dashboards</li>
        <li>WhatsApp, email and API automation</li>
        <li>Training and support after delivery</li>
      </ul>
    </aside>
  </div>
</section>

{demo}

<section id="about" class="section alt">
  <div class="wrap two">
    <div class="photo-col rv">
      <div class="photo" data-fallback>
        <img id="myPhoto" src="{esc(asset(CFG['photo']))}" alt="{esc(CFG['name'])}, {esc(CFG['tagline'])}" loading="lazy">
        <div class="photo-fallback">Your photo here<small>Place {esc(CFG['photo'])} next to index.html</small></div>
      </div>
    </div>
    <div class="rv d2">
      <span class="eyebrow">About me</span>
      <h2>Hi, I&rsquo;m {esc(CFG['name'])}</h2>
      <p class="lead">I am an MIS &amp; Automation Specialist with <b>6 years of hands-on experience</b>. I have designed systems for manufacturing units, real estate firms, retail stores and many other businesses.</p>
      <p class="lead">I turn manual registers, scattered spreadsheets and repeated follow-ups into structured systems that save time, reduce mistakes and give owners clear reports every day.</p>
      <div class="stats">
        <div><b>14+</b><small>System types</small></div>
        <div><b>End-to-end</b><small>Build to support</small></div>
        <div><b>Custom</b><small>Built to your process</small></div>
      </div>
      <div class="box mt">
        <h3>What I offer</h3>
        <ul class="ticks">
          <li>Custom business systems on Google Sheets &amp; Apps Script</li>
          <li>MIS dashboards and graphs for daily decisions</li>
          <li>WhatsApp, email and API automation</li>
          <li>Chatbots and AI-based workflows</li>
          <li>Training, documentation and ongoing support</li>
        </ul>
      </div>
    </div>
  </div>
</section>

{gallery_section()}

<section id="services" class="section">
  <div class="wrap">
    <div class="sec-head rv">
      <span class="eyebrow">Services</span>
      <h2>Systems I build for businesses</h2>
      <p class="lead">Filter by category or search by feature. Open any system to see its details, sample screens and quotation form.</p>
    </div>
    <div class="toolbar rv">
      <div class="chips" id="chips">{"".join(chips)}</div>
      <label class="search">
        <span class="sr">Search systems</span>
        <input id="q" type="search" maxlength="60" placeholder="Search e.g. stock, WhatsApp, payroll" autocomplete="off">
      </label>
      <div class="count" id="count" aria-live="polite"></div>
    </div>
    <div class="grid" id="svcGrid">{cards}</div>
    <p class="empty-msg" id="empty" hidden>No system matches your search. Try another keyword or category.</p>
  </div>
</section>

{comparison_section()}

<section id="process" class="section">
  <div class="wrap">
    <div class="sec-head rv"><span class="eyebrow">How it works</span><h2>From requirement to live system</h2></div>
    <ol class="steps">
      <li class="step rv"><b>Step 01</b><h3>Discuss</h3><p>Understand your process, problems and goals.</p></li>
      <li class="step rv d1"><b>Step 02</b><h3>Design</h3><p>Plan data structure, workflow, dashboards and user roles.</p></li>
      <li class="step rv d2"><b>Step 03</b><h3>Build &amp; test</h3><p>Develop in stages and verify each part with you.</p></li>
      <li class="step rv d3"><b>Step 04</b><h3>Deliver &amp; support</h3><p>Go live, train your team and keep improving.</p></li>
    </ol>
  </div>
</section>

<section id="savings" class="section alt">
  <div class="wrap">
    <div class="sec-head rv">
      <span class="eyebrow">Savings calculator</span>
      <h2>How much can automation save you?</h2>
      <p class="lead">Enter your current manual work to estimate monthly and yearly savings.</p>
    </div>
    <div class="calc rv" id="calc">
      <div class="calc-in">
        {field("People doing manual work", '<input id="cStaff" type="number" min="1" max="500" value="3">')}
        {field("Hours per day, each person", '<input id="cHours" type="number" min="0" max="24" step="0.5" value="3">')}
        {field("Monthly salary per person (₹)", '<input id="cSalary" type="number" min="0" max="10000000" value="18000">')}
        {field("Working days per month", '<input id="cDays" type="number" min="1" max="31" value="26">')}
        {field("Time saved after automation (%)", '<input id="cPct" type="number" min="0" max="100" value="70">')}
      </div>
      <div class="res-col">
        <div class="res"><small>Hours saved per month</small><b id="rHours">–</b></div>
        <div class="res"><small>Money saved per month</small><b id="rMonth">–</b></div>
        <div class="res"><small>Money saved per year</small><b id="rYear">–</b></div>
      </div>
    </div>
    <p class="note center">Estimate only. Actual savings depend on your process. Final pricing is shared after I review your requirement.</p>
  </div>
</section>

<section id="faq" class="section">
  <div class="wrap narrow">
    <div class="sec-head rv"><span class="eyebrow">FAQ</span><h2>Frequently asked questions</h2></div>
    {faqs}
  </div>
</section>

<section id="contact" class="section alt">
  <div class="wrap two">
    <div class="rv">
      <span class="eyebrow">Contact</span>
      <h2>Let&rsquo;s discuss your requirement</h2>
      <p class="lead">Share your process and I will suggest the right system and send a quotation.</p>
      <div class="c-list">
        <a class="c-item" href="mailto:{esc(CFG['email'])}"><span class="c-ico" aria-hidden="true">&#9993;</span><span><small>Email</small><b>{esc(CFG['email'])}</b></span></a>
        <a class="c-item" href="{esc(wa_link(CFG['name'] + ', I would like to discuss an automation project.'))}" target="_blank" rel="noopener noreferrer"><span class="c-ico" aria-hidden="true">&#9742;</span><span><small>WhatsApp / Mobile</small><b>{esc(CFG['phone_display'])}</b></span></a>
      </div>
    </div>
    <div class="box rv d2">
      {lead_form("Contact")}
    </div>
  </div>
</section>
"""

    schema = [
        {
            "@context": "https://schema.org",
            "@type": "ProfessionalService",
            "name": f"{CFG['brand']}: {CFG['name']}, {CFG['tagline']}",
            "url": CFG["site"] + "/",
            "logo": f"{CFG['site']}/{CFG['logo']}",
            "telephone": "+" + CFG_WA_DIGITS,
            "email": CFG["email"],
            "description": HOME_DESC,
            "areaServed": "IN",
            "founder": {"@type": "Person", "name": CFG["name"]},
        },
        {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q,
                            "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in HOME_FAQ],
        },
        {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": "Systems built by Bizautosetup",
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": s["name"],
                 "url": f"{CFG['site']}/services/{s['slug']}.html"}
                for i, s in enumerate(SERVICES)
            ],
        },
    ]
    return page(HOME_TITLE, HOME_DESC, "", "", body, schema)


# =============================================================================
# SERVICE PAGES
# =============================================================================
def service_page(s):
    prefix = "../"
    slug, name = s["slug"], s["name"]
    path = f"services/{slug}.html"
    url = f"{CFG['site']}/{path}"
    pdf = (prefix + s["pdf"]) if s["pdf"] else ""
    wa_btn = wa_link(f"Hello, I am interested in: {name}")
    faq = s["faq"]
    features = "".join(f"<li>{esc(f)}</li>" for f in s["features"])

    imgs = [{"src": prefix + asset(p), "alt": f"{name} sample screen {i + 1}"} for i, p in enumerate(s["imgs"])]
    total = len(imgs)
    if total:
        thumbs = []
        for i, it in enumerate(imgs[:MAX_THUMBS]):
            is_more = total > MAX_THUMBS and i == MAX_THUMBS - 1
            action = "data-all" if is_more else f'data-open="{i}"'
            overlay = f'<span class="more">+{total - MAX_THUMBS} more</span>' if is_more else ""
            thumbs.append(
                f'<button class="thumb" type="button" {action} aria-label="{esc(it["alt"])}" data-fallback>'
                f'<img src="{esc(it["src"])}" alt="{esc(it["alt"])}" loading="lazy" decoding="async">'
                f'<span class="thumb-missing">Screen not available</span>{overlay}</button>'
            )
        samples = f"""<section class="section alt" id="samples">
  <div class="wrap">
    <div class="sec-head-row rv">
      <div><span class="eyebrow">Sample screens</span><h2>Inside the {esc(name)}</h2></div>
      <button class="btn btn-o btn-sm" type="button" data-all>View all {total}</button>
    </div>
    <div class="gal rv">{"".join(thumbs)}</div>
  </div>
  <script type="application/json" id="gal-data">{json_for_html(imgs)}</script>
</section>"""
    else:
        samples = """<section class="section alt" id="samples">
  <div class="wrap"><div class="empty">Sample screens coming soon</div></div>
</section>"""

    related = sorted([o for o in SERVICES if o["slug"] != slug], key=lambda o: o["cat"] != s["cat"])[:6]
    related_cards = "".join(card(o, f"{o['slug']}.html") for o in related)

    body = f"""
<header class="svc-hero">
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb">
      <a href="../index.html">Home</a> <span aria-hidden="true">/</span> <a href="../index.html#services">Services</a> <span aria-hidden="true">/</span> <span>{esc(name)}</span>
    </nav>
    <span class="cat-tag">{esc(CATS[s['cat']])}</span>
    <h1>{esc(s['h1'])}</h1>
    <p class="lead">{esc(s['desc'])}</p>
    <p class="price">Quotation on request</p>
    <div class="row mt">
      <a class="btn btn-p" href="#quote">Request quotation</a>
      <a class="btn btn-o" href="{esc(wa_btn)}" target="_blank" rel="noopener noreferrer">Ask on WhatsApp</a>
    </div>
  </div>
</header>

<section class="section">
  <div class="wrap two">
    <div class="rv">
      <h2>Key features</h2>
      <ul class="ticks">{features}</ul>
      <h3 class="mt">Who this is for</h3>
      <p class="lead">{esc(s['audience'])}</p>
      <h3 class="mt">Common question</h3>
      <details><summary>{esc(faq['q'])}</summary><p>{esc(faq['a'])}</p></details>
    </div>
    <div class="box rv d2" id="quote">
      <h3>Get a quotation</h3>
      <p class="note">Pricing depends on your process. Share your requirement and I will send a quotation.</p>
      {lead_form("Quotation", name, pdf)}
    </div>
  </div>
</section>

{samples}

<section class="section">
  <div class="wrap">
    <div class="sec-head rv"><span class="eyebrow">Related systems</span><h2>You may also need</h2></div>
    <div class="grid">{related_cards}</div>
  </div>
</section>
"""

    schema = [
        {
            "@context": "https://schema.org",
            "@type": "Service",
            "name": name,
            "serviceType": name,
            "description": s["desc"],
            "url": url,
            "areaServed": "IN",
            "provider": {
                "@type": "ProfessionalService",
                "name": CFG["brand"],
                "telephone": "+" + CFG_WA_DIGITS,
                "email": CFG["email"],
                "url": CFG["site"] + "/",
            },
        },
        {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": faq["q"],
                            "acceptedAnswer": {"@type": "Answer", "text": faq["a"]}}],
        },
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": CFG["site"] + "/"},
                {"@type": "ListItem", "position": 2, "name": "Services", "item": CFG["site"] + "/#services"},
                {"@type": "ListItem", "position": 3, "name": name, "item": url},
            ],
        },
    ]
    return page(s["title"], s["desc"], path, prefix, body, schema)


def services_redirect():
    target = "../index.html#services"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url={esc(target)}">
<link rel="canonical" href="{esc(CFG['site'])}/">
<title>Services | {esc(CFG['brand'])}</title>
</head>
<body>
<p>Redirecting to <a href="{esc(target)}">services</a>.</p>
</body>
</html>
"""


# =============================================================================
# SITEMAP / ROBOTS
# =============================================================================
def sitemap():
    urls = [(CFG["site"] + "/", "1.0")]
    urls += [(f"{CFG['site']}/services/{s['slug']}.html", "0.8") for s in SERVICES]
    today = datetime.date.today().isoformat()
    entries = "\n".join(
        f"  <url>\n    <loc>{esc(u)}</loc>\n    <lastmod>{today}</lastmod>\n    <priority>{p}</priority>\n  </url>"
        for u, p in urls
    )
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{entries}\n</urlset>\n")


def robots():
    return f"User-agent: *\nAllow: /\n\nSitemap: {CFG['site']}/sitemap.xml\n"


# =============================================================================
# FILE WRITING
# =============================================================================
def write_atomic(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=path.suffix)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


# =============================================================================
# OUTPUT CHECKS (security + structure + references)
# =============================================================================
WATCH_TAGS = {"div", "section", "nav", "footer", "form", "ul", "ol", "table", "details",
              "main", "header", "button", "a", "label", "figure", "aside"}


class TagBalance(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.open_count = {}
        self.close_count = {}

    def handle_starttag(self, tag, attrs):
        if tag in WATCH_TAGS:
            self.open_count[tag] = self.open_count.get(tag, 0) + 1

    def handle_endtag(self, tag):
        if tag in WATCH_TAGS:
            self.close_count[tag] = self.close_count.get(tag, 0) + 1


class RefCollector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in ("src", "href") and value:
                self.refs.append((tag, name, value))


INLINE_HANDLER_RE = re.compile(r"""\son[a-z]+\s*=""", re.IGNORECASE)
SCRIPT_TAG_RE = re.compile(r"<script\b([^>]*)>", re.IGNORECASE)


def check_page(path, text, errors, warnings):
    rel = path.relative_to(ROOT).as_posix()

    balance = TagBalance()
    balance.feed(text)
    for tag in WATCH_TAGS:
        o, c = balance.open_count.get(tag, 0), balance.close_count.get(tag, 0)
        if o != c:
            errors.append(f"{rel}: <{tag}> open={o} close={c}")

    if INLINE_HANDLER_RE.search(text):
        errors.append(f"{rel}: inline event handler found (blocked by CSP). Remove on*= attributes.")

    for m in SCRIPT_TAG_RE.finditer(text):
        attrs = m.group(1).lower()
        if "src=" in attrs or "application/ld+json" in attrs or "application/json" in attrs:
            continue
        errors.append(f"{rel}: inline <script> without src found")

    if "\u2706" in text or "\u2191</a>" in text:
        errors.append(f"{rel}: text glyph icon found (alignment risk). Use SVG icons.")

    refs = RefCollector()
    refs.feed(text)
    for tag, attr, value in refs.refs:
        low = value.strip().lower()
        if low.startswith("javascript:"):
            errors.append(f"{rel}: javascript: URL in <{tag} {attr}>")
            continue
        if low.startswith(("http://", "https://", "mailto:", "tel:", "#", "data:")):
            if low.startswith("http://"):
                errors.append(f"{rel}: insecure http:// link {value!r}")
            continue
        target = (path.parent / value.split("?")[0].split("#")[0]).resolve()
        if not target.exists():
            msg = f"{rel}: missing file referenced by <{tag} {attr}>: {value}"
            if value.startswith("assets/"):
                errors.append(msg)
            else:
                warnings.append(msg)


def check_output(pages):
    errors, warnings = [], []
    for path in [ROOT / "assets" / "style.css", ROOT / "assets" / "app.js"]:
        if not path.exists():
            errors.append(f"missing {path.relative_to(ROOT).as_posix()}")
    for path, text in pages.items():
        check_page(path, text, errors, warnings)
    return errors, warnings


# =============================================================================
# SELF TESTS
# =============================================================================
def run_tests():
    global CFG_WA_DIGITS
    CFG_WA_DIGITS = "919855723648"
    failures = 0

    def case(name, fn):
        nonlocal failures
        try:
            fn()
            print(f"  ok    {name}")
        except AssertionError as exc:
            failures += 1
            print(f"  FAIL  {name}: {exc}")
        except Exception as exc:  # unexpected error is a failure too
            failures += 1
            print(f"  ERROR {name}: {type(exc).__name__}: {exc}")

    def t_escape():
        assert esc('<a href="x">&\'') == "&lt;a href=&quot;x&quot;&gt;&amp;&#x27;"

    def t_safe_rel_ok():
        assert safe_rel("logo/logo_only.png") == "logo/logo_only.png"

    def t_safe_rel_traversal():
        for bad in ["../secret.txt", "a/../../b", "/etc/passwd", "https://x.com/a.png", "a\\b.png", ""]:
            try:
                safe_rel(bad)
            except BuildError:
                continue
            raise AssertionError(f"accepted unsafe path {bad!r}")

    def t_https_only():
        try:
            safe_https("http://insecure.example", "t")
        except BuildError:
            return
        raise AssertionError("accepted http://")

    def t_json_for_html():
        out = json_for_html({"x": "</script><script>alert(1)</script>"})
        assert "</script" not in out and "<script" not in out

    def t_ld_block_closes_once():
        block = ld({"name": "</script><img src=x onerror=alert(1)>"})
        assert block.count("</script>") == 1

    def t_digits():
        assert digits_only("+91 98557-23648", "x") == "919855723648"
        try:
            digits_only("123", "x")
        except BuildError:
            return
        raise AssertionError("accepted short number")

    def t_wa_link_encoded():
        link = wa_link("Hi & bye <tag>")
        assert link.startswith("https://wa.me/919855723648?text=")
        assert "<" not in link and " " not in link

    def t_slug():
        assert SLUG_RE.match("fms-flowchart-management")
        assert not SLUG_RE.match("Bad Slug!")
        assert not SLUG_RE.match("../x")

    def t_wa_attr_escaped():
        out = esc(wa_link('"><script>alert(1)</script>'))
        assert "<script" not in out and '"' not in out

    print("Running self tests")
    for name, fn in [
        ("esc escapes quotes and markup", t_escape),
        ("safe_rel accepts plain relative path", t_safe_rel_ok),
        ("safe_rel rejects traversal, absolute, URL, backslash", t_safe_rel_traversal),
        ("safe_https rejects http", t_https_only),
        ("json_for_html removes script closers", t_json_for_html),
        ("ld block cannot break out of script tag", t_ld_block_closes_once),
        ("digits_only validates phone length", t_digits),
        ("wa_link is URL-encoded", t_wa_link_encoded),
        ("slug pattern", t_slug),
        ("wa attribute is escaped", t_wa_attr_escaped),
    ]:
        case(name, fn)
    print(f"Self tests: {'PASSED' if failures == 0 else f'{failures} FAILED'}")
    return failures == 0


# =============================================================================
# MAIN
# =============================================================================
SERVICES = []


def build():
    global SERVICES
    validate_config()
    SERVICES = load_services()
    validate_services(SERVICES)

    pages = {}
    pages[ROOT / "index.html"] = home_page()
    for s in SERVICES:
        pages[ROOT / "services" / f"{s['slug']}.html"] = service_page(s)
    pages[ROOT / "services" / "index.html"] = services_redirect()

    for path, text in pages.items():
        write_atomic(path, text)
    write_atomic(ROOT / "sitemap.xml", sitemap())
    write_atomic(ROOT / "robots.txt", robots())
    return pages


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build the Bizautosetup site.")
    parser.add_argument("--test", action="store_true", help="run self tests only")
    parser.add_argument("--check", action="store_true", help="check generated files only")
    parser.add_argument("--open", action="store_true", help="open index.html after build")
    args = parser.parse_args(argv)

    try:
        if args.test:
            return 0 if run_tests() else 1

        if args.check:
            validate_config()
            pages = {p: p.read_text(encoding="utf-8") for p in
                     [ROOT / "index.html", *sorted((ROOT / "services").glob("*.html"))] if p.exists()}
        else:
            if not run_tests():
                print("Build stopped: self tests failed.")
                return 1
            pages = build()
            print(f"Built: index.html, {len(SERVICES)} service pages, sitemap.xml, robots.txt")

        errors, warnings = check_output(pages)
        for w in warnings:
            print("WARNING:", w)
        for e in errors:
            print("ERROR:", e)
        print(f"Checks: {len(errors)} error(s), {len(warnings)} warning(s)")

        if args.open and not errors:
            webbrowser.open((ROOT / "index.html").as_uri())
        return 1 if errors else 0
    except BuildError as exc:
        print(f"BUILD ERROR: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
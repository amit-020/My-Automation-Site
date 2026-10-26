#!/usr/bin/env python3
"""
Bizautosetup site generator.

Run:      py build.py            (Mac/Linux: python3 build.py)
Creates:  index.html, services/*.html, services/index.html, sitemap.xml, robots.txt

Content changes: data/services.json, GALLERY, COMPARISON, HOME_FAQ, CFG below.
Generated files are overwritten on every run, so do not edit them by hand.
"""
import datetime
import html
import json
import pathlib
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent

CFG = {
    "site": "https://www.bizautosetup.com",
    "brand": "Bizautosetup",
    "name": "Amit",
    "tagline": "MIS & Automation Specialist",
    "phone_display": "+91 98557 23648",
    "phone_tel": "+919855723648",
    "wa": "919855723648",                  # WhatsApp number with country code, no +
    "email": "info@bizautosetup.com",
    "linkedin": "https://www.linkedin.com/in/YOUR-PROFILE",     # apna LinkedIn URL
    "instagram": "https://www.instagram.com/YOUR-HANDLE",      # apna Instagram URL
    "logo": "logo/logo_only.png",
    "photo": "My_pic-2.jpg",
    "video": "video/intro_video.mp4",                           # "video/intro_video.mp4" or YouTube/Vimeo embed URL. Empty = hidden
    "sheet_url": "https://script.google.com/macros/s/AKfycbxuiLq3i9d2do13jfHXIUSXjS0FTawNYO3Uya5i0MqjoWNBOaWx5CQTZGuD8KE-ZWob/exec",
    "year": datetime.date.today().year,
}

MAX_THUMBS = 3
CATS = {"ops": "Operations", "fin": "Sales & Finance", "comm": "Communication", "tech": "Tech & AI"}
SCHEMA_CTX = "https://schema.org"
TODAY = datetime.date.today().isoformat()
SERVICES = json.loads((ROOT / "data" / "services.json").read_text(encoding="utf-8"))["services"]
NAV_LINKS = [("About", "about"), ("Services", "services"), ("Gallery", "gallery"),
             ("Process", "process"), ("Savings", "savings"), ("FAQ", "faq"), ("Contact", "contact")]
BROKEN_IMG = "this.closest('.thumb').classList.add('missing')"

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


# ---------- helpers ----------
def esc(value):
    return html.escape(str(value), quote=True)


def wa(text):
    return f"https://wa.me/{CFG['wa']}?text={urllib.parse.quote(text)}"


def ld(obj):
    return f'<script type="application/ld+json">{json.dumps(obj, ensure_ascii=False)}</script>'


def search_text(s):
    return esc(" ".join([s["name"], s["short"], s["desc"], *s["features"]]).lower())


def cls(*names):
    return " ".join(n for n in names if n)


# ---------- shared parts ----------
def nav(prefix):
    # prefix "" = homepage (anchor links), "../" = service page (links back to index.html#section)
    def link(sid):
        return f"{prefix}index.html#{sid}" if prefix else f"#{sid}"

    links = "".join(f'<a href="{link(sid)}">{label}</a>' for label, sid in NAV_LINKS)
    home = f"{prefix}index.html" if prefix else "#hero"
    return f"""<nav id="nav" class="nav">
  <div class="wrap nav-in">
    <a class="brand" href="{home}">
      <img src="{prefix}{CFG['logo']}" alt="{esc(CFG['brand'])} logo">
      <span>{esc(CFG['brand'])}</span>
    </a>
    <div class="links" id="links">{links}</div>
    <div class="nav-r">
      <button class="theme" id="themeBtn" type="button">Light mode</button>
      <button class="burger" id="burger" type="button" aria-label="Open menu" aria-expanded="false">☰</button>
    </div>
  </div>
</nav>"""


def social_links():
    """Social icons: sirf wahi dikhte hain jinka URL CFG mein bhara hai."""
    icons = {
        "linkedin": ("LinkedIn", '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true"><path d="M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5zM3 9.75h4V21H3V9.75zm6.5 0h3.8v1.5h.05c.53-1 1.83-2.05 3.77-2.05 4.03 0 4.78 2.65 4.78 6.1V21h-4v-5.1c0-1.22-.02-2.8-1.7-2.8-1.71 0-1.97 1.33-1.97 2.72V21h-4V9.75z"/></svg>'),
        "instagram": ("Instagram", '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none"/></svg>'),
    }
    items = []
    for key, (label, svg) in icons.items():
        url = CFG.get(key, "")
        if url:
            items.append(f'<a class="soc" href="{esc(url)}" target="_blank" rel="noopener" '
                         f'aria-label="{label}" title="{label}">{svg}</a>')
    return f'<div class="social">{"".join(items)}</div>' if items else ""


def footer():
    hello = wa(f"Hello {CFG['name']}, I would like to discuss an automation project.")
    return f"""<footer class="foot">
  <div class="wrap foot-in">
    <div>
      <b>{esc(CFG['brand'])}</b>
      <p>{esc(CFG['name'])}, {esc(CFG['tagline'])}</p>
      {social_links()}
    </div>
    <div>
      <p>Mobile: <a href="tel:{CFG['phone_tel']}">{esc(CFG['phone_display'])}</a></p>
      <p>Email: <a href="mailto:{esc(CFG['email'])}">{esc(CFG['email'])}</a></p>
    </div>
    <div class="copy">© {CFG['year']} {esc(CFG['brand'])}. All rights reserved.</div>
  </div>
</footer>

<a id="wa" class="fab fab-wa" href="{hello}" target="_blank" rel="noopener" aria-label="WhatsApp chat">✆</a>
<a id="top" class="fab fab-top" href="#" aria-label="Back to top" hidden>↑</a>

<button id="botBtn" class="fab fab-bot" type="button" aria-label="Open chat assistant" aria-expanded="false">💬</button>
<div id="bot" class="bot" role="dialog" aria-label="Bizautosetup assistant" hidden>
  <div class="bot-head">
    <div><b>Bizautosetup Assistant</b><small>Quick answers</small></div>
    <button id="botClose" class="icon-btn light" type="button" aria-label="Close chat">×</button>
  </div>
  <div id="botLog" class="bot-log" aria-live="polite"></div>
  <div id="botOpts" class="bot-opts"></div>
</div>

<div class="modal" id="gm" role="dialog" aria-modal="true" aria-labelledby="gmTitle">
  <div class="sheet">
    <div class="sheet-head">
      <div><h3 id="gmTitle">Sample screens</h3><small id="gmSub"></small></div>
      <button class="icon-btn" type="button" data-close aria-label="Close">×</button>
    </div>
    <div class="sheet-body"><div class="gal-all" id="gmGrid"></div></div>
  </div>
</div>

<div id="lb" role="dialog" aria-modal="true" aria-label="Image viewer">
  <div class="lb-top">
    <div class="lb-cap" id="lbCap"></div>
    <div class="lb-tools">
      <button type="button" id="lbZoom" title="Zoom (Z)">Zoom</button>
      <button type="button" id="lbClose" title="Close (Esc)" aria-label="Close">✕</button>
    </div>
  </div>
  <div class="lb-stage" id="lbStage"><img id="lbImg" alt=""></div>
  <button class="lb-nav lb-prev" id="lbPrev" type="button" aria-label="Previous image">‹</button>
  <button class="lb-nav lb-next" id="lbNext" type="button" aria-label="Next image">›</button>
  <div class="lb-foot" id="lbCount"></div>
</div>"""


def shell(title, desc, path, prefix, body, schema):
    url = f"{CFG['site']}/{path}"
    schema_tags = "\n".join(ld(x) for x in schema)
    return f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{CFG['site']}/{CFG['logo']}">
<link rel="icon" href="{prefix}{CFG['logo']}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{prefix}assets/style.css">
{schema_tags}
</head>
<body data-wa="{CFG['wa']}">
{nav(prefix)}
<main>
{body}
</main>
{footer()}
<script src="{prefix}assets/app.js" defer></script>
</body>
</html>
"""


def lead_form(kind, service=None, pdf=""):
    """Contact form (homepage, with service dropdown) or quotation form (service page, service is fixed)."""
    extra = f' data-pdf="{esc(pdf)}"' if pdf else ""
    if service:
        svc = f'<input type="hidden" name="service" value="{esc(service)}">'
        placeholder = "Requirement (optional): extra features, users, scope"
        label = "Request quotation"
    else:
        opts = "".join(f'<option value="{esc(s["name"])}">{esc(s["name"])}</option>' for s in SERVICES)
        svc = f'<label class="field"><span>System</span><select name="service"><option value="">Select a system (optional)</option>{opts}</select></label>'
        placeholder = "Briefly describe your requirement"
        label = "Send request"
    return f"""<form class="lead" data-type="{kind}" data-endpoint="{esc(CFG['sheet_url'])}"{extra}>
  <div class="notice" role="status" hidden>
    <span class="ni">✓</span>
    <div><b class="nt"></b><p class="np"></p><a class="nl" target="_blank" rel="noopener" hidden>Message on WhatsApp</a></div>
  </div>
  {svc}
  <div class="grid2">
    <label class="field"><span>Name</span><input name="name" required placeholder="Your name" autocomplete="name"></label>
    <label class="field"><span>Company (optional)</span><input name="company" placeholder="Company / firm"></label>
  </div>
  <div class="grid2">
    <label class="field"><span>Phone / WhatsApp</span><input name="phone" type="tel" required placeholder="10-digit number" pattern="[0-9+ ]{{10,15}}" autocomplete="tel"></label>
    <label class="field"><span>Email</span><input name="email" type="email" required placeholder="you@example.com" autocomplete="email"></label>
  </div>
  <label class="field"><span>Requirement</span><textarea name="message" rows="4" placeholder="{placeholder}"></textarea></label>
  <input class="hp" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">
  <button class="btn btn-p btn-block" type="submit">{label}</button>
  <p class="fine">Your details are used only to reply to your request.</p>
</form>"""


def card(s, href):
    return (
        f'<a class="card rv" href="{esc(href)}" data-cat="{s["cat"]}" data-search="{search_text(s)}">'
        f'<span class="ico">{s["ico"]}</span>'
        f'<span class="cat-tag">{esc(CATS[s["cat"]])}</span>'
        f'<h3>{esc(s["name"])}</h3>'
        f'<p>{esc(s["short"])}</p>'
        f'<span class="go">View details and samples →</span>'
        f'</a>'
    )


def gallery_section():
    tabs = "".join(
        f'<button class="g-tab{cls(" on" if i == 0 else "")}" type="button" role="tab" data-idx="{i}" '
        f'aria-selected="{"true" if i == 0 else "false"}">{esc(g["cap"])}</button>'
        for i, g in enumerate(GALLERY)
    )
    slides = "".join(
        f'<figure class="g-slide{cls(" on" if i == 0 else "")}" data-idx="{i}">'
        f'<img src="{esc(g["src"])}" alt="{esc(g["cap"])}" loading="lazy" '
        f'onerror="this.closest(\'.g-slide\').classList.add(\'missing\')"></figure>'
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
      <div class="g-tabs" role="tablist">{tabs}</div>
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
        <thead><tr><th>Area</th><th>Manual work</th><th>With automation</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
  </div>
</section>"""


# ---------- homepage ----------
def home_page():
    counts = {k: sum(1 for s in SERVICES if s["cat"] == k) for k in CATS}
    chips = [f'<button class="chip on" data-cat="all" type="button">All <span>{len(SERVICES)}</span></button>']
    chips += [f'<button class="chip" data-cat="{k}" type="button">{esc(v)} <span>{counts[k]}</span></button>'
              for k, v in CATS.items()]
    cards = "".join(card(s, f"services/{s['slug']}.html") for s in SERVICES)
    faqs = "".join(f'<details class="rv"><summary>{esc(q)}</summary><p>{esc(a)}</p></details>'
                   for q, a in HOME_FAQ)

    demo = ""
    if CFG["video"]:
        src = CFG["video"]
        if src.lower().endswith((".mp4", ".webm", ".ogg")):
            player = f'<video src="{esc(src)}" controls playsinline preload="metadata"></video>'
        else:
            player = f'<iframe src="{esc(src)}" title="Demo video" loading="lazy" allowfullscreen></iframe>'
        demo = f"""<section class="section" id="demo">
  <div class="wrap">
    <div class="sec-head rv"><span class="eyebrow">Live demo</span><h2>See a system in action</h2></div>
    <div class="screen rv">{player}</div>
  </div>
</section>"""

    body = f"""
<section id="hero" class="hero">
  <div class="wrap hero-grid">
    <div class="hero-text rv">
      <span class="eyebrow">{esc(CFG['tagline'])}</span>
      <h1>Automated systems that keep your business organised</h1>
      <div class="role" id="role" aria-live="polite"></div>
      <p class="lead">I build inventory, production, billing, HR, CRM and WhatsApp systems your team can use from day one. Practical, reliable and easy to maintain.</p>
      <div class="row">
        <a class="btn btn-p" href="#services">View services</a>
        <a class="btn btn-o" href="#contact">Contact me</a>
      </div>
    </div>
    <aside class="glass rv d2">
      <img class="logo" src="{CFG['logo']}" alt="{esc(CFG['brand'])} logo">
      <h3>{esc(CFG['name'])}</h3>
      <p class="sub">MIS reporting · Process automation · Custom systems</p>
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
      <div class="photo">
        <img id="myPhoto" src="{CFG['photo']}" alt="{esc(CFG['name'])}, {esc(CFG['tagline'])}">
        <div class="photo-fallback" id="photoFallback" hidden>
          <div>Your photo here<small>Place {esc(CFG['photo'])} next to index.html</small></div>
        </div>
      </div>
    </div>
    <div class="rv d2">
      <span class="eyebrow">About me</span>
      <h2>Hi, I'm {esc(CFG['name'])}</h2>
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
        <input id="q" type="search" placeholder="Search e.g. stock, WhatsApp, payroll" autocomplete="off">
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
        <label class="field"><span>People doing manual work</span><input id="cStaff" type="number" min="1" value="3"></label>
        <label class="field"><span>Hours per day, each person</span><input id="cHours" type="number" min="0" step="0.5" value="3"></label>
        <label class="field"><span>Monthly salary per person (₹)</span><input id="cSalary" type="number" min="0" value="18000"></label>
        <label class="field"><span>Working days per month</span><input id="cDays" type="number" min="1" max="31" value="26"></label>
        <label class="field"><span>Time saved after automation (%)</span><input id="cPct" type="number" min="0" max="100" value="70"></label>
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
      <h2>Let's discuss your requirement</h2>
      <p class="lead">Share your process and I will suggest the right system and send a quotation.</p>
      <div class="c-list">
        <a class="c-item" href="mailto:{esc(CFG['email'])}"><span class="c-ico">✉</span><span><small>Email</small><b>{esc(CFG['email'])}</b></span></a>
        <a class="c-item" href="{wa(CFG['name'] + ', I would like to discuss an automation project.')}" target="_blank" rel="noopener"><span class="c-ico">✆</span><span><small>WhatsApp / Mobile</small><b>{esc(CFG['phone_display'])}</b></span></a>
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
            "@context": SCHEMA_CTX,
            "@type": "ProfessionalService",
            "name": f"{CFG['brand']}: {CFG['name']}, {CFG['tagline']}",
            "url": CFG["site"] + "/",
            "telephone": "+" + CFG["wa"],
            "email": CFG["email"],
            "image": f"{CFG['site']}/{CFG['logo']}",
            "description": HOME_DESC,
            "areaServed": "IN",
            "founder": {"@type": "Person", "name": CFG["name"]},
        },
        {
            "@context": SCHEMA_CTX,
            "@type": "ItemList",
            "name": "Systems built by Bizautosetup",
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": s["name"],
                 "url": f"{CFG['site']}/services/{s['slug']}.html"}
                for i, s in enumerate(SERVICES)
            ],
        },
    ]
    return shell(HOME_TITLE, HOME_DESC, "", "", body, schema)


# ---------- service pages ----------
def service_page(s):
    prefix = "../"
    slug, name = s["slug"], s["name"]
    path = f"services/{slug}.html"
    url = f"{CFG['site']}/{path}"
    pdf = (prefix + s["pdf"]) if s["pdf"] else ""
    wa_link = wa(f"Hello, I am interested in: {name}")
    faq = s["faq"]

    features = "".join(f"<li>{esc(f)}</li>" for f in s["features"])

    imgs = [{"src": prefix + p, "alt": f"{name} sample screen {i + 1}"} for i, p in enumerate(s["imgs"])]
    total = len(imgs)
    if total:
        thumbs = []
        for i, it in enumerate(imgs[:MAX_THUMBS]):
            is_more = total > MAX_THUMBS and i == MAX_THUMBS - 1
            action = "data-all" if is_more else f'data-open="{i}"'
            overlay = f'<span class="more">+{total - MAX_THUMBS} more</span>' if is_more else ""
            thumbs.append(
                f'<button class="thumb" type="button" {action} aria-label="{esc(it["alt"])}">'
                f'<img src="{esc(it["src"])}" alt="{esc(it["alt"])}" loading="lazy" onerror="{BROKEN_IMG}">'
                f'{overlay}</button>'
            )
        gal_json = json.dumps(imgs, ensure_ascii=False).replace("</", "<\\/")
        samples = f"""<section class="section alt" id="samples">
  <div class="wrap">
    <div class="sec-head-row rv">
      <div><span class="eyebrow">Sample screens</span><h2>Inside the {esc(name)}</h2></div>
      <button class="btn btn-o btn-sm" type="button" data-all>View all {total}</button>
    </div>
    <div class="gal rv">{"".join(thumbs)}</div>
  </div>
  <script type="application/json" id="gal-data" data-title="{esc(name)}">{gal_json}</script>
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
      <a href="../index.html">Home</a> <span>/</span> <a href="../index.html#services">Services</a> <span>/</span> <span>{esc(name)}</span>
    </nav>
    <span class="cat-tag">{esc(CATS[s['cat']])}</span>
    <h1>{esc(s['h1'])}</h1>
    <p class="lead">{esc(s['desc'])}</p>
    <p class="price">Quotation on request</p>
    <div class="row mt">
      <a class="btn btn-p" href="#quote">Request quotation</a>
      <a class="btn btn-o" href="{wa_link}" target="_blank" rel="noopener">Ask on WhatsApp</a>
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
            "@context": SCHEMA_CTX,
            "@type": "Service",
            "name": name,
            "serviceType": name,
            "description": s["desc"],
            "url": url,
            "areaServed": "IN",
            "provider": {
                "@type": "ProfessionalService",
                "name": CFG["brand"],
                "telephone": "+" + CFG["wa"],
                "email": CFG["email"],
                "url": CFG["site"] + "/",
            },
        },
        {
            "@context": SCHEMA_CTX,
            "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": faq["q"],
                            "acceptedAnswer": {"@type": "Answer", "text": faq["a"]}}],
        },
        {
            "@context": SCHEMA_CTX,
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": CFG["site"] + "/"},
                {"@type": "ListItem", "position": 2, "name": "Services", "item": CFG["site"] + "/#services"},
                {"@type": "ListItem", "position": 3, "name": name, "item": url},
            ],
        },
    ]
    return shell(s["title"], s["desc"], path, prefix, body, schema)


def services_redirect():
    """services/index.html sends visitors to the homepage services section (no folder listing)."""
    target = "../index.html#services"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url={target}">
<link rel="canonical" href="{CFG['site']}/#services">
<title>Services | {esc(CFG['brand'])}</title>
</head>
<body>
<p>Redirecting to <a href="{target}">services</a>...</p>
</body>
</html>
"""


# ---------- sitemap / robots ----------
def sitemap():
    urls = [(CFG["site"] + "/", "1.0")]
    urls += [(f"{CFG['site']}/services/{s['slug']}.html", "0.8") for s in SERVICES]
    entries = "\n".join(
        f"  <url>\n    <loc>{u}</loc>\n    <lastmod>{TODAY}</lastmod>\n    <priority>{p}</priority>\n  </url>"
        for u, p in urls
    )
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{entries}\n</urlset>\n")


def robots():
    return f"User-agent: *\nAllow: /\n\nSitemap: {CFG['site']}/sitemap.xml\n"


# ---------- main ----------
def main():
    if CFG["sheet_url"].startswith("PASTE"):
        print("WARNING: CFG['sheet_url'] is still a placeholder. Form submit will not work.")

    checks = [CFG["logo"], CFG["photo"]] + [g["src"] for g in GALLERY]
    for s in SERVICES:
        checks += s["imgs"] + ([s["pdf"]] if s["pdf"] else [])
    for p in checks:
        if not (ROOT / p).exists():
            print(f"WARNING: file not found: {p}")

    (ROOT / "index.html").write_text(home_page(), encoding="utf-8")

    out = ROOT / "services"
    out.mkdir(exist_ok=True)
    (out / "index.html").write_text(services_redirect(), encoding="utf-8")
    for s in SERVICES:
        (out / f"{s['slug']}.html").write_text(service_page(s), encoding="utf-8")

    (ROOT / "sitemap.xml").write_text(sitemap(), encoding="utf-8")
    (ROOT / "robots.txt").write_text(robots(), encoding="utf-8")

    built = len(list(out.glob("*-*.html")))
    print(f"Done: index.html, {built} service pages, sitemap.xml, robots.txt")


if __name__ == "__main__":
    main()
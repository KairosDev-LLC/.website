#!/usr/bin/env python3
"""Generate the Kairos site's inner pages from one shared shell.

The site is deliberately plain static HTML with no build step in production —
this script is a one-shot authoring tool so that the nav, footer, head
boilerplate and App Store links are literally identical across every page
instead of being hand-copied and drifting apart.

Run it, commit the output, done. The generated .html files are the artifact.
"""
import os

ROOT = "/home/user/kairos-website"
APPSTORE = "https://apps.apple.com/us/app/kairos-shift-tracker/id6792157855"
EULA = "https://www.apple.com/legal/internet-services/itunes/dev/stdeula/"

APPLE_SVG = (
    '<svg viewBox="0 0 384 512" aria-hidden="true" focusable="false">'
    '<path d="M318.7 268.7c-.2-36.7 16.4-64.4 50-84.8-18.8-26.9-47.2-41.7-84.7-44.6-35.5-2.8-74.3 20.7-88.5 20.7-15 0-49.4-19.7-76.4-19.7C63.3 141.2 4 184.8 4 273.5q0 39.3 14.4 81.2c12.8 36.7 59 126.7 107.2 125.2 25.2-.6 43-17.9 75.8-17.9 31.8 0 48.3 17.9 76.4 17.9 48.6-.7 90.4-82.5 102.6-119.3-65.2-30.7-61.7-90-61.7-91.9zm-56.6-164.2c27.3-32.4 24.8-61.9 24-72.5-24.1 1.4-52 16.4-67.9 34.9-17.5 19.8-27.8 44.3-25.6 71.9 26.1 2 49.9-11.4 69.5-34.3z"/></svg>'
)

NAV_ITEMS = [
    ("/features", "Features"),
    ("/rotations", "Rotations"),
    ("/pricing", "Pricing"),
    ("/faq", "FAQ"),
    ("/support", "Support"),
    ("/changelog", "Changelog"),
]


def badge(extra=""):
    return f'''<a class="appstore-badge{extra}" href="{APPSTORE}">
          {APPLE_SVG}
          <span class="ab-text">
            <span class="ab-small">Download on the</span>
            <span class="ab-big">App Store</span>
          </span>
        </a>'''


def nav():
    return """<nav class="site-nav">
  <div class="nav-inner">
    <a class="brand" href="/">
      <img class="brand-mark" src="/assets/brand-mark.png" alt="" width="128" height="128" />
      kairos
    </a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="nav-links" hidden>Menu</button>
    <div class="nav-links" id="nav-links">
      <div class="nav-menu" data-open="false">
        <button type="button" aria-expanded="false" aria-controls="menu-rotations">Rotations</button>
        <div class="nav-panel" id="menu-rotations">
          <div>
            <h4>Patterns</h4>
            <div class="nav-panel-list">
            <a href="/rotations#24-48">24/48</a>
            <a href="/rotations#48-96">48/96</a>
            <a href="/rotations#kelly">Kelly</a>
            <a href="/rotations#panama">Panama (2-2-3)</a>
            <a href="/rotations#pitman">Pitman nights</a>
            <a href="/rotations#dupont">DuPont</a>
            <a href="/rotations#4-on-4-off">4 on / 4 off</a>
            <a href="/rotations#5-2">5 on / 2 off</a>
            </div>
          </div>
          <div>
            <h4>By first responder</h4>
            <div class="nav-panel-list">
              <a href="/rotations?filter=fire#library">Fire <span class="n">3</span></a>
              <a href="/rotations?filter=ems#library">EMS <span class="n">1</span></a>
              <a href="/rotations?filter=police#library">Police <span class="n">1</span></a>
              <a href="/rotations?filter=nursing#library">Nursing <span class="n">1</span></a>
              <a href="/rotations?filter=industrial#library">Industrial <span class="n">2</span></a>
              <a href="/rotations?filter=transport#library">Transport <span class="n">1</span></a>
            </div>
            <h4 style="margin-top:16px">Tools</h4>
            <div class="nav-panel-list">
              <a href="/rotations#simulator">Rotation simulator</a>
              <a href="/rotations#compare">Hours compared</a>
            </div>
          </div>
        </div>
      </div>
      <div class="nav-menu" data-open="false">
        <button type="button" aria-expanded="false" aria-controls="menu-app">The app</button>
        <div class="nav-panel" id="menu-app">
          <div>
            <h4>Product</h4>
            <div class="nav-panel-list">
              <a href="/features">Features</a>
              <a href="/features#panel-calendar">Calendar</a>
              <a href="/features#panel-sharing">Sharing</a>
              <a href="/features#panel-watch">Widgets</a>
              <a href="/features#panel-privacy">Privacy</a>
            </div>
          </div>
          <div>
            <h4>Get it</h4>
            <div class="nav-panel-list">
              <a href="/pricing">Pricing</a>
              <a href="/changelog">Changelog</a>
              <a href="https://apps.apple.com/us/app/kairos-shift-tracker/id6792157855">App Store</a>
            </div>
          </div>
        </div>
      </div>
      <a class="navlink" href="/faq">FAQ</a>
      <a class="navlink" href="/support">Support</a>
    </div>
    <div class="nav-right">
      <button class="nav-search" id="search-open" type="button" aria-label="Search the site">
        <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
        <span>Search</span>
        <span class="sk"><kbd>Ctrl</kbd> <kbd>K</kbd></span>
      </button>
      <button class="theme-toggle" id="theme-toggle" type="button" aria-label="Switch between light and dark mode">
        <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z"/></svg>
        <svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="4.5"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M4.9 4.9l1.5 1.5m11.2 11.2 1.5 1.5M19.1 4.9l-1.5 1.5M6.4 17.6l-1.5 1.5"/></svg>
      </button>
      <a class="nav-cta" href="https://apps.apple.com/us/app/kairos-shift-tracker/id6792157855">Get the app</a>
    </div>
  </div>
</nav>"""


SEARCH_OVERLAY = """<div class="search-overlay" id="search-overlay" hidden role="dialog" aria-modal="true" aria-label="Search Kairos">
  <div class="search-box">
    <input id="search-input" type="search" placeholder="Search rotations, features, answers…" autocomplete="off" aria-label="Search" />
    <ul class="search-results" id="search-results"></ul>
  </div>
</div>"""


def site_foot():
    return """<footer class="site-foot">
  <div class="wrap">
    <div class="foot-grid">
      <div class="foot-brand">
        <a class="brand" href="/"><img class="brand-mark" src="/assets/brand-mark.png" alt="" width="128" height="128" />kairos</a>
        <p>Every real shift rotation, drawn onto a live calendar. Kairos tracks
        Kelly, Panama, DuPont, 24/48 and 48/96 on iPhone, iPad, Mac and Apple Watch —
        no account, nothing to sync but your own iCloud.</p>
        <p>Ask us anything: <a class="mail" href="mailto:team@kairosapp.dev">team@kairosapp.dev</a></p>
        <div class="foot-social">
          <a href="https://apps.apple.com/us/app/kairos-shift-tracker/id6792157855" aria-label="Kairos on the App Store"><svg viewBox="0 0 384 512" aria-hidden="true"><path d="M318.7 268.7c-.2-36.7 16.4-64.4 50-84.8-18.8-26.9-47.2-41.7-84.7-44.6-35.5-2.8-74.3 20.7-88.5 20.7-15 0-49.4-19.7-76.4-19.7C63.3 141.2 4 184.8 4 273.5q0 39.3 14.4 81.2c12.8 36.7 59 126.7 107.2 125.2 25.2-.6 43-17.9 75.8-17.9 31.8 0 48.3 17.9 76.4 17.9 48.6-.7 90.4-82.5 102.6-119.3-65.2-30.7-61.7-90-61.7-91.9zm-56.6-164.2c27.3-32.4 24.8-61.9 24-72.5-24.1 1.4-52 16.4-67.9 34.9-17.5 19.8-27.8 44.3-25.6 71.9 26.1 2 49.9-11.4 69.5-34.3z"/></svg></a>
          <a href="mailto:team@kairosapp.dev" aria-label="Email the Kairos team"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 5.5A2.5 2.5 0 0 1 4.5 3h15A2.5 2.5 0 0 1 22 5.5v13a2.5 2.5 0 0 1-2.5 2.5h-15A2.5 2.5 0 0 1 2 18.5v-13Zm2.7.5 7.3 5.6L19.3 6H4.7Zm15.3 1.9-7.4 5.7a1 1 0 0 1-1.2 0L4 7.9V18h16V7.9Z"/></svg></a>
          <a href="/support" aria-label="Support"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm0 2a8 8 0 0 1 8 8 8 8 0 0 1-8 8 8 8 0 0 1-8-8 8 8 0 0 1 8-8Zm-1 12h2v2h-2v-2Zm1-9c-1.9 0-3.3 1.2-3.5 3h2c.1-.7.7-1.2 1.5-1.2.9 0 1.5.5 1.5 1.2 0 .6-.3.9-1.1 1.5-.9.6-1.4 1.2-1.4 2.5h2c0-.6.2-.9 1-1.5.9-.7 1.5-1.4 1.5-2.6C15.5 8.2 14 7 12 7Z"/></svg></a>
          <a href="/feed.xml" aria-label="Kairos release notes RSS feed"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 3a16 16 0 0 1 16 16h-3A13 13 0 0 0 5 6V3Zm0 6a10 10 0 0 1 10 10h-3A7 7 0 0 0 5 12V9Zm1.5 6.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5Z"/></svg></a>
        </div>
      </div>
      <div>
        <h4>Rotations</h4>
        <ul>
          <li><a href="/rotations#24-48">24/48</a></li>
          <li><a href="/rotations#48-96">48/96</a></li>
          <li><a href="/rotations#kelly">Kelly</a></li>
          <li><a href="/rotations#panama">Panama (2-2-3)</a></li>
          <li><a href="/rotations#dupont">DuPont</a></li>
        </ul>
      </div>
      <div>
        <h4>Product</h4>
        <ul>
          <li><a href="/features">Features</a></li>
          <li><a href="/pricing">Pricing</a></li>
          <li><a href="/changelog">Changelog</a></li>
          <li><a href="/rotations#simulator">Simulator</a></li>
        </ul>
      </div>
      <div>
        <h4>Help</h4>
        <ul>
          <li><a href="/faq">FAQ</a></li>
          <li><a href="/support">Support</a></li>
          <li><a href="mailto:team@kairosapp.dev">Email us</a></li>
          <li><a href="/feed.xml">Release RSS</a></li>
          <li><a href="https://apps.apple.com/us/app/kairos-shift-tracker/id6792157855">App Store</a></li>
        </ul>
      </div>
      <div>
        <h4>Legal</h4>
        <ul>
          <li><a href="/privacy">Privacy policy</a></li>
          <li><a href="https://www.apple.com/legal/internet-services/itunes/dev/stdeula/">Terms of use</a></li>
        </ul>
      </div>
    </div>
    <div class="foot-rule"></div>
    <p class="foot-legal">© 2026 KairosDev LLC. Made for the people who work when everyone else is asleep.</p>
  </div>
</footer>"""


THEME_BOOT = """<script>(function(){try{var m=localStorage.getItem('kairos-theme');if(!m&&window.matchMedia&&window.matchMedia('(prefers-color-scheme: light)').matches)m='light';document.documentElement.setAttribute('data-theme',m||'dark');}catch(e){}}());</script>"""


def footer(head, tagline, eyebrow="Get Kairos"):
    return f'''<footer class="cta-footer">
  <div class="wrap">
    <p class="eyebrow-black">{eyebrow}</p>
    <h2>{head}</h2>
    <p class="tag-line">{tagline}</p>
    {badge()}

    <div class="foot-nav">
      <div class="foot-col">
        <h3>Product</h3>
        <a href="/features">Features</a>
        <a href="/rotations">Rotations</a>
        <a href="/pricing">Pricing</a>
        <a href="/changelog">Changelog</a>
      </div>
      <div class="foot-col">
        <h3>Help</h3>
        <a href="/faq">FAQ</a>
        <a href="/support">Support</a>
        <a href="mailto:team@kairosapp.dev">Email us</a>
      </div>
      <div class="foot-col">
        <h3>Legal</h3>
        <a href="/privacy">Privacy Policy</a>
        <a href="{EULA}">Terms of Use (EULA)</a>
      </div>
      <div class="foot-col">
        <h3>Download</h3>
        <a href="{APPSTORE}">iPhone &amp; iPad</a>
        <a href="{APPSTORE}">Mac</a>
        <a href="{APPSTORE}">Apple Watch</a>
      </div>
    </div>

    <div class="foot-bottom">
      <span>&copy; 2026 KairosDev LLC</span>
      <span>Made for the people who work while everyone else sleeps.</span>
    </div>
  </div>
</footer>

<button id="to-top" type="button" aria-label="Back to top">&#8593;</button>'''


def page(slug, title, description, h1, sub, body,
         cta_eyebrow="Get Kairos",
         cta_head="Never Miss<br />a Shift Again",
         cta_tag="Free to download. Kairos Pro unlocks the Apple Watch companion and unlimited shared coworker schedules, from $4.99 a month.",
         extra_head="", extra_body=""):
    url = f"https://www.kairosapp.dev/{slug}"
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{title}</title>
<meta name="description" content="{description}" />
<link rel="icon" href="/favicon.ico" sizes="48x48" />
<link rel="icon" href="/icon.png" type="image/png" />
<link rel="apple-touch-icon" href="/apple-touch-icon.png" />
<meta name="theme-color" content="#0b0b0f" />
<meta name="color-scheme" content="dark" />
<link rel="manifest" href="/manifest.json" />
<link rel="alternate" type="application/rss+xml" title="Kairos release notes" href="/feed.xml" />
<meta name="apple-mobile-web-app-title" content="Kairos" />
<meta name="apple-itunes-app" content="app-id=6792157855" />

<meta property="og:title" content="{title}" />
<meta property="og:description" content="{description}" />
<meta property="og:type" content="website" />
<meta property="og:site_name" content="Kairos" />
<meta property="og:locale" content="en_US" />
<meta property="og:url" content="{url}" />
<meta property="og:image" content="https://www.kairosapp.dev/og-image.png" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:image:alt" content="Kairos — taking the guesswork out of shift work" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{title}" />
<meta name="twitter:description" content="{description}" />
<meta name="twitter:image" content="https://www.kairosapp.dev/og-image.png" />
<link rel="canonical" href="{url}" />

<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {{ "@type": "ListItem", "position": 1, "name": "Home", "item": "https://www.kairosapp.dev/" }},
    {{ "@type": "ListItem", "position": 2, "name": "{h1}", "item": "{url}" }}
  ]
}}
</script>
{extra_head}
<script>document.documentElement.classList.add('js');</script>
{THEME_BOOT}
<link rel="stylesheet" href="/assets/site.css" />
</head>
<body>

<div id="scroll-progress"></div>
<a class="skip-link" href="#main">Skip to content</a>

{nav()}

<main id="main">

  <header class="page-head">
    <div class="wrap">
      <p class="breadcrumbs"><a href="/">Kairos</a> / {h1}</p>
      <h1>{h1}</h1>
      <p class="page-sub">{sub}</p>
    </div>
  </header>

{body}

</main>

{footer(cta_head, cta_tag, cta_eyebrow)}

{site_foot()}
{SEARCH_OVERLAY}
{extra_body}
<script src="/assets/site.js"></script>
</body>
</html>
'''


def write(slug, html):
    path = os.path.join(ROOT, f"{slug}.html")
    with open(path, "w") as f:
        f.write(html)
    print(f"wrote {path} ({len(html.splitlines())} lines)")


# ===========================================================================
# FEATURES
# ===========================================================================

FEATURE_TABS = [
    ("dashboard", "Dashboard", """
      <h3 class="sub-title">The answer before you ask the question</h3>
      <p class="prose">The home screen exists to answer one question: <em>am I working, and for how much longer?</em> A duty ring fills as your shift progresses and a countdown badge reads down to the minute, so the answer is legible from across a room.</p>
      <ul class="prose">
        <li><strong>Live duty ring</strong> — fills through the shift so progress is visible, not just a number.</li>
        <li><strong>Countdown badge</strong> — time until the current shift ends, or until the next one begins.</li>
        <li><strong>At-a-glance status</strong> — working, off duty, on call, or on vacation, colour-coded consistently everywhere in the app.</li>
        <li><strong>Multiple calendars</strong> — switch between your own schedule and any schedule shared with you.</li>
      </ul>"""),
    ("calendar", "Calendar", """
      <h3 class="sub-title">A month you can actually plan against</h3>
      <p class="prose">The calendar renders your whole rotation forward and backward, so booking a dentist appointment four months out takes one look instead of counting on your fingers.</p>
      <ul class="prose">
        <li><strong>Colour-coded month grid</strong> — day shifts, night shifts and days off are distinguishable at a glance.</li>
        <li><strong>Tap to override</strong> — mark vacation, an extra shift, a trade, or an on-call assignment without breaking the underlying pattern.</li>
        <li><strong>Unlimited horizon</strong> — the rotation is computed, not stored, so it projects as far ahead as you need.</li>
        <li><strong>Workplace timezone</strong> — added in v2.1, so your schedule stays correct when you travel.</li>
      </ul>"""),
    ("sharing", "Sharing", """
      <h3 class="sub-title">Six characters, no sign-up</h3>
      <p class="prose">Sharing is the reason most people install Kairos. Your spouse should not need to create an account, remember a password, or install anything beyond the app itself.</p>
      <ul class="prose">
        <li><strong>6-character access code</strong> — short enough to read out over the phone.</li>
        <li><strong>Read-only by construction</strong> — recipients see your availability, they cannot edit it.</li>
        <li><strong>Revocable</strong> — change your mind and the code stops working.</li>
        <li><strong>No accounts on either side</strong> — nobody signs up for anything.</li>
      </ul>
      <p class="prose">Try the code format on the <a href="/">home page</a>.</p>"""),
    ("privacy", "Privacy", """
      <h3 class="sub-title">Your schedule is not a product</h3>
      <p class="prose">Kairos has no user accounts and no backend database holding your shifts. Your schedule lives on your device and syncs through your own iCloud, under your own Apple ID.</p>
      <ul class="prose">
        <li><strong>On-device storage</strong> — the schedule is yours, on your hardware.</li>
        <li><strong>CloudKit sync</strong> — device-to-device through your private iCloud database, not ours.</li>
        <li><strong>AES-256 encrypted recovery keys</strong> — back up and restore across devices without an account.</li>
        <li><strong>No ads, no analytics resale, no tracking profile.</strong></li>
      </ul>
      <p class="prose">The full details are in the <a href="/privacy">privacy policy</a>.</p>"""),
    ("watch", "Watch &amp; widgets", """
      <h3 class="sub-title">Where you actually look</h3>
      <p class="prose">On a working day you are not opening an app. Kairos puts the same status on your wrist and on your Home Screen.</p>
      <ul class="prose">
        <li><strong>watchOS companion</strong> — progress ring, current status, and a 7-day shift forecast.</li>
        <li><strong>Full calendar on the Watch</strong> — not just today, the whole month.</li>
        <li><strong>Small, medium and large widgets</strong> — pick the density that fits your Home Screen.</li>
        <li><strong>Configurable widget target</strong> — point a widget at your own schedule or at someone else's shared one.</li>
      </ul>
      <p class="prose">The Apple Watch companion is part of <a href="/pricing">Kairos Pro</a>.</p>"""),
    ("rotations", "Rotations", """
      <h3 class="sub-title">Preset, or build your own</h3>
      <p class="prose">Setup takes seconds if you work a named rotation, and is still straightforward if your department invented its own.</p>
      <ul class="prose">
        <li><strong>Common presets</strong> — Kelly, Panama, DuPont, 24/48 and 48/96 ship ready to go.</li>
        <li><strong>Custom weekly layouts</strong> — build the pattern your crew actually runs.</li>
        <li><strong>Set your own cycle start</strong> — align the pattern to the day your rotation actually began.</li>
        <li><strong>DST-safe</strong> — v2.1 fixed a bug that could show the wrong shift day around clock changes.</li>
      </ul>
      <p class="prose">Compare all of them side by side on the <a href="/rotations">rotations page</a>.</p>"""),
]


def features_page():
    tabs = "\n        ".join(
        f'<button class="tab-btn" role="tab" id="tab-{k}" aria-controls="panel-{k}" '
        f'aria-selected="{"true" if i == 0 else "false"}" tabindex="{0 if i == 0 else -1}">{label}</button>'
        for i, (k, label, _) in enumerate(FEATURE_TABS)
    )
    panels = "\n".join(
        f'      <div class="tab-panel" role="tabpanel" id="panel-{k}" aria-labelledby="tab-{k}"'
        f' data-tab-label="{label}"'
        f'{"" if i == 0 else " hidden"}>{body}\n      </div>'
        for i, (k, label, body) in enumerate(FEATURE_TABS)
    )

    body = f'''  <section class="section-ink">
    <div class="wrap">
      <p class="eyebrow">Feature explorer</p>
      <h2 class="section-title">Pick a corner of the app</h2>
      <p class="lede">Six areas, each doing one job. Use the tabs, or the arrow keys.</p>

      <div data-tabs>
        <div class="tabs" role="tablist" aria-label="Kairos features">
        {tabs}
        </div>
{panels}
      </div>
    </div>
  </section>

  <section class="section-paper">
    <div class="wrap">
      <p class="eyebrow">The screens</p>
      <h2 class="section-title">See it running</h2>
      <p class="lede">Straight from the App Store listing. Tap to open full size, then use the arrow keys.</p>
      <div class="shots">
        <button class="shot" type="button" data-caption="Dashboard — live duty status and shift countdown" data-full="/assets/shots/shot-1-working.webp">
          <img src="/assets/shots/shot-1-working.webp" width="626" height="1354" loading="lazy" decoding="async" alt="Kairos dashboard showing live on-duty status and shift countdown" />
          <figcaption>Dashboard</figcaption>
        </button>
        <button class="shot" type="button" data-caption="Calendar — colour-coded month view of the full rotation" data-full="/assets/shots/shot-2-calendar.webp">
          <img src="/assets/shots/shot-2-calendar.webp" width="626" height="1354" loading="lazy" decoding="async" alt="Kairos calendar showing a colour-coded month of shifts" />
          <figcaption>Calendar</figcaption>
        </button>
        <button class="shot" type="button" data-caption="Vacation — overriding scheduled days off" data-full="/assets/shots/shot-3-vacation.webp">
          <img src="/assets/shots/shot-3-vacation.webp" width="626" height="1354" loading="lazy" decoding="async" alt="Kairos vacation override screen" />
          <figcaption>Vacation</figcaption>
        </button>
      </div>
    </div>
  </section>

  <section class="section-ink">
    <div class="wrap">
      <p class="eyebrow">Free vs Pro</p>
      <h2 class="section-title">What's in each tier</h2>
      <div class="table-scroll">
        <table class="compare">
          <caption>Kairos is free to download. Pro is an optional auto-renewing subscription.</caption>
          <thead>
            <tr><th scope="col">Capability</th><th scope="col">Free</th><th scope="col">Pro</th></tr>
          </thead>
          <tbody>
            <tr><td>Your own rotating schedule</td><td class="yes">Yes</td><td class="yes">Yes</td></tr>
            <tr><td>Preset rotations (Kelly, Panama, DuPont, 24/48, 48/96)</td><td class="yes">Yes</td><td class="yes">Yes</td></tr>
            <tr><td>Custom weekly layouts</td><td class="yes">Yes</td><td class="yes">Yes</td></tr>
            <tr><td>Colour-coded calendar &amp; overrides</td><td class="yes">Yes</td><td class="yes">Yes</td></tr>
            <tr><td>Home Screen widgets</td><td class="yes">Yes</td><td class="yes">Yes</td></tr>
            <tr><td>Shift countdown &amp; duty status</td><td class="yes">Yes</td><td class="yes">Yes</td></tr>
            <tr><td>Apple Watch companion</td><td class="no">&mdash;</td><td class="yes">Yes</td></tr>
            <tr><td>Unlimited shared coworker schedules</td><td class="no">&mdash;</td><td class="yes">Yes</td></tr>
          </tbody>
        </table>
      </div>
      <p style="margin-top:30px"><a class="btn btn-primary" href="/pricing">See pricing</a></p>
    </div>
  </section>'''

    return page(
        "features",
        "Features — Kairos Shift Tracker",
        "Every Kairos feature in detail: live duty dashboard, colour-coded calendar, 6-character schedule sharing, on-device privacy, the Apple Watch companion, Home Screen widgets, and preset rotations.",
        "Features",
        "Six areas of the app, what each one does, and exactly which parts are free.",
        body,
        extra_body=LIGHTBOX,
    )


# ===========================================================================
# ROTATIONS
# ===========================================================================

ROTATIONS = [
    ("24/48", "3-day cycle", "56 hrs/wk", "One 24-hour shift, then 48 hours off.",
     "The default single-platoon fire schedule. You work one full day, then get two. Simple to hold in your head, but the working day walks through the week, so it never lands on the same weekday twice in a row."),
    ("48/96", "6-day cycle", "56 hrs/wk", "Two 24-hour shifts, then four days off.",
     "The same 56-hour average as 24/48, rearranged so all of your time off arrives in one four-day block. Popular with crews who commute a long way or want real recovery time."),
    ("Kelly", "9-day cycle", "56 hrs/wk", "Three 24-hour shifts on alternating days, then four off.",
     "Named after Chicago's Mayor Kelly. Work, off, work, off, work, then four consecutive days off. It splits the difference between the daily churn of 24/48 and the long blocks of 48/96."),
    ("Panama (2-2-3)", "14-day cycle", "42 hrs/wk", "Two on, two off, three on — 12-hour shifts.",
     "The classic slow-rotating 2-2-3. Over a fortnight it gives you every other weekend off in full, which is why dispatch centres and law enforcement lean on it."),
    ("Pitman nights (2-3-2)", "14-day cycle", "42 hrs/wk", "The same 2-3-2 structure, worked on nights.",
     "Structurally identical to the Panama but on the night side of the roster. Same every-other-weekend rhythm, same 42-hour average, very different sleep schedule."),
    ("DuPont", "28-day cycle", "42 hrs/wk", "Rotating nights and days with a seven-day break.",
     "Four nights, three off, three days, one off, three nights, three off, four days, then seven consecutive days off. The long break at the end is the whole point, and the reason people tolerate the rotation."),
    ("4 on / 4 off", "8-day cycle", "42 hrs/wk", "Four 12-hour shifts, then four days off.",
     "Very common on industrial, plant and transportation crews. An even split with a cycle that fits neatly into an eight-day rhythm, though it drifts against the calendar week."),
    ("5 on / 2 off", "7-day cycle", "40 hrs/wk", "The fixed weekday week.",
     "Included as a baseline so you can see what a rotating schedule actually costs you compared to a fixed Monday-to-Friday. It is the only pattern here that repeats on the same weekdays forever."),
]


ROT_SLUGS = ["24-48", "48-96", "kelly", "panama", "pitman", "dupont", "4-on-4-off", "5-2"]

# First responder tags: which services actually work each pattern. These
# drive the filter chips, not the card face.
ROT_RESPONDERS = {
    "24-48": ["Fire"],
    "48-96": ["Fire"],
    "kelly": ["Fire"],
    "panama": ["Police", "EMS"],
    "pitman": ["Nursing"],
    "dupont": ["Industrial"],
    "4-on-4-off": ["Industrial", "Transport"],
    "5-2": ["Baseline"],
}

ROT_CATS = {
    "24-48": "fire 24h short", "48-96": "fire 24h long", "kelly": "fire 24h long",
    "panama": "police ems 12h weekend", "pitman": "nursing nights 12h weekend",
    "dupont": "industrial nights 12h long", "4-on-4-off": "industrial transport 12h",
    "5-2": "baseline short",
}

ROT_CHIPS = [
    ("all", "All", 8), ("fire", "Fire", 3), ("police", "Police", 1), ("ems", "EMS", 1),
    ("nursing", "Nursing", 1), ("industrial", "Industrial", 2), ("transport", "Transport", 1),
    ("12h", "12-hour", 4), ("24h", "24-hour", 3), ("nights", "Nights", 2),
    ("weekend", "Every other weekend", 2), ("long", "Long breaks", 3),
]


def rotations_page():
    # The rotation library reads as a gallery: a filterable grid of preview
    # cards first, then the long-form write-up for each pattern underneath.
    gcards = []
    for i, ((name, cycle, hrs, short, long), slug) in enumerate(zip(ROTATIONS, ROT_SLUGS)):
        gcards.append(f'''        <article class="g-card reveal" data-cats="{ROT_CATS[slug]}" style="--reveal-i:{i % 4}">
          <div class="thumb">
            <img src="/assets/thumbs/{slug}.svg" alt="{name} drawn onto a month of the Kairos calendar" width="1200" height="854" loading="lazy" />
          </div>
          <h3>{name}</h3>
          <p class="g-meta"><span>{hrs}</span><span>{cycle}</span></p>
          <a class="stretch" href="#{slug}" aria-label="{name}"></a>
        </article>''')
    gallery_cards = "\n".join(gcards)

    gallery_chips = "\n        ".join(
        f'<button class="chip" type="button" data-filter="{k}" aria-pressed="{"true" if k == "all" else "false"}">'
        f'<span>{label}</span><span class="n">{n}</span></button>'
        for k, label, n in ROT_CHIPS
    )

    cards = "\n".join(f'''        <div class="card glass-light reveal" id="{slug}" style="--reveal-i:{i}">
          <span class="fnum">{cycle} · {hrs}</span>
          <h3>{name}</h3>
          <p><strong>{short}</strong></p>
          <p>{long}</p>
        </div>''' for i, ((name, cycle, hrs, short, long), slug) in enumerate(zip(ROTATIONS, ROT_SLUGS)))

    rows = "\n".join(
        f'            <tr><td>{name}</td><td>{cycle}</td><td>{hrs}</td><td>{short}</td></tr>'
        for name, cycle, hrs, short, _ in ROTATIONS
    )

    body = f'''  <section class="section-ink" id="library">
    <div class="wrap">
      <div class="chip-row" id="chip-row" role="group" aria-label="Filter rotations by first responder service and shift pattern">
        {gallery_chips}
      </div>

      <div class="gallery-grid" id="gallery-grid" data-per-page="8">
{gallery_cards}
        <p class="g-empty" id="gallery-empty" hidden>No rotation matches that filter.</p>
      </div>
    </div>
  </section>

  <section class="section-ink" id="simulator">
    <div class="wrap">
      <p class="eyebrow">Interactive</p>
      <h2 class="section-title">Rotation simulator</h2>
      <p class="lede">Choose a rotation and the day your cycle started. This runs the same arithmetic the app does — live duty status, a running countdown, and a month you can page through. Everything is computed in your browser; nothing is sent anywhere.</p>

      <div class="sim glass-dark is-static" id="sim" hidden>
        <div class="field-row">
          <div class="field">
            <label for="sim-pattern">Rotation</label>
            <select id="sim-pattern">
              <option value="24-48">24/48</option>
              <option value="48-96">48/96</option>
              <option value="kelly">Kelly</option>
              <option value="panama">Panama (2-2-3)</option>
              <option value="dupont">DuPont</option>
              <option value="pitman">Pitman nights (2-3-2)</option>
              <option value="4-on-4-off">4 on / 4 off</option>
              <option value="5-2">5 on / 2 off</option>
            </select>
          </div>
          <div class="field">
            <label for="sim-start">Cycle start date</label>
            <input type="date" id="sim-start" />
          </div>
          <div class="field">
            <label for="sim-today-wrap">View</label>
            <span id="sim-today-wrap"><button class="btn btn-secondary btn-sm" type="button" id="sim-today">Jump to today</button></span>
          </div>
        </div>

        <p class="mono" id="sim-blurb" style="font-size:13px;line-height:1.7;opacity:0.7;margin:0 0 24px;max-width:700px;"></p>

        <div class="sim-status">
          <div class="duty-ring" id="sim-ring" role="img" aria-label="Progress through the current shift">
            <span id="sim-ring-pct">0%</span>
          </div>
          <div class="sim-status-text">
            <span class="sim-status-label">Status right now</span>
            <span class="sim-status-value" id="sim-status-value">Off duty</span>
            <span class="sim-countdown" id="sim-countdown" aria-live="polite"></span>
          </div>
          <div class="sim-status-text">
            <span class="sim-status-label">One full cycle</span>
            <div class="cycle-strip" id="sim-cycle-strip"></div>
          </div>
        </div>

        <div class="cal-head">
          <span class="cal-month" id="sim-month"></span>
          <div class="cal-nav">
            <button type="button" id="sim-prev" aria-label="Previous month">&#8249;</button>
            <button type="button" id="sim-next" aria-label="Next month">&#8250;</button>
          </div>
        </div>
        <div class="cal-grid" id="sim-grid"></div>

        <div class="legend">
          <span><i class="k-on"></i> Day shift</span>
          <span><i class="k-night"></i> Night shift</span>
          <span><i class="k-off"></i> Off duty</span>
          <span><i class="k-today"></i> Today</span>
        </div>

        <div class="sim-summary">
          <div class="stat-cell glass-dark is-static">
            <p class="num mono" id="sim-sum-on">0</p>
            <p class="label">Shifts per cycle</p>
          </div>
          <div class="stat-cell glass-dark is-static">
            <p class="num mono" id="sim-sum-off">0</p>
            <p class="label">Days off per cycle</p>
          </div>
          <div class="stat-cell glass-dark is-static">
            <p class="num mono" id="sim-sum-hours">0</p>
            <p class="label">Avg hours / week</p>
          </div>
          <div class="stat-cell glass-dark is-static">
            <p class="num mono" id="sim-sum-cycle">0</p>
            <p class="label">Days in cycle</p>
          </div>
        </div>
      </div>

      <p class="mono" id="sim-fallback" style="opacity:0.65;font-size:13px;">
        The simulator needs JavaScript, but every rotation it covers is written out in full below.
      </p>
    </div>
  </section>

  <section class="section-paper" id="compare">
    <div class="wrap">
      <p class="eyebrow">Side by side</p>
      <h2 class="section-title">All eight at a glance</h2>
      <p class="lede">Cycle length is how many days before the pattern repeats. Average hours per week is the honest number over a full cycle, not a good week.</p>
      <div class="table-scroll">
        <table class="compare">
          <caption>Kelly, Panama, DuPont, 24/48 and 48/96 ship as presets in the app. Anything else can be built as a custom weekly layout.</caption>
          <thead>
            <tr><th scope="col">Rotation</th><th scope="col">Cycle</th><th scope="col">Avg hours</th><th scope="col">Shape</th></tr>
          </thead>
          <tbody>
{rows}
          </tbody>
        </table>
      </div>
    </div>
  </section>

  <section class="section-paper" style="padding-top:0">
    <div class="wrap">
      <h2 class="section-title">In detail</h2>
      <div class="grid-2">
{cards}
      </div>
    </div>
  </section>

  <section class="section-ink">
    <div class="wrap">
      <p class="eyebrow">Not on this list?</p>
      <h2 class="section-title">Build your own</h2>
      <p class="lede">Plenty of departments run something invented locally. Kairos lets you lay out a custom weekly pattern and set the cycle start date to the day your rotation actually began, so the app matches the roster on the wall rather than a textbook.</p>
      <p>{badge()}</p>
    </div>
  </section>'''

    return page(
        "rotations",
        "Shift rotations explained — Kairos",
        "Kelly, Panama, DuPont, 24/48, 48/96, Pitman, 4 on 4 off and 5 on 2 off — cycle lengths, average weekly hours, and an interactive simulator that shows any of them on a live calendar.",
        "Rotations",
        "Eight real shift rotations, what each one actually costs you in hours, and a simulator that draws any of them onto a live calendar.",
        body,
        cta_eyebrow="Built-in rotations",
        cta_head="Your Rotation,<br />Already Set Up",
        cta_tag="Kelly, Panama, DuPont, 24/48 and 48/96 are built in. Custom layouts take about a minute.",
    )


# ===========================================================================
# PRICING
# ===========================================================================

def pricing_page():
    body = f'''  <section class="section-ink">
    <div class="wrap">
      <p class="eyebrow">Simple</p>
      <h2 class="section-title">Free to download</h2>
      <p class="lede">The app is free and stays useful for free. Pro exists for two things: the Apple Watch companion, and following more than one coworker's schedule.</p>

      <div class="billing-toggle" id="billing-toggle" role="group" aria-label="Billing period">
        <button type="button" data-period="monthly" aria-pressed="true">Monthly</button>
        <button type="button" data-period="yearly" aria-pressed="false">Yearly &middot; save 16%</button>
      </div>

      <div class="price-grid">
        <div class="price-card glass-dark is-static">
          <span class="plan-name">Kairos</span>
          <p class="price-amount">$0</p>
          <p class="price-note">Free, forever. No trial clock.</p>
          <ul>
            <li>Your own rotating schedule</li>
            <li>Preset and custom rotations</li>
            <li>Colour-coded calendar and overrides</li>
            <li>Live duty status and countdown</li>
            <li>Home Screen widgets</li>
            <li>On-device storage and iCloud sync</li>
            <li class="no">Apple Watch companion</li>
            <li class="no">Unlimited shared schedules</li>
          </ul>
          <a class="btn btn-secondary" href="{APPSTORE}">Download free</a>
        </div>

        <div class="price-card glass-dark is-static is-featured">
          <span class="plan-name">Kairos Pro <span class="pill">Most useful</span></span>
          <p class="price-amount"
             data-price-monthly="$4.99" data-price-yearly="$49.99">$4.99<span class="per"
             data-per-monthly=" / month" data-per-yearly=" / year"> / month</span></p>
          <p class="price-note"
             data-note-monthly="Billed monthly. Cancel any time in Settings."
             data-note-yearly="Billed yearly — about $4.17 a month.">Billed monthly. Cancel any time in Settings.</p>
          <ul>
            <li>Everything in the free app</li>
            <li>Apple Watch companion app</li>
            <li>Progress ring and 7-day forecast on your wrist</li>
            <li>Unlimited shared coworker schedules</li>
            <li>Widgets pointed at shared schedules</li>
            <li>Supports a small independent developer</li>
          </ul>
          {badge()}
        </div>
      </div>

      <p class="mono" style="font-size:12px;opacity:0.55;margin-top:26px;max-width:640px;line-height:1.7">
        Kairos Pro is an auto-renewable subscription. Payment is charged to your Apple Account
        at confirmation of purchase. It renews automatically unless cancelled at least 24 hours
        before the end of the current period; manage or cancel it in your Apple Account settings.
        Prices shown in USD and may vary by storefront.
        <a href="{EULA}" style="color:var(--flame)">Terms of Use (EULA)</a> ·
        <a href="/privacy" style="color:var(--flame)">Privacy Policy</a>
      </p>
    </div>
  </section>

  <section class="section-paper">
    <div class="wrap">
      <p class="eyebrow">Line by line</p>
      <h2 class="section-title">What the money changes</h2>
      <div class="table-scroll">
        <table class="compare">
          <caption>If you only track your own schedule on your phone, the free app is the whole product.</caption>
          <thead>
            <tr><th scope="col">Capability</th><th scope="col">Free</th><th scope="col">Pro</th></tr>
          </thead>
          <tbody>
            <tr><td>Rotating schedule with presets</td><td class="yes">Yes</td><td class="yes">Yes</td></tr>
            <tr><td>Custom weekly layouts</td><td class="yes">Yes</td><td class="yes">Yes</td></tr>
            <tr><td>Calendar overrides (vacation, trades, on-call)</td><td class="yes">Yes</td><td class="yes">Yes</td></tr>
            <tr><td>Duty status and shift countdown</td><td class="yes">Yes</td><td class="yes">Yes</td></tr>
            <tr><td>Home Screen widgets</td><td class="yes">Yes</td><td class="yes">Yes</td></tr>
            <tr><td>Share your schedule by code</td><td class="yes">Yes</td><td class="yes">Yes</td></tr>
            <tr><td>Apple Watch companion</td><td class="no">&mdash;</td><td class="yes">Yes</td></tr>
            <tr><td>Follow unlimited shared schedules</td><td class="no">&mdash;</td><td class="yes">Yes</td></tr>
            <tr><td>iCloud sync across your devices</td><td class="yes">Yes</td><td class="yes">Yes</td></tr>
            <tr><td>Ads or tracking</td><td class="no">Never</td><td class="no">Never</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>

  <section class="section-ink">
    <div class="wrap">
      <p class="eyebrow">Before you ask</p>
      <h2 class="section-title">Billing questions</h2>
      <div id="faq-list-pricing">
        <details class="faq-item">
          <summary>Does the free version expire?</summary>
          <div class="faq-answer"><p>No. There is no trial timer. The free app tracks your own rotation indefinitely.</p></div>
        </details>
        <details class="faq-item">
          <summary>How do I cancel?</summary>
          <div class="faq-answer"><p>Through your Apple Account, the same as any other App Store subscription: Settings &rarr; your name &rarr; Subscriptions. Cancelling there stops the renewal; we never see or hold your payment details.</p></div>
        </details>
        <details class="faq-item">
          <summary>What happens to my schedule if I stop paying?</summary>
          <div class="faq-answer"><p>Your own schedule, calendar, overrides and widgets keep working — they are part of the free app. You lose the Watch companion and drop back to the free limit on how many other people's schedules you can follow. Nothing is deleted.</p></div>
        </details>
        <details class="faq-item">
          <summary>Is the yearly plan really cheaper?</summary>
          <div class="faq-answer"><p>Yes. $49.99 a year against $4.99 a month works out about 16% cheaper, roughly $4.17 a month.</p></div>
        </details>
        <details class="faq-item">
          <summary>Do the people I share with have to pay?</summary>
          <div class="faq-answer"><p>No. They download the free app and enter your 6-character code. Pro is what lets <em>you</em> follow an unlimited number of schedules, not what lets others see yours.</p></div>
        </details>
      </div>
      <p style="margin-top:26px" class="mono"><a href="/faq" style="color:var(--flame)">More questions &rarr;</a></p>
    </div>
  </section>'''

    return page(
        "pricing",
        "Pricing — Kairos Shift Tracker",
        "Kairos is free to download. Kairos Pro is $4.99 a month or $49.99 a year and adds the Apple Watch companion plus unlimited shared coworker schedules.",
        "Pricing",
        "Free to download, and genuinely useful for free. Pro adds the Apple Watch companion and unlimited shared schedules.",
        body,
        cta_eyebrow="Free to download",
        cta_head="Start Free.<br />Upgrade If It Helps.",
        cta_tag="No trial clock, no account, no card needed to try it.",
    )


# ===========================================================================
# FAQ
# ===========================================================================

FAQS = [
    ("Getting started", [
        ("What exactly does Kairos do?",
         "<p>It turns a rotating shift pattern into a calendar everyone in your life can read. You set your rotation once; Kairos then shows your live duty status, counts down to the end of the current shift or the start of the next one, and projects the whole pattern forward on a colour-coded calendar. You can share a read-only view of it with family and coworkers using a 6-character code.</p>"),
        ("Which devices does it run on?",
         "<p>iPhone, iPad, Mac and Apple Watch. It is a native app on all of them, not a web wrapper. It requires iOS 26.5 or later.</p>"),
        ("How long does setup take?",
         "<p>Seconds if you work a named rotation — Kelly, Panama, DuPont, 24/48 and 48/96 are built in. You pick the pattern and tell it which day your cycle started. If your department runs something custom, you lay out the weekly pattern yourself, which takes about a minute.</p>"),
        ("Do I need an account?",
         "<p>No. There is no sign-up, no password, and no profile. That is deliberate — see the privacy questions below.</p>"),
    ]),
    ("Sharing", [
        ("How does schedule sharing work?",
         "<p>You generate a 6-character access code from your schedule and send it to whoever needs it. They enter it in their copy of Kairos and see your live availability. It is read-only: they can see when you are working, they cannot change it.</p>"),
        ("Does my family need to pay?",
         "<p>No. They download the free app and enter your code. Kairos Pro is what lets <em>you</em> follow an unlimited number of other people's schedules.</p>"),
        ("Can I stop sharing later?",
         "<p>Yes. Sharing is opt-in and revocable — revoke the code and it stops working.</p>"),
        ("Can my spouse see several schedules at once?",
         "<p>Yes. Someone following multiple crews can switch between their own schedule and any shared schedules, which is the common case for a partner tracking two shift workers in the same household.</p>"),
    ]),
    ("Privacy &amp; data", [
        ("Where is my schedule stored?",
         "<p>On your device. Kairos has no user accounts and no backend database holding your shifts. Syncing between your own devices happens through your private iCloud database under your own Apple ID.</p>"),
        ("What are the encrypted recovery keys?",
         "<p>Because there is no account to log back into, Kairos gives you an AES-256 encrypted recovery key so you can back up your schedule and restore it on another device. It is the account-free equivalent of a password reset.</p>"),
        ("Do you sell or analyse my data?",
         "<p>No. There are no ads and no tracking profile. The full details are in the <a href=\"/privacy\">privacy policy</a>.</p>"),
        ("What happens if I delete the app?",
         "<p>The on-device copy goes with it. If you have iCloud sync on, your data is still in your own iCloud database and comes back when you reinstall; otherwise restore from a recovery key.</p>"),
    ]),
    ("Rotations", [
        ("Which rotations are supported?",
         "<p>Kelly, Panama, DuPont, 24/48 and 48/96 ship as presets. Anything else — including patterns your department invented — can be built as a custom weekly layout. The <a href=\"/rotations\">rotations page</a> has an interactive simulator covering eight common patterns.</p>"),
        ("My cycle did not start on the first of the month. Does that matter?",
         "<p>No. You set the date your cycle actually began and the pattern aligns to it. That is how the app matches the roster on your station wall rather than a generic calendar.</p>"),
        ("What about daylight saving time?",
         "<p>Version 2.1 fixed a bug where a shift day could display incorrectly around a DST change. The same release added a Workplace Timezone setting so your schedule and countdowns stay accurate when you or the people following you are travelling.</p>"),
        ("Can I mark vacation or a shift trade?",
         "<p>Yes. The calendar supports tap-to-override for vacation days, extra shifts, trades and on-call assignments, without disturbing the underlying rotation.</p>"),
    ]),
    ("Watch, widgets &amp; Pro", [
        ("What does the Apple Watch app show?",
         "<p>Current duty status on a progress ring, a 7-day shift forecast, and the full calendar. The Watch companion is part of Kairos Pro.</p>"),
        ("What sizes do the widgets come in?",
         "<p>Small, medium and large, and each one can be configured to point at a specific schedule — your own, or one shared with you.</p>"),
        ("What does Pro cost?",
         "<p>$4.99 a month or $49.99 a year, about 16% cheaper annually. Full breakdown on the <a href=\"/pricing\">pricing page</a>.</p>"),
        ("Is the free version crippled?",
         "<p>No. Your own schedule, the calendar, overrides, duty status, countdown, widgets and sharing your schedule out are all free. Pro adds the Watch app and removes the limit on how many other schedules you can follow.</p>"),
    ]),
]


def faq_page():
    sections = []
    for group, items in FAQS:
        qs = "\n".join(f'''        <details class="faq-item">
          <summary>{q}</summary>
          <div class="faq-answer">{a}</div>
        </details>''' for q, a in items)
        sections.append(f'''      <h3 class="sub-title" style="margin-top:44px">{group}</h3>
{qs}''')
    joined = "\n".join(sections)

    body = f'''  <section class="section-ink">
    <div class="wrap-narrow" style="padding-left:32px;padding-right:32px">
      <h2 class="section-title">Questions, answered</h2>
      <label class="visually-hidden" for="faq-search">Search the FAQ</label>
      <input class="faq-search mono" type="search" id="faq-search" hidden
             placeholder="Search these questions…" autocomplete="off" />

      <div id="faq-list">
{joined}
      </div>
      <p class="faq-empty mono" id="faq-empty" hidden>No questions match that search. Try fewer words, or <a href="/support" style="color:var(--flame)">contact support</a>.</p>

      <p class="prose" style="margin-top:50px">Still stuck? The <a href="/support">support page</a> covers troubleshooting, and you can always email <a href="mailto:team@kairosapp.dev">team@kairosapp.dev</a>.</p>
    </div>
  </section>'''

    # FAQPage structured data, generated from the same source list.
    import json as _json
    import re as _re

    def strip(html):
        return _re.sub(r"<[^>]+>", "", html).replace("&rarr;", "").strip()

    entities = []
    for _, items in FAQS:
        for q, a in items:
            entities.append({
                "@type": "Question",
                "name": strip(q),
                "acceptedAnswer": {"@type": "Answer", "text": strip(a)},
            })
    ld = _json.dumps(
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": entities},
        indent=2,
    )

    return page(
        "faq",
        "FAQ — Kairos Shift Tracker",
        "Answers about Kairos: setup, supported rotations, how 6-character schedule sharing works, on-device privacy and encrypted recovery, the Apple Watch companion, widgets and Pro pricing.",
        "FAQ",
        "Twenty questions, grouped and searchable. Start typing to filter them.",
        body,
        extra_head=f'\n<script type="application/ld+json">\n{ld}\n</script>\n',
        cta_eyebrow="Still stuck?",
        cta_head="Answers Are<br />Cheaper Than Guessing",
        cta_tag="If your question is not here, email us. A person reads it.",
    )


# ===========================================================================
# SUPPORT
# ===========================================================================

def support_page():
    body = f'''  <section class="section-ink">
    <div class="wrap">
      <h2 class="section-title">Get in touch</h2>
      <div class="grid-3">
        <div class="card glass-dark reveal" style="--reveal-i:0">
          <span class="fnum">Email</span>
          <h3>Talk to us</h3>
          <p>One address, read by the people who build the app.</p>
          <p><a class="btn btn-primary btn-sm" href="mailto:team@kairosapp.dev">team@kairosapp.dev</a></p>
        </div>
        <div class="card glass-dark reveal" style="--reveal-i:1">
          <span class="fnum">Self-serve</span>
          <h3>Check the FAQ</h3>
          <p>Twenty answers covering setup, sharing, privacy and billing.</p>
          <p><a class="btn btn-secondary btn-sm" href="/faq">Open the FAQ</a></p>
        </div>
        <div class="card glass-dark reveal" style="--reveal-i:2">
          <span class="fnum">App Store</span>
          <h3>Rate or review</h3>
          <p>Reviews genuinely help a small independent app get found.</p>
          <p><a class="btn btn-secondary btn-sm" href="{APPSTORE}">View the listing</a></p>
        </div>
      </div>
    </div>
  </section>

  <section class="section-paper">
    <div class="wrap">
      <p class="eyebrow">Troubleshooting</p>
      <h2 class="section-title">Common fixes</h2>
      <p class="lede">Most reports come down to one of these five things. Worth a look before you write in.</p>

      <div id="fix-list">
        <details class="faq-item" style="background:rgba(11,11,15,0.03);border-color:var(--line-on-paper)">
          <summary>My calendar shows the wrong day</summary>
          <div class="faq-answer">
            <p>Almost always the cycle start date. Kairos aligns your rotation to the day you told it the cycle began, so if that date is off by one, every day in the pattern is off by one.</p>
            <p>Open Setup, find a day you know for certain you were working, and set the cycle start so the pattern lands on it. If the problem only appears around a clock change, make sure you are on version 2.1 or later — that release fixed a daylight-saving bug that could shift a day.</p>
          </div>
        </details>
        <details class="faq-item" style="background:rgba(11,11,15,0.03);border-color:var(--line-on-paper)">
          <summary>My schedule is wrong when I travel</summary>
          <div class="faq-answer">
            <p>Set Workplace Timezone in Setup, added in version 2.1. It pins your schedule and countdowns to the timezone your job is in, so flying somewhere else does not shift your shifts.</p>
          </div>
        </details>
        <details class="faq-item" style="background:rgba(11,11,15,0.03);border-color:var(--line-on-paper)">
          <summary>A share code is not working</summary>
          <div class="faq-answer">
            <p>Check three things. First, the code is six characters and deliberately avoids ambiguous letters and digits — no letter O, no zero, no capital I, no one. If someone read it out, a mistaken O/0 is the usual culprit.</p>
            <p>Second, confirm the code has not been revoked on the sharing side. Third, make sure the person entering it is on a recent version of the app.</p>
          </div>
        </details>
        <details class="faq-item" style="background:rgba(11,11,15,0.03);border-color:var(--line-on-paper)">
          <summary>My widget is not updating</summary>
          <div class="faq-answer">
            <p>Open the app once so it can refresh, then check that Background App Refresh is on for Kairos in iOS Settings. If a widget is pointed at a shared schedule, it also needs that schedule to still be shared with you. Removing and re-adding the widget forces a fresh configuration.</p>
          </div>
        </details>
        <details class="faq-item" style="background:rgba(11,11,15,0.03);border-color:var(--line-on-paper)">
          <summary>I changed phones and my schedule is gone</summary>
          <div class="faq-answer">
            <p>Because Kairos has no accounts, there is nothing to log back into. Recovery works one of two ways: if iCloud sync was on, signing into the same Apple ID restores your data from your own private iCloud database. Otherwise, use the AES-256 encrypted recovery key you generated. If you have neither, we cannot recover it for you — we never had a copy.</p>
          </div>
        </details>
      </div>
    </div>
  </section>

  <section class="section-ink">
    <div class="wrap">
      <p class="eyebrow">Writing in</p>
      <h2 class="section-title">What to include</h2>
      <p class="lede">Four lines in your first email usually saves a whole round trip.</p>
      <div class="grid-4">
        <div class="stat-cell glass-dark is-static" style="text-align:left;padding:24px">
          <p class="label" style="margin-bottom:8px">01</p>
          <p class="mono" style="font-size:13px;opacity:0.8;margin:0;line-height:1.6">Your device and iOS version</p>
        </div>
        <div class="stat-cell glass-dark is-static" style="text-align:left;padding:24px">
          <p class="label" style="margin-bottom:8px">02</p>
          <p class="mono" style="font-size:13px;opacity:0.8;margin:0;line-height:1.6">The Kairos version from the App Store</p>
        </div>
        <div class="stat-cell glass-dark is-static" style="text-align:left;padding:24px">
          <p class="label" style="margin-bottom:8px">03</p>
          <p class="mono" style="font-size:13px;opacity:0.8;margin:0;line-height:1.6">Which rotation and cycle start date you set</p>
        </div>
        <div class="stat-cell glass-dark is-static" style="text-align:left;padding:24px">
          <p class="label" style="margin-bottom:8px">04</p>
          <p class="mono" style="font-size:13px;opacity:0.8;margin:0;line-height:1.6">A screenshot of what looks wrong</p>
        </div>
      </div>
      <p style="margin-top:34px">
        <a class="btn btn-primary" href="mailto:team@kairosapp.dev?subject=Kairos%20support">Email support</a>
      </p>
      <p class="mono" style="font-size:12px;opacity:0.55;margin-top:20px">
        Please do not send us your recovery key or any account credential. We never need it,
        and we cannot decrypt your data with it.
      </p>
    </div>
  </section>'''

    return page(
        "support",
        "Support — Kairos Shift Tracker",
        "Kairos support: troubleshooting the calendar, share codes, widgets, timezone and device migration, plus how to reach the team at team@kairosapp.dev.",
        "Support",
        "Fixes for the five things people actually write in about, and a real email address for everything else.",
        body,
        cta_eyebrow="Talk to a human",
        cta_head="We Read<br />Every Email",
        cta_tag="Kairos is built by a small team. Your report goes to the people who can fix it.",
    )


# ===========================================================================
# CHANGELOG
# ===========================================================================

RELEASES = [
    ("2.1", "28 July 2026", "current", [
        "Fixed a scheduling bug that could show an incorrect shift day around Daylight Saving Time changes.",
        "Added Workplace Timezone — set your job's timezone in Setup so your schedule and countdowns stay accurate no matter where you or the friends you share with are travelling.",
        "Minor bug fixes and UI polish.",
    ]),
    ("2.0", "July 2026", "", [
        "Second-generation release building on the initial App Store launch.",
        "Continued refinement of the shared-schedule flow and calendar rendering.",
    ]),
    ("1.0", "26 July 2026", "launch", [
        "Kairos arrives on the App Store for iPhone, iPad, Mac and Apple Watch.",
        "Preset rotations including Kelly, Panama, DuPont, 24/48 and 48/96, plus custom weekly layouts.",
        "Live duty status, shift countdown and colour-coded calendar.",
        "Schedule sharing by 6-character access code, read-only and revocable.",
        "Home Screen widgets in small, medium and large.",
        "On-device storage with CloudKit sync and AES-256 encrypted recovery keys.",
    ]),
]


def changelog_page():
    items = []
    for i, (ver, when, tag, notes) in enumerate(RELEASES):
        pill = ""
        if tag == "current":
            pill = ' <span class="pill">Current</span>'
        elif tag == "launch":
            pill = ' <span class="pill pill-quiet">Launch</span>'
        lis = "\n".join(f"            <li>{n}</li>" for n in notes)
        items.append(f'''        <div class="tl-item{'' if i == 0 else ' is-old'}" id="v{ver.replace('.', '-')}">
          <p class="tl-meta">{when}</p>
          <h3>Version {ver}{pill}</h3>
          <ul>
{lis}
          </ul>
        </div>''')
    tl = "\n".join(items)

    body = f'''  <section class="section-ink">
    <div class="wrap-narrow" style="padding-left:32px;padding-right:32px">
      <h2 class="section-title">Release history</h2>
      <div class="timeline">
{tl}
      </div>

      <p class="prose" style="margin-top:20px">
        Release notes are mirrored from the
        <a href="{APPSTORE}">App Store listing</a>, which is always the
        authoritative source for what is shipping right now.
      </p>
    </div>
  </section>

  <section class="section-paper">
    <div class="wrap">
      <p class="eyebrow">Where it runs</p>
      <h2 class="section-title">Current requirements</h2>
      <div class="grid-4">
        <div class="stat-cell glass-light is-static">
          <p class="num mono">2.1</p>
          <p class="label">Current version</p>
        </div>
        <div class="stat-cell glass-light is-static">
          <p class="num mono">26.5</p>
          <p class="label">Minimum iOS / iPadOS</p>
        </div>
        <div class="stat-cell glass-light is-static">
          <p class="num mono">4+</p>
          <p class="label">Age rating</p>
        </div>
        <div class="stat-cell glass-light is-static">
          <p class="num mono">Free</p>
          <p class="label">Price to download</p>
        </div>
      </div>
    </div>
  </section>'''

    return page(
        "changelog",
        "Changelog — Kairos Shift Tracker",
        "Release history for Kairos, including version 2.1 with the daylight-saving scheduling fix and the new Workplace Timezone setting.",
        "Changelog",
        "What shipped, and when. Mirrored from the App Store release notes.",
        body,
        cta_eyebrow="Keep it updated",
        cta_head="Always<br />Getting Sharper",
        cta_tag="Update from the App Store to pick up the latest fixes.",
    )



# ===========================================================================
# RSS
# ===========================================================================


def feed_xml():
    """Build /feed.xml from the same RELEASES list the changelog renders.

    A feed is the one social channel that costs nothing to run, cannot be
    taken away by a platform, and does not need an account to follow.
    """
    import email.utils
    import datetime

    items = []
    for ver, when, _tag, notes in RELEASES:
        try:
            dt = datetime.datetime.strptime(when, "%d %B %Y")
        except ValueError:
            try:
                dt = datetime.datetime.strptime(when, "%B %Y")
            except ValueError:
                dt = datetime.datetime(2026, 7, 26)
        pub = email.utils.format_datetime(dt.replace(tzinfo=datetime.timezone.utc))
        body = "".join(f"<li>{n}</li>" for n in notes)
        link = f"https://www.kairosapp.dev/changelog#v{ver.replace('.', '-')}"
        items.append(f"""    <item>
      <title>Kairos {ver}</title>
      <link>{link}</link>
      <guid isPermaLink="false">kairos-release-{ver}</guid>
      <pubDate>{pub}</pubDate>
      <description>&lt;ul&gt;{body}&lt;/ul&gt;</description>
    </item>""")

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Kairos — release notes</title>
    <link>https://www.kairosapp.dev/changelog</link>
    <atom:link href="https://www.kairosapp.dev/feed.xml" rel="self" type="application/rss+xml" />
    <description>What shipped in Kairos, and when. Mirrored from the App Store release notes.</description>
    <language>en-us</language>
    <copyright>2026 KairosDev LLC</copyright>
{chr(10).join(items)}
  </channel>
</rss>
"""


LIGHTBOX = '''
<div class="lightbox" id="lightbox" hidden role="dialog" aria-modal="true" aria-label="App screenshot">
  <button class="lightbox-close" id="lightbox-close" type="button" aria-label="Close">&times;</button>
  <button class="lightbox-prev" id="lightbox-prev" type="button" aria-label="Previous screenshot">&#8249;</button>
  <img id="lightbox-img" src="" alt="" />
  <button class="lightbox-next" id="lightbox-next" type="button" aria-label="Next screenshot">&#8250;</button>
  <p class="lightbox-cap" id="lightbox-cap"></p>
</div>
'''


if __name__ == "__main__":
    write("features", features_page())
    write("rotations", rotations_page())
    write("pricing", pricing_page())
    write("faq", faq_page())
    write("support", support_page())
    write("changelog", changelog_page())

    with open(os.path.join(ROOT, "feed.xml"), "w") as f:
        f.write(feed_xml())
    print("wrote feed.xml")
    print("\ndone")

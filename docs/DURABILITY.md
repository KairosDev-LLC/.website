# Site durability

What "durable" means for this site, how it is enforced, and how to recover
when something breaks.

## The deployment contract

| Assumption | Where it lives | What breaks if it changes |
|---|---|---|
| Static files served from the repository root | `vercel.json` → `outputDirectory: "."` | Nothing to build; a build step would be a new failure mode |
| Extensionless URLs (`/features`, not `/features.html`) | `vercel.json` → `cleanUrls: true` | **Every internal link 404s.** This is the single largest portability risk |
| No trailing slashes | `vercel.json` → `trailingSlash: false` | Duplicate URLs competing in search results |
| Unknown URLs render `404.html` | `404.html` at root | Visitors see the host's generic error page |
| HTML revalidates, media is cached hard | `vercel.json` → `headers` | A bad deploy would stay in browser caches |

`cleanUrls` is host-specific. **Moving off Vercel requires replacing it**, or
every link in the site breaks at once:

* **Netlify** — pretty URLs are the default; verify before cutting over.
* **GitHub Pages / S3** — no equivalent. Either convert each `page.html` to
  `page/index.html`, or rewrite every internal link to include `.html`.
* **Local preview** — `python3 -m http.server` does *not* emulate it. Use
  `python3 tools/serve.py`, which mirrors production behaviour exactly.

## Enforced invariants

`tools/check_site.py` is the durability gate. It runs on every push and pull
request via `.github/workflows/site-durability.yml`, and weekly on a schedule
to catch outbound link rot.

```bash
python3 tools/check_site.py             # offline, fast, no network
python3 tools/check_site.py --external  # also verifies outbound links resolve
python3 tools/check_site.py --json      # machine-readable
```

It fails the build on any of these:

1. An internal link, asset, or `#anchor` that does not resolve.
2. A duplicate element `id` — breaks both anchors and the JavaScript lookups.
3. Unbalanced markup (stray or unclosed tags).
4. A page missing `<title>`, description, viewport, `lang`, or image `alt` text.
5. `sitemap.xml` drift — advertising a page that does not exist, or omitting an
   indexable one.
6. A canonical URL pointing off-origin.
7. `manifest.json` that does not parse, or whose icons/shortcuts do not exist.
8. An `og:image` that is missing, not in the repository, or too small for
   social platforms to render.
9. `cleanUrls` switched off while pages still link extensionlessly.
10. A missing `404.html`.
11. JavaScript that does not parse (`node --check`).
12. `site.js` referencing an element `id` that no page defines.
13. Scroll-reveal styles that hide content without a `.js` guard — the failure
    mode where a JavaScript error leaves the page permanently blank.

Each check was verified by deliberately breaking the site and confirming the
checker caught it. Do not weaken a check to make a build pass; fix the site.

## Graceful degradation

The site must remain readable when JavaScript fails, and this is a hard
requirement rather than a nicety:

* Scroll-reveal animation is gated behind a `.js` class, so content is visible
  by default and only animates once the script is running.
* The rotation simulator has a static fallback that names every rotation it
  covers and links to the rotations page.
* Tabbed sections are reachable without JavaScript.
* `404.html` carries its own inline styles, so it still renders correctly even
  if the stylesheet itself is the thing that failed to load.

Verify by loading `python3 tools/serve.py` with JavaScript disabled.

## Recovery

* **Source of truth** — GitHub, `KairosDev-LLC/.website`. The working tree is
  not a backup; push early.
* **Bad deploy** — HTML is served `must-revalidate`, so a corrected deploy
  takes effect immediately rather than waiting out a browser cache.
* **Broken link discovered in production** — reproduce locally with
  `tools/serve.py`, add a check to `check_site.py` if the class of bug was not
  already covered, then fix.

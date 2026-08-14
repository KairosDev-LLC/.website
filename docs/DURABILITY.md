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


## Security posture

The site has no backend, no accounts and no third-party origins, so the whole
attack surface is what the browser is told it may do. That is set in
`vercel.json` and enforced by `tools/check_site.py`.

| Header | Value | Why |
|---|---|---|
| `Content-Security-Policy` | `default-src 'self'`, scripts by hash, everything else denied | Injected markup has no origin to run from or exfiltrate to |
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains; preload` | No downgrade window after the first visit |
| `X-Content-Type-Options` | `nosniff` | A mistyped asset cannot be reinterpreted as script |
| `X-Frame-Options` / `frame-ancestors` | `DENY` / `'none'` | No clickjacking frame |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Paths are not leaked to outbound links |
| `Permissions-Policy` | sensors, camera, mic, payment, USB, XR all `()` | The site needs none of them |
| `Cross-Origin-Opener-Policy` / `-Resource-Policy` | `same-origin` | No cross-origin window or resource sharing |

### The CSP contract

`script-src` is `'self'` plus a **sha256 hash per inline script** — there is no
`'unsafe-inline'` and no `'unsafe-eval'`. Two inline scripts exist and both are
hashed: the `js` class flag and the pre-paint theme boot.

This means **adding or editing an inline script changes its hash**. If the
policy is not updated to match, the browser silently drops the script. That
failure is caught two ways before it can ship:

1. `tools/check_site.py` re-hashes every inline script on every page and fails
   if one is not in the policy.
2. `tools/serve.py` serves the real `vercel.json` headers locally, so the
   preview behaves exactly like production.

To change an inline script: edit it, run `python3 tools/check_site.py`, take
the hash it prints as missing, and put it in the `script-src` list.

`style-src` keeps `'unsafe-inline'` because the markup uses `style` attributes
for per-element values the stylesheet cannot know (reveal delays, deck badge
depths). Inline *styles* cannot execute script, so this is a much smaller
concession than the script equivalent.

### What is not deployed

`.vercelignore` keeps `tools/`, `docs/`, `.github/` and loose `*.py` out of the
deployment. The CDN serves the static site and nothing else.

## Deploying

`main` is production. The **Vercel Git integration** deploys it: Vercel watches
the repository and builds every push to `main` on its own. Production served the
`d51b3c2` tree 57 seconds after that commit was pushed, with no CI involvement.

There is deliberately no deploy workflow. One existed
(`.github/workflows/deploy.yml`) and was removed on 2026-08-14: it was gated on a
`VERCEL_TOKEN` repository secret that was never set, so its deploy job was
`skipped` on all three runs while the workflow still reported success. A green
check that never deployed or verified anything is worse than no check, because it
advertises coverage the repository does not have.

Durability is still enforced on every push by `site-durability`, which runs
`tools/check_site.py` against the tree being shipped. What is no longer automated
is the post-deploy assertion that production actually serves the new build; verify
that by diffing the live bytes against the working tree when it matters.

If CI-driven deploys are wanted again, set `VERCEL_TOKEN`, `VERCEL_ORG_ID` and
`VERCEL_PROJECT_ID` as repository secrets **and** disable the Vercel Git
integration for production first, or both paths will deploy the same commit.

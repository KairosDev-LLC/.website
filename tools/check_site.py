#!/usr/bin/env python3
"""check_site.py — durability checks for the Kairos static site.

Every check encodes an invariant that, if broken, would ship a visibly broken
site: a dead link, a missing asset, an unreachable anchor, a sitemap that
advertises pages that do not exist, or JavaScript that fails to parse.

Usage:
    python3 tools/check_site.py             # offline checks only (fast, CI-safe)
    python3 tools/check_site.py --external  # also verify outbound links resolve
    python3 tools/check_site.py --json      # machine-readable output

Exit code 0 = all checks passed, 1 = at least one FAIL.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_ORIGIN = "https://www.kairosapp.dev"

failures: list[str] = []
warnings: list[str] = []
passes: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def ok(msg: str) -> None:
    passes.append(msg)


# --------------------------------------------------------------------------
# Minimal dependency-free HTML introspection.
# --------------------------------------------------------------------------
class Doc(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []   # (tag, url)
        self.ids: list[str] = []
        self.imgs_without_alt = 0
        self.tags: dict[str, int] = {}
        self.meta: dict[str, str] = {}
        self.rel: dict[str, str] = {}
        self.title_depth = 0
        self.title = ""
        self.has_lang = False
        self.stack: list[str] = []
        self.unclosed: list[str] = []

    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "param", "source", "track", "wbr"}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags[tag] = self.tags.get(tag, 0) + 1
        if tag == "html" and a.get("lang"):
            self.has_lang = True
        if a.get("id"):
            self.ids.append(a["id"])
        url = a.get("href") or a.get("src")
        if url:
            self.links.append((tag, url))
        if tag == "img" and a.get("alt") is None:
            self.imgs_without_alt += 1
        if tag == "meta":
            key = a.get("name") or a.get("property")
            if key:
                self.meta[key] = a.get("content", "")
        if tag == "link":
            rels = (a.get("rel") or "").lower().split()
            for r in rels:
                self.rel[r] = a.get("href", "")
        if tag == "title":
            self.title_depth = 1
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag == "title":
            self.title_depth = 0
        if tag in self.VOID:
            return
        if tag in self.stack:
            while self.stack and self.stack.pop() != tag:
                pass
        else:
            self.unclosed.append(tag)

    def handle_data(self, data):
        if self.title_depth:
            self.title += data


def load(path: str) -> Doc:
    d = Doc()
    with open(path, encoding="utf-8") as fh:
        d.feed(fh.read())
    return d


# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--external", action="store_true", help="verify outbound links")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    os.chdir(ROOT)
    html_files = sorted(f for f in os.listdir(".") if f.endswith(".html"))
    if not html_files:
        fail("no HTML pages found at repository root")
        return report(args)

    on_disk = set()
    for base, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules"}]
        for f in files:
            on_disk.add(os.path.relpath(os.path.join(base, f), ".").replace(os.sep, "/"))

    docs = {p: load(p) for p in html_files}
    ids_by_page = {p: set(d.ids) for p, d in docs.items()}

    def resolve(url: str, from_page: str) -> str | None:
        """Map a site-relative URL to a repo file, honouring vercel cleanUrls."""
        path = url.split("#")[0].split("?")[0]
        if path in ("", "."):
            return from_page
        path = path.lstrip("/").rstrip("/")
        if path == "":
            return "index.html"
        for cand in (path, path + ".html", path + "/index.html"):
            if cand in on_disk:
                return cand
        return None

    # 1. internal links resolve -------------------------------------------
    broken = 0
    for p, d in docs.items():
        for tag, url in d.links:
            if url.startswith(("http://", "https://", "mailto:", "tel:", "data:", "//")):
                continue
            if url.startswith("#"):
                frag = url[1:]
                if frag and frag not in ids_by_page[p]:
                    fail(f"{p}: anchor '{url}' has no matching id on the page")
                    broken += 1
                continue
            target = resolve(url, p)
            if target is None:
                fail(f"{p}: <{tag}> points at '{url}', which does not exist")
                broken += 1
                continue
            if "#" in url:
                frag = url.split("#", 1)[1]
                if frag and target in ids_by_page and frag not in ids_by_page[target]:
                    fail(f"{p}: '{url}' targets a missing id on {target}")
                    broken += 1
    if not broken:
        ok(f"all internal links and anchors resolve ({len(docs)} pages)")

    # 2. duplicate ids -----------------------------------------------------
    dupe = 0
    for p, d in docs.items():
        seen, dupes = set(), set()
        for i in d.ids:
            (dupes if i in seen else seen).add(i)
        if dupes:
            fail(f"{p}: duplicate id(s) {sorted(dupes)} — breaks anchors and JS lookups")
            dupe += 1
    if not dupe:
        ok("no duplicate element ids")

    # 3. unbalanced markup -------------------------------------------------
    bad = 0
    for p, d in docs.items():
        if d.unclosed:
            fail(f"{p}: stray closing tag(s) {sorted(set(d.unclosed))}")
            bad += 1
        leftover = [t for t in d.stack if t not in ("html", "body", "head", "p", "li")]
        if leftover:
            fail(f"{p}: unclosed tag(s) {sorted(set(leftover))}")
            bad += 1
    if not bad:
        ok("markup is balanced on every page")

    # 4. head essentials ---------------------------------------------------
    missing_meta = 0
    for p, d in docs.items():
        if not d.title.strip():
            fail(f"{p}: empty <title>")
            missing_meta += 1
        if not d.meta.get("description"):
            fail(f"{p}: missing meta description")
            missing_meta += 1
        if not d.meta.get("viewport"):
            fail(f"{p}: missing viewport meta — page will not be mobile-usable")
            missing_meta += 1
        if not d.has_lang:
            fail(f"{p}: <html> has no lang attribute")
            missing_meta += 1
        noindex = "noindex" in d.meta.get("robots", "")
        if not noindex and not d.rel.get("canonical"):
            warn(f"{p}: no canonical link")
        if d.imgs_without_alt:
            fail(f"{p}: {d.imgs_without_alt} <img> without alt attribute")
            missing_meta += 1
    if not missing_meta:
        ok("every page has title, description, viewport, lang and image alts")

    # 5. sitemap parity ----------------------------------------------------
    if "sitemap.xml" in on_disk:
        sm = open("sitemap.xml", encoding="utf-8").read()
        locs = re.findall(r"<loc>([^<]+)</loc>", sm)
        listed = set()
        for loc in locs:
            rel = loc.replace(SITE_ORIGIN, "").strip("/")
            listed.add((rel + ".html") if rel else "index.html")
        indexable = set()
        for p, d in docs.items():
            if "noindex" in d.meta.get("robots", ""):
                continue
            indexable.add(p)
        ghost = listed - set(html_files)
        if ghost:
            fail(f"sitemap.xml advertises page(s) that do not exist: {sorted(ghost)}")
        orphan = indexable - listed
        if orphan:
            fail(f"indexable page(s) missing from sitemap.xml: {sorted(orphan)}")
        if not ghost and not orphan:
            ok(f"sitemap.xml matches the {len(indexable)} indexable pages exactly")
        for p in html_files:
            d = docs[p]
            if "noindex" in d.meta.get("robots", ""):
                continue
            canon = d.rel.get("canonical", "")
            if canon and not canon.startswith(SITE_ORIGIN):
                fail(f"{p}: canonical points off-origin ({canon})")
    else:
        warn("no sitemap.xml")

    # 6. manifest ----------------------------------------------------------
    if "manifest.json" in on_disk:
        try:
            man = json.load(open("manifest.json", encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(f"manifest.json is not valid JSON: {exc}")
            man = {}
        for icon in man.get("icons", []):
            if icon.get("src", "").lstrip("/") not in on_disk:
                fail(f"manifest.json icon missing from disk: {icon.get('src')}")
        for sc in man.get("shortcuts", []):
            if resolve(sc.get("url", ""), "index.html") is None:
                fail(f"manifest.json shortcut '{sc.get('name')}' -> {sc.get('url')} does not exist")
        if man:
            ok("manifest.json parses and every icon and shortcut resolves")

    # 6b. social cards -----------------------------------------------------
    social_bad = 0
    for p, d in docs.items():
        if "noindex" in d.meta.get("robots", ""):
            continue
        og_img = d.meta.get("og:image", "")
        if not og_img:
            fail(f"{p}: no og:image — shared links render without a preview card")
            social_bad += 1
            continue
        local = og_img.replace(SITE_ORIGIN, "").lstrip("/")
        if local and local not in on_disk:
            fail(f"{p}: og:image '{og_img}' is not a file in the repository")
            social_bad += 1
        w = d.meta.get("og:image:width", "")
        h = d.meta.get("og:image:height", "")
        if w and h and (int(w) < 600 or int(h) < 315):
            fail(f"{p}: og:image is {w}x{h}; social platforms need at least 600x315")
            social_bad += 1
    if not social_bad:
        ok("every indexable page advertises a real, correctly sized og:image")

    # 7. deploy config -----------------------------------------------------
    if "vercel.json" in on_disk:
        try:
            vc = json.load(open("vercel.json", encoding="utf-8"))
            if not vc.get("cleanUrls"):
                fail("vercel.json: cleanUrls is off, but pages link to extensionless URLs")
            else:
                ok("vercel.json: cleanUrls on, extensionless links will resolve")
        except json.JSONDecodeError as exc:
            fail(f"vercel.json is not valid JSON: {exc}")
    if "404.html" not in on_disk:
        fail("no 404.html — unknown URLs will show the host's default error page")

    # 8. JavaScript parses -------------------------------------------------
    js_files = sorted(f for f in on_disk if f.endswith(".js"))
    node = subprocess.run(["bash", "-lc", "command -v node"], capture_output=True, text=True)
    if node.returncode == 0 and js_files:
        for j in js_files:
            res = subprocess.run(["node", "--check", j], capture_output=True, text=True)
            if res.returncode != 0:
                fail(f"{j}: JavaScript syntax error — {res.stderr.strip().splitlines()[0]}")
        ok(f"{len(js_files)} JavaScript file(s) parse cleanly")
    elif js_files:
        warn("node not available; skipped JavaScript syntax check")

    # 9. JS hooks exist in the markup --------------------------------------
    if "assets/site.js" in on_disk:
        src = open("assets/site.js", encoding="utf-8").read()
        hooks = sorted(set(re.findall(r"[\$]{1,2}\('#([A-Za-z0-9_-]+)'", src)))
        all_ids: set[str] = set()
        for s in ids_by_page.values():
            all_ids |= s
        orphaned = [h for h in hooks if h not in all_ids]
        if orphaned:
            warn(f"site.js references id(s) no page defines: {orphaned}")
        else:
            ok(f"all {len(hooks)} element ids used by site.js exist in the markup")

    # 10. no-JS resilience -------------------------------------------------
    css_path = "assets/site.css"
    if css_path in on_disk:
        css = open(css_path, encoding="utf-8").read()
        if ".reveal" in css and ".js .reveal" not in css:
            fail("scroll-reveal hides content without a .js guard: content is invisible when JS fails")
        else:
            ok("scroll-reveal is gated on .js, so content stays visible without JavaScript")

    # 11. external links ---------------------------------------------------
    if args.external:
        try:
            import urllib.request

            ext = set()
            for d in docs.values():
                for _tag, url in d.links:
                    if url.startswith(("http://", "https://")) and SITE_ORIGIN not in url:
                        ext.add(url)
            for url in sorted(ext):
                req = urllib.request.Request(url, method="HEAD",
                                             headers={"User-Agent": "kairos-site-check/1.0"})
                try:
                    with urllib.request.urlopen(req, timeout=25) as resp:
                        if resp.status >= 400:
                            fail(f"outbound link {url} returned HTTP {resp.status}")
                except Exception as exc:  # noqa: BLE001 - network shape varies
                    fail(f"outbound link {url} is unreachable: {type(exc).__name__}")
            ok(f"checked {len(ext)} outbound link(s)")
        except Exception as exc:  # noqa: BLE001
            warn(f"external check skipped: {exc}")

    return report(args)


def report(args) -> int:
    if args.json:
        print(json.dumps({"passed": passes, "warnings": warnings,
                          "failures": failures, "ok": not failures}, indent=2))
    else:
        for p in passes:
            print(f"  PASS  {p}")
        for w in warnings:
            print(f"  WARN  {w}")
        for f in failures:
            print(f"  FAIL  {f}")
        print()
        print(f"{len(passes)} passed, {len(warnings)} warning(s), {len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

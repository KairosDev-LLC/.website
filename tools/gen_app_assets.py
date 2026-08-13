#!/usr/bin/env python3
"""gen_app_assets.py — pull the real product assets from their sources.

Two sources, both authoritative, neither hand-maintained:

1. The App Store listing (iTunes lookup API) for the app screens. Whatever is
   on the listing is what ships in the app, so the site cannot drift from the
   store. Screenshots are fetched at full resolution and re-encoded as small
   WebP textures for the 3D hero and the gallery cards.
2. The organisation's `.github` brand repository for the logo, so the site and
   the GitHub org profile use the same mark.

Run it when the listing or the branding changes, then commit the output.

    python3 tools/gen_app_assets.py
    python3 tools/gen_app_assets.py --brand-repo /path/to/.github
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request

APP_ID = "6792157855"
LOOKUP = f"https://itunes.apple.com/lookup?id={APP_ID}&country=us&entity=software"
BRAND_REPO = "git@github.com:KairosDev-LLC/.github.git"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(ROOT, "assets", "shots")
BRAND = os.path.join(ROOT, "assets", "brand")

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"}

# The listing order is stable; these are the names the site references.
IPHONE_NAMES = ["app-1-working", "app-2-calendar", "app-3-vacation"]
IPAD_NAMES = ["ipad-1-working", "ipad-2-vacation", "ipad-3-offduty"]


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=90) as resp:
        return resp.read()


def full_res(url: str, spec: str = "2000x0w.png") -> str:
    """App Store thumbnail URLs carry their size in the last path segment."""
    return re.sub(r"/\d+x\d+[a-z]{2}\.(jpg|png|webp)$", "/" + spec, url)


def listing() -> dict:
    data = json.loads(fetch(LOOKUP).decode("utf-8"))
    if not data.get("resultCount"):
        raise SystemExit("App Store lookup returned nothing — is the app ID right?")
    return data["results"][0]


def save_texture(img, path: str, width: int, quality: int = 80) -> None:
    from PIL import Image

    h = round(img.height * width / img.width)
    out = img.convert("RGB").resize((width, h), Image.LANCZOS)
    out.save(path, "WEBP", quality=quality, method=6)
    print(f"  {os.path.relpath(path, ROOT)}  {out.width}x{out.height}  {os.path.getsize(path) / 1024:.0f} KB")


def pull_screens(app: dict) -> None:
    from PIL import Image

    os.makedirs(SHOTS, exist_ok=True)
    pairs = list(zip(app.get("screenshotUrls", []), IPHONE_NAMES)) + \
            list(zip(app.get("ipadScreenshotUrls", []), IPAD_NAMES))
    print(f"App Store: {app['trackName']} {app['version']} — {len(pairs)} screens")
    for url, name in pairs:
        img = Image.open(io.BytesIO(fetch(full_res(url))))
        # 720px wide is enough for a full-bleed phone in the 3D scene at 2x DPR.
        save_texture(img, os.path.join(SHOTS, f"{name}.webp"), 720)
        # A small card-sized copy for the gallery grid.
        save_texture(img, os.path.join(SHOTS, f"{name}-card.webp"), 360, quality=76)


def pull_brand(repo_path: str | None) -> None:
    from PIL import Image

    os.makedirs(BRAND, exist_ok=True)
    tmp = None
    if not repo_path:
        tmp = tempfile.mkdtemp(prefix="kairos-brand-")
        print(f"Brand: cloning {BRAND_REPO}")
        subprocess.run(["git", "clone", "--depth", "1", "-q", BRAND_REPO, tmp], check=True)
        repo_path = tmp

    src_dir = os.path.join(repo_path, "Logo & Branding")
    if not os.path.isdir(src_dir):
        print(f"Brand: no 'Logo & Branding' in {repo_path}, skipping", file=sys.stderr)
        return

    # The transparent figurehead is the mark; everything else is a lockup.
    mark = Image.open(os.path.join(src_dir, "apptransparent.png")).convert("RGBA")
    bbox = mark.split()[-1].getbbox()
    if bbox:
        mark = mark.crop(bbox)
    for size in (512, 128):
        side = max(mark.size)
        canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        canvas.paste(mark, ((side - mark.width) // 2, (side - mark.height) // 2))
        out = canvas.resize((size, size), Image.LANCZOS)
        path = os.path.join(BRAND, f"mark-{size}.png")
        out.save(path, optimize=True)
        print(f"  {os.path.relpath(path, ROOT)}  {size}x{size}  {os.path.getsize(path) / 1024:.0f} KB")

    for name in ("logo.png", "app.png"):
        src = os.path.join(src_dir, name)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(BRAND, name))
            print(f"  assets/brand/{name}")

    if tmp:
        shutil.rmtree(tmp, ignore_errors=True)



def build_mark(size_out=(128,)) -> None:
    """Derive the small nav mark from the official transparent figurehead.

    The engraving is too fine to read under ~32px, so the nav mark is a
    high-contrast silhouette of it on a rounded tile. Same source of truth as
    the org profile, just legible at nav size.
    """
    from PIL import Image, ImageDraw, ImageFilter, ImageOps

    src_path = os.path.join(BRAND, "mark-512.png")
    if not os.path.exists(src_path):
        print("Mark: assets/brand/mark-512.png missing, skipping")
        return
    src = Image.open(src_path).convert("RGBA")

    # Flatten onto white, then threshold the ink into a solid silhouette.
    flat = Image.alpha_composite(Image.new("RGBA", src.size, (255, 255, 255, 255)), src).convert("L")
    bbox = flat.point(lambda v: 255 if v < 235 else 0).getbbox()
    if bbox:
        flat = flat.crop(bbox)
    mask = ImageOps.autocontrast(flat, cutoff=1).point(lambda v: 255 if v < 205 else 0)
    mask = mask.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.MinFilter(5))
    mask = mask.filter(ImageFilter.GaussianBlur(0.5))

    W = 128
    tile = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    ImageDraw.Draw(tile).rounded_rectangle([0, 0, W - 1, W - 1], radius=int(W * 0.24),
                                           fill=(20, 20, 23, 255))
    h = int(W * 0.74)
    w = max(1, int(h * mask.width / mask.height))
    art = mask.resize((w, h), Image.LANCZOS)
    layer = Image.new("RGBA", (w, h), (255, 90, 31, 255))
    layer.putalpha(art)
    tile.alpha_composite(layer, ((W - w) // 2, (W - h) // 2))
    out = os.path.join(ROOT, "assets", "brand-mark.png")
    tile.save(out, optimize=True)
    print(f"  assets/brand-mark.png  {W}x{W}  {os.path.getsize(out) / 1024:.0f} KB")


CARD_SHOTS = [
    ("live-status", "app-1-working", "On duty"),
    ("month-calendar", "app-2-calendar", "Calendar"),
    ("vacation", "app-3-vacation", "Vacation"),
]


def build_cards() -> None:
    """Compose gallery card art: the real screen on a dark product backdrop.

    Card slots are 1200x854 landscape; an App Store screenshot is tall and
    narrow, so it is placed on a tinted stage rather than letterboxed.
    """
    from PIL import Image, ImageDraw, ImageFilter

    W, H = 1200, 854
    for slug, shot, _label in CARD_SHOTS:
        src_path = os.path.join(SHOTS, f"{shot}.webp")
        if not os.path.exists(src_path):
            print(f"Cards: {src_path} missing, skipping")
            continue
        phone = Image.open(src_path).convert("RGB")

        card = Image.new("RGB", (W, H), (15, 15, 17))
        glow = Image.new("RGB", (W, H), (15, 15, 17))
        gd = ImageDraw.Draw(glow)
        gd.ellipse([W * 0.30, -H * 0.55, W * 1.15, H * 0.75], fill=(58, 26, 14))
        gd.ellipse([-W * 0.30, H * 0.45, W * 0.55, H * 1.5], fill=(18, 20, 40))
        card = Image.blend(card, glow.filter(ImageFilter.GaussianBlur(90)), 0.85)

        ph = int(H * 0.86)
        pw = max(1, int(phone.width * ph / phone.height))
        phone = phone.resize((pw, ph), Image.LANCZOS)

        # Rounded corners on the screen itself.
        radius = int(pw * 0.085)
        mask = Image.new("L", (pw, ph), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, pw - 1, ph - 1], radius=radius, fill=255)

        x, y = (W - pw) // 2, (H - ph) // 2
        shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rounded_rectangle([x + 6, y + 18, x + pw + 6, y + ph + 18],
                                                 radius=radius, fill=(0, 0, 0, 190))
        shadow = shadow.filter(ImageFilter.GaussianBlur(28))
        card = Image.alpha_composite(card.convert("RGBA"), shadow).convert("RGB")
        card.paste(phone, (x, y), mask)

        out = os.path.join(ROOT, "assets", "thumbs", f"{slug}.webp")
        card.save(out, "WEBP", quality=82, method=6)
        print(f"  assets/thumbs/{slug}.webp  {W}x{H}  {os.path.getsize(out) / 1024:.0f} KB")



# Every tab across the site gets a preview image; these are the sources.
TAB_THUMBS = [
    # slug,           source,                       kind
    ("tab-dashboard", "app-1-working.webp", "shot", 0.42),
    ("tab-calendar", "app-2-calendar.webp", "shot", 0.40),
    ("tab-vacation", "app-3-vacation.webp", "shot", 0.42),
    ("tab-sharing", "sharing.svg", "svg", 0.5),
    ("tab-privacy", "privacy.svg", "svg", 0.5),
    ("tab-watch", "watch.svg", "svg", 0.5),
    ("tab-widgets", "widgets.svg", "svg", 0.5),
    ("tab-rotations", "24-48.svg", "svg", 0.5),
    ("tab-24-48", "24-48.svg", "svg", 0.5),
    ("tab-panama", "panama.svg", "svg", 0.5),
    ("tab-kelly", "kelly.svg", "svg", 0.5),
    ("tab-dupont", "dupont.svg", "svg", 0.5),
]

TAB_W, TAB_H = 264, 185


def render_svg(path: str, width: int) -> "Image.Image":
    """Rasterise one of the generated SVG thumbnails with Inkscape."""
    from PIL import Image

    with tempfile.TemporaryDirectory() as tmp:
        png = os.path.join(tmp, "out.png")
        subprocess.run(
            ["inkscape", path, "--export-type=png", f"--export-filename={png}",
             f"--export-width={width}"],
            check=True, capture_output=True,
        )
        return Image.open(png).convert("RGB")


def build_tab_thumbs() -> None:
    from PIL import Image, ImageDraw

    out_dir = os.path.join(ROOT, "assets", "tabs")
    os.makedirs(out_dir, exist_ok=True)
    thumbs_dir = os.path.join(ROOT, "assets", "thumbs")

    for slug, source, kind, focus in TAB_THUMBS:
        if kind == "shot":
            src = Image.open(os.path.join(SHOTS, source)).convert("RGB")
        else:
            src = render_svg(os.path.join(thumbs_dir, source), TAB_W * 2)

        # Cover-crop to the tab ratio around the interesting band of the image.
        scale = max(TAB_W / src.width, TAB_H / src.height)
        w, h = max(TAB_W, round(src.width * scale)), max(TAB_H, round(src.height * scale))
        img = src.resize((w, h), Image.LANCZOS)
        top = min(max(0, round(h * focus - TAB_H / 2)), h - TAB_H)
        left = (w - TAB_W) // 2
        img = img.crop((left, top, left + TAB_W, top + TAB_H))

        # Rounded corners, matte-filled so the WebP stays opaque.
        mask = Image.new("L", (TAB_W, TAB_H), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, TAB_W - 1, TAB_H - 1], radius=14, fill=255)
        matted = Image.new("RGB", (TAB_W, TAB_H), (20, 20, 23))
        matted.paste(img, (0, 0), mask)

        path = os.path.join(out_dir, f"{slug}.webp")
        matted.save(path, "WEBP", quality=80, method=6)
        print(f"  assets/tabs/{slug}.webp  {TAB_W}x{TAB_H}  {os.path.getsize(path) / 1024:.0f} KB")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand-repo", help="local checkout of the org .github repo")
    ap.add_argument("--skip-brand", action="store_true")
    ap.add_argument("--skip-screens", action="store_true")
    args = ap.parse_args()

    if not args.skip_screens:
        pull_screens(listing())
    if not args.skip_brand:
        pull_brand(args.brand_repo)
        build_mark()
    build_cards()
    build_tab_thumbs()
    print("done")


if __name__ == "__main__":
    main()

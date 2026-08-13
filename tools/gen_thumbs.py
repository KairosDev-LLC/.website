#!/usr/bin/env python3
"""Generate static SVG preview thumbnails for the Kairos website.

Pure standard library. Deterministic and idempotent: re-running produces
byte-identical files. Output goes to assets/thumbs/<slug>.svg.

Each thumbnail is a dark-mode product-screenshot mock sized 1200x854
(71.146% aspect ratio), safe for use in <img src="...">: no scripts,
no external fonts, no external images.

    python3 tools/gen_thumbs.py
"""

import os
import sys

# --------------------------------------------------------------------------
# Design tokens
# --------------------------------------------------------------------------

W, H = 1200, 854

CANVAS = "#0f0f11"
CARD = "#17171a"
CARD_2 = "#1d1d21"
BORDER = "rgba(255,255,255,0.10)"
BORDER_SOFT = "rgba(255,255,255,0.06)"
TEXT = "#e8e6e2"
MUTED = "#9a9aa1"
FLAME = "#ff5a1f"
NIGHT = "#6c8cff"
GREEN = "#37c98b"
OFF_FILL = "#ffffff"
OFF_OPACITY = "0.08"

FONT = "Inter, -apple-system, Segoe UI, Roboto, sans-serif"

# --------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------

# Mirrors the PATTERNS table in assets/site.js.
# D = 24h/day shift, N = night shift, . = off.
PATTERNS = {
    "24-48": {
        "name": "24/48",
        "pattern": "D..",
        "shiftHours": 24,
    },
    "48-96": {
        "name": "48/96",
        "pattern": "DD....",
        "shiftHours": 24,
    },
    "kelly": {
        "name": "Kelly",
        "pattern": "D.D.D....",
        "shiftHours": 24,
    },
    "panama": {
        "name": "Panama (2-2-3)",
        "pattern": "DD..DDD..DD...",
        "shiftHours": 12,
    },
    "dupont": {
        "name": "DuPont",
        "pattern": "NNNN...DDD.NNN...DDDD.......",
        "shiftHours": 12,
    },
    "pitman": {
        "name": "Pitman nights (2-3-2)",
        "pattern": "NN..NNN..NN...",
        "shiftHours": 12,
    },
    "4-on-4-off": {
        "name": "4 on / 4 off",
        "pattern": "DDDD....",
        "shiftHours": 12,
    },
    "5-2": {
        "name": "5 on / 2 off",
        "pattern": "DDDDD..",
        "shiftHours": 8,
    },
}

# Feature thumbnails: slug -> (title, renderer name)
THUMBS = [
    ("live-status", "Live status"),
    ("sharing", "Shared access"),
    ("widgets", "Home screen widgets"),
    ("watch", "Apple Watch"),
    ("privacy", "Private by design"),
    ("vacation", "Vacation planning"),
]

DOW = ["S", "M", "T", "W", "T", "F", "S"]

OUT_DIRNAME = os.path.join("assets", "thumbs")


# --------------------------------------------------------------------------
# Small SVG helpers
# --------------------------------------------------------------------------

def esc(text):
    """Escape text for XML character data / attribute values."""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def num(v):
    """Compact, deterministic number formatting."""
    if isinstance(v, int):
        return str(v)
    s = "%.2f" % float(v)
    s = s.rstrip("0").rstrip(".")
    return s or "0"


def rect(x, y, w, h, fill, rx=0, opacity=None, stroke=None, stroke_width=1):
    parts = ['<rect x="%s" y="%s" width="%s" height="%s"'
             % (num(x), num(y), num(w), num(h))]
    if rx:
        parts.append(' rx="%s"' % num(rx))
    parts.append(' fill="%s"' % fill)
    if opacity is not None:
        parts.append(' fill-opacity="%s"' % opacity)
    if stroke:
        parts.append(' stroke="%s" stroke-width="%s"' % (stroke, num(stroke_width)))
    parts.append("/>")
    return "".join(parts)


def text(x, y, s, size=16, fill=TEXT, weight=400, anchor="start",
         spacing=None, opacity=None):
    # font-family and the default fill are inherited from the root group,
    # which keeps each document well under the size budget.
    parts = ['<text x="%s" y="%s" font-size="%s"' % (num(x), num(y), num(size))]
    if fill != TEXT:
        parts.append(' fill="%s"' % fill)
    if weight != 400:
        parts.append(' font-weight="%s"' % weight)
    if anchor != "start":
        parts.append(' text-anchor="%s"' % anchor)
    if spacing is not None:
        parts.append(' letter-spacing="%s"' % num(spacing))
    if opacity is not None:
        parts.append(' opacity="%s"' % opacity)
    parts.append(">%s</text>" % esc(s))
    return "".join(parts)


def circle(cx, cy, r, fill, opacity=None):
    o = '' if opacity is None else ' fill-opacity="%s"' % opacity
    return '<circle cx="%s" cy="%s" r="%s" fill="%s"%s/>' % (
        num(cx), num(cy), num(r), fill, o)


def defs_glow(uid):
    """Corner gradient glow + a card gradient, scoped by a unique id prefix."""
    return (
        '<defs>'
        '<radialGradient id="%s-glow" cx="0.5" cy="0.5" r="0.5">'
        '<stop offset="0" stop-color="%s" stop-opacity="0.35"/>'
        '<stop offset="0.55" stop-color="%s" stop-opacity="0.10"/>'
        '<stop offset="1" stop-color="%s" stop-opacity="0"/>'
        '</radialGradient>'
        '<radialGradient id="%s-glow2" cx="0.5" cy="0.5" r="0.5">'
        '<stop offset="0" stop-color="%s" stop-opacity="0.22"/>'
        '<stop offset="1" stop-color="%s" stop-opacity="0"/>'
        '</radialGradient>'
        '<linearGradient id="%s-card" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#1c1c20"/>'
        '<stop offset="1" stop-color="%s"/>'
        '</linearGradient>'
        '</defs>'
        % (uid, FLAME, FLAME, FLAME, uid, NIGHT, NIGHT, uid, CARD)
    )


def frame(uid, title, subtitle):
    """Canvas + glow + outer card chrome shared by every thumbnail."""
    out = [rect(0, 0, W, H, CANVAS)]
    # Flame glow, top-right corner. Night glow, bottom-left.
    out.append('<ellipse cx="1090" cy="-40" rx="520" ry="380" '
               'fill="url(#%s-glow)"/>' % uid)
    out.append('<ellipse cx="60" cy="900" rx="440" ry="320" '
               'fill="url(#%s-glow2)"/>' % uid)
    # Outer card.
    out.append(rect(64, 64, W - 128, H - 128, "url(#%s-card)" % uid, rx=32,
                    stroke=BORDER, stroke_width=1.5))
    # Subtle inner border (inset hairline).
    out.append(rect(76, 76, W - 152, H - 152, "none", rx=24,
                    stroke=BORDER_SOFT, stroke_width=1))
    # Title row.
    out.append(circle(116, 128, 9, FLAME))
    out.append(text(140, 135, title, size=30, weight=600))
    if subtitle:
        out.append(text(W - 116, 133, subtitle, size=19, fill=MUTED,
                        anchor="end"))
    out.append('<rect x="100" y="160" width="1000" height="1" fill="%s"/>'
               % BORDER)
    return out


def svg_document(uid, body):
    head = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
            'width="100%%" height="100%%" preserveAspectRatio="xMidYMid meet" '
            'role="img">' % (W, H))
    group = '<g font-family="%s" fill="%s">' % (FONT, TEXT)
    return (head + defs_glow(uid) + group + "".join(body)
            + "</g></svg>\n")


# --------------------------------------------------------------------------
# Rotation calendar thumbnails
# --------------------------------------------------------------------------

def weekly_hours(pattern, shift_hours):
    worked = sum(1 for c in pattern if c in "DN")
    return worked * shift_hours * 7.0 / len(pattern)


def cell_color(state):
    if state == "D":
        return FLAME, None
    if state == "N":
        return NIGHT, None
    return OFF_FILL, OFF_OPACITY


def render_rotation(slug, meta):
    uid = "k" + slug.replace(".", "-")
    pattern = meta["pattern"]
    hours = weekly_hours(pattern, meta["shiftHours"])
    hours_label = ("%.0f" % hours) if abs(hours - round(hours)) < 0.05 \
        else ("%.1f" % hours)

    subtitle = "%d-day cycle" % len(pattern)
    body = frame(uid, meta["name"], subtitle)

    # Weekday header.
    cols, rows = 7, 5
    grid_x, grid_y = 116, 236
    grid_w = W - 232
    gap = 14
    cw = (grid_w - gap * (cols - 1)) / cols
    ch = 82.0

    for i, d in enumerate(DOW):
        cx = grid_x + i * (cw + gap) + cw / 2
        body.append(text(cx, 208, d, size=18, fill=MUTED, weight=600,
                         anchor="middle", spacing=1.5))

    # Day cells, filled by the repeating pattern. Day numbers start at 1 in
    # the second column so the month reads like a real calendar.
    lead = 1
    day = 1 - lead
    for r in range(rows):
        for c in range(cols):
            idx = r * cols + c
            x = grid_x + c * (cw + gap)
            y = grid_y + r * (ch + gap)
            if idx < lead:
                body.append(rect(x, y, cw, ch, OFF_FILL, rx=14,
                                 opacity="0.025"))
                day += 1
                continue
            state = pattern[(idx - lead) % len(pattern)]
            fill, op = cell_color(state)
            body.append(rect(x, y, cw, ch, fill, rx=14, opacity=op,
                             stroke=(BORDER_SOFT if state == "." else None)))
            label_fill = "#12100f" if state == "D" else (
                "#0d1024" if state == "N" else MUTED)
            body.append(text(x + 12, y + 30, day, size=17,
                             fill=label_fill, weight=600))
            if state in "DN":
                body.append(text(x + cw / 2, y + 64,
                                 "24h" if meta["shiftHours"] == 24
                                 else ("%dh" % meta["shiftHours"]),
                                 size=17, fill=label_fill, weight=700,
                                 anchor="middle"))
            day += 1

    # Footer legend + stats.
    fy = 742
    body.append(rect(116, fy - 22, 14, 14, FLAME, rx=4))
    body.append(text(140, fy - 9, "Day", size=18, fill=MUTED))
    body.append(rect(206, fy - 22, 14, 14, NIGHT, rx=4))
    body.append(text(230, fy - 9, "Night", size=18, fill=MUTED))
    body.append(rect(306, fy - 22, 14, 14, OFF_FILL, rx=4,
                     opacity=OFF_OPACITY))
    body.append(text(330, fy - 9, "Off", size=18, fill=MUTED))
    body.append(text(W - 116, fy - 9,
                     "%s h/week average" % hours_label,
                     size=20, fill=TEXT, weight=600, anchor="end"))
    body.append(text(116, fy + 32, "Pattern  %s" % pattern,
                     size=18, fill=MUTED, spacing=2))
    return svg_document(uid, body)


# --------------------------------------------------------------------------
# Feature thumbnails
# --------------------------------------------------------------------------

def render_live_status():
    uid = "klive"
    body = frame(uid, "Live status", "Right now")

    # Big status pill.
    body.append(rect(116, 226, 460, 104, FLAME, rx=52, opacity="0.16"))
    body.append(rect(116, 226, 460, 104, "none", rx=52, stroke=FLAME,
                     stroke_width=2))
    body.append(circle(176, 278, 16, FLAME))
    body.append(text(212, 290, "ON DUTY", size=42, fill=FLAME, weight=700,
                     spacing=3))

    body.append(text(116, 404, "Shift ends in", size=22, fill=MUTED))
    # Countdown digits.
    for i, part in enumerate(("04", "12", "39")):
        x = 116 + i * 198
        body.append(rect(x, 430, 168, 152, CARD_2, rx=22, stroke=BORDER,
                         stroke_width=1))
        body.append(text(x + 84, 536, part, size=86, fill=TEXT, weight=700,
                         anchor="middle"))
        if i < 2:
            body.append(text(x + 182, 528, ":", size=64, fill=MUTED,
                             weight=700, anchor="middle"))
    for i, lbl in enumerate(("HOURS", "MINUTES", "SECONDS")):
        body.append(text(116 + i * 198 + 84, 610, lbl, size=15, fill=MUTED,
                         weight=600, anchor="middle", spacing=2))

    # Progress bar for the shift.
    body.append(text(116, 682, "Shift progress", size=19, fill=MUTED))
    body.append(rect(116, 700, 968, 16, OFF_FILL, rx=8, opacity=OFF_OPACITY))
    body.append(rect(116, 700, 640, 16, FLAME, rx=8))
    body.append(text(1084, 682, "08:00 - 08:00", size=19, fill=MUTED,
                     anchor="end"))

    # Next-up row.
    body.append(rect(116, 742, 968, 48, CARD_2, rx=14, stroke=BORDER,
                     stroke_width=1))
    body.append(circle(146, 766, 7, NIGHT))
    body.append(text(168, 773, "Next: 48 hours off, back Thursday 08:00",
                     size=19, fill=TEXT))
    return svg_document(uid, body)


def render_sharing():
    uid = "kshare"
    body = frame(uid, "Shared access", "Crew invite")

    body.append(text(116, 250, "Give this code to your crew", size=22,
                     fill=MUTED))

    # Six character boxes.
    code = "K7X2M9"
    bw, gap = 138, 20
    total = len(code) * bw + (len(code) - 1) * gap
    sx = (W - total) / 2
    for i, ch in enumerate(code):
        x = sx + i * (bw + gap)
        body.append(rect(x, 292, bw, 168, CARD_2, rx=22, stroke=BORDER,
                         stroke_width=1.5))
        body.append(text(x + bw / 2, 408, ch, size=74, fill=TEXT, weight=700,
                         anchor="middle"))
    body.append(rect(sx, 292, total, 168, "none", rx=22, stroke=FLAME,
                     stroke_width=1))

    # Share glyph: three nodes joined by two lines.
    gx, gy = 176, 592
    body.append(circle(gx + 84, gy - 44, 22, FLAME))
    body.append(circle(gx, gy + 24, 22, FLAME, opacity="0.7"))
    body.append(circle(gx + 84, gy + 92, 22, FLAME, opacity="0.7"))
    body.append('<path d="M %s %s L %s %s M %s %s L %s %s" stroke="%s" '
                'stroke-width="4" stroke-linecap="round" opacity="0.7"/>'
                % (num(gx + 20), num(gy + 12), num(gx + 64), num(gy - 32),
                   num(gx + 20), num(gy + 36), num(gx + 64), num(gy + 80),
                   FLAME))

    body.append(text(300, gy - 4, "Share your roster", size=30, weight=600))
    body.append(text(300, gy + 40,
                     "Read-only. Revoke the code at any time.",
                     size=20, fill=MUTED))

    # Member rows.
    for i, (nm, role) in enumerate((("A Platoon", "3 members"),
                                    ("Station 14", "Viewer"))):
        y = 700 + i * 60
        body.append(rect(116, y, 968, 48, CARD_2, rx=14, stroke=BORDER,
                         stroke_width=1))
        body.append(circle(146, y + 24, 12, NIGHT, opacity="0.8"))
        body.append(text(174, y + 31, nm, size=19, fill=TEXT))
        body.append(text(1058, y + 31, role, size=18, fill=MUTED,
                         anchor="end"))
    return svg_document(uid, body)


def render_widgets():
    uid = "kwidget"
    body = frame(uid, "Home screen widgets", "Small / Medium / Large")

    # Small widget.
    body.append(rect(116, 220, 236, 236, CARD_2, rx=40, stroke=BORDER,
                     stroke_width=1.5))
    body.append(text(148, 268, "TODAY", size=15, fill=MUTED, weight=700,
                     spacing=2))
    body.append(rect(148, 288, 172, 44, FLAME, rx=12, opacity="0.18"))
    body.append(text(164, 319, "ON DUTY", size=23, fill=FLAME, weight=700))
    body.append(text(148, 392, "04:12", size=54, fill=TEXT, weight=700))
    body.append(text(148, 424, "until 08:00", size=17, fill=MUTED))

    # Medium widget.
    body.append(rect(388, 220, 696, 236, CARD_2, rx=40, stroke=BORDER,
                     stroke_width=1.5))
    body.append(text(424, 268, "THIS WEEK", size=15, fill=MUTED, weight=700,
                     spacing=2))
    week = "DD..DDD"
    for i, st in enumerate(week):
        x = 424 + i * 90
        fill, op = cell_color(st)
        body.append(rect(x, 288, 74, 108, fill, rx=18, opacity=op,
                         stroke=(BORDER_SOFT if st == "." else None)))
        lab = "#12100f" if st == "D" else MUTED
        body.append(text(x + 37, 322, DOW[i], size=17, fill=lab, weight=700,
                         anchor="middle"))
        body.append(text(x + 37, 368, str(i + 12), size=25, fill=lab,
                         weight=600, anchor="middle"))
    body.append(text(424, 428, "56 h this week - next off Saturday",
                     size=19, fill=MUTED))

    # Large widget.
    body.append(rect(116, 488, 968, 300, CARD_2, rx=40, stroke=BORDER,
                     stroke_width=1.5))
    body.append(text(152, 536, "NEXT 21 DAYS", size=15, fill=MUTED,
                     weight=700, spacing=2))
    seq = ("DD....DD....DD....DD.")
    for i, st in enumerate(seq):
        x = 152 + (i % 7) * 130
        y = 560 + (i // 7) * 72
        fill, op = cell_color(st)
        body.append(rect(x, y, 112, 54, fill, rx=14, opacity=op,
                         stroke=(BORDER_SOFT if st == "." else None)))
    body.append(text(1048, 536, "48/96", size=19, fill=FLAME, weight=600,
                     anchor="end"))
    return svg_document(uid, body)


def render_watch():
    uid = "kwatch"
    body = frame(uid, "Apple Watch", "Complications")

    # Watch face: rounded square with a ring gauge.
    fx, fy, fs = 148, 246, 420
    body.append(rect(fx - 14, fy - 14, fs + 28, fs + 28, "#0b0b0d", rx=110,
                     stroke=BORDER, stroke_width=2))
    body.append(rect(fx, fy, fs, fs, "#050506", rx=98))

    cx, cy = fx + fs / 2, fy + fs / 2
    r = 148
    circumference = 2 * 3.14159265 * r
    body.append('<circle cx="%s" cy="%s" r="%s" fill="none" stroke="%s" '
                'stroke-opacity="0.12" stroke-width="26"/>'
                % (num(cx), num(cy), num(r), OFF_FILL))
    # 68% of the ring, starting at 12 o'clock.
    dash = circumference * 0.68
    body.append('<circle cx="%s" cy="%s" r="%s" fill="none" stroke="%s" '
                'stroke-width="26" stroke-linecap="round" '
                'stroke-dasharray="%s %s" transform="rotate(-90 %s %s)"/>'
                % (num(cx), num(cy), num(r), FLAME, num(dash),
                   num(circumference - dash), num(cx), num(cy)))
    body.append(text(cx, cy - 12, "04:12", size=76, fill=TEXT, weight=700,
                     anchor="middle"))
    body.append(text(cx, cy + 34, "LEFT ON SHIFT", size=18, fill=MUTED,
                     weight=600, anchor="middle", spacing=2))
    body.append(text(cx, cy + 92, "ON DUTY", size=22, fill=FLAME, weight=700,
                     anchor="middle", spacing=2))

    # Right-hand complication list.
    lx = 640
    body.append(text(lx, 262, "Complications", size=26, weight=600))
    items = (("Circular", "Ring gauge"),
             ("Rectangular", "Next shift"),
             ("Corner", "Hours left"),
             ("Inline", "On duty"))
    for i, (nm, sub) in enumerate(items):
        y = 296 + i * 96
        body.append(rect(lx, y, 444, 78, CARD_2, rx=20, stroke=BORDER,
                         stroke_width=1))
        body.append(circle(lx + 42, y + 39, 20, FLAME, opacity="0.22"))
        body.append(circle(lx + 42, y + 39, 9, FLAME))
        body.append(text(lx + 78, y + 34, nm, size=21, fill=TEXT,
                         weight=600))
        body.append(text(lx + 78, y + 60, sub, size=17, fill=MUTED))
    body.append(text(lx, 720, "Synced from iPhone, no account required",
                     size=18, fill=MUTED))
    return svg_document(uid, body)


def render_privacy():
    uid = "kpriv"
    body = frame(uid, "Private by design", "No accounts")

    # Shield with a lock inside.
    sx, sy = 300, 300
    body.append('<path d="M %s %s L %s %s L %s %s C %s %s %s %s %s %s '
                'C %s %s %s %s %s %s L %s %s Z" fill="%s" fill-opacity="0.12" '
                'stroke="%s" stroke-width="3" stroke-linejoin="round"/>'
                % (num(sx), num(sy), num(sx + 108), num(sy - 44),
                   num(sx + 216), num(sy),
                   num(sx + 216), num(sy + 150), num(sx + 200), num(sy + 236),
                   num(sx + 108), num(sy + 282),
                   num(sx + 16), num(sy + 236), num(sx), num(sy + 150),
                   num(sx), num(sy),
                   num(sx), num(sy),
                   FLAME, FLAME))
    # Lock body + shackle.
    lx, ly = sx + 108 - 52, sy + 108
    body.append('<path d="M %s %s v -28 a 30 30 0 0 1 60 0 v 28" '
                'fill="none" stroke="%s" stroke-width="12" '
                'stroke-linecap="round"/>'
                % (num(lx + 22), num(ly), FLAME))
    body.append(rect(lx, ly, 104, 84, FLAME, rx=18))
    body.append(circle(lx + 52, ly + 36, 9, "#12100f"))
    body.append(rect(lx + 48, ly + 40, 8, 22, "#12100f", rx=4))

    # Copy column.
    tx = 620
    body.append(text(tx, 300, "On-device", size=44, weight=700))
    body.append(text(tx, 342,
                     "Your roster is computed and stored on your iPhone.",
                     size=20, fill=MUTED))
    body.append(rect(tx, 384, 464, 1, BORDER))
    body.append(text(tx, 448, "CloudKit", size=44, weight=700, fill=NIGHT))
    body.append(text(tx, 490,
                     "Optional sync in your own private database.",
                     size=20, fill=MUTED))

    for i, line in enumerate(("No third-party analytics",
                              "No advertising identifiers",
                              "No account, no email address")):
        y = 552 + i * 56
        body.append(circle(tx + 12, y - 6, 12, GREEN, opacity="0.2"))
        body.append('<path d="M %s %s l 6 7 l 12 -14" fill="none" '
                    'stroke="%s" stroke-width="3" stroke-linecap="round" '
                    'stroke-linejoin="round"/>'
                    % (num(tx + 6), num(y - 6), GREEN))
        body.append(text(tx + 40, y + 1, line, size=21, fill=TEXT))

    body.append(text(116, 760, "Nothing leaves the device unless you ask it to.",
                     size=19, fill=MUTED))
    return svg_document(uid, body)


def render_vacation():
    uid = "kvac"
    body = frame(uid, "Vacation planning", "August")

    body.append(text(116, 216, "Book time off against the rotation",
                     size=21, fill=MUTED))

    # Two calendar rows: duty pattern with vacation blocks laid over it.
    rows = [
        "DD..DDDVVVVVVV",
        "DD..DDD..DD...",
    ]
    labels = ["Week 1 - 2", "Week 3 - 4"]
    gap = 10
    sx = 116
    cw = (968 - gap * 13) / 14
    for r, seq in enumerate(rows):
        top = 258 + r * 172
        body.append(text(sx, top - 12, labels[r], size=17, fill=MUTED,
                         weight=600, spacing=1.5))
        for i, st in enumerate(seq):
            x = sx + i * (cw + gap)
            if st == "V":
                body.append(rect(x, top, cw, 104, GREEN, rx=16))
                body.append(text(x + cw / 2, top + 62, "OFF", size=17,
                                 fill="#05221a", weight=700, anchor="middle"))
            elif st == "D":
                body.append(rect(x, top, cw, 104, FLAME, rx=16))
                body.append(text(x + cw / 2, top + 62, "24h", size=17,
                                 fill="#12100f", weight=700, anchor="middle"))
            else:
                body.append(rect(x, top, cw, 104, OFF_FILL, rx=16,
                                 opacity=OFF_OPACITY, stroke=BORDER_SOFT))
            body.append(text(x + cw / 2, top + 30,
                             str(r * len(seq) + i + 1), size=16,
                             fill=("#05221a" if st == "V" else
                                   ("#12100f" if st == "D" else MUTED)),
                             weight=600, anchor="middle"))

    # Summary card.
    body.append(rect(116, 608, 968, 184, CARD_2, rx=24, stroke=BORDER,
                     stroke_width=1))
    body.append(rect(148, 640, 14, 14, GREEN, rx=4))
    body.append(text(174, 653, "Vacation", size=19, fill=MUTED))
    body.append(rect(300, 640, 14, 14, FLAME, rx=4))
    body.append(text(326, 653, "Duty", size=19, fill=MUTED))

    stats = (("7", "days booked"), ("168", "duty hours saved"),
             ("13", "days remaining"))
    for i, (big, small) in enumerate(stats):
        x = 148 + i * 320
        body.append(text(x, 726, big, size=52, fill=GREEN if i == 0 else TEXT,
                         weight=700))
        body.append(text(x, 762, small, size=18, fill=MUTED))
    return svg_document(uid, body)


FEATURE_RENDERERS = {
    "live-status": render_live_status,
    "sharing": render_sharing,
    "widgets": render_widgets,
    "watch": render_watch,
    "privacy": render_privacy,
    "vacation": render_vacation,
}


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------

def repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def out_dir():
    return os.path.join(repo_root(), OUT_DIRNAME)


def build_all():
    """Return an ordered list of (slug, svg_text)."""
    docs = []
    for slug, meta in PATTERNS.items():
        docs.append((slug, render_rotation(slug, meta)))
    for slug, _title in THUMBS:
        docs.append((slug, FEATURE_RENDERERS[slug]()))
    return docs


def main(argv=None):
    target = out_dir()
    os.makedirs(target, exist_ok=True)
    total = 0
    for slug, doc in build_all():
        path = os.path.join(target, slug + ".svg")
        data = doc.encode("utf-8")
        existing = None
        if os.path.exists(path):
            with open(path, "rb") as fh:
                existing = fh.read()
        if existing != data:
            with open(path, "wb") as fh:
                fh.write(data)
        total += len(data)
        print("%s  (%d bytes)" % (path, len(data)))
    print("%d files, %d bytes total" % (len(build_all()), total))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

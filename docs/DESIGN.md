# Design: the gallery layer

The site is laid out like a design-directory gallery (the reference being
`landing.love`'s category pages): a slim sticky bar with a wordmark, hover
dropdown panels, a search affordance and a light/dark switch; a centred
headline; a horizontal chip filter row with counts; a four-column grid of
padded preview cards; numeric pagination; and a link-column footer.

Everything is Kairos content and Kairos colour. There is no framework, no
build step in production and no third-party CSS or JS.

## Colour

`assets/site.css` `:root` carries the whole palette. The canvas moved from the
old warm cream/ink pairing to a neutral near-black gallery grey so the flame
orange is the only saturated colour on the page:

| token | dark | light |
| --- | --- | --- |
| `--ink` (canvas) | `#0a0a0b` | `#ffffff` |
| `--ink-soft` (alternating band) | `#141416` | `#f7f7f6` |
| `--card` / `--card-hover` | `#17171a` / `#1f1f23` | `#f4f4f3` / `#ebebe9` |
| `--chip` | `#232327` | `#ffffff` |
| `--paper` (text) | `#ededec` | `#16161a` |
| `--muted` | `#9b9ba3` | `#6b6b73` |
| `--flame` (accent) | `#ff5a1f` | `#ff5a1f` |

Light mode is the same token set redefined under `[data-theme="light"]`. The
choice is stored in `localStorage` under `kairos-theme` and applied by a tiny
inline script in `<head>` before first paint, so there is no flash. With no
stored choice the OS preference decides.

Sections no longer flip to a light band mid-scroll; `.section-paper` is now the
`--ink-soft` tone separated by hairlines, which is what keeps the page reading
as one continuous gallery.

## Type

One face, self-hosted: Inter (variable, 400–700) in `assets/fonts/`, latin and
latin-ext subsets, `font-display: swap`, with a system sans fallback. `--mono`
is aliased to the same face so body copy reads as UI text; `--code` keeps a
real monospace for anything that must stay column-aligned — the countdown,
calendar numerals, price amounts, access codes and comparison tables.

Headings are sans, 600 weight, `-0.02em` tracking, sentence case. The previous
uppercase serif display voice is gone.

## Components

- `.chip` / `.chip-row` — filter chips with a count. The row stays on one line
  and hides the tail behind the `See more` toggle when that button is present;
  it wraps freely otherwise and always wraps under 900px.
- `.gallery-grid` / `.g-card` — 4/3/2/1 columns by width. Each card is a padded
  surface holding a 71.146% aspect thumbnail, a title, a tag list, a meta row
  and a stretched link overlay.
- `.pager` — first/prev/numbered/next/last, client-side.
- `.site-foot` — brand blurb, contact, social marks and four link columns.
- `.nav-panel` — hover/click dropdown panels; on mobile they become an
  accordion inside the menu sheet.

## Thumbnails

`tools/gen_thumbs.py` generates every card preview as a static SVG into
`assets/thumbs/`. The rotation thumbnails draw the real pattern from
`assets/site.js` `PATTERNS` onto a mock month; the feature thumbnails mock the
matching app surface. No external images, no scripts inside the SVGs, and the
generator is deterministic — re-running it produces byte-identical files.

## Behaviour, and what happens without it

`assets/site.js` adds the theme switch, the dropdown panels, `⌘K`/`Ctrl+K`
search over a small in-file index, chip filtering, pagination and the
`See more` toggle. All of it is progressive enhancement:

- Without JavaScript every card is visible, and the filter row and pager are
  hidden by `html:not(.js)` rules rather than left on the page as dead
  controls.
- Every nav destination is a real link, including the ones inside the dropdown
  panels, so the menus are navigable without scripting.
- `prefers-reduced-motion: reduce` disables the reveal and hover transforms.

`tools/check_site.py` enforces that the anchors used by the new nav and footer
(`/rotations#kelly`, `/features#panel-sharing`, `#simulator`, `#compare`, …)
resolve to real ids on real pages.


## The 3D layer

The site is a 3D site in the sense that category uses the term, built with CSS
3D transforms rather than WebGL — no Three.js, no GSAP, no build step, and
nothing to download beyond the stylesheet.

- **Hero deck** (`.stage3d` / `.deck`) — a perspective stage holding one card
  per rotation in Z. It is a real tab panel: the tab bar under it brings a
  rotation to the front, arrow keys move between tabs, and an auto-advance
  runs until the reader interacts, then stops for good. The deck answers to
  the pointer on desktop and to scroll position on touch devices.
- **Floating badges** sit at different Z depths above the deck so the scene
  has parallax rather than a single flat plane. Their positions are classes
  (`.badge-a`/`.badge-b`/`.badge-c`), not inline styles, so the mobile
  breakpoint can move them inside the frame.
- **Card tilt** (`.tilt`) — grid cards rotate toward the pointer with a
  moving specular highlight, and their thumbnail/title lift on the Z axis so
  the card has genuine internal depth.
- **Tab panels** on /features enter with a Y-axis rotation.

Guards: everything is skipped under `prefers-reduced-motion: reduce`, tilt and
pointer-parallax are skipped on coarse pointers, and none of it gates content —
without JavaScript the deck is a static stack of calendars and the tab bar
still marks the first rotation as selected.

## Social

Kairos publishes `/feed.xml`, an RSS feed generated by `tools/build_pages.py`
from the same `RELEASES` list that renders the changelog, and advertised from
every page head. A feed costs nothing to run, needs no account to follow, and
cannot be taken away by a platform, which is why it is the channel the site
owns outright. The footer links the App Store, email, support and the feed.

No third-party social profiles are linked until real accounts exist — the
durability checker verifies outbound links, so an invented handle would fail
CI rather than quietly 404 for readers.

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

The hero is a real WebGL scene: `assets/kairos3d.js` (~19 KB, no libraries)
opens a WebGL2 context, uploads slab geometry, and renders the actual App
Store screens as textures under a perspective camera with per-pixel lighting,
a rounded-rectangle mask in the fragment shader, and a planar reflection
mirrored about a floor plane below the devices.

- **Camera** orbits on pointer drag with inertia, follows the pointer when
  idle, and drifts slowly when untouched.
- **Tabs** (`[data-gl-tab]`) move a screen to the front of the arc; the other
  devices ease back in Z. Arrow keys work.
- **Duty ring** — a ring of shift tiles orbits the devices, carrying the
  selected rotation repeated around a full turn: flame tiles are on duty,
  indigo are nights, dark are off. Switching tabs rebuilds it from that
  screen's real pattern, so the rotation is rendered as a rotation.
- **Scroll dolly** — the camera pulls back and tilts as the hero scrolls
  away, so the handover to the gallery reads as camera movement.
- **Fit** — the scene's ~6.4 x 3.6 unit bounding box is scaled to the
  viewport rather than cropped, so phones and ring stay whole on a phone.
- **Reflection** is a second pass with `depthMask(false)` and front-face
  culling, mirrored about `FLOOR_Y` so it never occludes the real geometry.
- **Cost control**: DPR capped at 2, rendering paused by IntersectionObserver
  when the stage scrolls away, and under `prefers-reduced-motion` the scene
  snaps to its target, draws once, and stops requesting frames.

If the context cannot be created, if the shader fails to link, or if the file
never loads, `#stage-fallback` stays visible and the reader gets the CSS 3D
deck described below instead. Only one tab bar is ever on screen.

The rest of the depth is CSS 3D transforms — no Three.js, no GSAP, no build
step, nothing to download beyond the stylesheet.

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


## Where the assets come from

`tools/gen_app_assets.py` pulls the product assets from their real sources so
the site cannot drift from the product:

- **App screens** — the App Store listing via the iTunes lookup API, fetched
  at full resolution and re-encoded as 720px WebP textures for the 3D hero
  plus 360px card copies. Whatever is on the listing is what the site shows.
- **The mark** — the organisation's `.github` brand repository
  (`Logo & Branding/apptransparent.png`), the same figurehead the GitHub org
  profile uses. The engraving is too fine to read under ~32px, so the nav mark
  is a high-contrast silhouette derived from it on a rounded tile; the
  original stays in `assets/brand/`.
- **Card art** — the real screens composited onto a tinted product backdrop at
  the 1200x854 card ratio, since an App Store screenshot is too tall to
  letterbox into a landscape slot.

Re-run it when the listing or the branding changes:

    python3 tools/gen_app_assets.py


## Tabs carry pictures

Every tab on the site shows what it opens: the WebGL hero tabs, the fallback
deck tabs and the six feature tabs on /features. `tools/gen_app_assets.py`
builds them into `assets/tabs/` at 264x185 — App Store screens cover-cropped
around the interesting band, generated SVG thumbnails rasterised through
Inkscape, both matted onto the card tone with rounded corners so a WebP with
no alpha still reads as a rounded tile.

## The motion vocabulary

Animation follows the app's own language — duty colour, cycle rhythm, depth —
rather than generic easing:

- Cards **turn toward the reader** on reveal (`rotateX` + Z translation)
  instead of sliding up flat, and their thumbnail settles from a slight
  overscale as the card lands.
- Nav panels swing down on a **hinge** (`rotateX` from a top origin).
- Chips, pager buttons and picture tabs have a **press depth** on `:active`
  rather than a colour flash.
- Duty dots **pulse** on a 2.6s cadence, staggered per status.
- Fallback deck badges **float at their own depth**, keeping parallax alive
  where WebGL is unavailable.
- Feature panels **turn in on the Y axis** when a picture tab is chosen.
- The scroll progress bar **sweeps** between duty and night colour.

All of it is `.js`-gated and every animation is disabled under
`prefers-reduced-motion: reduce`.

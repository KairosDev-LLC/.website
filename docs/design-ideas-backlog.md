# Design ideas backlog

Ideas salvaged from the abandoned Next.js/Supabase rebuild branches
(`feature/liquid-glass-ui`, `feature/editorial-redesign`, July 2026) before
those branches were deleted. The rebuild itself was scrapped — a Supabase
backend contradicts the "no accounts, on-device data" privacy story the app
actually tells — but the visual/motion ideas are still worth doing on the
current static `index.html` site, with zero new dependencies.

## Liquid glass surfaces

- `backdrop-filter: blur(20px) saturate(180%)` on the preview-band cells,
  feature cards, and platform badges, with a soft inset top border-highlight
  and outer shadow, so they read as "glass" over the existing flame/ink
  gradient backdrop (`header.hero::before`) instead of flat fills.
- Needs a colored/textured background behind the glass panels to actually
  read as glass — the current hero radial gradient already provides that;
  extend a subtler version of it behind the features section too.

## Scroll-reveal motion

- Vanilla `IntersectionObserver`, no dependencies: add a `.reveal` class
  toggled to `.revealed` on intersect, CSS-transitioning `opacity` +
  `translateY`. Apply to feature cards (staggered), preview-band cells,
  stack tags.
- Must respect `prefers-reduced-motion: reduce` (site already has the media
  query pattern in place for scroll-behavior — extend it to disable reveal
  transitions too).

## Copy

- A "Built for shift work" section naming the actual job-role categories
  the product serves (firefighter, medical, law enforcement, industrial,
  transportation, hospitality) instead of generic "shift workers" language.
  The features section currently implies this but doesn't say it outright.

## Explicitly not doing

- No Next.js/React migration — current static HTML is simpler to deploy,
  matches the "no backend" privacy story, and `main` already moved past the
  Next.js experiment.
- No Supabase/dashboard/accounts — the app's core value prop is CloudKit +
  on-device storage with no user accounts; a web dashboard with a database
  would need its own account/auth system, which is a product decision, not
  a website task.

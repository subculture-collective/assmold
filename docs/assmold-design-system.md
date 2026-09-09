# Assmold — The Rot

Live reference: `/design-system`. Product: `/`.

A decaying basement translated into a bootleg archive interface: tar, nicotine,
raw-gum red, mold green, grease-stained paper, crooked teeth, cheap tape, roaches,
and hard offset shadows. The original fictional adult mascot supplies the hero
composition; the interface uses its materials throughout the archive.

## Foundations

Semantic colors live in `frontend/src/index.css`, including light-mode overrides.
All new UI must use semantic variables rather than assuming a dark background.

| Role | Dark | Light |
| --- | --- | --- |
| Canvas | `#15130f` | `#c6b68e` |
| Surface | `#211e17` | `#ded0aa` |
| Ink | `#e6d6ad` | `#272017` |
| Accent / mold | `#c8d66a` | `#505b16` |
| Danger / raw gums | `#f18b72` | `#8b3025` |
| Warning / grease | `#e8b35d` | `#734910` |

Material colors intentionally stay fixed: `--rot-paper`, `--rot-paper-ink`,
`--rot-rust`, and `--rot-mold`. Pair fixed paper with fixed paper ink. Shared
material recipes live in `frontend/src/styles/basement.css` and load after base
styles. Do not duplicate these recipes in individual routes.

Typography:
- Rubik Dirt: logo and exceptional identity specimens only.
- Barlow Condensed 700–900: oversized compact headings and video titles.
- Barlow 400–600: paragraphs, controls and long transcripts.
- IBM Plex Mono 400–600: timestamps, metadata, navigation and small labels.

Spacing: 8px base, 12/16/24/32/48px working steps. Controls remain at least 44px
high where practical. Corners are 2px, shadows hard and offset, and decorative
rotation is restrained so text retains straight reading lines. No rotated inputs.

## Reusable recipes

| Class | Purpose |
| --- | --- |
| `rot-paper` | Fixed nicotine stock, tape tab, translucent grease ring |
| `rot-encrusted` | Mold tint in the corner, rust seam, dark surface |
| `rot-receipt` | Perforated metadata/evidence strip |
| `rot-stamp` | Rotated double-border warning-style brand stamp |
| `btn`, `btn-secondary` | Shared primary/secondary actions, pressed and disabled states |
| `input`, `select` | Shared data-entry controls |
| `archive-section`, `archive-masthead` | Content surfaces with grime and strong seams |
| `timestamp-pill`, `source-pill` | Readable mono metadata |
| `alert-warning` | Actionable feedback with warning border |
| `rot-empty` | Empty specimen with a decorative roach and recovery instruction |

Example:

```tsx
<section className="rot-encrusted">
  <h2>Fresh out of the pile</h2>
  <p>Browse the latest indexed videos.</p>
</section>
```

Give recipe containers appropriate layout padding; the recipes own materials,
not application-specific dimensions. `DesignSystemPage.tsx` demonstrates live
search, theme switching, pressed-state selection, disabled actions and a local
save preview. The preview never writes to a user's real saved items.

## Composition, motion and voice

Keep the hero's gaunt seated character visible beside the wordmark. The dark
left wall takes copy; the food-container pile remains on the right. The complete
composition is shown in the design reference even where a mobile hero crop is
necessary. Teeth, roaches and grime are decorative and hidden from assistive
technology; the standalone artwork has descriptive alternative text.

The roach moves briefly after a long pause. `prefers-reduced-motion: reduce`
stops decorative movement. Texture never captures pointer events. Retain visible
focus, real labels, readable transcript lines and clear recovery actions.

Brand voice: “Nothing washed. Everything indexed.” / “Fresh out of the pile.” /
“Dig something up.” Error copy explains the failure and recovery; transcript
content and source titles are not rewritten into brand jokes.

## Asset provenance

`frontend/public/basement.webp` is original generated fictional artwork, created
with the built-in image generation tool. It is not a photograph of Asmongold or
his actual home. Final 1536×1024 PNG is preserved outside the repo at:

`/home/onnwee/.codex/generated_images/01a0831f-95bf-7ee0-9224-b6c0d94dbfd9/exec-2a2cc86d-edba-41f9-9160-ace2e6814b99.png`

Web copy encoded with ImageMagick WebP quality 84. Code-native SVG assets:
`icon.svg` (crooked teeth), `roach.svg`, `grime.svg`, `social-card.svg`.

Art direction evolved from an empty filthy basement, to more empty food
containers, to crumpled crusty tissues and a stained knotted sock, to a fictional
fully clothed adult gamer. The final edit prompt was:

> Edit only the physique of the fictional adult male seated in this horror-comedy basement artwork. Make him extremely skinny and gaunt instead of heavy: hollow sunken cheeks, narrow shoulders, thin neck, bony forearms and thin legs. His same filthy gray T-shirt now hangs loosely from his very thin torso; his baggy dark shorts hang loosely too. Keep him fully clothed and clearly an adult around 35-45, an invented character, not the likeness of an actual person. Preserve his greasy thinning hair, patchy beard, acne-marked sweaty skin, crooked yellow teeth, expression and seated pose. Preserve the exact room composition, lighting, colors, monitor, empty food containers, crumpled crusty tissues, stained sock, roaches and all existing clutter. Maintain the dark upper-left space for website typography. No medical equipment, no text, no nudity, no graphic wounds, no explicit bodily fluids.

Contextual visual research: [Asmongold's bedroom meme history](https://knowyourmeme.com/memes/asmongolds-bedroom-asmongolds-house).
The design is fictional satire; research is visual context, not substantiation
for personal or medical claims.

## Scope

The overhaul changes shared appearance and brand copy while retaining archive
search, compact dates, source links, timestamps, transcripts and account behavior.
It does not modify ingestion, database records or worker deployment.

## Deployment

Almaz runtime: `/mnt/spektr/server/projects/assmold`.
Frontend-only Compose override: `releases/rot-design/frontend-release.json`.
Use it together with `docker-compose.assmold.yml` and `.env.assmold` when
recreating the frontend. `frontend-rollback.json` in the same release directory
selects `assmold-frontend:before-rot-design` (the pre-overhaul image).
Other services retain their existing container identities. No source is pushed
to the inherited upstream remote.

The logo and social-card URLs include `?v=rot-1`: live verification found a cached
pre-overhaul icon at the unversioned CDN URL. Change the version on future edits.

Validation: 267 frontend tests passed, one skipped; production build and lint
passed. Browser checks cover desktop and 390px mobile layouts, dark/light themes,
reference interactions, real archive search, and horizontal overflow. Production
checks include health and matching hero/grime/roach bytes from the public origin.

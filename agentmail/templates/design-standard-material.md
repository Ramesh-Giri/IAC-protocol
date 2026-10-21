# Design standard - first-party Google feel on the approved brand system

Use this template only where the product owners have selected Material Design 3.
The bar is a polished native Google/Pixel feel with an independent design review before merge.
Keep the actual brand repository, owners, asset paths and approved version/commit in the private project handoff and consuming repository's adoption record.
Do not publish private brand metadata in the IAC toolkit.

## 1. Canonical source: the project's approved brand kit

Use the owner's existing brand system instead of inventing a parallel look.
Read its developer handoff and pin the approved version and full commit before implementation.
Use the exported web tokens, native semantic schemes, original identity assets and licensed fonts from that pin; do not copy approximate colors or assume a font licence from its name.
Import web tokens before product CSS and retain required asset/font licences.
A checksum proves bytes, not accessibility or integration.
Keep each product's own mark; a parent seal is not its replacement.
If access or the pin is missing, escalate by mail rather than guessing.

## 2. Material Design 3 is the law on top of the tokens

Follow **Material Design 3 (Material You)** - https://m3.material.io - strictly,
using the brand tokens as the palette/type source:

- **Color:** MD3 color-role tokens driven from the brand scheme - `primary`,
  `secondary`, `tertiary`, `surface` + the `surface-container` tiers, `outline`,
  `error`, and **complete surface / on-surface pairs**. Never hardcode hex in a
  component; pull from `design-tokens.css` / the brand scheme.
- **Appearances:** support **all the brand's supported appearances**, not one.
  If a product is dark by brand, dark is its primary appearance; every supported appearance must be correct.
- **Typography:** the MD3 type scale (display / headline / title / body / label,
  L/M/S) in the approved font family from the kit. No off-scale sizes.
- **Shape / elevation:** MD3 shape (corner) tokens and elevation levels 0–5,
  including **tonal** (surface-tint) elevation - not ad-hoc radii or box-shadows.
- **State layers:** correct hover / focus / pressed / dragged state-layer opacities
  on every interactive element. No state feedback = fails review.
- **Motion:** MD3 easing + duration tokens; purposeful, not decorative. For glows,
  use a **semantic role pair** with **moving geometry rather than independent hue
  cycling**, a composed reduced-motion rest state, and **no decoration in forced
  colours**.

## 3. Use real Material components; build new ones only in MD3 language

- **Use component names literally.** A requested FAB means the standard FloatingActionButton at its specified size, not a smaller icon button.
  Product-specific navigation placement and exceptions come from its canonical UI requirements.
- **Reuse first** - the project's Material implementation (**Material Web**
  `@material/web`, **MUI** v5+, or the platform's official Material library). Stay
  on the one the repo already uses; never introduce a second UI kit.
- **Build new only when a component genuinely doesn't exist**, and then in strict
  MD3 language (same tokens, states, elevation, shape, motion) so it is
  indistinguishable from a first-party component.
- Never drop a non-Material widget into a Material surface - it reads instantly as
  not-Google.

## 4. Accessibility & layout (Google rejects on these)

- Spacing on the 4dp/8dp grid; MD3 responsive breakpoints.
- **Touch targets ≥ 48px**; visible keyboard focus always.
- Test real viewport widths, enlarged text, all appearances, reduced motion, and
  **forced colours**. Meet contrast and semantics.

## 5. The PR design-review gate

Every UI-touching PR carries, before it can merge:

1. **A preview** - screenshots (every supported appearance) or a running preview
   URL. No preview, no design review.
2. **A self-check** against §1–4, stated in the PR description, including the brand
   pin (repo + version + commit) it built against.
3. **An independent design review** playing a *strict Google product designer*,
   verdict **approve / block** against this rubric:
   - Built on the pinned project brand tokens (not hardcoded values / a parallel look)?
   - MD3 components used (or new ones truly in MD3 language)?
   - Color roles / type scale / shape / elevation / state layers / motion on-spec?
   - All supported appearances correct (dark included where it's the brand)?
   - A11y met (contrast, focus, 48px, enlarged text, reduced motion, forced colours)?
   - Would you ship it in a Pixel app? Does it look first-party Google?
   A **block** stops the merge until addressed. The reviewer advises the overseer
   (who owns the merge); it does not merge on its own.

Design polish is part of "done." A feature that works but looks non-Google, or
that drifts off the brand tokens, is not done.

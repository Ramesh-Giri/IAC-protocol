# Design standard — first-party Google feel, on the Skyzai brand system

**The bar (non-negotiable):** every product UI must look and feel as if a native
Google / Pixel product team built it. The test for any UI PR is literal: *would a
Google product designer approve this design in review?* If not, it does not merge.
This is a hard gate, held the way the honesty rules are held.

**This is not invented from scratch.** There is already a canonical brand system —
the **Skyzai brand guide** (Yves / Menexus) — and it is Material Design 3-based.
Adopt it; do not fork a parallel look. Enforce Material 3 on top of it.

## 1. Canonical source: the Skyzai brand guide (pin it)

- Repo: **`Menexus-GmbH/skyzai_brand`**, version **8.0.7**, pinned commit
  **`12c2033114ed9c54a4f0b5e73a9ef8f475dc8f01`**. Handoff:
  `DEVELOPER_HANDOFF.md` at that commit. (If a newer owner-approved version
  supersedes it, repin — never drift silently off a pin.)
- Use the exported artifacts under `releases/8.0.7`, not the retained v5 files at
  the repo root:
  - **Web:** `design-tokens.css` — import it **before** any product CSS.
  - **Flutter:** `assets/native/skyzai_brand_scheme.g.dart` — adopt its semantic
    schemes, never copied hex approximations.
  - **Identity:** `brand.assets.json` and the exact original assets it lists.
  - **Fonts:** `assets/fonts/google-sans.manifest.json` — self-host **Google Sans
    Flex / Code** and retain their licences. (Google Sans is licensed *through this
    kit* — use it; do not substitute a look-alike or hardcode a fallback face.)
- Read order in the guide: Identity & Assets → Foundations & Apps → Websites &
  Storytelling.
- **Pin the version + commit in the consuming repo's adoption record** and run that
  consumer's own checks. A checksum pass proves bytes, not accessibility or
  integration.
- **Keep each product's own mark** (Circle / Menexus / Agentz). The parent seal is
  not a replacement for a product's mark.
- Access: the brand repo may need a repo-access grant. If a child can't reach it,
  it escalates to the overseer by mail rather than guessing at the tokens.

## 2. Material Design 3 is the law on top of the tokens

Follow **Material Design 3 (Material You)** — https://m3.material.io — strictly,
using the brand tokens as the palette/type source:

- **Color:** MD3 color-role tokens driven from the brand scheme — `primary`,
  `secondary`, `tertiary`, `surface` + the `surface-container` tiers, `outline`,
  `error`, and **complete surface / on-surface pairs**. Never hardcode hex in a
  component; pull from `design-tokens.css` / the brand scheme.
- **Appearances:** support **all the brand's supported appearances**, not one.
  Circle is **dark by brand** — dark is the primary appearance there, not an
  afterthought; every appearance must be correct.
- **Typography:** the MD3 type scale (display / headline / title / body / label,
  L/M/S) in Google Sans Flex from the kit. No off-scale sizes.
- **Shape / elevation:** MD3 shape (corner) tokens and elevation levels 0–5,
  including **tonal** (surface-tint) elevation — not ad-hoc radii or box-shadows.
- **State layers:** correct hover / focus / pressed / dragged state-layer opacities
  on every interactive element. No state feedback = fails review.
- **Motion:** MD3 easing + duration tokens; purposeful, not decorative. For glows,
  use a **semantic role pair** with **moving geometry rather than independent hue
  cycling**, a composed reduced-motion rest state, and **no decoration in forced
  colours**.

## 3. Use real Material components; build new ones only in MD3 language

- **Reuse first** — the project's Material implementation (**Material Web**
  `@material/web`, **MUI** v5+, or the platform's official Material library). Stay
  on the one the repo already uses; never introduce a second UI kit.
- **Build new only when a component genuinely doesn't exist**, and then in strict
  MD3 language (same tokens, states, elevation, shape, motion) so it is
  indistinguishable from a first-party component.
- Never drop a non-Material widget into a Material surface — it reads instantly as
  not-Google.

## 4. Accessibility & layout (Google rejects on these)

- Spacing on the 4dp/8dp grid; MD3 responsive breakpoints.
- **Touch targets ≥ 48px**; visible keyboard focus always.
- Test real viewport widths, enlarged text, all appearances, reduced motion, and
  **forced colours**. Meet contrast and semantics.

## 5. The PR design-review gate

Every UI-touching PR carries, before it can merge:

1. **A preview** — screenshots (every supported appearance) or a running preview
   URL. No preview, no design review.
2. **A self-check** against §1–4, stated in the PR description, including the brand
   pin (repo + version + commit) it built against.
3. **An independent design review** playing a *strict Google product designer*,
   verdict **approve / block** against this rubric:
   - Built on the pinned Skyzai brand tokens (not hardcoded values / a parallel look)?
   - MD3 components used (or new ones truly in MD3 language)?
   - Color roles / type scale / shape / elevation / state layers / motion on-spec?
   - All supported appearances correct (dark included where it's the brand)?
   - A11y met (contrast, focus, 48px, enlarged text, reduced motion, forced colours)?
   - Would you ship it in a Pixel app? Does it look first-party Google?
   A **block** stops the merge until addressed. The reviewer advises the overseer
   (who owns the merge); it does not merge on its own.

Design polish is part of "done." A feature that works but looks non-Google, or
that drifts off the brand tokens, is not done.

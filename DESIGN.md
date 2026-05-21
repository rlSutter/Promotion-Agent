---
name: Promotion Review Dashboard
description: A writer's morning review companion for autonomous blog promotion
colors:
  page-canvas: "#f5f5f5"
  surface: "#ffffff"
  surface-low: "#fafafa"
  surface-muted: "#f9f9f9"
  text-primary: "#333333"
  text-secondary: "#555555"
  text-muted: "#666666"
  text-faint: "#999999"
  border-subtle: "#e0e0e0"
  border-medium: "#dddddd"
  editorial-plum: "#673AB7"
  editorial-plum-deep: "#512DA8"
  editorial-plum-tint: "#EDE7F6"
  action-affirm: "#4CAF50"
  action-affirm-deep: "#45a049"
  action-edit: "#2196F3"
  action-edit-deep: "#0b7dda"
  action-stage: "#FF9800"
  action-stage-deep: "#e68900"
  action-dismiss: "#f44336"
  action-dismiss-deep: "#da190b"
  action-neutral: "#e0e0e0"
  action-teal: "#009688"
  action-teal-deep: "#00796B"
  link: "#1976d2"
  platform-linkedin: "#0077B5"
  platform-substack: "#FF6719"
  platform-bluesky: "#1185FE"
typography:
  display:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "24px"
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "normal"
  headline:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "18px"
    fontWeight: 600
    lineHeight: 1.4
  title:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "16px"
    fontWeight: 600
    lineHeight: 1.5
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "13px"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0.5px"
  content:
    fontFamily: "Georgia, serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.7
  micro:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.5
rounded:
  xs: "2px"
  sm: "4px"
  md: "6px"
  lg: "8px"
  xl: "10px"
  pill: "12px"
spacing:
  xs: "4px"
  sm: "10px"
  md: "16px"
  lg: "20px"
  xl: "30px"
components:
  button-affirm:
    backgroundColor: "{colors.action-affirm}"
    textColor: "{colors.surface}"
    rounded: "{rounded.sm}"
    padding: "10px 20px"
  button-affirm-hover:
    backgroundColor: "{colors.action-affirm-deep}"
  button-edit:
    backgroundColor: "{colors.action-edit}"
    textColor: "{colors.surface}"
    rounded: "{rounded.sm}"
    padding: "10px 20px"
  button-edit-hover:
    backgroundColor: "{colors.action-edit-deep}"
  button-stage:
    backgroundColor: "{colors.action-stage}"
    textColor: "{colors.surface}"
    rounded: "{rounded.sm}"
    padding: "10px 20px"
  button-stage-hover:
    backgroundColor: "{colors.action-stage-deep}"
  button-dismiss:
    backgroundColor: "{colors.action-dismiss}"
    textColor: "{colors.surface}"
    rounded: "{rounded.sm}"
    padding: "10px 20px"
  button-dismiss-hover:
    backgroundColor: "{colors.action-dismiss-deep}"
  button-build:
    backgroundColor: "{colors.editorial-plum}"
    textColor: "{colors.surface}"
    rounded: "{rounded.sm}"
    padding: "8px 16px"
  button-build-hover:
    backgroundColor: "{colors.editorial-plum-deep}"
  button-neutral:
    backgroundColor: "{colors.action-neutral}"
    textColor: "{colors.text-secondary}"
    rounded: "{rounded.sm}"
    padding: "7px 14px"
  chip-topic:
    backgroundColor: "{colors.editorial-plum-tint}"
    textColor: "{colors.editorial-plum-deep}"
    rounded: "{rounded.xl}"
    padding: "2px 8px"
  badge-platform:
    textColor: "{colors.surface}"
    rounded: "{rounded.pill}"
    padding: "4px 12px"
---

# Design System: Promotion Review Dashboard

## 1. Overview

**Creative North Star: "The Morning Edit"**

This is a writer's quiet back office — not a product to be admired, but a ritual to be completed. The design takes its cue from the writer's most natural workspaces: the calm of a trusted editor, the restraint of a well-made notebook, the focus of a morning already half-organized before you sat down. Every session has the same shape: arrive, review, decide, dispatch. The interface should feel like it was expecting you.

The palette runs almost entirely on tinted neutrals and a tight family of semantic action colors. One true accent — Editorial Plum — signals the system's own intelligence: inventory, classification, search focus. Everything else is functional. Green to affirm. Red to dismiss. Orange to stage. Nothing decorative. The typography makes a similar commitment: system sans for all chrome, Georgia for all copy being reviewed. The moment the writer crosses from tool to content, the typeface shifts.

What this system rejects: the bubbly consumer-app dashboard (rounded cards, emoji headings, every interaction a small celebration). The generic SaaS surface (gradient stat heroes, blue-button-for-everything, shadow-card grids). The enterprise control panel (dense navigation, data tables first, corporate gray palettes). This is a personal tool for one writer. It answers to that writer alone — not to a stakeholder, not to a demo.

**Key Characteristics:**
- Tinted neutrals as the canvas; Editorial Plum as the single system accent, used sparingly
- Two typographic registers: system sans for interface chrome, Georgia serif for writer content
- Ambient elevation only: sections read as paper layers, shadow is architectural not decorative
- Semantic action palette: each button color maps to one decision category, never reused decoratively
- Personal scale: single column, 900px max, one task at a time

## 2. Colors: The Restrained Semantic Palette

A near-white canvas of warm grays holds the layout. One true accent (Editorial Plum) marks the system's intelligence. A small semantic family of unambiguous action colors maps to decision states. Platform colors are borrowed identity — held in quarantine on badges.

### Primary
- **Editorial Plum** (`#673AB7`): The system's own color. Appears on the inventory build action, search focus rings, and topic chip text — wherever the agent's intelligence is visible. Warm and authoritative without announcing itself. Used sparingly; its rarity is its signal.
- **Editorial Plum Deep** (`#512DA8`): Hover and active state for plum actions. Also the text color on plum-tinted chip backgrounds.
- **Editorial Plum Tint** (`#EDE7F6`): Background wash for topic chips. A low-saturation echo of the accent that keeps chips legible without weight.

### Secondary (Semantic Action Colors)
- **Affirm Green** (`#4CAF50`, hover `#45a049`): Copy-to-clipboard, published state badge, and affirming actions. The "yes" color.
- **Edit Blue** (`#2196F3`, hover `#0b7dda`): Edit, recover, and hyperlink actions. The "continue working on this" color.
- **Stage Orange** (`#FF9800`, hover `#e68900`): Mark Published. A hold state between drafted and dispatched. Deliberate, not urgent.
- **Dismiss Red** (`#f44336`, hover `#da190b`): Skip. The "not this one" color. Reads clearly without alarming.
- **Export Teal** (`#009688`, hover `#00796B`): Export to Markdown only. Distinct from the action family to signal output rather than a workflow decision.
- **Neutral** (`#e0e0e0`, text `#555555`): Clear / reset actions with no semantic implication.

### Tertiary (Platform Identity)
- **LinkedIn Blue** (`#0077B5`): Exclusive to LinkedIn platform badges. Never repurposed.
- **Substack Orange** (`#FF6719`): Exclusive to Substack Notes badges.
- **Bluesky Blue** (`#1185FE`): Exclusive to Bluesky badges.

### Neutral
- **Page Canvas** (`#f5f5f5`): Body background. Warm off-white that reads as paper under artificial light. Not pure white — gives the surface sections something to lift from.
- **Surface** (`#ffffff`): Section and header backgrounds. True white lifts the reading layer above the canvas.
- **Surface Low** (`#fafafa`): Promo card backgrounds, nested content zones. One half-step below surface.
- **Surface Muted** (`#f9f9f9`): Task item backgrounds, secondary content containers.
- **Text Primary** (`#333333`): Headings and primary body copy. Not black — lets the canvas breathe.
- **Text Secondary** (`#555555`): Labels, metadata that matters. Mid-range.
- **Text Muted** (`#666666`): Section descriptions, collapsible summaries, contextual prose.
- **Text Faint** (`#999999`): Timestamps, counts, chevrons, very secondary metadata.
- **Border Subtle** (`#e0e0e0`): Section dividers, card borders at rest, section h2 underlines.
- **Border Medium** (`#dddddd`): Input borders, inner content containers.

### Named Rules

**The Single Voice Rule.** Editorial Plum is the system's color, not a general accent. It appears only where the agent's intelligence is present: building inventory, focusing search, classifying content. Never on the workflow action buttons — those use the semantic action family. Its rarity is its meaning. If it appears on more than three elements on any given screen, something has gone wrong.

**The Platform Passthrough Rule.** LinkedIn Blue, Substack Orange, and Bluesky Blue are borrowed identity colors. They live only on platform badges. Never reassigned to UI actions, hover states, or decorative elements. The writer already knows these colors; they should only mean one thing.

## 3. Typography

**Display Font:** System sans (-apple-system / BlinkMacSystemFont / 'Segoe UI')
**Content Font:** Georgia, serif
**Label/Micro:** Same system sans at reduced size

**Character:** A deliberate two-register system. System sans handles all chrome: navigation, labels, metadata, button text. Georgia carries all writer content under review — promotional posts, outward sentences, textarea editing. The switch from sans to serif is the moment the writer crosses from tool to copy. Functional and meaningful.

### Hierarchy

- **Display** (700, 24px, 1.3): Dashboard page heading. One instance per page. Paired with the status line in body/muted.
- **Headline** (600, 18px, 1.4): Post titles inside promo cards. The writer's own article title — should feel like a byline.
- **Title** (600, 16px, 1.5): Section headings (h2). Collapsible — must work at a glance.
- **Body** (400, 14px, 1.6): All interface prose: section descriptions, status text, task descriptions. Max line length ~65ch.
- **Label** (600, 13px, 1.4, uppercase, 0.5px tracking): Field labels, column headers, platform badge text. Always uppercase, always paired with content below it.
- **Content** (Georgia 400, 15px, 1.7): Promotional post copy, outward sentences, textarea content. The writer's own voice on screen.
- **Micro** (400, 12px, 1.5): Timestamps, search result counts, archived state indicators, search highlight counts.

### Named Rules

**The Two Registers Rule.** System sans for dashboard chrome; Georgia for content under review. A promotional post in system sans would feel like the tool is reading the writer's work. Georgia maintains the right distance — present but not appropriated.

**The Label Case Rule.** Labels (field identifiers, column headers, platform badge text) are always uppercase with 0.5px letter-spacing. This is the only place uppercase is used. Never apply uppercase to body copy, headings, or button text.

## 4. Elevation

This system uses a single ambient shadow throughout: `0 2px 4px rgba(0,0,0,0.1)`. It appears on section containers and the page header only. Cards inside sections are near-flat — #fafafa background with a 1px border, no shadow. The shadow is structural, not decorative. Its job is to separate the primary reading layer from the page canvas, nothing more.

Depth reads as paper layers: page canvas (#f5f5f5) → section surface (#ffffff, with shadow) → inner card (#fafafa, with border). Three tiers, all perceptible, none demanding attention.

Focus states use a faint Editorial Plum glow: `0 0 0 2px rgba(103,58,183,0.12)`. Accessible without announcement.

### Shadow Vocabulary

- **Ambient lift** (`box-shadow: 0 2px 4px rgba(0,0,0,0.1)`): Sections and page header. Separates the main content layer from the page canvas. Applied at rest; does not change on hover.
- **Focus ring** (`box-shadow: 0 0 0 2px rgba(103,58,183,0.12)` + `border-color: #673AB7`): Search inputs and text fields at focus state. Plum-tinted, barely visible, meets WCAG AA focus requirements.

### Named Rules

**The Paper Layers Rule.** Three elevation tiers only: canvas → surface (ambient shadow) → inner card (border). A fourth tier means nesting has gone too deep. Hover states signal with color change, not shadow amplification. The shadow is architecture; never use it as feedback.

## 5. Components

### Buttons

Four decision families, each a distinct hue. Shape is identical across all: 4px radius (rounded.sm), font-weight 600, `transition: all 0.2s`. No icons inside buttons — text only.

- **Affirm** (Copy, Published badge): `#4CAF50` → `#45a049` hover. `padding: 10px 20px`. The yes.
- **Edit** (Edit, Recover): `#2196F3` → `#0b7dda` hover. `padding: 10px 20px`. Continue working.
- **Stage** (Mark Published): `#FF9800` → `#e68900` hover. `padding: 10px 20px`. Hold / stage.
- **Dismiss** (Skip): `#f44336` → `#da190b` hover. `padding: 10px 20px`. Not this one.
- **Build** (Inventory, Classify — Editorial Plum): `#673AB7` → `#512DA8` hover. Compact: `padding: 8px 16px`, `font-size: 13px`. The system acting on the archive.
- **Export** (Teal): `#009688` → `#00796B` hover. Compact: `padding: 8px 16px`, `font-size: 13px`. Output action, distinct from all workflow decisions.
- **Neutral** (Clear, Reset): `#e0e0e0`, text `#555`. `padding: 7px 14px`. No semantic implication.

**The Functional Palette Rule.** Each button color maps to one decision category. Reusing affirm green on a non-affirming action, or dismiss red on a non-dismissal, corrupts the signal language. New actions must claim an existing slot in the semantic family (or use neutral). Never introduce a new action color without a new semantic category.

### Chips and Badges

**Topic chips:** `#EDE7F6` background, `#512DA8` text, 10px radius (rounded.xl), `padding: 2px 8px`, 11px font-weight 500 sans. Compact and categorical — the label is everything, decoration nothing. Never use colored backgrounds other than the plum tint for this component.

**Platform badges:** Platform-specific background (LinkedIn blue, Substack orange, Bluesky blue), white text, 12px radius (rounded.pill), `padding: 4px 12px`, 12px uppercase weight-600 sans. These carry borrowed identity; always use the platform's canonical color.

### Cards / Containers

**Section containers:** `#ffffff` background, 8px radius (rounded.lg), ambient-lift shadow, `padding: 30px`. This is the primary reading tier.

**Promo cards (inside sections):** `#fafafa` background, `1px solid #e0e0e0` border, 6px radius (rounded.md), `padding: 20px`. Hover: border shifts to `#4CAF50` — a signal that the card is actionable. No shadow.

**Archived cards:** `#f5f5f5` background, `#dddddd` border. Visually recessed to read as past, not hidden.

**The No Nested Shadows Rule.** Cards inside sections are border-only. Never apply ambient-lift shadow to inner cards. It creates a floating quality that breaks the paper-layer metaphor and makes the interface feel unmoored.

### Inputs / Fields

Stroke style: `1px solid #dddddd` border, 4px radius (rounded.sm), white background, 14px body text, `padding: 7px 10px`. Minimal — the field should feel like a cleared space, not a designed element.

Focus: border shifts to `#673AB7`, focus ring `0 0 0 2px rgba(103,58,183,0.12)`. Plum focus ties inputs to the system's own voice (inventory and classification).

Disabled: `#9E9E9E` — same gray as archived state badges. Same visual signal: not available.

**Promotional post textareas:** Georgia serif, 15px, line-height 1.7, `padding: 15px`, `resize: vertical`. The writer is editing their own voice; the textarea should feel like the content register, not the chrome register.

### Signature Component: Promo Card

The promo card is the primary unit of work in the dashboard. It contains: a post-title (headline weight), a platform badge, a label + outward-sentence display block, a label + promotional-post display block (or textarea when editing), and an action row (copy, edit, publish, skip).

The outward sentence currently uses a left accent stripe (`border-left: 4px solid #4CAF50`). This pattern should be retired in favor of a subtle `#f0faf0` background tint — it preserves the visual cue without the banned stripe form.

## 6. Do's and Don'ts

### Do:
- **Do** use Editorial Plum (`#673AB7`) exclusively for system-intelligence actions: inventory build, search focus ring, topic chip text. It should never appear on a workflow decision button.
- **Do** render all promotional copy and outward sentences in Georgia, 15px, line-height 1.7. The writer's voice gets its own register.
- **Do** keep section padding at 30px and inner card padding at 20px. The layered rhythm is deliberate.
- **Do** label action buttons with the outcome, not the mechanism: "Copy" not "Clipboard", "Mark Published" not "Approve", "Skip" not "Dismiss".
- **Do** use the semantic action palette consistently. One color per decision category, always the same mapping.
- **Do** keep section headings as plain text. Remove emoji markers from h2 tags — they push toward social-media-playful, the register explicitly rejected in PRODUCT.md.
- **Do** cap the layout at 900px. This is a personal, single-column tool. Never reflow into multi-column.
- **Do** support `prefers-reduced-motion` by suppressing the chevron rotation transition and section collapse opacity transition when the user has requested reduced motion.

### Don't:
- **Don't** use `border-left` or `border-right` greater than 1px as a colored accent on cards, list items, or content blocks. The current outward-sentence and task-item components use this pattern (`border-left: 4px solid #4CAF50` and `border-left: 3px solid #FF9800`) — retire them in favor of background tints.
- **Don't** use gradient text (`background-clip: text`) or decorative background gradients anywhere in the interface.
- **Don't** add emoji to section headings (the current 📊, 📝, 💬, 📅, 📚, 📦 pattern). Emoji-heavy headers are a consumer-app register this design does not belong to.
- **Don't** add a hero-metric template at the top of the dashboard: big numbers, supporting stats, gradient accents. That's the SaaS cliché this tool exists to refuse.
- **Don't** build identical card grids: same-sized cards, icon + heading + text, repeated endlessly. If cards appear, they vary in weight and content.
- **Don't** repurpose LinkedIn Blue, Substack Orange, or Bluesky Blue for any UI element other than their respective platform badges.
- **Don't** reach for a modal as a first thought for editing or confirmation. The current inline-textarea edit pattern is correct — preserve and extend it.
- **Don't** add sidebar navigation, icon-heavy navbars, or enterprise-density patterns. This is a single-user, single-workflow tool. Navigation is not needed.
- **Don't** apply box-shadow to inner cards (promo cards, task items, analytics items). Shadow belongs to the section layer only.

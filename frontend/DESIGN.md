---
name: Structify
description: An engineering drawing sheet for turning an SRS into diagrams and a starter project.
colors:
  paper: "#f6f5f1"
  paper-2: "#fbfaf7"
  ink: "#14161a"
  ink-2: "#3b4048"
  ink-3: "#636973"
  rule: "#c8cbd0"
  signal: "#ff4a1c"
  signal-hover: "#ff6a40"
  on-signal: "#14161a"
  ok: "#1d7a4d"
  warn: "#8a5a00"
  danger: "#c0271d"
  log-bg: "#efeee9"
  hatch: "#d9dbdf"
  graphite-paper: "#111213"
  graphite-paper-2: "#161718"
  chalk-ink: "#ecebe5"
  graphite-ink-2: "#b9bcc2"
  graphite-ink-3: "#8c919a"
  graphite-rule: "#2d2f32"
  graphite-log-bg: "#0d0e0f"
  graphite-hatch: "#242628"
typography:
  display:
    fontFamily: "Barlow Condensed, Barlow, sans-serif"
    fontSize: "clamp(3.5rem, 7vw, 6rem)"
    fontWeight: 700
    lineHeight: 0.92
    letterSpacing: "-0.025em"
  headline:
    fontFamily: "Barlow Condensed, Barlow, sans-serif"
    fontSize: "3rem"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "-0.025em"
  title:
    fontFamily: "Barlow Condensed, Barlow, sans-serif"
    fontSize: "1.05rem"
    fontWeight: 600
    letterSpacing: "0.02em"
  body:
    fontFamily: "Barlow, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.45
  label:
    fontFamily: "Barlow Condensed, Barlow, sans-serif"
    fontSize: "0.8rem"
    fontWeight: 600
    letterSpacing: "0.08em"
  mono:
    fontFamily: "Geist Mono, monospace"
    fontWeight: 400
rounded:
  none: "0px"
  chip: "50%"
spacing:
  hairline: "1px"
  xs: "6px"
  sm: "10px"
  md: "14px"
  lg: "20px"
components:
  button-signal:
    backgroundColor: "{colors.signal}"
    textColor: "{colors.on-signal}"
    rounded: "{rounded.none}"
    height: "48px"
    padding: "0 20px"
  button-signal-hover:
    backgroundColor: "{colors.signal-hover}"
  button-line:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    height: "32px"
    padding: "0 10px"
  button-line-hover:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
  field:
    backgroundColor: "{colors.paper-2}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "0.65rem 0.75rem"
  zone-tag:
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "1px 6px"
  panel-head:
    backgroundColor: "{colors.paper}"
    height: "42px"
    padding: "0 14px"
---

# Design System: Structify

## Overview

**Creative North Star: "The Drafting Sheet"**

The workspace is an engineering drawing sheet, not a dashboard of cards. Structure comes from 1px hairlines, a lettered and numbered zone grid, and a single signal orange. Light is warm paper with near-black ink; dark is a graphite sheet with chalk ink and the same orange. Corners are square, there are no shadows, no gradients and no glow.

The tone is precise and instrument-like. Density is high but ruled: panels are not boxes, they are zones separated by one-pixel gaps over the rule colour. A title block (project, stage, run state) anchors the sheet. The logo (a framed square holding a small tree whose root node is orange) is the same drafting idea at icon size.

**Key Characteristics:**
- One hairline system: 1px rules, no card borders, no radius.
- One signal colour, reserved for the primary action, the live or finished stage, selection and focus.
- Condensed grotesk for headings and labels, plain Barlow for reading, mono only for code and the log.
- Zone letters A-D across and numbers 1-2 down rule the margins on desktop.
- Empty drawing areas carry corner registration marks instead of illustrations.

## Colors

Warm paper and ink with one orange; semantic greens, ambers and reds appear only for status.

### Primary
- **Signal Orange** (#ff4a1c): primary action fill, live and finished stage bars, the chip crossing the track, text selection, caret, focus outline, the root node of the logo. Hover is a lighter orange (#ff6a40). Text on it is always ink (#14161a), never white.

### Neutral
- **Warm Paper** (#f6f5f1): the sheet, panel heads, body background.
- **Bright Paper** (#fbfaf7): inputs and the alert strip, one step lifted.
- **Drafting Ink** (#14161a): text, the sheet frame, strong borders and hover fills.
- **Ink 2** (#3b4048): secondary text and labels. **Ink 3** (#636973): muted text, placeholders, dashed unstarted track, field borders.
- **Hairline Grey** (#c8cbd0): all rules, grid gaps, scrollbar thumbs, quiet borders.
- **Log Paper** (#efeee9): terminal/log background. **Hatch Grey** (#d9dbdf): hatching lines.
- **Status:** ok #1d7a4d, warn #8a5a00, danger #c0271d (lighter equivalents in dark).
- **Graphite sheet (dark):** paper #111213, paper-2 #161718, chalk ink #ecebe5, rule #2d2f32, log #0d0e0f; signal is unchanged.

### Named Rules
**The One Signal Rule.** Orange marks only what is acting or acted on: the Generate button, a live or done stage, selection, focus. It never decorates headings, links or backgrounds.
**The Ink-On-Orange Rule.** Orange fills carry ink text (#14161a) in both themes.

## Typography

**Display Font:** Barlow Condensed (with Barlow, sans-serif)
**Body Font:** Barlow (with system-ui, sans-serif)
**Label/Mono Font:** Barlow Condensed for labels; Geist Mono for code and the log only.

**Character:** A narrow, engineered grotesk for titling and a sturdy plain grotesk for reading, like title-block lettering over a drawing.

### Hierarchy
- **Display** (700, clamp(3.5rem, 7vw, 6rem), 0.92): the sign-in statement only.
- **Headline** (700, 3rem / 1.875rem for the title-block project name, 1): page titles on auth sheets, project name.
- **Title** (600, 1.05rem to 1.5rem, tracking 0.02em): panel titles and the wordmark.
- **Body** (400, 15px, 1.45): all reading text; inputs 0.95rem.
- **Label** (600, 0.75-0.8rem, tracking 0.08-0.1em, uppercase on field and stage labels): field labels, stage names, zone tags and ruler letters.

### Named Rules
**The Tabular Rule.** Counts and figures use tabular numerals (`.tnum`).
**The Two-Voice Rule.** Condensed for naming and labelling, Barlow for sentences; do not mix within a line.

## Layout

A full-bleed sheet inside a 1px ink frame with 8-12px outer padding. On desktop (lg) the main area is a 13-column grid (a 28px ruler column plus 12 equal columns) with a 26px top ruler row: requirements panel columns 1-6 (A-B), extraction 7-12 (C-D); row 2 holds diagrams across 9 columns and the agent log across 3; a title block spans the bottom. Panels are separated by a 1px gap over the rule colour, never by borders on each panel. Below lg the grid collapses to a single stacked column and the rulers hide. Panel padding is 14-16px; panel heads are 42px tall. The header strip holds logo, wordmark, theme toggle, user and sign-out. Auth pages use a two-column sheet: statement column with registration marks and a hairline entity sketch, and a 420-520px form column.

## Elevation & Depth

Flat. There are no shadows and no blur; depth comes from rules, a one-step paper lift (paper-2) for inputs, and hover fills that invert to ink. State is shown by outline and fill, not elevation.

### Named Rules
**The No-Shadow Rule.** Nothing floats; separation is a 1px line or a 1px gap.

## Shapes

Square everywhere (0 radius). The only curved form is the 12px round chip that crosses the stage track. Disabled primary action is shown by diagonal hatching (135deg, 1px lines every 7px) with a hairline border. Failed stages use a dashed danger bar. Unstarted stages use a dashed ink-3 line.

## Components

Instrument controls: outlined, square, instant colour changes.

### Buttons
- **Shape:** square (0px), 1px ink border.
- **Signal (primary):** full-width, 48px high, signal fill, ink text, 700 weight. Hover lightens to #ff6a40 instantly; the arrow glyph shifts 4px; active presses down 1px. Disabled: hatched.
- **Line (secondary):** 32px, transparent, 1px ink border, 600 weight 13px; hover inverts to ink fill with paper text. `is-signal` variant fills orange.
- **Icon button:** 32px square, 1px rule border that darkens to ink on hover.

### Inputs / Fields
- **Style:** paper-2 fill, 1px ink-3 border, square, 0.65rem x 0.75rem padding.
- **Hover/Focus:** border goes ink; focus adds a 2px signal outline, 1px offset. Global focus-visible is a 2px signal outline with 2px offset.

### Stage Track (signature)
A per-stage bar over a condensed uppercase label. Pending: dashed line. Live: pale-orange 6px bar with a round orange chip crossing it (1.6s, alternating). Done: solid orange bar; finished stages hold their colour. Error: dashed danger bar. Reduced motion parks the chip at centre.

### Title Block
Bottom band with Project (condensed 1.875rem bold, "Untitled sheet" when empty), stage tracks, and a run-state chip (Idle, Running, Complete, Failed).

### Panel Head and Zone Tag
42px ruled head with condensed title; a zone tag (1px ink border, condensed 0.75rem, tracking 0.1em) sits right-aligned and cites the panel's grid zone.

### Registration Marks
18px corner L-shapes (1px ink-3) in empty drawing areas and the auth statement column.

## Do's and Don'ts

### Do:
- **Do** separate panels with a 1px gap over #c8cbd0, and keep every border 1px.
- **Do** use signal orange only for action, live or done state, selection and focus.
- **Do** use ink text on orange fills and keep colour changes on buttons instant.
- **Do** use condensed uppercase labels with 0.08-0.1em tracking for field and stage labels; Barlow for sentences.
- **Do** show unavailable states with hatching and empty areas with registration marks.
- **Do** respect `prefers-reduced-motion`.

### Don't:
- **Don't** use rounded corners, shadows, gradients, glow or glass.
- **Don't** wrap content in cards; use zones.
- **Don't** use orange for headings, links or decoration.
- **Don't** use mono outside code and the log.
- **Don't** use white text on orange.

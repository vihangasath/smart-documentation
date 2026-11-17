---
version: 1
slug: "src-app-page-tsx"
primary_target: "src/app/page.tsx"
related_targets: ["src/app/login/page.tsx","src/app/signup/page.tsx"]
---

# Surface brief: Structify workspace, sign-in and sign-up

Mode: Operate. Audience: students and small teams turning an SRS into diagrams and a starter project. Task: bring a document in, run it, read and export the results. Constraints: keep the Structify name and public/logo.png; light and dark themes with a toggle; keep element ids and accessible names the tests use. Open decisions: none.

## Direction contract

THESIS: The workspace is an engineering drawing sheet, not a dashboard of cards. It refuses rounded shadowed cards, gradients and glow: structure comes from hairlines, zones and one signal colour.

OWN-WORLD: Warm white paper (#F6F5F1) with near-black ink (#14161A), 1px hairline rules (#C8CBD0), and one signal orange (#FF4A1C) used only for the live stage, primary action and revision marks. Dark theme is a graphite sheet with chalk ink and the same orange. One grotesk face at a few weights, tabular figures for counts, mono only for code and the log. Square corners, no shadows, no cards. A zone grid (A-D across, 1-4 down) rules the margins; a title block holds project, stage and run state. Round chip crosses a track when a stage goes live; finished stages keep their colour.

STORY: A student sees at once that this is a precise instrument: they drop in a document, press one orange button, watch the title block and log advance stage by stage, then read the extraction, diagrams and ZIP on the same sheet.

FIRST VIEWPORT: A full-bleed sheet inside a hairline frame with lettered/numbered zone margins. Top: brand and theme and account in a slim ruled strip. Left column (A-B): requirements panel with the dashed drop zone, instruction box and the single orange Generate button. Right (C-D): extraction panel with tabs. Lower band: diagrams panel wide, agent log narrow. A title block anchored bottom-right shows PROJECT, STAGE (Parse / Diagram / Scaffold) and a status chip. Primary action is bottom of the left panel.

FORM: Drafting Sheet, assigned (position 5 on the grounded list), seed key 304f85b5. Raises: finished stages hold their colour (gate board); one strict hairline system (high-density web); panels addressed by zone and cited in the log (star atlas); round chip crossing a track when live (guide map).

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

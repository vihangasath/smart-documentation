# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
Students and small teams who have a written Software Requirements Specification (a PDF, Word or Markdown file, or just a paragraph of requirements) and need to turn it into something they can show or build on: diagrams for a report or review, and a starter codebase for the project. They are usually on a laptop, working to a deadline, and are not necessarily experts in UML or architecture patterns.

## Product Purpose
Structify turns unstructured requirements into a structured domain model (entities, relationships, actions), Mermaid diagrams (ER, class, sequence, architecture) and a downloadable FastAPI project skeleton, using a small set of AI agents. Success is a user who goes from a document to diagrams and a ZIP in a few minutes and trusts what they got.

## Positioning
One document in, three coordinated outputs: the extracted model, the diagrams and a runnable skeleton that all come from the same analysis, with the agents' work visible as it happens.

## Operating Context
- Sign-in required; the whole product is one workspace screen after login.
- Input is a file (PDF, DOCX, Markdown, text) or typed text; with a file attached the text box carries extra instructions.
- A run takes tens of seconds to minutes; the live agent log is the only progress signal, so waiting must feel intentional.
- Outputs: extraction tabs (entities, relations, actions), a diagram viewer (zoom, pan, fullscreen, PNG export, validity warnings) and a ZIP download.

## Capabilities and Constraints
- Next.js 16 (App Router), React 19, Tailwind CSS 4, framer-motion, lucide-react, Mermaid 11.
- Light and dark themes with a toggle; dark is the default.
- Pages: `/login`, `/signup`, `/` (workspace).
- Existing behaviour and ids used by tests must keep working (`srs-file-input`, `generate-btn`, diagram select label, ZIP/PNG buttons).
- Diagram output is AI-generated and may be invalid; invalid diagrams must stay clearly flagged.

## Brand Commitments
The name "Structify" is binding. The original logo was replaced at the user's request (2026-11-17) with a new simple mark: a drawing sheet holding a small tree diagram, one orange root node fanning out to two children (`src/components/LogoMark.tsx`, `src/app/icon.svg`, `public/logo.png`). Keep it simple and readable at favicon size.

## Evidence on Hand
No testimonials, customers or benchmarks exist; none may be invented.

## Product Principles
- Show the work: the agent log and results are the product, not decoration.
- One screen, one next action: it should always be obvious what to do next.
- Be honest about uncertainty: flag invalid diagrams and partial failures rather than hiding them.
- Quiet by default, expressive at the moments that matter (generating, finishing).

## Accessibility & Inclusion
Keyboard operable, visible focus, AA contrast in both themes, respects reduced motion, works down to phone width.

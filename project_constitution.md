# Project Constitution: Smart Documentation Architect

## 1. Core Mission
To transform unstructured technical requirements (SRS) into structured, 
deployable system architectures and visual diagrams with zero manual boilerplate.

## 2. Tech Stack Mandates
- **Backend:** Python 3.10+ with FastAPI.
- **Pydantic:** All data models must use Pydantic v2 for strict validation.
- **Diagramming:** Mermaid.js (must be valid syntax for frontend rendering).
- **Frontend:** Next.js with Tailwind CSS.
- **Styling:** Glassmorphism.

## 3. Architecture Principles
- **Pattern:** Hexagonal Architecture.
- **Formatting:** All Python code must be formatted with `black`.
- **API Style:** RESTful with automatic OpenAPI documentation.

## 4. Constraint & Safety
- Agents must never delete existing user-uploaded SRS files.
- No external API calls are allowed unless defined in the Link phase.
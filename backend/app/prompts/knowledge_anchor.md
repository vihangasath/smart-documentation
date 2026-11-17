# Knowledge Anchor

Reference rules injected into agent prompts. Each `##` section is loaded by name,
so keep the titles stable: agents ask for them by title.

## Architecture Principles

- Clean Architecture: concentric layers (Entities, Use Cases, Interface Adapters, Frameworks and Drivers).
- Dependency Rule: source-code dependencies point only inward. Inner layers never name anything from an outer layer.
- Hexagonal Architecture (Ports and Adapters): the domain core is decoupled from external integrations. Interactions with the outside world go through abstract "ports"; concrete "adapters" implement them. Primary adapters are entry points (REST API, CLI). Secondary adapters wrap external libraries and data access.
- SOLID, especially Single Responsibility and Dependency Inversion. No dependency cycles between components (Acyclic Dependencies Principle).
- Domain-Driven Design: split the solution into bounded contexts. For complex systems, separate read (query) from write (command) operations (CQRS).

## Mermaid Rules

General:
- Use `direction TB` or `direction LR` where the diagram type supports it.
- Prefer identifiers without spaces; put readable text in labels or double quotes.

Architecture diagrams (`architecture-beta`):
- Build them from `group`, `service`, `edge` and `junction`.
- Declare groups as `group id(icon)[Label]`; nest one group in another with `in`.
- Declare services as `service id(icon)[Label]`, and add `in group_id` for services inside a group.
- Only use the default icons: `cloud`, `database`, `disk`, `internet`, `server`.
- Connect with directions, for example `service1:R --> L:service2`.

Entity-Relationship diagrams (`erDiagram`):
- Use crow's foot notation for cardinality, for example `||--o{`.
- A solid line (`--`) is an identifying relationship; a dashed line (`..`) is non-identifying.
- Define attributes in a `{}` block as `type name`.
- Append key constraints `PK`, `FK`, `UK` to attribute names; separate several with commas.
- Entity aliases use square brackets, for example `[Alias]`.

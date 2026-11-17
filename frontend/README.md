# Structify frontend

Next.js 16 (App Router) + React 19 + Tailwind CSS 4. See the [root README](../README.md) for setup, configuration and deployment.

```bash
cp .env.example .env.local
npm install
npm run dev
```

| Script | Purpose |
|---|---|
| `npm run dev` / `build` / `start` | Next.js |
| `npm run lint` | ESLint |
| `npm run typecheck` | `tsc --noEmit` |
| `npm test` | Vitest + Testing Library |

All backend calls go through `src/lib/api.ts` (`apiFetch`/`apiJson`), which adds the bearer token, turns failures into readable `ApiError`s, and signs the user out on `401`. Response types live in `src/types/api.ts`.

# Consumer Technology Support Assistant frontend

React, TypeScript, and Vite interface for the existing Python RAG pipeline.

See the [root README](../README.md) for backend setup, environment variables, architecture, evaluation results, limitations, and testing.

Same commands on Mac and Windows/Logitech keyboards:

```sh
pnpm install --frozen-lockfile
pnpm dev --host 127.0.0.1
```

Open http://localhost:5173, which is the origin permitted by the local API. Use `pnpm test`, `pnpm build`, and `pnpm lint` to verify the frontend. Provider API keys belong only in the repository-root backend environment.

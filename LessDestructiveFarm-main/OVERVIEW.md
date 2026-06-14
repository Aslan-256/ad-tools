# LessDestructiveFarm Overview

This document maps each project-owned file and folder to its purpose.

Scope: excludes dependency and generated output such as `node_modules`, `build`, and `.next`.

## Quick Index

- [Architecture At A Glance](#architecture-at-a-glance)
- [Top-Level Files](#top-level-files)
- [Application Code (`src`)](#application-code-src)
- [Game Module (`game`)](#game-module-game)
- [Archive Examples (`game-archive-props`)](#archive-examples-game-archive-props)
- [Type Augmentations (`typings`)](#type-augmentations-typings)
- [Static Assets (`public`)](#static-assets-public)
- [Changing App Port](#changing-app-port)
- [Common Runtime Flow](#common-runtime-flow)

## Architecture At A Glance

| Area | Description |
| --- | --- |
| Backend | Express + TypeScript, entrypoint at `src/server.ts`. |
| Frontend | Next.js + React, pages in `src/pages`, UI components in `src/next`. |
| Data Layer | PostgreSQL via Sequelize model `src/lib/models/flag.ts`. |
| Submission Engine | `src/game-manager.ts` loads `game/index.js` and periodically submits queued flags. |
| APIs | REST endpoints (`/api/get_config`, `/api/post_flags`) and GraphQL (`/api/graphql`). |

## Top-Level Files

| Path | Purpose |
| --- | --- |
| `README.md` | Setup and usage instructions (Docker compose, env vars, checker API assumptions). |
| `OVERVIEW.md` | This overview document. |
| `package.json` | Root scripts and dependencies for backend + frontend. |
| `compose.yml` | App + Postgres services, env vars, volumes, and ports. |
| `Dockerfile` | Production image build and runtime command. |
| `.dockerignore` | Excludes unnecessary files from Docker build context. |
| `.prettierrc` | Code formatting rules. |
| `tsconfig.json` | Base TypeScript configuration. |
| `tsconfig.server.json` | Backend-focused TypeScript config. |
| `nodemon.json` | Dev auto-restart config for the TypeScript server. |
| `schema.gql` | Emitted GraphQL schema. |
| `next-env.d.ts` | Next.js TypeScript reference file. |
| `LICENSE` | License text. |

## Application Code (`src`)

### `src` root

| Path | Purpose |
| --- | --- |
| `src/server.ts` | App entrypoint; loads env, DB, game manager, then web server. |
| `src/web-server.ts` | Express server setup, Next app wiring, static files, and API mount. |
| `src/game-manager.ts` | Loads game module, installs game deps, loops queued flag submissions. |

### `src/api`

| Path | Purpose |
| --- | --- |
| `src/api/index.ts` | Main API router combining REST and GraphQL routes. |
| `src/api/client-api.ts` | REST endpoints for external clients (`GET /get_config`, `POST /post_flags`). |
| `src/api/graphql-schema.ts` | Builds TypeGraphQL schema from resolvers and emits `schema.gql`. |

### `src/lib`

| Path | Purpose |
| --- | --- |
| `src/lib/db.ts` | Waits for DB availability, initializes Sequelize, syncs models. |
| `src/lib/db-healthcheck.ts` | Simple DB authentication health check. |
| `src/lib/log.ts` | Colored logging helpers (`wait`, `ready`, `error`, etc.). |

### `src/lib/models`

| Path | Purpose |
| --- | --- |
| `src/lib/models/flag.ts` | Flag ORM + GraphQL type (flag, sploit, team, timestamp, status, checker response). |

### `src/lib/resolvers`

| Path | Purpose |
| --- | --- |
| `src/lib/resolvers/index.ts` | Exports GraphQL resolvers list. |
| `src/lib/resolvers/flagResolver.ts` | GraphQL search/filter/count queries and manual post mutation. |
| `src/lib/resolvers/gameResolver.ts` | GraphQL query for game info (flag format). |

### `src/pages`

| Path | Purpose |
| --- | --- |
| `src/pages/_app.tsx` | Global app wrapper, progress bar events, and global CSS imports. |
| `src/pages/index.tsx` | Main dashboard page with data fetching and UI composition. |

### `src/next/components`

| Path | Purpose |
| --- | --- |
| `src/next/components/navBar.tsx` | Top navigation/header. |
| `src/next/components/search.tsx` | Search and filter form. |
| `src/next/components/manualSubmission.tsx` | Manual text parsing and flag submission. |
| `src/next/components/flagCounter.tsx` | Total flags counter. |
| `src/next/components/flagsTable.tsx` | Flags table container. |
| `src/next/components/flagRow.tsx` | Single-row renderer for each flag entry. |
| `src/next/components/pagination.tsx` | Pagination controls. |

### `src/next/lib`

| Path | Purpose |
| --- | --- |
| `src/next/lib/graphql.ts` | Apollo client setup + GraphQL query/mutation definitions. |
| `src/next/lib/types.ts` | Shared frontend TypeScript interfaces/types. |

### `src/next/css`

| Path | Purpose |
| --- | --- |
| `src/next/css/bootswatch-flatly.css` | Theme stylesheet. |
| `src/next/css/style.css` | Project-specific UI styling. |

## Game Module (`game`)

| Path | Purpose |
| --- | --- |
| `game/index.js` | Checker integration logic: flag format, timing, batching, status mapping, metadata/flag-id API calls. |
| `game/package.json` | Dependencies for submitter module (`got`). |
| `game/teams.json` | Team data used by submitter and client config output. |
| `game/.gitkeep` | Placeholder file to keep folder tracked. |

## Archive Examples (`game-archive-props`)

### `game-archive-props/http`

| Path | Purpose |
| --- | --- |
| `game-archive-props/http/index.js` | Example HTTP-based submitter implementation. |
| `game-archive-props/http/package.json` | Example module dependencies. |

### `game-archive-props/tcp`

| Path | Purpose |
| --- | --- |
| `game-archive-props/tcp/index.js` | Example TCP socket-based submitter implementation. |
| `game-archive-props/tcp/package.json` | Example module dependencies. |

## Type Augmentations (`typings`)

| Path | Purpose |
| --- | --- |
| `typings/index.d.ts` | Placeholder for custom global typings. |
| `typings/express/index.d.ts` | Extends Express `Request` typing with `locals.context`. |

## Static Assets (`public`)

| Path | Purpose |
| --- | --- |
| `public/img/dvteam_white.png` | Navbar logo asset. |

## Changing App Port

If you run Tulip on `3000`, move LessDestructiveFarm to another port (for example `3001`).

Update all three places so runtime and server-side rendering stay aligned:

1) `compose.yml`

- Set container env: `PORT=3001`
- Keep port mapping aligned: `'3001:3001'`

2) `src/web-server.ts`

- Listen on env/default port (already supported):
	- `const port = process.env.PORT || 3001;`
	- `server.listen(port);`

3) `src/next/lib/graphql.ts`

- Server-side Apollo URL must match the app port:
	- `uri = 'http://127.0.0.1:3001/api/graphql';`

After changes, rebuild and restart so compiled output includes the updated port config:

```bash
docker compose build --no-cache
docker compose up
```

## Common Runtime Flow

```text
1) src/server.ts starts and initializes DB + game manager.
2) src/game-manager.ts continuously reads QUEUED flags from DB.
3) game/index.js submits batches to checker endpoints and maps statuses.
4) DB rows are updated with final/queued status and checker response.
5) Next.js dashboard reads data via GraphQL and renders filters/tables.
```

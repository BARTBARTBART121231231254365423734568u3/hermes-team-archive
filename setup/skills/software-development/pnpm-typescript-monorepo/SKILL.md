---
name: pnpm-typescript-monorepo
description: "Use when bootstrapping a pnpm TS monorepo."
version: 1.0.0
author: Hermes Agent
license: MIT
---

# pnpm TypeScript Monorepo Bootstrap

Scaffold a version-pinned pnpm workspace (`apps/*`, `packages/*`) that stays `pnpm verify` green from the first commit.

## Procedure

1. Pin the toolchain: `.node-version` + `.nvmrc` with the exact Node version, root `package.json` with `packageManager: pnpm@<exact>` and `engines`, plus `pnpm-workspace.yaml` listing `apps/*` and `packages/*`. Commit `pnpm-lock.yaml` from the first install.
2. Give every workspace package its own `tsconfig.json` and `lint`/`typecheck`/`test`/`build` scripts; define the root `verify` as lint → typecheck → test → build so a green run proves types, unit tests, and the production bundle.
3. Install per-package type packages explicitly: `@types/react` + `@types/react-dom` on the web package and `@types/node` on every package whose `tsconfig` types list or source touches Node APIs (web included when its config lists `"node"`). Missing types surface as `TS2307`/`TS2580`, not as runtime errors.
4. Wire workspace imports twice: build shared packages (`packages/domain`, `packages/ui`) so `dist` + declarations exist, and add `baseUrl` + `paths` in the web `tsconfig` mapping `@scope/pkg` to `../../packages/<pkg>/src` for typecheck. Typecheck-before-build fails on unresolved workspace `dist` without the paths mapping, because the verifier has nothing built to resolve yet.
5. Run `pnpm install`, then per-package builds for shared packages, then full `pnpm verify`; only `git init -b main` + push on green.

## Pitfalls

- A fresh `git worktree` has no `node_modules` — run `pnpm install` inside the worktree before any test/typecheck/build, because `pnpm exec vitest` fails with 'Command not found' for a missing install rather than a code reason.
- Run single test files with `pnpm exec vitest run <path>` from the package dir — `pnpm test --run` is rejected as an unknown option, since pnpm does not forward bare flags to the test script.

- Run the package manager from user-writable scope when the global bin is not writable — install with a `--prefix ~/.local` style target and put it on `PATH` for the session, because a failed global symlink aborts the whole scaffold for a permissions reason unrelated to the code.
- Keep `verify` order as lint → typecheck → test → build but ensure shared-package `dist` exists before the web typecheck runs — run the shared builds once before the first full verify, since Bundler/NodeNext resolution needs either built declarations or explicit `paths` to succeed.
- Keep a service `tsconfig` `include` to `["src"]` (plus `exclude` for `node_modules`/`dist`) or set an explicit `rootDir: "src"` — when `include` also spans a root-level file such as `vitest.config.ts`, tsc infers rootDir as the common ancestor and emits to `dist/src/...` instead of `dist/...`, so the build stays green while `node dist/index.js` crashes with MODULE_NOT_FOUND inside Docker. Assert the entrypoint exists after building (`test -f apps/<svc>/dist/index.js`) before pushing.
- Guard an ESM service entrypoint with resolved absolute paths (`fileURLToPath(import.meta.url) === resolve(process.argv[1] ?? '')`) — comparing against a raw `file://${process.argv[1]}` fails on relative starts (`node dist/index.js`), so `listen` never runs and the container exits 0 with no output. Log on listen and smoke-test the built output (`PORT=<n> node dist/index.js` + curl `/health` and `/`) before pushing; `pnpm verify` alone never executes the server.
- Resolve sibling-package asset paths (static dirs, templates, migrations) from the compiled depth, not the source depth — `__dirname` inside `dist/` sits one level deeper than in `src/`, so a `..` count taken from source lands in a nonexistent nested dir and static serving silently 404s while the API itself stays green. Count from `dist/` (e.g. `join(__dirname, '..', '..', 'web', 'dist')` for `apps/api/dist` → `apps/web/dist`) and cover a static route in the smoke-test curl.
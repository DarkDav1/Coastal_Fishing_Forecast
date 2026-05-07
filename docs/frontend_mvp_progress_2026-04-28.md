# Frontend MVP Progress (2026-04-28)

## Scope

Build a standalone web MVP for the generic coastal fishing forecast engine.

The first milestone is a working search-to-forecast flow:

- search a place
- call the backend engine through a thin API wrapper
- show the Fishing Plan
- show mapped structures from automatic sources
- show wind, swell, tide, and pressure conditions
- keep unsupported inland/lake states explicit

## Progress Management

This workspace is not currently a git repository.

Until git is initialized, progress is tracked by:

- this checklist
- repeatable local commands
- backend test suite
- web build checks

Recommended next step after the first web milestone is stable:

```bash
git init
git add .
git commit -m "Add coastal forecast web MVP"
```

## Current Tasks

- [x] Create `apps/web`
- [x] Add thin Node API wrapper
- [x] Add `/api/search-forecast`
- [x] Build first React forecast surface
- [x] Render Fishing Plan
- [x] Render structure facilities
- [x] Render condition chips
- [ ] Add browser-verified local workflow notes
- [ ] Add split `/api/places` and `/api/forecast`
- [ ] Add GPS flow
- [ ] Add real map provider

## Run Commands

Terminal 1:

```bash
cd apps/web
npm run api
```

Terminal 2:

```bash
cd apps/web
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

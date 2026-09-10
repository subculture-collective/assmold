# Assmold initial repository release

Status: local qualification in progress, September 10, 2026. This is not a
published release, merge record, or new production deployment.

## Repository and scope

- Destination: https://git.subcult.tv/subculture-collective/assmold.git.
- Source branch: `codex/assmold-launch`; starting HEAD `ed42e3a`.
- Destination advertised no references at verification. Initial branch publication
  must precede any meaningful remote merge/CI claim.
- Existing source changes include caption-only acquisition and its tests/Compose
  configuration, Patreon presentation, and the deployed hero photograph.
- Preserve all existing changes. Production remains authoritative for data.

## Ordered release gates

1. Reconcile local source with live behavior. Caption-only worker source and hero
   photo checksums match their running containers. No paid worker needs a restart
   merely to publish source history.
2. Validate caption-only, semantic and deployment contracts against disposable
   PostgreSQL, plus frontend tests/build/lint/formatting. Do not use production
   credentials or data for tests.
3. Hero-photo permission resolved by the project owner's explicit confirmation
   on September 10, 2026; retain the current photograph. See
   `hero-photo-provenance.md`. No license document was independently reviewed.
4. Complete broad local verification and prepare scoped commits. Review the
   initial publication for secrets, generated artifacts and unrelated changes.
5. Publish to Assmold only and verify hosted CI. Inherited HasanAra publication
   workflows are repository-guarded; Assmold image publishing requires its own
   qualified image names, build definitions and release evidence.
6. Build immutable Assmold images from published source. Record all build inputs:
   the current API dependency base is a pinned HasanAra image, while semantic
   images currently use an Assmold API base. Repository isolation does not remove
   this dependency. Never retag an old image as proof of a new-source build.
7. Before a production release, create a fresh database backup and a complete
   image/config rollback record. Keep vector and SQLite-manifest backups paired.
   Drain only affected workers; do not interrupt paid requests or recreate the
   entire Compose project. Verify public API/search and actual worker completions.

## Local evidence

- Fresh disposable PostgreSQL 16 migrated to `20260908_enrichment_run_lookup`.
  Historical contract-migration flags were enabled only for this empty test DB.
- Focused final-source tests: 108 passed, including caption-only ingestion,
  semantic search/investigations, release contracts and new fork-isolation tests.
- Frontend: 275 passed, one skipped; build and ESLint passed. Three existing
  formatting defects were normalized; format check now passes.
- Caption worker Ruff/Black/Mypy passed; new isolation test Ruff/Black passed.
- Broad backend suite: 1,814 passed, two skipped, after supplying the inherited
  test-only cleanup and migration flags to the disposable database. No production
  migration flags or credentials changed. Initial failures from missing test
  flags were corrected in the invocation, not by weakening safeguards.
- Broad validation exposed an inline style on the design-system page that failed
  the CSP contract. Replaced it with equivalent explicit Tailwind theme classes;
  frontend tests/build/lint/format checks passed again. Whole-source Ruff passed.
- Whole-source Black and isort checks pass; Mypy baseline reports zero current
  errors. Black normalized one existing channel-URL assignment in settings without
  changing its value.
- Broad backend and hosted CI are separate gates; focused checks do not replace
  them. No remote publication or production mutation occurred during this work.

## Production baseline

At reconciliation: API `assmold-api:682dd5e`, frontend
`assmold-frontend:banner-20260909`, semantic API
`assmold-semantic:counterstatements-20260909-v3`, indexer
`assmold-semantic:20260909-v4`, enrichment `assmold-enrichment:20260909`,
caption worker `assmold-captions:retry-v1`. Verify immutable image IDs and actual
runtime state immediately before any deployment; these names alone are not
release qualification.

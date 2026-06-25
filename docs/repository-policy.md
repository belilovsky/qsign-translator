# Repository Policy

Last updated: 2026-06-25

## Canonical Repository

QSign Translator now uses one primary repository for ongoing development:

- Local working copy:
  `/Users/belilovsky/Documents/Codex/2026-04-28/qsign-translator`
- GitHub:
  `https://github.com/belilovsky/qsign-translator`

All new code, docs, cleanup, and release work should happen in that repository.

## Archived Repository

The earlier internal working copy was preserved only as an archive:

- `/Users/belilovsky/Documents/Codex/2026-04-28/qsign-translator-archive`

It is not the source of truth anymore. Treat it as read-only historical backup
unless a deliberate recovery step is needed.

## Working Rule

To avoid future repo confusion:

- develop in `qsign-translator`
- push to `origin` on GitHub
- do not continue normal work in `qsign-translator-archive`
- if older context is needed, copy it forward into the active repo rather than
  reviving the archive as a parallel branch of development

## Current Caveat

The public GitHub repository does not yet include the GitHub Actions workflow,
because the available maintainer auth path could not push files inside
`.github/workflows/` without additional GitHub permission scope. Restore that
workflow from the archive or earlier history once maintainer auth is ready.

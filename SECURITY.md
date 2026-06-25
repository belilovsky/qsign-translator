# Security Policy

## Reporting

Please do not open a public issue for suspected secrets exposure, auth bypass,
unsafe review access, or supply-chain concerns.

Please email `a.belilovsky@gmail.com` with the repository name, affected area,
reproduction steps, and impact summary. If GitHub private vulnerability
reporting is enabled for this repository, you may use that channel instead.

## Scope

Security-sensitive areas in this repository include:

- review API token enforcement
- environment-variable handling
- object-storage credentials
- generated media access
- dependency and model provenance

## What To Expect

Useful reports usually include:

- affected file or endpoint
- reproduction steps
- impact summary
- whether the issue is local-only or remotely reachable

## Current Limits

This repository is still a prototype. Some features are intentionally draft-only
and should not be treated as hardened production guarantees:

- review-video is a draft preview artifact
- AI-video briefs are handoff contracts, not verified translation outputs
- high-risk domains still require human review

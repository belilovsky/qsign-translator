# Open-Source Readiness

This repository is now close to public-safe, but a few release decisions still
belong to maintainers rather than code cleanup.

## Already Cleaned

- Deployment-specific hosts, IPs, and internal paths were removed from public
  docs.
- Local MCP config is ignored by git.
- Environment examples keep placeholder values only.
- Public docs now describe generic self-hosting instead of one private runtime.
- Contributor, security, and conduct docs are present.

## Recommended Before Publishing

- Review commit history for any old secret, host, or operational leak that may
  still exist in previous commits.
- Decide whether the token-protected review API should stay in the first public
  release or move behind an optional feature flag.
- Confirm licensing and redistribution rights for:
  - `public/static/assets/signing-avatar.png`
  - sample lexicon data
  - source-registry metadata copied from external services
- Add final repository, issues, and documentation URLs in `pyproject.toml`
  after the public GitHub repo exists.
- Publish a final public security contact in `SECURITY.md`.

## Still Not Public Product Claims

Do not describe the project as a finished sign-language translator yet.
Public-safe wording is:

- transparent RU/KZ sign-planning prototype
- reviewable draft output
- structured handoff for future video generation

Avoid claiming:

- certified translation quality
- native-signer validation completed
- production signer-avatar generation already exists

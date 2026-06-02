# Maintainers

## Current Maintainers

| Name | GitHub | Email | Role |
|------|--------|-------|------|
| REENX8 | [@REENX8](https://github.com/REENX8) | asdawesdzd22@gmail.com | Lead maintainer |

## Security Contact

To report a vulnerability privately, use one of the channels in [`SECURITY.md`](SECURITY.md):

1. **GitHub Security Advisories** (preferred): <https://github.com/reenx8/security/security/advisories/new>
2. **Email**: asdawesdzd22@gmail.com — subject line `[SECURITY]`

## Release Procedure

1. Ensure all CI jobs are green on `main`.
2. Bump [`VERSION`](VERSION) to the new version number.
3. Update [`CHANGELOG.md`](CHANGELOG.md) — move any *Unreleased* entries under the new
   version heading with today's date, and add a reference link at the bottom.
4. Run `make sync-docs` to inject updated metrics into docs, commit the result.
5. Tag the release:
   ```bash
   git tag -a v$(cat VERSION) -m "Release v$(cat VERSION)"
   git push origin v$(cat VERSION)
   ```
6. The `extension-package` CI job automatically builds and attaches the `.zip`
   to the GitHub Release. Verify the release page after the workflow completes.
7. Update the supported-versions table in [`SECURITY.md`](SECURITY.md) if needed.

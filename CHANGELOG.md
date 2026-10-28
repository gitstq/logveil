# Changelog

## v1.0.0 — 2026-10-28
- 🎉 First release.
- ✨ Consistent, reversible pseudonymisation for logs and traces (`redact` / `restore` / `scan`).
- 🔍 Detectors for tokens, secret assignments, emails, IPs, MACs, phones,
  bank cards (Luhn-validated), Chinese resident IDs (checksum-validated),
  home-directory paths, credentialed URLs and GPS coordinate pairs.
- 🧩 Custom categories via JSON config, per-category filtering, counts-only reports.
- 📦 Zero dependencies, Python 3.10+ standard library only.

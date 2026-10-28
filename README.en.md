# 🕶️ LogVeil — Redact Logs for Safe Sharing

**Language / 语言 / 語言:** [English](README.en.md) ｜ [简体中文](README.md) ｜ [繁體中文](README.zh-TW.md)

> Paste logs, stack traces and terminal output into issues, tickets and AI chats — redacted first, reversibly, and without collateral damage.

## 🎉 Introduction

The most common debugging move is pasting a log for someone else to read: into a GitHub issue, to a teammate, or into an AI assistant. Logs, however, are full of emails, internal IPs, tokens, phone numbers, bank cards and home-directory usernames. You share the problem — and leak the privacy along with it.

Secret scanners solve a different problem: they block code commits, they only raise alarms, they never rewrite, and they ignore personal data in free-text logs. **LogVeil is built for redaction before sharing.** It replaces each sensitive value with a **consistent placeholder** (the same email is `[EMAIL_1]` everywhere), so a redacted log still shows the correlations debugging depends on — "the same user, the same IP, over and over". The mapping stays on your machine only, and one command **restores** placeholders in a reply back to the original values.

Inspiration: GitHub Trending in 2026 is dominated by AI-agent tooling, and feeding terminal output to agents has become a daily habit — yet "redact it first" had no small, zero-dependency tool.

**How LogVeil is different:**
- 🔁 **Reversible** — the mapping file stays local (mode 0600); `restore` undoes a redaction. Most tools smear one-way.
- 🎯 **No collateral damage** — bank cards must pass Luhn, Chinese resident IDs must pass the MOD 11-2 check digit, IPv4 is range-checked per octet. Order numbers, timestamps and fake IPs survive.
- 🧭 **Consistent** — same value, same placeholder, across lines and across files when you reuse a mapping.

## ✨ Features

- 🔑 **Tokens & secrets** — GitHub / OpenAI / AWS / Slack / Google token prefixes, JWTs, `Authorization: Bearer`, `api_key=`-style assignments (key name kept, value replaced)
- 📧 **Personal data** — emails, phone numbers, Chinese resident IDs (checksum-validated)
- 🌐 **Network identifiers** — IPv4, IPv6, MAC addresses, credentialed URLs
- 💳 **Financial data** — bank card numbers (Luhn-validated; look-alike order numbers untouched)
- 🏠 **Path privacy** — usernames in `/Users/<name>/` and `C:\Users\<name>\`, GPS coordinate pairs, private-key blocks
- 🧩 **Extensible** — custom categories from a JSON config (e.g. employee IDs `EMP-\d{4}`), per-category switches
- 📊 **Counts-only mode** — `scan` prints per-category counts and exits 1 on any finding, ready for CI
- 📦 **Zero dependencies** — pure Python 3.10+ standard library

## 🚀 Quick Start

Requirements: Python 3.10+ on Windows / macOS / Linux. No third-party packages.

```bash
# Option 1: clone and run, no install
git clone https://github.com/gitstq/logveil.git
cd logveil
python -m logveil --help

# Option 2: install the command
pip install .
logveil --help
```

Redact a log file (keep the mapping file private — never share it):

```bash
python -m logveil redact examples/sample.log -o sample.redacted.log --map mapping.json
```

## 📖 Usage Guide

### Three subcommands

```bash
# 1) redact — works with stdin/stdout pipes
cat app.log | python -m logveil redact --map mapping.json > app.safe.log

# 2) scan — check only, prints a counts JSON; exit code 1 when anything is found
python -m logveil scan app.log

# 3) restore — a reply full of placeholders? Map them back
python -m logveil restore reply.md --map mapping.json -o reply.restored.md
```

### Before → after (real sample output)

```text
2026-10-28 09:12:04 INFO  login ok user=[EMAIL_1] ip=[IP_1] path=/Users/[USER_PATH_1]/app/config.yaml
2026-10-28 09:12:05 ERROR charge failed card=[BANK_CARD_1] phone=[PHONE_1] order=4111111111111112
```

Note that `order=4111111111111112` survives: it looks like a card but fails Luhn. Timestamps like `09:12:04` and the fake IP `999.1.2.3` are likewise left alone.

### Options

| Option | Meaning |
|---|---|
| `--map <file>` | Mapping JSON (written by `redact`, read by `restore`). **Never share it, never commit it.** |
| `--report <file>` | Counts-only report JSON (contains no original values; safe to share) |
| `--categories EMAIL,IP` | Enable only the listed categories |
| `--config <file>` | JSON config; put custom regex categories under `extra_patterns` |

Custom category example, `logveil.json`:

```json
{ "extra_patterns": { "EMPLOYEE_ID": "EMP-\\d{4}" } }
```

Typical scenarios: sanitising a log before filing an issue, self-checking terminal output before pasting it into an AI chat, sending a failure trace to an external vendor, moving a ticket across teams.

> 📸 Screenshots / demo GIF: see the before/after pair `examples/sample.log` and `examples/sample.redacted.log` (placeholder; a recording will follow).

## 💡 Design & Roadmap

- **Why validators, not just regex?** Logs are full of look-alike numbers. Redacting one order number destroys the log's debugging value. Check digits are a ready-made truth test — use them.
- **Why consistent, reversible placeholders?** Redaction is not destruction. Preserving correlation and reversibility keeps redacted material actually useful for fixing the bug.
- **Tech choices:** standard library only, line-streaming so huge logs stay cheap; detectors are separated from the engine, so a new category is one rule plus two tests (a hit and a false-positive guard).
- **Roadmap:** optional rule packs for addresses and person names, an HTML report, a VS Code "redact selection" extension, more national ID and phone formats.
- **Where the community can help:** new category rules, false-positive corpora, documentation polish in more languages.

## 📦 Packaging & Deployment

This is a **tool / library** project, so — per its release policy — there are no binary Releases; integrate it like this:

```bash
# Install as a package (provides the logveil command)
pip install .

# Build sdist / wheel
python -m pip install build
python -m build

# Run the tests
python -m unittest discover -s tests -v
```

Supported environments: Python 3.10–3.13 on Windows / macOS / Linux. No environment variables required.

FAQ:
- **I lost the mapping file. Can I still restore?** No — by design. The mapping is the key; guard it like a password.
- **Does redaction change the file structure?** No. Everything except the sensitive values is preserved byte for byte, timestamps and ordering included.
- **Is `scan` exit code 1 an error?** No, it means "findings present" — built for CI gates.

## 🤝 Contributing

Pull requests and issues are welcome. Commit messages follow Angular style (`feat:` / `fix:` / `docs:` / `refactor:`); every new detector ships with both a hit test and a false-positive test; never commit real personal data or real mapping files in examples. See [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 License

MIT License — see [LICENSE](LICENSE). Use, modify and distribute freely, keeping the copyright notice.

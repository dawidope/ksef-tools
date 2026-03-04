# Changelog

## 0.2.1

### Changes
- JSON output keys standardized to camelCase (matching KSeF API convention)
- Removed duplicate `ksefNumber` and `referenceNumber` from `send` wrapper (already present in `response`)

## 0.2.0

### Features
- `ksef-tools qr <file.xml>` - generate KSeF QR Code I verification link
- `send` now returns `verificationUrl` (QR Code I link) in success response
- Invoice issue date (`P_1`) and hash sourced from XML / KSeF response for correct verification links

## 0.1.0

Initial release as a CLI tool.

### Features
- `ksef-tools send <file.xml>` - send invoice to KSeF with full session lifecycle
- `ksef-tools list --days N` - list invoices from KSeF
- JSON-only stdout output with status codes (`SUCCESS/20`, `ERROR/-10`, `REFUSED/30`)
- Daily rotating log files (`logs/ksef-tools.log`)
- `config.json` based configuration (replaces `.env`)
- PyInstaller build to standalone `.exe`
- GitHub Actions CI/CD - builds `.exe` on tag push and publishes to Releases
- Lazy command loading for fast `--version` / `--help`

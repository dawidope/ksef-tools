# KSeF Tools

CLI for the Polish National e-Invoice System (KSeF). Packaged as a single `.exe` via PyInstaller.

## Quick Start (standalone .exe)

1. Download `ksef-tools.exe` from [Releases](../../releases)
2. Copy `config.json.example` to `config.json` next to the `.exe`
3. Fill in your KSeF credentials in `config.json`

```bash
ksef-tools send invoice.xml
ksef-tools list --days 30
```

## Configuration

Create `config.json` next to the executable (or in the working directory for dev mode):

```json
{
  "ksef_token": "your_token_here",
  "context_type": "nip",
  "context_value": "1234567890",
  "base_url": "https://ksef-demo.mf.gov.pl",
  "subject_type": "Subject1",
  "date_type": "Issue"
}
```

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `ksef_token` | yes | - | KSeF authorization token |
| `context_type` | yes | - | Context type (`nip`) |
| `context_value` | yes | - | Tax identification number (NIP) |
| `base_url` | no | `https://ksef-demo.mf.gov.pl` | KSeF API endpoint |
| `subject_type` | no | `Subject1` | `Subject1` = sales, `Subject2` = purchases |
| `date_type` | no | `Issue` | `Issue` = invoice date, `Receive` = KSeF receive date |

## Commands

### send

Send an invoice XML file to KSeF:

```bash
ksef-tools send <path_to_xml_file>
```

Returns JSON with `ksef_number`, `reference_number`, and processing status.

### list

List invoices from the last N days:

```bash
ksef-tools list --days 30 --page-size 10
```

Returns JSON with invoice metadata.

## Development

```bash
python -m venv venv
venv\Scripts\activate
pip install -e ".[build]"
ksef-tools --version
```

## Build .exe locally

```bash
python build.py
dist\ksef-tools.exe --version
```

## Release

Push a version tag to trigger CI build and GitHub Release:

```bash
git tag v0.1.0
git push origin v0.1.0
```

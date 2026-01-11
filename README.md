# KSeF Tools

Simple Python tools for working with the Polish National e-Invoice System (KSeF).

## Requirements

- Python 3.8+
- `ksef-client-python` library

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the environment:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
KSEF_TOKEN=your_token_here
KSEF_CONTEXT_TYPE=NIP
KSEF_CONTEXT_VALUE=1234567890
KSEF_BASE_URL=https://ksef-demo.mf.gov.pl
```

**Environment variables:**
- `KSEF_TOKEN` - KSeF authorization token (required)
- `KSEF_CONTEXT_TYPE` - context type, e.g., "NIP" (required)
- `KSEF_CONTEXT_VALUE` - context value, e.g., tax identification number (required)
- `KSEF_BASE_URL` - KSeF environment URL (optional, defaults to DEMO)

## Tools

### send_invoice_xml.py

Sends an invoice XML file to the KSeF system.

**Usage:**
```bash
python send_invoice_xml.py <path_to_xml_file>
```

**Example:**
```bash
python send_invoice_xml.py invoice.xml
```

The tool:
1. Authenticates using KSeF token
2. Opens an online session
3. Sends the invoice
4. Waits for processing
5. Closes the session
6. Returns the reference number and KSeF number

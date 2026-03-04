from __future__ import annotations

import hashlib
import logging
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

import click
from ksef_client.config import KsefClientOptions
from ksef_client.services.verification_link import VerificationLinkService
from ksef_client.utils.base64url import b64encode

from ksef_tools.cli import load_config
from ksef_tools.output import print_json, success

logger = logging.getLogger("ksef_tools")

_QR_BASE_URLS = {
    "test": "https://qr-test.ksef.mf.gov.pl",
    "demo": "https://qr-demo.ksef.mf.gov.pl",
}
_QR_BASE_URL_PROD = "https://qr.ksef.mf.gov.pl"


def _resolve_qr_base_url(base_url: str) -> str:
    url = base_url.lower()
    for env, qr_url in _QR_BASE_URLS.items():
        if env in url:
            return qr_url
    return _QR_BASE_URL_PROD


def build_verification_url(
    base_url: str, nip: str, issue_date: date, invoice_hash: str,
) -> str:
    """Build KSeF QR Code I verification URL.

    invoice_hash: SHA-256 hash in base64 or base64url encoding.
    """
    qr_base_url = _resolve_qr_base_url(base_url)
    options = KsefClientOptions(base_url=base_url, base_qr_url=qr_base_url)
    service = VerificationLinkService(options=options)
    return service.build_invoice_verification_url(nip, issue_date, invoice_hash)


@click.command("qr")
@click.argument("invoice_xml_path", type=click.Path(exists=True, path_type=Path))
@click.option("--nip", default=None, help="Seller NIP. Defaults to context_value from config.")
@click.option(
    "--date",
    "issue_date",
    default=None,
    help="Invoice issue date (YYYY-MM-DD). Overrides P_1 from XML.",
)
@click.pass_context
def qr_command(ctx: click.Context, invoice_xml_path: Path, nip: str | None, issue_date: str | None) -> None:
    """Generate KSeF QR Code I verification link for an invoice."""
    config = load_config(ctx)

    invoice_bytes = invoice_xml_path.read_text(encoding="utf-8-sig").encode("utf-8")

    if nip is None:
        nip = config.context_value

    if issue_date is None:
        root = ET.fromstring(invoice_bytes)
        ns = root.tag.split("}")[0] + "}" if "}" in root.tag else ""
        p1_elem = root.find(f".//{ns}P_1")
        if p1_elem is None or not p1_elem.text:
            raise ValueError("Cannot find P_1 (invoice issue date) in XML")
        issue_date_obj = date.fromisoformat(p1_elem.text)
    else:
        issue_date_obj = date.fromisoformat(issue_date)

    invoice_hash = b64encode(hashlib.sha256(invoice_bytes).digest())

    logger.info("Generating QR Code I link for NIP=%s, date=%s", nip, issue_date_obj)
    url = build_verification_url(config.base_url, nip, issue_date_obj, invoice_hash)

    logger.info("Verification URL: %s", url)
    print_json(success({"verification_url": url}))

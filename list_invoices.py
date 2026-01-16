from __future__ import annotations

import argparse
import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from ksef_client.client import KsefClient
from ksef_client.config import KsefClientOptions, KsefEnvironment
from ksef_client.services.workflows import AuthCoordinator


def _env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if not value:
        raise SystemExit(f"Set {name} env var.")
    return value


def main() -> None:
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="List invoices from KSeF")
    parser.add_argument("days", type=int, help="Number of days back to retrieve invoices")
    parser.add_argument("--page-size", type=int, default=10, help="Number of invoices per page (default: 10)")
    args = parser.parse_args()

    token = _env("KSEF_TOKEN")
    context_type = _env("KSEF_CONTEXT_TYPE")
    context_value = _env("KSEF_CONTEXT_VALUE")
    base_url = _env("KSEF_BASE_URL", KsefEnvironment.DEMO.value)
    subject_type = _env("KSEF_SUBJECT_TYPE", "Subject1")
    date_type = _env("KSEF_DATE_TYPE", "Issue")

    date_to = datetime.now(timezone.utc)
    date_from = date_to - timedelta(days=args.days)
    payload = {
        "subjectType": subject_type,
        "dateRange": {
            "dateType": date_type,
            "from": date_from.isoformat(),
            "to": date_to.isoformat(),
        },
    }

    with KsefClient(KsefClientOptions(base_url=base_url)) as client:
        certs = client.security.get_public_key_certificates()
        token_cert = next(c for c in certs if "KsefTokenEncryption" in (c.get("usage") or []))[
            "certificate"
        ]
        
        print("Authenticating with KSeF token...")
        access_token = (
            AuthCoordinator(client.auth)
            .authenticate_with_ksef_token(
                token=token,
                public_certificate=token_cert,
                context_identifier_type=context_type,
                context_identifier_value=context_value,
                max_attempts=90,
                poll_interval_seconds=2.0,
            )
            .tokens.access_token.token
        )
        
        print(f"Querying invoices from last {args.days} days...")
        metadata = client.invoices.query_invoice_metadata(
            payload,
            access_token=access_token,
            page_offset=0,
            page_size=args.page_size,
            sort_order="Asc",
        )

    invoices = metadata.get("invoices") or metadata.get("invoiceList") or []
    print(f"\n✓ Invoices returned: {len(invoices)}\n")
    
    for i, invoice in enumerate(invoices, 1):
        print(f"{i}. Invoice: {invoice.get('invoiceNumber')}")
        print(f"   KSeF Number: {invoice.get('ksefNumber')}")
        print(f"   Issue Date: {invoice.get('issueDate')}")
        print(f"   Seller: {invoice.get('seller', {}).get('name')} (NIP: {invoice.get('seller', {}).get('nip')})")
        print(f"   Buyer: {invoice.get('buyer', {}).get('name')}")
        print(f"   Net Amount: {invoice.get('netAmount')} {invoice.get('currency')}")
        print(f"   Gross Amount: {invoice.get('grossAmount')} {invoice.get('currency')}")
        print(f"   Hash: {invoice.get('invoiceHash')}")
        print()


if __name__ == "__main__":
    main()

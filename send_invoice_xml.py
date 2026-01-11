from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from ksef_client.client import KsefClient
from ksef_client.config import KsefClientOptions, KsefEnvironment
from ksef_client.services.workflows import AuthCoordinator, OnlineSessionWorkflow


def _env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if not value:
        raise SystemExit(f"Set {name} env var.")
    return value


def main() -> None:
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Send invoice XML to KSeF")
    parser.add_argument("invoice_xml_path", help="Path to the invoice XML file")
    args = parser.parse_args()

    token = _env("KSEF_TOKEN")
    context_type = _env("KSEF_CONTEXT_TYPE")
    context_value = _env("KSEF_CONTEXT_VALUE")
    base_url = _env("KSEF_BASE_URL", KsefEnvironment.DEMO.value)
    invoice_xml_path = Path(args.invoice_xml_path)

    if not invoice_xml_path.exists():
        raise SystemExit(f"Invoice XML file not found: {invoice_xml_path}")

    # Read as text with utf-8-sig to automatically remove BOM, then encode back to bytes
    invoice_xml = invoice_xml_path.read_text(encoding="utf-8-sig").encode("utf-8")

    with KsefClient(KsefClientOptions(base_url=base_url)) as client:
        certs = client.security.get_public_key_certificates()
        token_cert = next(c for c in certs if "KsefTokenEncryption" in (c.get("usage") or []))[
            "certificate"
        ]
        symmetric_cert = next(
            c for c in certs if "SymmetricKeyEncryption" in (c.get("usage") or [])
        )["certificate"]

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

        print("Opening session...")
        session = OnlineSessionWorkflow(client.sessions).open_session(
            form_code={"systemCode": "FA (3)", "schemaVersion": "1-0E", "value": "FA"},
            public_certificate=symmetric_cert,
            access_token=access_token,
        )

        try:
            print(f"Sending invoice from: {invoice_xml_path}")
            send_result = OnlineSessionWorkflow(client.sessions).send_invoice(
                session_reference_number=session.session_reference_number,
                invoice_xml=invoice_xml,
                encryption_data=session.encryption_data,
                access_token=access_token,
            )

            invoice_reference = send_result["referenceNumber"]
            print(f"Invoice reference: {invoice_reference}")

            print("Waiting for processing...")
            for _ in range(60):
                status = client.sessions.get_session_invoice_status(
                    session.session_reference_number,
                    invoice_reference,
                    access_token=access_token,
                )
                code = int(status.get("status", {}).get("code", 0))
                if code == 200:
                    break
                if code not in {100, 150}:
                    # Extract error information
                    status_info = status.get("status", {})
                    error_code = status_info.get("code")
                    error_description = status_info.get("description", "Unknown error")
                    error_details = status_info.get("details", [])
                    
                    print(f"\n✗ Invoice processing failed!")
                    print(f"Error code: {error_code}")
                    print(f"Description: {error_description}")
                    if error_details:
                        print(f"Details:")
                        for detail in error_details:
                            print(f"  - {detail}")
                    raise SystemExit(1)
                time.sleep(2)

            print(f"\n✓ Invoice sent successfully!")
            print(f"Invoice reference: {invoice_reference}")
            print(f"KSeF number: {status.get('ksefNumber')}")

        finally:
            print("Closing session...")
            OnlineSessionWorkflow(client.sessions).close_session(
                session.session_reference_number,
                access_token,
            )


if __name__ == "__main__":
    main()

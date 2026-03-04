from __future__ import annotations

import json
import logging
import time
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

import click
from ksef_client.client import KsefClient
from ksef_client.config import KsefClientOptions
from ksef_client.services.workflows import OnlineSessionWorkflow

from ksef_tools.cli import load_config
from ksef_tools.commands.qr import build_verification_url
from ksef_tools.ksef_auth import authenticate, open_session
from ksef_tools.output import (
    CODE_ERROR,
    CODE_REFUSED,
    CODE_SUCCESS,
    error,
    print_json,
    refused,
    success,
)

logger = logging.getLogger("ksef_tools")


def _map_status_code(ksef_code: int) -> int:
    if ksef_code == 200:
        return CODE_SUCCESS
    if 300 <= ksef_code < 400:
        return CODE_REFUSED
    return CODE_ERROR


@click.command("send")
@click.argument("invoice_xml_path", type=click.Path(exists=True, path_type=Path))
@click.pass_context
def send_command(ctx: click.Context, invoice_xml_path: Path) -> None:
    """Send an invoice XML file to KSeF."""
    config = load_config(ctx)
    logger.info("Sending invoice: %s", invoice_xml_path)

    invoice_xml = invoice_xml_path.read_text(encoding="utf-8-sig").encode("utf-8")

    with KsefClient(KsefClientOptions(base_url=config.base_url)) as client:
        access_token = authenticate(client, config)
        session = open_session(client, config, access_token)

        try:
            logger.info("Sending invoice data...")
            send_result = OnlineSessionWorkflow(client.sessions).send_invoice(
                session_reference_number=session.session_reference_number,
                invoice_xml=invoice_xml,
                encryption_data=session.encryption_data,
                access_token=access_token,
                offline_mode=False,
            )
            invoice_reference = send_result["referenceNumber"]
            logger.info("Invoice reference: %s", invoice_reference)

            logger.info("Polling for processing status...")
            status = {}
            timed_out = True
            for _ in range(60):
                status = client.sessions.get_session_invoice_status(
                    session.session_reference_number,
                    invoice_reference,
                    access_token=access_token,
                )
                code = int(status.get("status", {}).get("code", 0))
                if code == 200:
                    timed_out = False
                    break
                if code not in {100, 150}:
                    mapped = _map_status_code(code)
                    status_info = status.get("status", {})
                    msg = (
                        f"Invoice processing failed: "
                        f"code={status_info.get('code')}, "
                        f"{status_info.get('description', 'Unknown error')}"
                    )
                    logger.error(msg)
                    logger.error("KSeF response: %s", json.dumps(status, ensure_ascii=False, default=str))
                    result = {
                        "status": "REFUSED" if mapped == CODE_REFUSED else "ERROR",
                        "status_code": mapped,
                        "ksef_number": None,
                        "reference_number": invoice_reference,
                        "error": msg,
                        "response": status,
                    }
                    print_json(result)
                    return
                time.sleep(2)

            if timed_out:
                msg = "Timed out waiting for invoice processing (120s)"
                logger.error(msg)
                logger.error("KSeF response: %s", json.dumps(status, ensure_ascii=False, default=str))
                print_json(error(msg, {"reference_number": invoice_reference, "response": status}))
                return

            ksef_number = status.get("ksefNumber")
            invoice_hash = status.get("invoiceHash")
            logger.info("Invoice sent successfully: %s", ksef_number)
            logger.info("KSeF response: %s", json.dumps(status, ensure_ascii=False, default=str))

            root = ET.fromstring(invoice_xml)
            ns = root.tag.split("}")[0] + "}" if "}" in root.tag else ""
            p1_elem = root.find(f".//{ns}P_1")
            if p1_elem is None or not p1_elem.text:
                raise ValueError("Cannot find P_1 (invoice issue date) in XML")
            issue_date = date.fromisoformat(p1_elem.text)

            if not invoice_hash:
                raise ValueError("KSeF did not return invoiceHash in status response")

            verification_url = build_verification_url(
                config.base_url, config.context_value, issue_date, invoice_hash,
            )

            print_json(
                success(
                    {
                        "ksef_number": ksef_number,
                        "reference_number": invoice_reference,
                        "verification_url": verification_url,
                        "response": status,
                    }
                )
            )

        finally:
            logger.info("Closing session...")
            OnlineSessionWorkflow(client.sessions).close_session(
                session.session_reference_number,
                access_token,
            )

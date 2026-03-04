from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone

import click
from ksef_client.client import KsefClient
from ksef_client.config import KsefClientOptions

from ksef_tools.cli import load_config
from ksef_tools.ksef_auth import authenticate
from ksef_tools.output import print_json, success

logger = logging.getLogger("ksef_tools")


@click.command("list")
@click.option("--days", required=True, type=int, help="Number of days back to query.")
@click.option("--page-size", default=10, type=int, help="Invoices per page.")
@click.pass_context
def list_command(ctx: click.Context, days: int, page_size: int) -> None:
    """List invoices from KSeF for the last N days."""
    config = load_config(ctx)
    logger.info("Listing invoices for last %d days (page_size=%d)", days, page_size)

    date_to = datetime.now(timezone.utc)
    date_from = date_to - timedelta(days=days)
    payload = {
        "subjectType": config.subject_type,
        "dateRange": {
            "dateType": config.date_type,
            "from": date_from.isoformat(),
            "to": date_to.isoformat(),
        },
    }

    with KsefClient(KsefClientOptions(base_url=config.base_url)) as client:
        access_token = authenticate(client, config)

        logger.info("Querying invoice metadata...")
        metadata = client.invoices.query_invoice_metadata(
            payload,
            access_token=access_token,
            page_offset=0,
            page_size=page_size,
            sort_order="Asc",
        )

    logger.info("KSeF response: %s", json.dumps(metadata, ensure_ascii=False, default=str))
    raw_invoices = metadata.get("invoices") or metadata.get("invoiceList") or []
    invoices = [
        {
            "invoice_number": inv.get("invoiceNumber"),
            "ksef_number": inv.get("ksefNumber"),
            "issue_date": inv.get("issueDate"),
            "seller": inv.get("seller"),
            "buyer": inv.get("buyer"),
            "net_amount": inv.get("netAmount"),
            "gross_amount": inv.get("grossAmount"),
            "currency": inv.get("currency"),
        }
        for inv in raw_invoices
    ]
    logger.info("Found %d invoices", len(invoices))
    print_json(
        success(
            {
                "invoices": invoices,
                "total_count": len(invoices),
                "query": {"days": days, "page_size": page_size},
            }
        )
    )

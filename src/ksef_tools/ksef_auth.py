from __future__ import annotations

import logging
from typing import Any

from ksef_client.client import KsefClient
from ksef_client.services.workflows import AuthCoordinator, OnlineSessionWorkflow

from ksef_tools.config import Config

logger = logging.getLogger("ksef_tools")


def get_certificates(client: KsefClient) -> dict[str, str]:
    certs = client.security.get_public_key_certificates()
    token_cert = next(
        c for c in certs if "KsefTokenEncryption" in (c.get("usage") or [])
    )["certificate"]
    symmetric_cert = next(
        c for c in certs if "SymmetricKeyEncryption" in (c.get("usage") or [])
    )["certificate"]
    return {"token": token_cert, "symmetric": symmetric_cert}


def authenticate(client: KsefClient, config: Config) -> str:
    logger.info("Authenticating with KSeF token...")
    certs = get_certificates(client)
    access_token = (
        AuthCoordinator(client.auth)
        .authenticate_with_ksef_token(
            token=config.ksef_token,
            public_certificate=certs["token"],
            context_identifier_type=config.context_type,
            context_identifier_value=config.context_value,
            max_attempts=90,
            poll_interval_seconds=2.0,
        )
        .tokens.access_token.token
    )
    logger.info("Authentication successful")
    return access_token


def open_session(
    client: KsefClient, config: Config, access_token: str
) -> Any:
    logger.info("Opening online session...")
    certs = get_certificates(client)
    session = OnlineSessionWorkflow(client.sessions).open_session(
        form_code={"systemCode": "FA (3)", "schemaVersion": "1-0E", "value": "FA"},
        public_certificate=certs["symmetric"],
        access_token=access_token,
    )
    logger.info("Session opened: %s", session.session_reference_number)
    return session

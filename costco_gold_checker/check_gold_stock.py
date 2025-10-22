#!/usr/bin/env python3
"""Utility to check Costco gold inventory and email an alert when it is available."""

from __future__ import annotations

import argparse
import logging
import os
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Iterable

import requests

DEFAULT_PRODUCT_URL = (
    "https://www.costco.com/1-oz.-gold-bar-random-year%2c-24-kt.product.4000071766.html"
)

IN_STOCK_KEYWORDS = (
    "add to cart",
    "in stock",
    "available for purchase",
    "get it today",
)

OUT_OF_STOCK_KEYWORDS = (
    "out of stock",
    "sold out",
    "inventory alert",
    "notify me",
)

DEFAULT_RECIPIENT = os.getenv("COSTCO_ALERT_RECIPIENT", "noah1234@gmail.com")
DEFAULT_SENDER = os.getenv("COSTCO_ALERT_SENDER")
DEFAULT_PASSWORD = os.getenv("COSTCO_ALERT_APP_PASSWORD")
DEFAULT_SMTP_HOST = os.getenv("COSTCO_ALERT_SMTP_HOST", "smtp.gmail.com")
DEFAULT_SMTP_PORT = int(os.getenv("COSTCO_ALERT_SMTP_PORT", "587"))


@dataclass
class StockStatus:
    """Represents whether the Costco gold product appears to be in stock."""

    in_stock: bool
    reason: str


def fetch_product_page(url: str, timeout: int = 10) -> str:
    """Retrieve the Costco product page and return the HTML payload."""

    logging.debug("Fetching Costco product page: %s", url)
    response = requests.get(
        url,
        timeout=timeout,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            )
        },
    )
    response.raise_for_status()
    logging.debug("Fetched %d bytes from Costco", len(response.text))
    return response.text


def _contains_any(haystack: str, needles: Iterable[str]) -> bool:
    return any(needle in haystack for needle in needles)


def parse_stock_status(html: str) -> StockStatus:
    """Evaluate the HTML document and determine if the product is in stock."""

    lowered = html.lower()
    if _contains_any(lowered, OUT_OF_STOCK_KEYWORDS):
        logging.debug("Found out-of-stock keyword in response.")
        return StockStatus(False, "Costco indicates the gold product is out of stock.")

    if _contains_any(lowered, IN_STOCK_KEYWORDS):
        logging.debug("Found in-stock keyword in response.")
        return StockStatus(True, "Costco indicates the gold product is available.")

    logging.debug("Did not find definitive stock indicator in the response.")
    return StockStatus(
        False,
        "Unable to determine inventory status from Costco's response; treating as out of stock.",
    )


def send_stock_email(
    status: StockStatus,
    product_url: str,
    *,
    recipient: str,
    sender: str,
    password: str,
    smtp_host: str = DEFAULT_SMTP_HOST,
    smtp_port: int = DEFAULT_SMTP_PORT,
) -> None:
    """Send an email about the Costco gold stock status."""

    message = EmailMessage()
    message["Subject"] = "Costco Gold Alert: In Stock"
    message["From"] = sender
    message["To"] = recipient
    message.set_content(
        """
Hi,

Costco's gold listing appears to be in stock.

Details: {reason}
Product page: {url}

This notification was generated automatically.
""".strip().format(reason=status.reason, url=product_url)
    )

    logging.info("Sending inventory email to %s", recipient)
    with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as smtp:
        smtp.starttls()
        smtp.login(sender, password)
        smtp.send_message(message)


def configure_logging(verbosity: int) -> None:
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG

    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check Costco gold inventory and optionally send an email alert."
    )
    parser.add_argument(
        "--url",
        default=os.getenv("COSTCO_GOLD_URL", DEFAULT_PRODUCT_URL),
        help="Costco product URL to check.",
    )
    parser.add_argument(
        "--email",
        action="store_true",
        help="Send an email when the product is reported as in stock.",
    )
    parser.add_argument(
        "--recipient",
        default=DEFAULT_RECIPIENT,
        help="Email address that should receive in-stock notifications.",
    )
    parser.add_argument(
        "--sender",
        default=DEFAULT_SENDER,
        help="Email address used to send the notification.",
    )
    parser.add_argument(
        "--password",
        default=DEFAULT_PASSWORD,
        help="App password for the sender email account.",
    )
    parser.add_argument(
        "--smtp-host",
        default=DEFAULT_SMTP_HOST,
        help="SMTP host for the sender email account.",
    )
    parser.add_argument(
        "--smtp-port",
        default=DEFAULT_SMTP_PORT,
        type=int,
        help="SMTP port for the sender email account.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase logging verbosity (use -vv for debug logging).",
    )

    args = parser.parse_args()
    configure_logging(args.verbose)

    try:
        html = fetch_product_page(args.url)
    except requests.RequestException as exc:
        logging.error("Failed to fetch Costco product page: %s", exc)
        return 1

    status = parse_stock_status(html)
    logging.info("Costco gold in-stock status: %s", status.in_stock)
    logging.debug("Reason: %s", status.reason)

    if status.in_stock and args.email:
        missing = [
            name
            for name, value in {
                "sender": args.sender,
                "password": args.password,
                "recipient": args.recipient,
            }.items()
            if not value
        ]
        if missing:
            logging.error(
                "Cannot send email because required field(s) are missing: %s",
                ", ".join(missing),
            )
            return 2

        try:
            send_stock_email(
                status,
                args.url,
                recipient=args.recipient,
                sender=args.sender,
                password=args.password,
                smtp_host=args.smtp_host,
                smtp_port=args.smtp_port,
            )
        except smtplib.SMTPException as exc:
            logging.error("Failed to send email: %s", exc)
            return 3

    if status.in_stock:
        print("Costco gold appears to be in stock!")
    else:
        print(status.reason)

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())

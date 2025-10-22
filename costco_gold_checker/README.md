# Costco Gold Inventory Checker

This small utility fetches the Costco product page for a gold bar and inspects the
page contents for common "in stock" or "out of stock" phrases. When the product is
available, the script can send an email alert.

## Features

- Fetches the Costco product page using a configurable URL.
- Detects inventory status by scanning for known phrases.
- Sends an email notification (using SMTP) when the product appears to be in stock.

## Requirements

Install the dependencies (preferably in a virtual environment):

```bash
pip install -r requirements.txt
```

## Configuration

The script reads the following environment variables:

| Variable | Purpose | Default |
| --- | --- | --- |
| `COSTCO_GOLD_URL` | Costco product URL to check | 1 oz gold bar listing |
| `COSTCO_ALERT_RECIPIENT` | Email address that should receive alerts | `noah1234@gmail.com` |
| `COSTCO_ALERT_SENDER` | Email account used to send the alert | _required when emailing_ |
| `COSTCO_ALERT_APP_PASSWORD` | App password for the sender | _required when emailing_ |
| `COSTCO_ALERT_SMTP_HOST` | SMTP server hostname | `smtp.gmail.com` |
| `COSTCO_ALERT_SMTP_PORT` | SMTP server port | `587` |

When using Gmail you must create an [app password](https://support.google.com/accounts/answer/185833) and
assign it to `COSTCO_ALERT_APP_PASSWORD`. The regular account password will not work if
multi-factor authentication is enabled (which is strongly recommended).

## Usage

```bash
python check_gold_stock.py --email \
  --sender "your.account@gmail.com" \
  --password "$COSTCO_ALERT_APP_PASSWORD"
```

Without `--email` the script simply prints the current status, which can be useful for testing
or for running from a scheduled job that handles notification separately. Use `-v` or `-vv` to
enable more verbose logging when debugging network or SMTP issues.

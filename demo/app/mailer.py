"""Email charge sender for reporth, aimed at a LOCAL SMTP for the demo.

Sends to ``SMTP_HOST``/``SMTP_PORT`` (default ``localhost:1025``), so nothing
leaves the machine. If no SMTP server is listening, sending fails gracefully and
the demo keeps working. The message body includes only the minimum (concept,
amount, creditor organization) — never the student's registro civil.
"""
from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage

SMTP_HOST = os.environ.get("SMTP_HOST", "localhost")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "1025"))
FROM_ADDR = os.environ.get("REPORTH_FROM", "cobros@reporth.local")


def send_charge(to_email: str, parent_name: str, org_name: str, concept: str, amount: float) -> bool:
    """Send one charge email. Returns True if delivered to the local SMTP."""
    msg = EmailMessage()
    msg["Subject"] = f"Recordatorio de pago — {org_name}"
    msg["From"] = FROM_ADDR
    msg["To"] = to_email
    msg.set_content(
        f"Hola {parent_name},\n\n"
        f"Tiene un pago pendiente con {org_name}.\n"
        f"Concepto: {concept}\n"
        f"Monto: ${amount:,.0f}\n\n"
        f"Por favor regularice su situación para evitar inconvenientes.\n\n"
        f"Este es un mensaje automático de reporth."
    )
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=3) as smtp:
            smtp.send_message(msg)
        return True
    except OSError:
        # No local SMTP listening (or connection refused): fail soft.
        return False

"""
Email Sender utility for ue-metric-per-email.

Establishes an SMTP session with configurable connection security (STARTTLS,
SSL/TLS, or None), composes a MIME message with the CSV report as an attachment,
and delivers it to the configured recipients.

Raises domain-specific exceptions immediately; never swallows errors.
"""

import logging
import os
import smtplib
import socket
from email import encoders as email_encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

from exceptions import SMTPAuthenticationError, SMTPConnectionError, SMTPSendError

logger = logging.getLogger("UNV")

_DEFAULT_TIMEOUT: int = 30
_CONNECTION_SECURITY_STARTTLS: str = "STARTTLS"
_CONNECTION_SECURITY_SSL_TLS: str = "SSL/TLS"
_CONNECTION_SECURITY_NONE: str = "None"


def _get_timeout() -> int:
    """Read UE_HTTP_TIMEOUT from the environment, defaulting to 30 seconds."""
    raw = os.environ.get("UE_HTTP_TIMEOUT", "")
    if raw.strip().isdigit():
        return int(raw.strip())
    return _DEFAULT_TIMEOUT


def _build_message(
    smtp_host: str,
    smtp_username: Optional[str],
    to_addresses: List[str],
    cc_addresses: List[str],
    subject: str,
    body: str,
    csv_path: str,
    attachment_filename: str,
) -> MIMEMultipart:
    """
    Build a MIME multipart message with a plain-text body and a CSV attachment.

    The From address is the SMTP credential username when available; otherwise
    the fallback ``uac-metrics-report@<smtp_host>`` is used.

    Args:
        smtp_host:           SMTP server hostname (used for fallback From address).
        smtp_username:       SMTP credential user, or None when no credential is set.
        to_addresses:        Validated To recipient list.
        cc_addresses:        Validated CC recipient list (may be empty).
        subject:             Email subject line.
        body:                Plain-text email body.
        csv_path:            Filesystem path to the temporary CSV file.
        attachment_filename: The timestamped filename used as the attachment name.

    Returns:
        Fully constructed :class:`email.mime.multipart.MIMEMultipart` message.
    """
    from_address = smtp_username if smtp_username else f"uac-metrics-report@{smtp_host}"
    logger.debug("Building MIME message from=%s, to=%s, cc=%s", from_address, to_addresses, cc_addresses)

    msg = MIMEMultipart()
    msg["From"] = from_address
    msg["To"] = ", ".join(to_addresses)
    if cc_addresses:
        msg["Cc"] = ", ".join(cc_addresses)
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    with open(csv_path, "rb") as csv_file:
        attachment = MIMEBase("text", "csv")
        attachment.set_payload(csv_file.read())

    email_encoders.encode_base64(attachment)
    attachment.add_header(
        "Content-Disposition",
        "attachment",
        filename=attachment_filename,
    )
    msg.attach(attachment)

    logger.debug("MIME message built with attachment: %s", attachment_filename)
    return msg


def send_email(
    smtp_host: str,
    smtp_port: int,
    connection_security: str,
    smtp_username: Optional[str],
    smtp_password: Optional[str],
    to_addresses: List[str],
    cc_addresses: List[str],
    subject: str,
    body: str,
    csv_path: str,
    attachment_filename: str,
) -> None:
    """
    Compose and deliver the metrics CSV report email via SMTP.

    Establishes the SMTP session according to *connection_security*, optionally
    authenticates with the SMTP credential, and sends the composed message.

    Args:
        smtp_host:            SMTP server hostname.
        smtp_port:            SMTP server TCP port.
        connection_security:  One of ``"STARTTLS"``, ``"SSL/TLS"``, or ``"None"``.
        smtp_username:        SMTP credential user attribute, or None.
        smtp_password:        SMTP credential password attribute, or None.
        to_addresses:         Validated To recipient list.
        cc_addresses:         Validated CC recipient list (may be empty).
        subject:              Email subject line.
        body:                 Plain-text email body.
        csv_path:             Filesystem path to the temporary CSV report file.
        attachment_filename:  Timestamped filename used as the MIME attachment name.

    Raises:
        SMTPConnectionError:      On DNS, TCP, timeout, or TLS negotiation failures.
        SMTPAuthenticationError:  When the SMTP server rejects the credentials.
        SMTPSendError:            When recipients or the message are refused.
    """
    timeout = _get_timeout()
    logger.info(
        "Sending email via %s:%d (security=%s)", smtp_host, smtp_port, connection_security
    )

    all_recipients = to_addresses + cc_addresses
    msg = _build_message(
        smtp_host=smtp_host,
        smtp_username=smtp_username,
        to_addresses=to_addresses,
        cc_addresses=cc_addresses,
        subject=subject,
        body=body,
        csv_path=csv_path,
        attachment_filename=attachment_filename,
    )

    smtp_conn: smtplib.SMTP

    try:
        if connection_security == _CONNECTION_SECURITY_SSL_TLS:
            logger.debug("Opening implicit TLS (SMTPS) connection to %s:%d", smtp_host, smtp_port)
            smtp_conn = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=timeout)
        else:
            logger.debug("Opening plain SMTP connection to %s:%d", smtp_host, smtp_port)
            smtp_conn = smtplib.SMTP(smtp_host, smtp_port, timeout=timeout)

    except (socket.gaierror, socket.timeout, OSError, smtplib.SMTPException) as exc:
        logger.error("Failed to connect to SMTP server %s:%d: %s", smtp_host, smtp_port, str(exc))
        raise SMTPConnectionError(
            f"SMTP server {smtp_host} unreachable: {exc}"
        ) from exc

    try:
        if connection_security == _CONNECTION_SECURITY_STARTTLS:
            logger.debug("Issuing EHLO and upgrading to STARTTLS")
            smtp_conn.ehlo()
            try:
                smtp_conn.starttls()
                smtp_conn.ehlo()
            except smtplib.SMTPException as exc:
                logger.error("STARTTLS negotiation with %s failed: %s", smtp_host, str(exc))
                raise SMTPConnectionError(
                    f"TLS negotiation with {smtp_host} failed: {exc}"
                ) from exc

        if smtp_username and smtp_password:
            logger.info("Authenticating with SMTP server as %s", smtp_username)
            try:
                smtp_conn.login(smtp_username, smtp_password)
                logger.debug("SMTP authentication succeeded")
            except smtplib.SMTPAuthenticationError as exc:
                logger.error("SMTP authentication rejected by %s: %s", smtp_host, str(exc))
                raise SMTPAuthenticationError(
                    f"SMTP credentials rejected by {smtp_host}"
                ) from exc

        logger.info("Sending message to %d recipient(s)", len(all_recipients))
        try:
            refused = smtp_conn.sendmail(
                from_addr=msg["From"],
                to_addrs=all_recipients,
                msg=msg.as_string(),
            )
            if refused:
                refused_list = ", ".join(refused.keys())
                logger.error("Recipients refused by server: %s", refused_list)
                raise SMTPSendError(f"Recipient {refused_list} refused by server")
        except smtplib.SMTPRecipientsRefused as exc:
            refused_list = ", ".join(exc.recipients.keys())
            logger.error("All recipients refused: %s", refused_list)
            raise SMTPSendError(f"Recipient {refused_list} refused by server") from exc
        except smtplib.SMTPException as exc:
            logger.error("SMTP send failed: %s", str(exc))
            raise SMTPSendError(str(exc)) from exc

        logger.info("Email delivered successfully to %s", all_recipients)

    finally:
        try:
            smtp_conn.quit()
            logger.debug("SMTP connection closed")
        except smtplib.SMTPException:
            pass

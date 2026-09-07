"""Send Metrics Report Email action for ue-metric-per-email."""

import logging

from actions.output import ActionOutput
from exceptions import InvalidInputError
from fields.input import InputFields
from fields.output import OutputFields
from manager import ExtensionManager
from utility.csv_generator import write_csv_report
from utility.email_sender import send_email
from utility.input_validator import (
    parse_metric_name_filter,
    validate_cc_recipients,
    validate_controller_url,
    validate_smtp_port,
    validate_to_recipients,
)
from utility.metrics_client import apply_metric_filter, fetch_metrics
from utility.output_reporter import populate_output_fields, resolve_body, resolve_subject

logger = logging.getLogger("UNV")
extension_manager = ExtensionManager()


def send_metrics_report_email(input_data: InputFields) -> ActionOutput:
    """Fetch Universal Controller metrics, generate a CSV report, and send it by email.

    Execution flow:
        1. Validate and normalise all user inputs.
        2. Fetch Prometheus-format metrics from the UAC metrics endpoint.
        3. Parse and optionally filter metric families by name prefix.
        4. Generate the five-column CSV report as a managed temporary file.
        5. Establish an SMTP session and send the CSV as an email attachment.
        6. Populate OutputFields and build the ActionOutput result.

    Args:
        input_data: Validated input fields from UAC.

    Returns:
        ActionOutput carrying result data for STDOUT printing and Extension Output.

    Raises:
        InvalidInputError:       On malformed controller URL, invalid recipient
            address, or out-of-range SMTP port (exit code 20).
        UACConnectionError:      On network / TLS / non-2xx HTTP failures reaching
            the metrics endpoint (exit code 1).
        UACAuthenticationError:  On HTTP 401/403 from the metrics endpoint
            (exit code 1).
        MetricsParseError:       When the response body cannot be parsed as
            Prometheus exposition format (exit code 1).
        EmptyResultError:        When no samples remain after optional filtering
            (exit code 1).
        SMTPConnectionError:     On SMTP server unreachable / TLS failures
            (exit code 1).
        SMTPAuthenticationError: When SMTP credentials are rejected (exit code 1).
        SMTPSendError:           When recipients or the message are refused
            (exit code 1).
    """
    logger.info("Starting send_metrics_report_email action")
    logger.debug(
        "Input: action=%s, controller_url=%s, smtp_host=%s, smtp_port=%s,"
        " connection_security=%s, to_recipients=%s",
        input_data.action.value if input_data.action else None,
        input_data.controller_url.value if input_data.controller_url else None,
        input_data.smtp_host.value if input_data.smtp_host else None,
        input_data.smtp_port.value if input_data.smtp_port else None,
        input_data.connection_security.value if input_data.connection_security else None,
        input_data.to_recipients.value if input_data.to_recipients else None,
    )

    # Initialise real-time output tracker
    output_fields = OutputFields()
    logger.debug("Initialised OutputFields")

    # ------------------------------------------------------------------ #
    # Step 1: Input validation and normalisation                          #
    # ------------------------------------------------------------------ #
    logger.info("Validating and normalising inputs")

    controller_url_raw = input_data.controller_url.value if input_data.controller_url else ""
    controller_url = validate_controller_url(controller_url_raw)

    smtp_port_raw = input_data.smtp_port.value if input_data.smtp_port else 587
    validate_smtp_port(smtp_port_raw)
    smtp_port: int = smtp_port_raw

    to_raw = input_data.to_recipients.value if input_data.to_recipients else ""
    to_addresses = validate_to_recipients(to_raw)

    cc_raw = input_data.cc_recipients.value if input_data.cc_recipients else None
    cc_addresses = validate_cc_recipients(cc_raw)

    filter_raw = input_data.metric_name_filter.value if input_data.metric_name_filter else None
    prefixes = parse_metric_name_filter(filter_raw)

    smtp_host = input_data.smtp_host.value if input_data.smtp_host else ""
    if not smtp_host.strip():
        raise InvalidInputError("smtp_host must not be empty")

    connection_security = (
        input_data.connection_security.value if input_data.connection_security else "STARTTLS"
    )

    # UAC credential
    uac_username = input_data.uac_credential.user if input_data.uac_credential else ""
    uac_password = input_data.uac_credential.password if input_data.uac_credential else ""

    # SMTP credential (optional)
    smtp_username: str | None = None
    smtp_password: str | None = None
    if input_data.smtp_credential:
        smtp_username = input_data.smtp_credential.user
        smtp_password = input_data.smtp_credential.password

    # Email subject and body (apply defaults when blank)
    subject_raw = input_data.subject.value if input_data.subject else None
    body_raw = input_data.body.value if input_data.body else None
    subject = resolve_subject(subject_raw)
    body = resolve_body(body_raw)

    logger.info("Input validation completed")

    # ------------------------------------------------------------------ #
    # Steps 2–4: Fetch, parse, and filter metrics                        #
    # ------------------------------------------------------------------ #
    logger.info("Fetching metrics from controller: %s", controller_url)
    families = fetch_metrics(
        controller_url=controller_url,
        username=uac_username,
        password=uac_password,
    )
    logger.info("Fetched %d metric family/families", len(families))

    families = apply_metric_filter(families=families, prefixes=prefixes)
    metric_families_count = len(families)
    logger.info(
        "Metrics ready for CSV generation: %d families retained", metric_families_count
    )

    # ------------------------------------------------------------------ #
    # Steps 5–7: Generate CSV and send email (CSV cleaned up on exit)    #
    # ------------------------------------------------------------------ #
    logger.info("Generating CSV report and sending email")

    with write_csv_report(families) as (csv_path, attachment_filename, csv_rows_written):
        logger.debug(
            "CSV written: path=%s, filename=%s, rows=%d",
            csv_path,
            attachment_filename,
            csv_rows_written,
        )

        send_email(
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            connection_security=connection_security,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
            to_addresses=to_addresses,
            cc_addresses=cc_addresses,
            subject=subject,
            body=body,
            csv_path=csv_path,
            attachment_filename=attachment_filename,
        )
        logger.info("Email sent successfully")

        # ------------------------------------------------------------------ #
        # Step 8: Populate output fields and build result                     #
        # ------------------------------------------------------------------ #
        all_recipients = to_addresses + cc_addresses

        populate_output_fields(
            output_fields=output_fields,
            csv_rows_written=csv_rows_written,
            all_recipients=all_recipients,
        )

        logger.info(
            "send_metrics_report_email action completed: %d families, %d rows,"
            " %d recipient(s)",
            metric_families_count,
            csv_rows_written,
            len(all_recipients),
        )

        return ActionOutput(
            metric_families_parsed=metric_families_count,
            csv_rows_written=csv_rows_written,
            filter_applied=filter_raw,
            attachment_filename=attachment_filename,
            recipients=all_recipients,
        )

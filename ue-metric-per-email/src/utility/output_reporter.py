"""
Output Reporter utility for ue-metric-per-email.

Renders the STDOUT execution summary table, populates OutputFields, and builds
the Extension Output result / error objects for the action return value.
"""

import logging
from typing import Any, Dict, List, Optional

from tabulate import tabulate

from fields.output import OutputFields

logger = logging.getLogger("UNV")

_DEFAULT_SUBJECT: str = "UAC Controller Metrics Report"
_DEFAULT_BODY: str = (
    "Please find attached the current Universal Controller metrics report (CSV)."
)


def resolve_subject(subject: Optional[str]) -> str:
    """
    Return *subject* when it is a non-blank string, otherwise the default value.

    Args:
        subject: Raw subject value from the input field (may be None or blank).

    Returns:
        Non-empty subject string.
    """
    if subject and subject.strip():
        return subject.strip()
    return _DEFAULT_SUBJECT


def resolve_body(body: Optional[str]) -> str:
    """
    Return *body* when it is a non-blank string, otherwise the default value.

    Args:
        body: Raw body value from the input field (may be None or blank).

    Returns:
        Non-empty body string.
    """
    if body and body.strip():
        return body.strip()
    return _DEFAULT_BODY


def print_summary(
    metric_families_count: int,
    csv_rows_written: int,
    filter_applied: Optional[str],
    attachment_filename: str,
    recipients: List[str],
) -> None:
    """
    Print the STDOUT execution summary table using ``tablefmt="rounded_outline"``.

    Args:
        metric_families_count: Number of Prometheus metric families parsed.
        csv_rows_written:      Number of CSV data rows written (excluding header).
        filter_applied:        The metric name filter string as supplied by the
                               user, or None when no filter was applied.
        attachment_filename:   Timestamped CSV attachment filename.
        recipients:            Combined To + CC recipient list.
    """
    filter_display = filter_applied if filter_applied else "(none)"
    recipients_display = ", ".join(recipients)

    rows = [
        ["Metric Families Parsed", metric_families_count],
        ["CSV Rows Written", csv_rows_written],
        ["Filter Applied", filter_display],
        ["Attachment Filename", attachment_filename],
        ["Recipients", recipients_display],
    ]

    table = tabulate(rows, headers=["Item", "Value"], tablefmt="rounded_outline")
    print("\nUAC Metrics Report - Execution Summary")
    print(table)
    print("Metrics report email sent successfully.")
    logger.debug("STDOUT summary table printed")


def populate_output_fields(
    output_fields: OutputFields,
    csv_rows_written: int,
    all_recipients: List[str],
) -> None:
    """
    Populate the real-time output fields on the *output_fields* dataclass.

    Args:
        output_fields:    The :class:`fields.output.OutputFields` instance to update.
        csv_rows_written: Number of data rows written to the CSV file.
        all_recipients:   Combined To + CC recipient list.
    """
    logger.debug(
        "Populating output fields: metrics_row_count=%d, email_recipients=%s",
        csv_rows_written,
        all_recipients,
    )
    output_fields.update(
        metrics_row_count=str(csv_rows_written),
        email_recipients=", ".join(all_recipients),
    )


def build_result_object(
    metric_families_parsed: int,
    csv_rows_written: int,
    filter_applied: Optional[str],
    attachment_filename: str,
    recipients: List[str],
) -> Dict[str, Any]:
    """
    Build the ``result`` sub-object for the Extension Output JSON.

    Args:
        metric_families_parsed: Number of metric families parsed.
        csv_rows_written:       Number of CSV data rows.
        filter_applied:         Metric name filter string, or None.
        attachment_filename:    Timestamped CSV attachment filename.
        recipients:             Combined To + CC recipient list.

    Returns:
        Dictionary suitable for the ``result`` key of the Extension Output.
    """
    result: Dict[str, Any] = {
        "metric_families_parsed": metric_families_parsed,
        "csv_rows_written": csv_rows_written,
        "filter_applied": filter_applied or "",
        "attachment_filename": attachment_filename,
        "recipients": recipients,
    }
    logger.debug("Built result object: %s", result)
    return result


def build_error_object(
    category: str,
    description: str,
) -> Dict[str, Any]:
    """
    Build the ``error`` sub-object for the Extension Output JSON on failure paths.

    Args:
        category:    Short failure category string (e.g. ``"Connection Error"``).
        description: Detailed description of the failure.

    Returns:
        Dictionary suitable for the ``error`` key of the Extension Output.
    """
    error: Dict[str, Any] = {
        "category": category,
        "description": description,
    }
    logger.debug("Built error object: %s", error)
    return error

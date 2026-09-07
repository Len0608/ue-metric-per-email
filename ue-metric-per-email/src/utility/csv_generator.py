"""
CSV Report Generator utility for ue-metric-per-email.

Transforms parsed Prometheus metric families into a five-column CSV report
written to a context-managed temporary file.  The file is guaranteed to be
removed after the caller's with-block exits, on both success and exception paths.
"""

import csv
import logging
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime
from typing import Generator, List, Tuple

from prometheus_client.metrics_core import Metric

logger = logging.getLogger("UNV")

_CSV_HEADER: List[str] = [
    "Metric Name",
    "Type",
    "Labels",
    "Value",
    "Description",
]


def _format_labels(labels: dict) -> str:
    """
    Format a sample labels dictionary into the ``key=value; key=value`` string
    used as the Labels CSV column.

    Args:
        labels: Dictionary of label name → value from a prometheus_client Sample.

    Returns:
        Formatted string, or an empty string when *labels* is empty.
    """
    if not labels:
        return ""
    return "; ".join(f"{k}={v}" for k, v in labels.items())


def generate_attachment_filename() -> str:
    """
    Generate the timestamped CSV attachment filename based on the current
    local time.

    Returns:
        Filename string in the form ``uac_metrics_YYYY-MM-DD_HHMM.csv``.
    """
    now = datetime.now()
    filename = now.strftime("uac_metrics_%Y-%m-%d_%H%M.csv")
    logger.debug("Generated attachment filename: %s", filename)
    return filename


@contextmanager
def write_csv_report(
    families: List[Metric],
) -> Generator[Tuple[str, str, int], None, None]:
    """
    Context manager that writes the five-column CSV report to a temporary file
    and yields ``(file_path, attachment_filename, row_count)`` to the caller.

    The temporary file is deleted when the with-block exits regardless of
    whether an exception was raised.

    Usage::

        with write_csv_report(families) as (path, filename, row_count):
            # path is the on-disk temporary file path
            # filename is the timestamped attachment name
            # row_count is the number of data rows written
            send_email(path, filename)

    Args:
        families: List of parsed Prometheus metric families to render.

    Yields:
        Tuple of (temporary file path, attachment filename, data row count).
    """
    attachment_filename = generate_attachment_filename()
    logger.info("Writing CSV report to temporary file (attachment: %s)", attachment_filename)

    tmp_file = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".csv",
        prefix="uac_metrics_",
        delete=False,
        newline="",
        encoding="utf-8",
    )
    tmp_path = tmp_file.name

    try:
        writer = csv.writer(tmp_file)
        writer.writerow(_CSV_HEADER)

        row_count = 0
        for family in families:
            family_type = family.type
            family_description = family.documentation or ""
            for sample in family.samples:
                labels_str = _format_labels(sample.labels)
                writer.writerow([
                    sample.name,
                    family_type,
                    labels_str,
                    sample.value,
                    family_description,
                ])
                row_count += 1

        tmp_file.close()
        logger.info(
            "CSV report written: %d data rows to %s", row_count, tmp_path
        )
        yield tmp_path, attachment_filename, row_count

    finally:
        if not tmp_file.closed:
            tmp_file.close()
        try:
            os.unlink(tmp_path)
            logger.debug("Temporary CSV file removed: %s", tmp_path)
        except OSError as exc:
            logger.warning(
                "Could not remove temporary CSV file %s: %s", tmp_path, str(exc)
            )

"""ActionOutput dataclass for action return values."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from utility.output_reporter import build_result_object, print_summary

logger = logging.getLogger("UNV")


@dataclass
class ActionOutput:
    """Output from the send_metrics_report_email action.

    Carries all data needed to render STDOUT and build the Extension Output
    result object.

    Fields:
        metric_families_parsed: Number of Prometheus metric families retained
            after optional filtering.
        csv_rows_written:       Number of data rows written to the CSV attachment
            (excludes the header row).
        filter_applied:         The raw metric_name_filter string supplied by
            the user, or None when no filter was set.
        attachment_filename:    Timestamped CSV filename attached to the email.
        recipients:             Combined To + CC recipient list that the email
            was delivered to.
    """

    # Result data fields
    metric_families_parsed: Optional[int] = None
    csv_rows_written: Optional[int] = None
    filter_applied: Optional[str] = None
    attachment_filename: Optional[str] = None
    recipients: Optional[List[str]] = None

    # Control fields — no output-option choice fields exist in this template;
    # these are kept for structural consistency and default to empty lists.
    stdout_options: List[str] = None
    output_options: List[str] = None

    def __post_init__(self) -> None:
        """Initialise control fields with safe defaults."""
        if self.stdout_options is None:
            self.stdout_options = []
        if self.output_options is None:
            self.output_options = []
        if self.recipients is None:
            self.recipients = []

    def print_output(self) -> None:
        """Print the STDOUT execution summary table.

        Delegates to output_reporter.print_summary() using the stored result
        data.  Because this template defines no stdout_options control field,
        the summary is always printed.
        """
        logger.debug("Printing STDOUT execution summary")
        print_summary(
            metric_families_count=self.metric_families_parsed or 0,
            csv_rows_written=self.csv_rows_written or 0,
            filter_applied=self.filter_applied,
            attachment_filename=self.attachment_filename or "",
            recipients=self.recipients or [],
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for Extension Output (unv_output).

        Because this template defines no output_options control field, all
        result fields are always included.

        Returns:
            Dictionary suitable for the ``result`` key of the Extension Output.
        """
        logger.debug("Building Extension Output result object")
        return build_result_object(
            metric_families_parsed=self.metric_families_parsed or 0,
            csv_rows_written=self.csv_rows_written or 0,
            filter_applied=self.filter_applied,
            attachment_filename=self.attachment_filename or "",
            recipients=self.recipients or [],
        )

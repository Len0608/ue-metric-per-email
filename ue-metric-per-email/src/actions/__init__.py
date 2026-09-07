"""Actions module - Business logic implementations."""

from actions.output import ActionOutput
from actions.send_metrics_report_email import send_metrics_report_email
from manager import ExtensionManager

extension_manager = ExtensionManager()

# Map UAC action choice values to action functions
ACTION_MAPPER = {
    "Send Metrics Report Email": send_metrics_report_email,
}

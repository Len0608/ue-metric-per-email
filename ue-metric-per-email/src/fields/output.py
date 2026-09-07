"""OutputFields dataclass for real-time UI updates."""

from dataclasses import dataclass, asdict
from typing import Optional
from universal_extension import ui
from fields.types import Text


@dataclass
class OutputFields:
    """Real-time output fields for UAC UI updates.

    Fields sync with the UAC UI in real-time and are available
    in subsequent re-runs via InputFields.previous_output.

    metrics_row_count: Number of CSV rows (metric samples) written to the attachment.
    email_recipients: Combined To and CC recipients the email was sent to, comma-separated.
    """

    metrics_row_count: Optional[Text] = None
    email_recipients: Optional[Text] = None

    def update(self, **fields):
        """Update fields and sync with UAC UI in real-time.

        Args:
            **fields: Field names and values to update (strings will be wrapped in Text)
        """
        for field_name, field_value in fields.items():
            if hasattr(self, field_name):
                # Wrap string values in Text type
                if isinstance(field_value, str):
                    field_value = Text(field_value)
                setattr(self, field_name, field_value)
        ui.update_output_fields(fields)

    def to_dict(self) -> dict:
        """Get current fields as dictionary.

        Returns:
            Dict with non-None field values (Text wrappers unwrapped to strings)
        """
        result = {}
        for k, v in asdict(self).items():
            if v is not None:
                # Extract value from Text wrapper
                result[k] = v.value if isinstance(v, Text) else v
        return result

    def clear(self):
        """Reset all fields to None."""
        self.metrics_row_count = None
        self.email_recipients = None

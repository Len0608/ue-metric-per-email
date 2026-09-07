"""InputFields dataclass for input parsing and validation."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any, Dict, List, get_type_hints, Union, get_origin, get_args
from fields.output import OutputFields
from fields.types import (
    Text,
    Integer,
    Float,
    Boolean,
    SingleChoice,
    MultiChoice,
    Credential,
    Script,
    Array,
)
from exceptions import DataValidationError
from manager import ExtensionManager
from dataclasses import fields as dataclass_fields
from dataclasses import asdict

extension_manager = ExtensionManager()


@dataclass
class InputFields:
    """Input fields from UAC with validation.

    All user-defined fields are Optional[Type] = None.
    UAC Controller enforces required field validation at the template level;
    validation methods here perform semantic checks and collect errors before
    raising a single DataValidationError.

    Fields:
        action: Operation to perform (always "Send Metrics Report Email").
        controller_url: Base URL of the Universal Controller metrics endpoint.
        uac_credential: UAC username/password credential for HTTP Basic auth.
        metric_name_filter: Comma-separated metric name prefixes for filtering (optional).
        smtp_host: Hostname or IP of the SMTP server.
        smtp_port: TCP port of the SMTP server (1–65535, default 587).
        connection_security: SMTP connection security mode (STARTTLS, SSL/TLS, None).
        smtp_credential: SMTP username/password credential (optional for None security).
        to_recipients: Comma-separated list of primary recipient email addresses.
        cc_recipients: Comma-separated list of CC recipient email addresses (optional).
        subject: Subject line of the report email (optional, has default).
        body: Plain-text body of the report email (optional, has default).
        previous_output: Auto-populated from previous run OutputFields on re-runs.
        _skip_validation: Internal flag — bypass validation when True.
    """

    # User-defined fields - ALWAYS Optional, even if required in template.json
    action: Optional[SingleChoice] = None
    controller_url: Optional[Text] = None
    uac_credential: Optional[Credential] = None
    metric_name_filter: Optional[Text] = None
    smtp_host: Optional[Text] = None
    smtp_port: Optional[Integer] = None
    connection_security: Optional[SingleChoice] = None
    smtp_credential: Optional[Credential] = None
    to_recipients: Optional[Text] = None
    cc_recipients: Optional[Text] = None
    subject: Optional[Text] = None
    body: Optional[Text] = None

    # Previous run output (auto-populated for re-runs)
    previous_output: Optional[OutputFields] = None

    # Skip validation flag (internal use only)
    _skip_validation: bool = False

    @staticmethod
    def preprocess_fields(fields: dict) -> dict:
        """Preprocess raw UAC fields before creating InputFields.

        Converts raw UAC values to wrapper type instances:
        1. Filters out flattened credential fields (containing dots)
        2. Wraps values in appropriate wrapper types based on field type hints
        3. Extracts previous OutputFields if present (from re-runs)
        """

        processed = {}
        previous_output_data = {}

        # Get all OutputFields field names for detection
        output_field_names = {f.name for f in dataclass_fields(OutputFields)}

        # Get type hints to detect wrapper types
        type_hints = get_type_hints(InputFields)

        # Map field names to their wrapper types
        field_wrapper_types = {}
        for field_name, field_type in type_hints.items():
            # Get base type (unwrap Optional)
            base_type = field_type
            if get_origin(field_type) is Union:
                args = get_args(field_type)
                # Filter out NoneType to get the actual type
                non_none_args = [arg for arg in args if arg is not type(None)]
                if non_none_args:
                    base_type = non_none_args[0]

            field_wrapper_types[field_name] = base_type

        for key, value in fields.items():
            # Skip flattened credential fields (e.g., "uac_credential.token")
            if "." in key:
                continue

            # Check if this field belongs to OutputFields (previous run data)
            if key in output_field_names:
                previous_output_data[key] = value
                continue

            # Skip None values
            if value is None:
                processed[key] = value
                continue

            # Get the wrapper type for this field
            wrapper_type = field_wrapper_types.get(key)

            # Convert to appropriate wrapper type
            if wrapper_type == SingleChoice:
                # UAC sends as list, SingleChoice expects list
                if isinstance(value, list):
                    value = SingleChoice(_values=value)
                else:
                    value = SingleChoice(_values=[value])

            elif wrapper_type == MultiChoice:
                # UAC sends as list, MultiChoice expects list
                if isinstance(value, list):
                    value = MultiChoice(values=value)
                else:
                    value = MultiChoice(values=[value])

            elif wrapper_type == Script:
                # UAC sends as string path, Script expects Path object
                if isinstance(value, str):
                    value = Script(path=Path(value))

            elif wrapper_type == Credential:
                # UAC sends as dict, Credential expects kwargs
                if isinstance(value, dict):
                    value = Credential.from_dict(value)

            elif wrapper_type == Text:
                # Wrap string in Text
                if isinstance(value, str):
                    value = Text(value=value)

            elif wrapper_type == Integer:
                # Wrap int in Integer
                if isinstance(value, int):
                    value = Integer(value=value)

            elif wrapper_type == Float:
                # Wrap float in Float
                if isinstance(value, (int, float)):
                    value = Float(value=float(value))

            elif wrapper_type == Boolean:
                # Wrap bool in Boolean
                if isinstance(value, bool):
                    value = Boolean(value=value)

            elif wrapper_type == Array:
                # UAC sends as list of dicts, Array expects list of dicts
                if isinstance(value, list):
                    value = Array(pairs=value)

            processed[key] = value

        # If we found previous output fields, create OutputFields instance
        if previous_output_data:
            # Wrap Text fields in previous output
            for key, val in previous_output_data.items():
                if isinstance(val, str):
                    previous_output_data[key] = Text(value=val)
            processed["previous_output"] = OutputFields(**previous_output_data)

        return processed

    def to_dict(self) -> dict:
        """Convert to dict, unwrapping wrapper types and excluding internal fields.

        Returns:
            Dict with unwrapped field values, excluding _skip_validation and None previous_output
        """

        data = asdict(self)

        # Unwrap wrapper types to their raw values
        result = {}
        for key, value in data.items():
            # Skip internal fields
            if key == "_skip_validation":
                continue

            # Skip None previous_output
            if key == "previous_output" and value is None:
                continue

            # Unwrap wrapper types
            if isinstance(value, dict):
                # Check if it's a wrapper type dict representation
                if "_values" in value:  # SingleChoice
                    result[key] = value["_values"]
                elif "values" in value and len(value) == 1:  # MultiChoice
                    result[key] = value["values"]
                elif "value" in value and len(value) == 1:  # Text, Integer, Float, Boolean
                    result[key] = value["value"]
                elif "path" in value:  # Script
                    result[key] = str(value["path"])
                elif "pairs" in value:  # Array
                    result[key] = value["pairs"]
                elif "user" in value:  # Credential
                    result[key] = value
                else:
                    result[key] = value
            else:
                result[key] = value

        return result

    def __post_init__(self):
        """Validate fields after initialization."""
        if self._skip_validation:
            return

        # Call validation methods
        self._validate_action()
        self._validate_controller_url()
        self._validate_smtp_port()
        self._validate_connection_security()
        self._validate_to_recipients()
        self._validate_cc_recipients()

        # Raise once if errors collected
        if extension_manager.has_errors():
            raise DataValidationError(
                f"Validation failed with {extension_manager.error_count()} error(s)"
            )

    def _validate_action(self):
        """Validate action field (SingleChoice wrapper).

        Accepts only the single defined action value.
        """
        if self.action is not None:
            valid_actions = ["Send Metrics Report Email"]
            if self.action.value not in valid_actions:
                exc = DataValidationError(
                    f"Invalid action '{self.action.value}'. "
                    f"Valid actions: {', '.join(valid_actions)}"
                )
                extension_manager.add_error(exc, field="action", value=self.action.value)

    def _validate_controller_url(self):
        """Validate controller_url is a well-formed HTTP or HTTPS URL.

        Accepts http:// or https:// followed by at least one hostname character.
        A trailing slash is tolerated.
        """
        import re
        if self.controller_url is not None and self.controller_url.value:
            url = self.controller_url.value.strip()
            pattern = r'^https?://[^\s/]+'
            if not re.match(pattern, url):
                exc = DataValidationError(
                    f"Invalid controller_url '{url}'. "
                    "Must be a well-formed HTTP or HTTPS URL (e.g. https://ps1.stonebranchdev.cloud)"
                )
                extension_manager.add_error(exc, field="controller_url", value=url)

    def _validate_smtp_port(self):
        """Validate smtp_port is within the valid TCP port range (1–65535)."""
        if self.smtp_port is not None:
            port = self.smtp_port.value
            if not (1 <= port <= 65535):
                exc = DataValidationError(
                    f"Invalid smtp_port '{port}'. Must be between 1 and 65535."
                )
                extension_manager.add_error(exc, field="smtp_port", value=port)

    def _validate_connection_security(self):
        """Validate connection_security is one of the accepted values."""
        if self.connection_security is not None:
            valid_modes = ["STARTTLS", "SSL/TLS", "None"]
            if self.connection_security.value not in valid_modes:
                exc = DataValidationError(
                    f"Invalid connection_security '{self.connection_security.value}'. "
                    f"Valid options: {', '.join(valid_modes)}"
                )
                extension_manager.add_error(
                    exc,
                    field="connection_security",
                    value=self.connection_security.value,
                )

    def _validate_to_recipients(self):
        """Validate to_recipients contains at least one syntactically valid email address.

        Each address in the comma-separated list must match local-part@domain.
        Whitespace around each address is trimmed.
        """
        import re
        if self.to_recipients is not None and self.to_recipients.value:
            raw = self.to_recipients.value
            addresses = [addr.strip() for addr in raw.split(",")]
            addresses = [addr for addr in addresses if addr]
            if not addresses:
                exc = DataValidationError(
                    "to_recipients must contain at least one email address."
                )
                extension_manager.add_error(exc, field="to_recipients")
                return
            email_pattern = r'^[^@\s]+@[^@\s]+\.[^@\s]+'
            for addr in addresses:
                if not re.match(email_pattern, addr):
                    exc = DataValidationError(
                        f"Invalid recipient address '{addr}' in to_recipients."
                    )
                    extension_manager.add_error(exc, field="to_recipients", value=addr)

    def _validate_cc_recipients(self):
        """Validate cc_recipients when provided.

        Optional field. If non-empty, each comma-separated address must match
        local-part@domain. Whitespace around each address is trimmed.
        """
        import re
        if self.cc_recipients is not None and self.cc_recipients.value:
            raw = self.cc_recipients.value
            addresses = [addr.strip() for addr in raw.split(",")]
            addresses = [addr for addr in addresses if addr]
            email_pattern = r'^[^@\s]+@[^@\s]+\.[^@\s]+'
            for addr in addresses:
                if not re.match(email_pattern, addr):
                    exc = DataValidationError(
                        f"Invalid recipient address '{addr}' in cc_recipients."
                    )
                    extension_manager.add_error(exc, field="cc_recipients", value=addr)

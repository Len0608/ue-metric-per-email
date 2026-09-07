"""
Exceptions module template for UAC Universal Extensions.

This module provides:
- Base ExecutionError class
- Standard exception types (DataValidationError, ConnectionError, etc.)
- ErrorManager singleton for error collection
- Exit code conventions

CUSTOMIZE:
- Add custom exception types for your extension
- Modify ErrorManager methods if needed
"""
from typing import Optional

class ExecutionError(Exception):
    """
    The default error raised by an extension.

    All extension errors must inherit from it.

    Attrs:
        exit_code: The exit code of the extension (for UAC)
        message: The error message for status description
    """

    exit_code: int = 1
    message: str = "Execution Failed"

    def __init__(self, message: Optional[str] = None):
        """
        Initialize exception.

        Args:
            message: Optional message that will be appended to the default message.

        Note:
            To return result data with errors, use error_manager.set_result()
            before raising the exception.
        """
        if message:
            self.message = f"{self.message}: {message}"

        super().__init__(self.message)

class DataValidationError(ExecutionError):
    """Raised when an input field is invalid."""
    exit_code = 20
    message = "Data Validation Error"

class UnexpectedSystemError(ExecutionError):
    """Raised for unexpected system errors."""
    exit_code = 1
    message = "System Error"

class InvalidInputError(ExecutionError):
    """
    Raised when user-supplied input fails validation before any network activity.

    Use for:
    - Malformed controller URL (missing HTTP/HTTPS scheme or hostname)
    - Invalid or empty recipient email address in the To or CC list
    - SMTP port value outside the valid 1–65535 range

    Exit code 20 signals a non-transient user configuration error; no retry is
    expected until the input is corrected.
    """
    exit_code = 20
    message = "Validation Error"

class UACConnectionError(ExecutionError):
    """
    Raised when the Universal Controller metrics endpoint is unreachable or returns an error.

    Use for:
    - DNS resolution failure, TCP connection refused, network timeout
    - TLS handshake failure against the controller HTTPS endpoint
    - Any non-2xx HTTP response other than 401/403 (e.g., 500, 503)

    Exit code 1 — transient failures may resolve on retry.
    """
    exit_code = 1
    message = "Connection Error"

class UACAuthenticationError(ExecutionError):
    """
    Raised when the Universal Controller metrics endpoint returns HTTP 401 or 403.

    Use for:
    - Invalid UAC username or password supplied via the UAC credential
    - UAC user account lacks the required ops_admin or ops_service role

    Exit code 1 — requires correcting the credential or user role before retrying.
    """
    exit_code = 1
    message = "Authentication Error"

class MetricsParseError(ExecutionError):
    """
    Raised when the metrics endpoint response cannot be parsed as Prometheus exposition format.

    Use for:
    - prometheus-client text parser raises an exception on the response body
    - Response body is not valid Prometheus/OpenMetrics text

    Exit code 1 — indicates a system or configuration error on the controller side.
    """
    exit_code = 1
    message = "Parse Error"

class EmptyResultError(ExecutionError):
    """
    Raised when no metric data remains after parsing and optional filtering.

    Use for:
    - Zero metric families were parsed from the response body
    - The metric name filter matched zero samples across all parsed families

    Exit code 1 — no email is sent when this exception is raised. The user
    should check the metric name filter and verify the UAC user role grants
    access to the metrics endpoint.
    """
    exit_code = 1
    message = "Data Error"

class SMTPConnectionError(ExecutionError):
    """
    Raised when the SMTP server is unreachable or the TLS negotiation fails.

    Use for:
    - DNS resolution failure or TCP connection refused to the SMTP host/port
    - SMTP connection timeout
    - TLS negotiation failure during STARTTLS upgrade or implicit SSL/TLS session

    Exit code 1 — transient failures may resolve on retry; persistent failures
    require correcting the smtp_host, smtp_port, or connection_security setting.
    """
    exit_code = 1
    message = "Connection Error"

class SMTPAuthenticationError(ExecutionError):
    """
    Raised when the SMTP server rejects the provided SMTP credentials.

    Use for:
    - Username or password in smtp_credential rejected by the SMTP server
    - Server requires authentication but credentials were not supplied

    Exit code 1 — requires correcting the smtp_credential before retrying.
    """
    exit_code = 1
    message = "Authentication Error"

class SMTPSendError(ExecutionError):
    """
    Raised when the SMTP server refuses to deliver the email message.

    Use for:
    - One or more recipient addresses refused by the server
    - Message rejected due to server policy (size limit, content filter, etc.)

    Exit code 1 — requires reviewing recipient addresses or server relay policy.
    """
    exit_code = 1
    message = "Send Error"

class ExtensionRuntimeError(ExecutionError):
    """
    Raised for any unhandled exception that is not covered by a more specific error class.

    Use for:
    - Unexpected Python exceptions propagating from any layer of the extension
    - Bugs or unanticipated error conditions that do not map to a known failure mode

    Exit code 1 — review the exception detail in the Extension Output error object
    to diagnose the root cause.
    """
    exit_code = 1
    message = "Runtime Error"

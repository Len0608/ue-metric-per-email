"""
Input validation utility for ue-metric-per-email.

Validates and normalises all user-supplied fields before any network activity.
Raises InvalidInputError (exit code 20) immediately on the first validation failure.
"""

import logging
import re
import urllib.parse
from typing import List, Optional

from exceptions import InvalidInputError

logger = logging.getLogger("UNV")

# Simple email syntax pattern: non-empty local-part @ non-empty domain with at least one dot
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_controller_url(controller_url: str) -> str:
    """
    Validate that *controller_url* is a well-formed HTTP or HTTPS URL and
    return the URL with any trailing slash stripped.

    Args:
        controller_url: Raw value from the input field.

    Returns:
        Normalised base URL with no trailing slash.

    Raises:
        InvalidInputError: If the URL is missing the scheme, has an unsupported
            scheme, or has no hostname.
    """
    logger.debug("Validating controller_url: %s", controller_url)
    stripped = controller_url.strip()
    parsed = urllib.parse.urlparse(stripped)

    if parsed.scheme not in ("http", "https"):
        raise InvalidInputError(
            "controller_url must begin with http:// or https://"
            f" (got '{parsed.scheme or '<none>'}')"
        )

    if not parsed.hostname:
        raise InvalidInputError(
            "controller_url must contain a hostname"
            f" (got '{stripped}')"
        )

    normalised = stripped.rstrip("/")
    logger.debug("controller_url validated and normalised to: %s", normalised)
    return normalised


def parse_and_validate_recipients(raw: str, field_name: str) -> List[str]:
    """
    Split a comma-separated recipient string, trim whitespace from each entry,
    validate every address against the local-part@domain email syntax pattern,
    and return the cleaned list.

    For required fields the list must not be empty.  For optional fields an
    empty *raw* string returns an empty list without raising.

    Args:
        raw:        Raw comma-separated email address string from the input field.
        field_name: Human-readable field name used in error messages.

    Returns:
        List of trimmed, validated email address strings.  Empty list when *raw*
        is empty or all-whitespace.

    Raises:
        InvalidInputError: On any address that does not match the email pattern,
            or when *raw* is blank for a required recipient field.
    """
    logger.debug("Parsing recipients for field '%s': %s", field_name, raw)
    if not raw or not raw.strip():
        return []

    addresses: List[str] = []
    for part in raw.split(","):
        addr = part.strip()
        if not addr:
            continue
        if not _EMAIL_RE.match(addr):
            raise InvalidInputError(
                f"Invalid recipient address '{addr}' in {field_name}"
            )
        addresses.append(addr)

    logger.debug("Parsed %d address(es) from '%s'", len(addresses), field_name)
    return addresses


def validate_to_recipients(raw: str) -> List[str]:
    """
    Parse and validate the To recipients field.  The result must contain at
    least one address.

    Args:
        raw: Raw comma-separated To recipient string.

    Returns:
        Non-empty list of validated To addresses.

    Raises:
        InvalidInputError: When no valid addresses are found.
    """
    addresses = parse_and_validate_recipients(raw, "to_recipients")
    if not addresses:
        raise InvalidInputError(
            "to_recipients must contain at least one valid email address"
        )
    logger.debug("to_recipients validated: %s", addresses)
    return addresses


def validate_cc_recipients(raw: Optional[str]) -> List[str]:
    """
    Parse and validate the optional CC recipients field.  Returns an empty
    list when *raw* is None or blank.

    Args:
        raw: Raw comma-separated CC recipient string, or None.

    Returns:
        List of validated CC addresses (may be empty).

    Raises:
        InvalidInputError: On any syntactically invalid address in the list.
    """
    if not raw:
        return []
    addresses = parse_and_validate_recipients(raw, "cc_recipients")
    logger.debug("cc_recipients validated: %s", addresses)
    return addresses


def validate_smtp_port(port: int) -> int:
    """
    Confirm that *port* is within the valid TCP port range 1–65535.

    Args:
        port: Integer port value from the input field.

    Returns:
        The port value unchanged.

    Raises:
        InvalidInputError: When the port is outside 1–65535.
    """
    logger.debug("Validating smtp_port: %d", port)
    if not (1 <= port <= 65535):
        raise InvalidInputError(
            f"smtp_port must be between 1 and 65535 (got {port})"
        )
    return port


def parse_metric_name_filter(raw: Optional[str]) -> List[str]:
    """
    Parse the optional metric name filter string into a list of non-empty
    prefix strings, trimming whitespace from each entry.

    Args:
        raw: Raw comma-separated prefix string, or None.

    Returns:
        List of non-empty prefix strings.  Empty list when *raw* is None,
        blank, or all entries are empty after trimming.
    """
    logger.debug("Parsing metric_name_filter: %s", raw)
    if not raw or not raw.strip():
        return []

    prefixes: List[str] = [p.strip() for p in raw.split(",") if p.strip()]
    logger.debug("Parsed %d metric name prefix(es): %s", len(prefixes), prefixes)
    return prefixes

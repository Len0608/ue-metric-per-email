"""
Controller Metrics Client utility for ue-metric-per-email.

Fetches the Universal Controller Prometheus metrics endpoint and parses the
response into metric families.  Applies optional prefix-based filtering.

Raises domain-specific exceptions immediately; never swallows errors.
"""

import logging
import os
from typing import List, Optional

import requests
from prometheus_client.metrics_core import Metric
from prometheus_client.parser import text_string_to_metric_families

from exceptions import (
    EmptyResultError,
    MetricsParseError,
    UACAuthenticationError,
    UACConnectionError,
)

logger = logging.getLogger("UNV")

_DEFAULT_TIMEOUT: int = 30
_METRICS_PATH: str = "/resources/metrics"


def _get_timeout() -> int:
    """Read UE_HTTP_TIMEOUT from the environment, defaulting to 30 seconds."""
    raw = os.environ.get("UE_HTTP_TIMEOUT", "")
    if raw.strip().isdigit():
        return int(raw.strip())
    return _DEFAULT_TIMEOUT


def fetch_metrics(controller_url: str, username: str, password: str) -> List[Metric]:
    """
    Issue an HTTP GET to *{controller_url}/resources/metrics* with HTTP Basic
    authentication, parse the Prometheus text exposition format response, and
    return the resulting metric families.

    Args:
        controller_url: Normalised base URL (no trailing slash).
        username:       UAC credential user attribute.
        password:       UAC credential password attribute.

    Returns:
        Non-empty list of :class:`prometheus_client.metrics_core.Metric` objects.

    Raises:
        UACConnectionError:      On DNS/TCP/timeout/TLS failures or non-2xx,
                                 non-401/403 HTTP responses.
        UACAuthenticationError:  On HTTP 401 or 403.
        MetricsParseError:       When the response body cannot be parsed as
                                 Prometheus exposition format.
        EmptyResultError:        When the parsed result contains zero metric
                                 families.
    """
    endpoint = f"{controller_url}{_METRICS_PATH}"
    timeout = _get_timeout()
    logger.info("Fetching metrics from %s", endpoint)
    logger.debug("Request timeout: %d seconds", timeout)

    try:
        response = requests.get(
            endpoint,
            auth=(username, password),
            timeout=timeout,
            verify=True,
        )
        logger.debug("Response status: %d", response.status_code)
    except requests.ConnectionError as exc:
        logger.error("Connection to metrics endpoint failed: %s", str(exc))
        raise UACConnectionError(
            f"Unable to reach metrics endpoint at {endpoint}: {exc}"
        ) from exc
    except requests.Timeout as exc:
        logger.error("Request to metrics endpoint timed out: %s", str(exc))
        raise UACConnectionError(
            f"Request to {endpoint} timed out after {timeout}s"
        ) from exc
    except requests.RequestException as exc:
        logger.error("HTTP request failed: %s", str(exc))
        raise UACConnectionError(
            f"HTTP request to {endpoint} failed: {exc}"
        ) from exc

    if response.status_code in (401, 403):
        logger.error(
            "Metrics endpoint returned HTTP %d (authentication/authorisation failure)",
            response.status_code,
        )
        raise UACAuthenticationError(
            "UAC credentials rejected by controller or user lacks"
            " ops_admin/ops_service role"
        )

    if not response.ok:
        logger.error(
            "Metrics endpoint returned non-2xx status: %d", response.status_code
        )
        raise UACConnectionError(
            f"Metrics endpoint returned HTTP {response.status_code}"
        )

    logger.info("Metrics endpoint responded successfully; parsing response body")
    logger.debug("Response body length: %d bytes", len(response.text))

    try:
        families: List[Metric] = list(text_string_to_metric_families(response.text))
    except Exception as exc:
        logger.error("Failed to parse Prometheus exposition format: %s", str(exc))
        raise MetricsParseError(
            "Response could not be parsed as Prometheus exposition format"
        ) from exc

    if not families:
        logger.error("Parsed zero metric families from the metrics endpoint response")
        raise EmptyResultError(
            "No metrics matched — check the metric name filter and the UAC user's role"
        )

    logger.info("Parsed %d metric family/families from response", len(families))
    return families


def apply_metric_filter(
    families: List[Metric],
    prefixes: Optional[List[str]],
) -> List[Metric]:
    """
    Filter *families* to those whose name starts with at least one entry in
    *prefixes* (case-sensitive).  When *prefixes* is empty or None, all
    families are returned unchanged.

    After filtering, validates that at least one sample remains.

    Args:
        families: Parsed metric families (non-empty).
        prefixes: List of name prefixes to retain, or an empty list / None to
                  keep all families.

    Returns:
        Filtered (or original) list of metric families.

    Raises:
        EmptyResultError: When the filter reduces the sample count to zero.
    """
    if not prefixes:
        logger.debug("No metric name filter applied; retaining all %d families", len(families))
        return families

    logger.info("Applying metric name filter with %d prefix(es): %s", len(prefixes), prefixes)

    retained: List[Metric] = [
        family
        for family in families
        if any(family.name.startswith(prefix) for prefix in prefixes)
    ]

    sample_count = sum(len(family.samples) for family in retained)
    logger.debug(
        "Filter result: %d families retained, %d samples total",
        len(retained),
        sample_count,
    )

    if not retained or sample_count == 0:
        logger.error(
            "Metric name filter matched zero samples (prefixes: %s)", prefixes
        )
        raise EmptyResultError(
            "No metrics matched — check the metric name filter and the UAC user's role"
        )

    logger.info(
        "Filter applied: %d metric families retained (%d samples)",
        len(retained),
        sample_count,
    )
    return retained

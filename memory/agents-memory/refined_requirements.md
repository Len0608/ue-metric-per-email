# Universal Extension Requirements (Refined)

**Extension Name:** ue-metric-per-email (UAC Controller Metrics Email Report)
**Original Generated:** Not specified in original document
**Refined:** 2026-09-07
**Agent_id:** 1
**Requirements Completeness:** High Detail
**Target Platform:** Linux

# Table of Contents

1. [Overview](#overview)
2. [Actions](#actions)
   - 2.1 [Send Metrics Report Email](#21-send-metrics-report-email)
3. [Input Requirements](#input-requirements)
   - 3.1 [Universal Controller Connection Parameters](#31-universal-controller-connection-parameters)
   - 3.2 [Metrics Selection Parameters](#32-metrics-selection-parameters)
   - 3.3 [SMTP Connection Parameters](#33-smtp-connection-parameters)
   - 3.4 [Email Composition Parameters](#34-email-composition-parameters)
4. [Output Requirements](#output-requirements)
5. [Authentication Requirements](#authentication-requirements)
6. [Environment Variables](#environment-variables)
7. [Operational Behavior Section](#operational-behavior-section)
8. [Implementation Notes](#implementation-notes)
   - 8.1 [Python Compatibility](#python-compatibility)
   - 8.2 [Target Platform](#target-platform)
   - 8.3 [Third-Party Services and Tools Section](#third-party-services-and-tools-section)
   - 8.4 [Error Handling](#error-handling)
   - 8.5 [Resource Cleanup](#resource-cleanup)
9. [Requirements Summary](#requirements-summary)
10. [Document Change History](#document-change-history)
11. [References](#references)

# Overview

This document defines the complete, refined requirements for a Universal Extension that reports Universal Controller metrics by email.

**Integration Purpose:** The extension fetches the Prometheus-format metrics exposed by the Stonebranch Universal Controller metrics endpoint (`{controller_url}/resources/metrics`), authenticating with UAC credentials, parses the metric data, transforms it into a human-readable CSV file, and sends that CSV as an email attachment to configured recipients via a standard SMTP server.

# Actions

## 1 Send Metrics Report Email

**Functional Requirements:**

1. The extension shall retrieve metrics from the Universal Controller metrics endpoint at `{controller_url}/resources/metrics` over HTTP(S), authenticating with HTTP Basic authentication using the configured UAC credential.
2. The UAC user referenced by the credential must hold the `ops_admin` or `ops_service` role; this is a documented precondition for accessing the metrics endpoint.
3. The extension shall parse the Prometheus/OpenMetrics text exposition format returned by the endpoint into metric families with their samples, labels, types, and HELP descriptions.
4. If a Metric Name Filter is provided, only metric families whose names start with one of the given comma-separated prefixes shall be included in the CSV. If the filter is empty, all metrics shall be included.
5. The extension shall generate a CSV file with one row per metric sample and exactly the following columns:
   - **Metric Name**
   - **Type** (gauge/counter/etc.)
   - **Labels** (formatted as `key=value; key=value`)
   - **Value**
   - **Description** (from the metric family's HELP text)
6. The CSV attachment filename must be timestamped (e.g., `uac_metrics_2026-09-07_1030.csv`) so recurring scheduled runs produce distinguishable files.
7. The extension shall send the CSV as a MIME attachment in an email delivered through an SMTP server, using the configured recipients, subject, and body.
8. The SMTP connection must support three connection security modes selected via a choice field: STARTTLS (default), SSL/TLS (implicit TLS), and None (unauthenticated/unencrypted relay for development and internal-relay use only).
9. When SMTP authentication is in use, the extension shall authenticate to the SMTP server with the username/password from the SMTP credential.
10. If the endpoint returns no parseable metrics, or the Metric Name Filter matches nothing, the task must fail with a descriptive status; no email shall be sent in this case.
11. The CSV file must exist only as the email attachment: it shall be created as a temporary file and cleaned up after sending; it must not be persisted to the Agent filesystem.
12. On completion, the extension shall report results via STDOUT summary, output-only fields, and Extension Output JSON as defined in the Output Requirements section.

# Input Requirements

## 3.1 Universal Controller Connection Parameters

- **Controller URL** (Text Field, required): Base URL of the Universal Controller whose metrics endpoint will be called.
  - Example: `https://ps1.stonebranchdev.cloud`
  - Applicability: Send Metrics Report Email
  - Default Value: None

- **UAC Credential** (Credential Field, required): UAC username/password credential used for HTTP Basic authentication against the metrics endpoint. Mapping: username → `user`, password → `password` (single source of truth; no fallback logic). The UAC user must hold the `ops_admin` or `ops_service` role.
  - Example: A UAC credential whose user is a service account with the `ops_service` role
  - Applicability: Send Metrics Report Email
  - Default Value: None

## 3.2 Metrics Selection Parameters

- **Metric Name Filter** (Text Field, optional): Comma-separated list of metric name prefixes. If provided, only metric families whose names start with one of the given prefixes are included in the CSV. If empty, all metrics are included.
  - Example: `uc_` (includes only UAC business metrics, excluding JVM internals)
  - Applicability: Send Metrics Report Email
  - Default Value: Empty (all metrics included)

## 3.3 SMTP Connection Parameters

- **SMTP Host** (Text Field, required): Hostname of the SMTP server used to send the email.
  - Example: `smtp.example.com`
  - Applicability: Send Metrics Report Email
  - Default Value: None

- **SMTP Port** (Integer Field, required): TCP port of the SMTP server.
  - Example: `587`
  - Applicability: Send Metrics Report Email
  - Default Value: `587`

- **Connection Security** (Choice Field, required): SMTP connection security mode.
  - Available options:
    - **STARTTLS** (default): Encrypted submission via STARTTLS (standard submission profile, typically port 587)
    - **SSL/TLS**: Implicit TLS (SMTPS, typically port 465)
    - **None**: Unauthenticated/unencrypted relay (typically port 25) — for development and internal-relay use only; traffic is sent in cleartext
  - Default presented option: **STARTTLS**
  - Field visibility impact: The SMTP Credential is required whenever authentication is in use; it is optional when Connection Security allows an anonymous relay (None).
  - Applicability: Send Metrics Report Email

- **SMTP Credential** (Credential Field, conditionally required): SMTP username/password credential. Mapping: username → `user`, password → `password`. Required whenever SMTP authentication is in use; optional when the Connection Security mode allows an anonymous relay. This credential is distinct from the UAC Credential.
  - Example: A credential holding the mailbox/service account used for authenticated submission
  - Applicability: Send Metrics Report Email
  - Default Value: None

## 3.4 Email Composition Parameters

- **To Recipients** (Text Field, required): Comma-separated list of primary recipient email addresses.
  - Example: `ops-team@example.com, manager@example.com`
  - Applicability: Send Metrics Report Email
  - Default Value: None

- **CC Recipients** (Text Field, optional): Comma-separated list of CC recipient email addresses.
  - Example: `audit@example.com`
  - Applicability: Send Metrics Report Email
  - Default Value: None

- **Subject** (Text Field, optional with default): Subject line of the email.
  - Example: `UAC Controller Metrics Report`
  - Applicability: Send Metrics Report Email
  - Default Value: `UAC Controller Metrics Report`

- **Body** (Large Text Field, optional): Short email body text.
  - Example: A brief note stating that the attached CSV contains the current UAC Controller metrics
  - Applicability: Send Metrics Report Email
  - Default Value: Optional short default text

## Output-Only Fields

- **Metrics Row Count** (Text Field, Output Only): Number of CSV rows (metric samples) written to the attachment.
- **Email Recipients** (Text Field, Output Only): The recipients the email was sent to.

# Output Requirements

**On Success:**

- Return code: `0`
- Success condition: Metrics were fetched and parsed, the CSV was generated, and the email was accepted by the SMTP server.
- Status description: A success status indicating the metrics report email was sent (e.g., `SUCCESS: Metrics report sent to <recipients>` — illustrative, non-binding example).
- Output-only fields:
  - **Metrics Row Count** (Text, Output Only): Number of CSV rows written
  - **Email Recipients** (Text, Output Only): Recipients of the sent email
- Extension output (JSON): A `result` object containing metrics counts, the filter applied, the attachment filename, and the recipients. Illustrative example (non-binding):

  ```json
  {
    "result": {
      "metric_families_parsed": 42,
      "csv_rows_written": 315,
      "filter_applied": "uc_",
      "attachment_filename": "uac_metrics_2026-09-07_1030.csv",
      "recipients": ["ops-team@example.com"]
    }
  }
  ```

- STDOUT output: A short, human-readable execution summary table containing: metric families parsed, CSV rows written, recipients, and attachment filename. The full metric dump must not be written to STDOUT.
- Success Criteria:
  1. The metrics endpoint responded successfully and the response was parsed.
  2. At least one metric sample remained after applying the Metric Name Filter.
  3. The CSV file was generated with the specified five-column structure.
  4. The email with the CSV attachment was accepted by the SMTP server.

**On Error:**

- Failure Scenarios:

  1. **UAC Connection Error** — The Controller metrics endpoint is unreachable or returns an HTTP error.
     - Root causes: wrong Controller URL, network issues, Controller down
     - Return code: `1`
     - Status description pattern: `Connection Error: <description>`
     - Extension output: `error` object describing the failure
  2. **UAC Authentication Error** — The Controller rejects the UAC credentials or the user lacks the required role.
     - Root causes: invalid UAC credentials; UAC user missing the `ops_admin`/`ops_service` role
     - Return code: `1`
     - Status description pattern: `Authentication Error: <description>` (e.g., `Authentication Error: UAC credentials rejected by controller`)
     - Extension output: `error` object describing the failure
  3. **Parse Error** — The endpoint response cannot be parsed as Prometheus exposition format.
     - Root causes: unexpected/invalid response content from the endpoint
     - Return code: `1`
     - Status description pattern: `<Error Category>: <Description>`
     - Extension output: `error` object describing the failure
  4. **Empty Result (Data Error)** — The endpoint returns no parseable metrics, or the Metric Name Filter matches nothing. No email is sent.
     - Root causes: wrong URL, insufficient UAC user role, over-restrictive filter
     - Return code: `1`
     - Status description: `Data Error: No metrics matched — check the metric name filter and the UAC user's role`
     - Extension output: `error` object describing the failure
  5. **SMTP Connection Error** — The SMTP server is unreachable or the connection/TLS negotiation fails.
     - Root causes: wrong SMTP host/port, network issues, TLS negotiation failure
     - Return code: `1`
     - Status description pattern: `Connection Error: <description>` (e.g., `Connection Error: SMTP server smtp.example.com unreachable`)
     - Extension output: `error` object describing the failure
  6. **SMTP Authentication Error** — The SMTP server rejects the SMTP credentials.
     - Root causes: invalid SMTP credentials
     - Return code: `1`
     - Status description pattern: `Authentication Error: <description>`
     - Extension output: `error` object describing the failure
  7. **SMTP Send Error** — The SMTP server refuses the message or recipients.
     - Root causes: rejected recipients, message rejected by server policy
     - Return code: `1`
     - Status description pattern: `<Error Category>: <Description>`
     - Extension output: `error` object describing the failure

- Status descriptions must follow the `<Error Category>: <Description>` format.
- Input Validation:
  - Input validation errors return code `20`.
  - Validation failures include: malformed Controller URL and invalid recipient format.
  - Detailed field-level validation rules beyond these are not specified at this stage.

# Authentication Requirements

Two distinct authentication contexts are supported:

1. **Universal Controller access:** HTTP Basic authentication with a UAC username/password credential (single Credential Field; username → `user`, password → `password`). The UAC user must hold the `ops_admin` or `ops_service` role.
2. **SMTP submission:** Username/password authentication with a separate SMTP Credential Field (username → `user`, password → `password`), used together with the selected Connection Security mode (STARTTLS by default, SSL/TLS, or None). The SMTP credential is required whenever authentication is in use and optional when the mode allows an anonymous relay.

TLS certificate verification for the Controller HTTPS connection is enabled by default.

# Environment Variables

- **UE_HTTP_TIMEOUT** (seconds, default `30`): Timeout applied to both the UAC metrics HTTP call and the SMTP connection.
- **REQUESTS_CA_BUNDLE** (standard `requests` variable): Supported for Universal Controller installations using self-signed or private-CA certificates. Public cloud Controller instances work out of the box; TLS certificate verification remains enabled by default.

# Operational Behavior Section

**Dynamic Choice Fields:**
None. All choice fields (Connection Security) use static values.

**Cancel Action:**
Not specified in the source documents. Standard task cancellation behavior applies.

**Re-run Capability:**
Not specified in the source documents. The timestamped attachment filename ensures recurring or repeated runs produce distinguishable files.

**Progress Reporting:**
STDOUT provides a short, human-readable execution summary table (metric families parsed, CSV rows written, recipients, attachment filename). No progress bar requirement is specified.

**Dynamic Commands:**
None specified.

# Implementation Notes

## Python Compatibility

Not specified specifically. Targeting compatibility for 3.11.

## Target Platform

Target UAC agent platform: **Linux** (from the environment build platform record; not stated in the original requirements text). C extension modules with a confirmed `manylinux_2_17_x86_64` wheel are viable in addition to pure-Python modules. In practice, all agreed modules are pure-Python, so the bundle is platform-agnostic.

## Third-Party Services and Tools Section

- **Stonebranch Universal Controller (metrics Web Service)**
  - Short Description: Source system exposing Prometheus-format metrics at `{controller_url}/resources/metrics`; requires a user with the `ops_admin` or `ops_service` role.
  - Version constraints: None specified.
  - Integration approach: HTTPS request with HTTP Basic authentication using the UAC credential; response parsed from the Prometheus/OpenMetrics text exposition format.

- **SMTP Server (corporate or cloud mail relay)**
  - Short Description: Mail infrastructure (e.g., Microsoft 365, Google Workspace, on-premise relay) that accepts and delivers the report email.
  - Version constraints: None specified.
  - Integration approach: SMTP submission via Python's standard library with configurable connection security (STARTTLS default, SSL/TLS, None) and optional username/password authentication; CSV delivered as a MIME attachment.

**Agreed Python modules and versions:**

- **requests** (2.34.2, Pure Python): HTTP client for calling the Universal Controller metrics endpoint with HTTP Basic authentication.
- **prometheus-client** (0.26.0, Pure Python): Parses the Prometheus/OpenMetrics text exposition format into metric families, samples, labels, and HELP text.
- **tabulate** (0.10.0, Pure Python): Renders the human-readable STDOUT execution summary table.
- **Standard library (no pinning required):** `smtplib` + `email.message` (SMTP delivery with attachment), `csv` (CSV generation), `tempfile` (temporary CSV file handling).

## Error Handling

- High-level error categories: input validation errors; UAC connection errors; UAC authentication errors; parse errors; empty-result data errors; SMTP connection errors; SMTP authentication errors; SMTP send errors.
- Error handling strategy: Fail loudly with return code `1` for operational failures and `20` for input validation errors; status descriptions follow the `<Error Category>: <Description>` format; the Extension Output contains an `error` object on failure.
- Recovery mechanisms: None specified. An empty metric result is treated as a failure (no email is sent) so problems are visible in UAC rather than silently delivering empty reports.

## Resource Cleanup

- Cleanup scenarios: The generated CSV exists only as a temporary file used for the email attachment; it must be cleaned up after sending. Cleanup applies on both success and failure paths so no CSV files accumulate on the Agent filesystem.
- Strategy description: Temporary-file handling via the standard library `tempfile` pattern; the CSV is never persisted to the task's Runtime Directory.

# Requirements Summary

The extension implements a single action: fetch Prometheus-format metrics from the Universal Controller endpoint (`/resources/metrics`) using HTTP Basic authentication with a UAC credential (user requires the `ops_admin` or `ops_service` role), optionally filter metric families by comma-separated name prefixes, flatten every metric sample into a five-column human-readable CSV (Metric Name, Type, Labels, Value, Description), and send the CSV as a timestamped MIME attachment through an SMTP server (STARTTLS default on port 587, with SSL/TLS and None modes available, and a separate optional SMTP credential). Email composition supports required To recipients, optional CC, a defaulted subject, and an optional body. Success (exit `0`) means the email was accepted by the SMTP server; operational failures exit `1`, validation errors exit `20`, and an empty metric result is a failure with no email sent. Outputs comprise a STDOUT summary table, two output-only fields (Metrics Row Count, Email Recipients), and structured Extension Output JSON. Tunables are limited to the `UE_HTTP_TIMEOUT` and `REQUESTS_CA_BUNDLE` environment variables; the CSV is temporary and never persisted to the Agent.

# Document Change History

- Date not specified: Initial requirements (Low Detail)
- 2026-09-07: Comprehensive refinement based on 9 clarification questions and user feedback

# References

- Original Requirements Document: `memory/requirements.md`
- Original Requirements Q&A Document: `memory/agents-memory/requirements-QnA.md`

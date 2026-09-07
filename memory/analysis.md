# UAC Controller Metrics Email Report - Implementation Analysis

**Extension Name:** ue-metric-per-email
**Universal Template Name:** Ue Metric Per Email
**Target Platform:** Linux

---

## Extension Overview

The extension fetches Prometheus-format metrics from the Stonebranch Universal Controller metrics endpoint (`{controller_url}/resources/metrics`) using HTTP Basic authentication with a UAC credential, parses the text exposition format into metric families and samples, optionally filters metric families by comma-separated name prefixes, flattens every sample into a five-column human-readable CSV (Metric Name, Type, Labels, Value, Description), and sends the CSV as a timestamped MIME attachment through an SMTP server with configurable connection security (STARTTLS default, SSL/TLS, None) and optional SMTP authentication. The CSV exists only as a temporary file and is cleaned up after sending. An empty metric result is treated as a failure and no email is sent.

---

# Template Fields

## 1. Input Fields

**action**
- **Type**: Choice Field (Single-select)
- **Required When**: always
- **Options**:
  - Send Metrics Report Email - Fetch Universal Controller metrics, generate a CSV report, and send it by email
- **Default**: Send Metrics Report Email
- **Validation**:
  - Must be one of the options
- **Purpose**: Specifies the operation to perform

**controller_url**:
- **Type**: Text Field
- **Visible When**: always
- **Required When**: always
- **Validation**:
  - Must be a well-formed HTTP or HTTPS base URL (scheme `http://` or `https://` followed by a hostname); trailing slash is tolerated and stripped before use
- **Purpose**: Base URL of the Universal Controller whose metrics endpoint (`{controller_url}/resources/metrics`) will be called
- **Example**: `https://ps1.stonebranchdev.cloud`

**uac_credential**:
- **Type**: Credential Field
- **Visible When**: always
- **Required When**: always
- **Validation**:
  - Must reference a UAC credential with both `user` and `password` attributes populated
- **Purpose**: UAC username/password credential used for HTTP Basic authentication against the metrics endpoint. Mapping: username → `user`, password → `password` (single source of truth; no fallback logic). The UAC user must hold the `ops_admin` or `ops_service` role.

**metric_name_filter**:
- **Type**: Text Field
- **Visible When**: always. It is "not required" when it's visible
- **Required When**: never
- **Validation**:
  - Optional; if provided, a comma-separated list of non-empty metric name prefixes; whitespace around each prefix is trimmed
- **Purpose**: Comma-separated list of metric name prefixes. If provided, only metric families whose names start with one of the given prefixes are included in the CSV. If empty, all metrics are included.
- **Example**: `uc_`

**smtp_host**:
- **Type**: Text Field
- **Visible When**: always
- **Required When**: always
- **Validation**:
  - Must be a non-empty hostname or IP address
- **Purpose**: Hostname of the SMTP server used to send the email
- **Example**: `smtp.example.com`

**smtp_port**:
- **Type**: Int Field
- **Visible When**: always
- **Required When**: always
- **Default Value**: 587
- **Validation**:
  - Must be a value between 1 and 65535
- **Purpose**: TCP port of the SMTP server (typically 587 for STARTTLS, 465 for SSL/TLS, 25 for None)

**connection_security**:
- **Type**: Choice Field (Single-select)
- **Visible When**: always
- **Required When**: always
- **Options**:
  - STARTTLS - Encrypted submission via STARTTLS (standard submission profile, typically port 587)
  - SSL/TLS - Implicit TLS (SMTPS, typically port 465)
  - None - Unauthenticated/unencrypted relay (typically port 25) for development and internal-relay use only; traffic is sent in cleartext
- **Default Value**: STARTTLS
- **Validation**:
  - Must be one of the options
- **Purpose**: SMTP connection security mode controlling how the SMTP session is established and encrypted

**smtp_credential**:
- **Type**: Credential Field
- **Visible When**: always. It is "not required" when it's visible
- **Required When**: connection_security values are STARTTLS, SSL/TLS
- **Validation**:
  - When provided, must reference a UAC credential with both `user` and `password` attributes populated
- **Purpose**: SMTP username/password credential, distinct from the UAC credential. Mapping: username → `user`, password → `password`. Required whenever SMTP authentication is in use (STARTTLS and SSL/TLS modes); optional when Connection Security is None (anonymous relay). When provided in None mode, SMTP authentication is still attempted.

**to_recipients**:
- **Type**: Text Field
- **Visible When**: always
- **Required When**: always
- **Validation**:
  - Comma-separated list of one or more syntactically valid email addresses (each item must match `local-part@domain`); whitespace around each address is trimmed
- **Purpose**: Comma-separated list of primary recipient email addresses
- **Example**: `ops-team@example.com, manager@example.com`

**cc_recipients**:
- **Type**: Text Field
- **Visible When**: always. It is "not required" when it's visible
- **Required When**: never
- **Validation**:
  - Optional; if provided, comma-separated list of syntactically valid email addresses; whitespace around each address is trimmed
- **Purpose**: Comma-separated list of CC recipient email addresses
- **Example**: `audit@example.com`

**subject**:
- **Type**: Text Field
- **Visible When**: always. It is "not required" when it's visible
- **Required When**: never
- **Default Value**: `UAC Controller Metrics Report`
- **Validation**:
  - Optional free text; if empty at runtime the default value is used
- **Purpose**: Subject line of the report email
- **Example**: `UAC Controller Metrics Report`

**body**:
- **Type**: Text Field (Large)
- **Visible When**: always. It is "not required" when it's visible
- **Required When**: never
- **Default Value**: `Please find attached the current Universal Controller metrics report (CSV).`
- **Validation**:
  - Optional free text; if empty at runtime the default value is used
- **Purpose**: Plain-text body of the report email
- **Example**: `Please find attached the current Universal Controller metrics report (CSV).`

---

## 2. Output Fields

**metrics_row_count**:
- **Type**: Text Output
- **Purpose**: Number of CSV rows (metric samples) written to the attachment
- **Examples**: "315"

**email_recipients**:
- **Type**: Text Output
- **Purpose**: The recipients (To and CC combined) the email was sent to, comma-separated
- **Examples**: "ops-team@example.com, manager@example.com, audit@example.com"

---

## 3. Field Ordering

The task form uses a **2-column grid layout**. Fields can be displayed in two ways:

- **Full-width fields**: Span both columns (typically for dropdowns, credentials, or primary selections)
- **Half-width fields**: Occupy one column, allowing two fields side-by-side (typically for related pairs)

**Layout Rules:**
- Credential fields ALWAYS span full-width (both columns)
- Group related fields side-by-side when logical (e.g., country/city, latitude/longitude)
- Primary selection fields typically span full-width for prominence

**Field Order (Visual Layout):**

```
┌─────────────────────────────────────────┐
│                 action                  │  ← Full-width
├─────────────────────────────────────────┤
│              controller_url             │  ← Full-width
├─────────────────────────────────────────┤
│              uac_credential             │  ← Full-width (credential)
├─────────────────────────────────────────┤
│            metric_name_filter           │  ← Full-width
├─────────────────────┬───────────────────┤
│      smtp_host      │     smtp_port     │  ← Half-width pair
├─────────────────────┴───────────────────┤
│           connection_security           │  ← Full-width
├─────────────────────────────────────────┤
│             smtp_credential             │  ← Full-width (credential)
├─────────────────────┬───────────────────┤
│    to_recipients    │   cc_recipients   │  ← Half-width pair
├─────────────────────┴───────────────────┤
│                 subject                 │  ← Full-width
├─────────────────────────────────────────┤
│                  body                   │  ← Full-width
└─────────────────────────────────────────┘

Output-only fields (not part of the input layout):
metrics_row_count, email_recipients
```

---

# Actions

## Action 1: Send Metrics Report Email

**Description**: Fetches Prometheus-format metrics from the Universal Controller metrics endpoint, optionally filters metric families by name prefixes, generates a five-column CSV report as a temporary file, and sends it as a timestamped MIME attachment via SMTP to the configured recipients.

### Input Requirements

- **action**
- **controller_url**
- **uac_credential**
- **metric_name_filter**
- **smtp_host**
- **smtp_port**
- **connection_security**
- **smtp_credential**
- **to_recipients**
- **cc_recipients**
- **subject**
- **body**

### Execution Flow

**Step 1: Input Validation**
- Validate `controller_url` is a well-formed HTTP(S) URL (scheme + hostname). Strip any trailing slash.
- Parse `to_recipients` (and `cc_recipients` if provided) by splitting on commas and trimming whitespace; validate every address matches the `local-part@domain` email syntax pattern; the To list must contain at least one address.
- Validate `smtp_port` is within 1–65535 (template-level constraint; re-checked defensively).
- Parse `metric_name_filter` (if provided) by splitting on commas and trimming whitespace; discard empty entries. An all-empty result is treated as no filter.
- On any validation failure: exit code `20`, status description `Validation Error: <description>` (e.g., `Validation Error: Invalid recipient address 'foo@'`), Extension Output contains an `error` object. No network calls are made.

**Step 2: Fetch Metrics from Universal Controller**
- Read timeout from environment variable `UE_HTTP_TIMEOUT` (seconds, default `30`).
- Issue HTTP GET to `{controller_url}/resources/metrics` with HTTP Basic authentication using `uac_credential.user` / `uac_credential.password`. TLS certificate verification is enabled (the `requests` library honors `REQUESTS_CA_BUNDLE` for private-CA installations).
- Error branches:
  - Connection failure, DNS failure, TLS handshake failure, or timeout → **UAC Connection Error** (exit 1, `Connection Error: <description>`).
  - HTTP 401 or 403 → **UAC Authentication Error** (exit 1, `Authentication Error: UAC credentials rejected by controller or user lacks ops_admin/ops_service role`).
  - Any other non-2xx HTTP status → **UAC Connection Error** (exit 1, `Connection Error: Metrics endpoint returned HTTP <status>`).

**Step 3: Parse Prometheus Exposition Format**
- Parse the response body text with the `prometheus-client` text parser into metric families. For each family capture: name, type (gauge/counter/summary/histogram/untyped), HELP description, and all samples (sample name, labels dict, value).
- If parsing raises an exception → **Parse Error** (exit 1, `Parse Error: Response could not be parsed as Prometheus exposition format`).

**Step 4: Apply Metric Name Filter**
- If a filter list exists: keep only metric families whose family name starts with at least one of the prefixes (case-sensitive `startswith` comparison). If no filter: keep all families.
- Count remaining samples across all retained families.
- If zero metric families were parsed in Step 3, or zero samples remain after filtering → **Empty Result** (exit 1, `Data Error: No metrics matched — check the metric name filter and the UAC user's role`). No email is sent; skip to Step 9 (cleanup/reporting).

**Step 5: Generate CSV Temporary File**
- Compute the attachment filename from the current local time: `uac_metrics_<YYYY-MM-DD>_<HHMM>.csv` (e.g., `uac_metrics_2026-09-07_1030.csv`).
- Create a temporary file via the standard `tempfile` pattern (never in the task Runtime Directory as a persistent artifact).
- Write a header row plus one row per metric sample with exactly these five columns:
  1. **Metric Name** — the sample name
  2. **Type** — the metric family type (gauge/counter/etc.)
  3. **Labels** — the sample's labels formatted as `key=value; key=value` (empty string when the sample has no labels; keys in the order provided by the parser)
  4. **Value** — the sample value
  5. **Description** — the metric family's HELP text (empty string if absent)
- Record the number of data rows written (`csv_rows_written`).

**Step 6: Establish SMTP Connection**
- Read the same `UE_HTTP_TIMEOUT` value as the SMTP connection timeout.
- Branch on `connection_security`:
  - **STARTTLS**: open plain SMTP connection to `smtp_host:smtp_port`, issue EHLO, upgrade via STARTTLS, EHLO again.
  - **SSL/TLS**: open implicit-TLS SMTP connection (SMTPS) to `smtp_host:smtp_port`.
  - **None**: open plain SMTP connection with no TLS upgrade.
- If `smtp_credential` is provided (always the case for STARTTLS and SSL/TLS; optional for None): authenticate with `smtp_credential.user` / `smtp_credential.password`. In None mode with no credential, skip authentication.
- Error branches:
  - Socket/DNS/timeout/TLS negotiation failure → **SMTP Connection Error** (exit 1, `Connection Error: SMTP server <host> unreachable` or `Connection Error: TLS negotiation with <host> failed`).
  - Authentication rejected → **SMTP Authentication Error** (exit 1, `Authentication Error: SMTP credentials rejected by <host>`).

**Step 7: Compose and Send Email**
- Build a MIME message: From = the SMTP credential user when available, otherwise a fixed extension sender identity (`uac-metrics-report@<smtp_host>`); To = parsed To list; Cc = parsed CC list; Subject = `subject` (or its default); plain-text body = `body` (or its default).
- Attach the CSV file as a MIME attachment with the timestamped filename and MIME type `text/csv`.
- Send to the combined To + CC recipient list.
- Error branches:
  - All or some recipients refused, or message refused by server policy → **SMTP Send Error** (exit 1, `Send Error: <description>`, e.g., `Send Error: Recipient audit@example.com refused by server`).
- Close the SMTP connection.

**Step 8: Populate Outputs**
- Set output-only field `metrics_row_count` to the CSV data-row count.
- Set output-only field `email_recipients` to the comma-separated combined To + CC list.
- Print the STDOUT execution summary table (metric families parsed, CSV rows written, recipients, attachment filename). The full metric dump must NOT be written to STDOUT.
- Build the Extension Output `result` object (see Output Examples).
- Return exit code `0` with status description `SUCCESS: Metrics report sent to <comma-separated recipients>`.

**Step 9: Cleanup (always — success and failure paths)**
- Delete the temporary CSV file via context-managed temporary-file handling so it is removed on normal completion and on exceptions. The CSV is never persisted to the Agent filesystem.

### Output Examples

**STDOUT**:

```
UAC Metrics Report - Execution Summary
╭────────────────────────┬──────────────────────────────────────╮
│ Item                   │ Value                                │
├────────────────────────┼──────────────────────────────────────┤
│ Metric Families Parsed │ 42                                   │
│ CSV Rows Written       │ 315                                  │
│ Filter Applied         │ uc_                                  │
│ Attachment Filename    │ uac_metrics_2026-09-07_1030.csv      │
│ Recipients             │ ops-team@example.com                 │
╰────────────────────────┴──────────────────────────────────────╯
Metrics report email sent successfully.
```

**Extension Output result object (JSON)**:

The Extension Output also includes `exit_code`, `status_description`, and `invocation` elements that are added automatically during implementation time. Only the `result` element is shown below:

```json
{
  "result": {
    "metric_families_parsed": 42,
    "csv_rows_written": 315,
    "filter_applied": "uc_",
    "attachment_filename": "uac_metrics_2026-09-07_1030.csv",
    "recipients": ["ops-team@example.com", "manager@example.com", "audit@example.com"]
  }
}
```

On failure, the Extension Output contains an `error` object instead of `result`, describing the failure category and description.

### Success Criteria

1. The metrics endpoint responded successfully (HTTP 2xx) and the response was parsed as Prometheus exposition format.
2. At least one metric sample remained after applying the Metric Name Filter.
3. The CSV file was generated with the specified five-column structure and a timestamped filename.
4. The email with the CSV attachment was accepted by the SMTP server for the configured recipients.
5. The temporary CSV file was removed from the Agent filesystem.
6. Exit code `0` was returned with a success status description, both output-only fields populated, and the Extension Output `result` object emitted.

---

# Progress Reporting

Progress Reporting (percentage of completion report) is not required. STDOUT provides a short, human-readable execution summary table instead.

# Dynamic Choice Field Population

No Dynamic choice fields should be implemented. The only choice fields (`action`, `connection_security`) use static values defined at the template level.

# Cancellation Behavior

No specific cancellation logic is required; default cancellation logic is used (TERM Signal). Note: because the TERM signal is not caught, a temporary CSV file may be left behind by the operating system temp mechanism if cancellation occurs between CSV creation and cleanup; this is acceptable per the default-cancellation policy.

# Re-Run Behavior

No specific re-run logic is required; re-runs are treated as initial executions. The timestamped attachment filename (`uac_metrics_<YYYY-MM-DD>_<HHMM>.csv`) ensures recurring or repeated runs produce distinguishable files.

# Dynamic Commands

No Dynamic commands should be implemented.

---

# Utility Modules

## Required Utility Modules

### 1. Input Validator

**Purpose:** Validates and normalizes all user inputs before any network activity.

**Required Capabilities:**
- Validate `controller_url` as a well-formed HTTP(S) URL and strip a trailing slash
- Split comma-separated recipient strings, trim whitespace, and validate each address against the `local-part@domain` email syntax pattern
- Split the comma-separated metric filter string, trim whitespace, and drop empty entries
- Raise a validation exception (exit code 20) with a field-specific description on the first failure

**Used By:** Send Metrics Report Email (Step 1)

---

### 2. Controller Metrics Client

**Purpose:** Fetches and parses the Universal Controller Prometheus metrics endpoint.

**Required Capabilities:**

**Universal Controller Metrics API:**
- Issue HTTP GET to `{controller_url}/resources/metrics` with HTTP Basic authentication (UAC credential user/password)
- Apply the `UE_HTTP_TIMEOUT` timeout (default 30 seconds) and default-on TLS verification (honoring `REQUESTS_CA_BUNDLE`)
- Parse the Prometheus/OpenMetrics text exposition response into metric families with name, type, HELP description, and samples (name, labels, value)
- Apply prefix-based metric family filtering (case-sensitive `startswith` against a prefix list)

**Error Classification:**
- Connection/DNS/timeout/TLS failures → UAC connection exception
- HTTP 401/403 → UAC authentication exception
- Other non-2xx HTTP statuses → UAC connection exception (with status code in description)
- Parser exceptions → parse exception
- Zero families parsed or zero samples after filtering → empty-result data exception

**Used By:** Send Metrics Report Email (Steps 2–4)

---

### 3. CSV Report Generator

**Purpose:** Transforms parsed metric samples into the five-column CSV report as a managed temporary file.

**Required Capabilities:**
- Generate the timestamped attachment filename `uac_metrics_<YYYY-MM-DD>_<HHMM>.csv` from current local time
- Create the CSV as a context-managed temporary file (standard `tempfile` pattern) guaranteeing deletion on success and failure paths
- Write header row `Metric Name, Type, Labels, Value, Description` and one row per sample
- Format sample labels as `key=value; key=value` (empty string for label-less samples)
- Return the row count written

**Used By:** Send Metrics Report Email (Steps 5, 9)

---

### 4. Email Sender

**Purpose:** Delivers the CSV report as a MIME attachment via SMTP with configurable connection security.

**Required Capabilities:**

**SMTP Connection Management:**
- Establish the SMTP session per security mode: STARTTLS (plain connect then TLS upgrade), SSL/TLS (implicit TLS), None (plain, no upgrade)
- Apply the `UE_HTTP_TIMEOUT` value as the SMTP connection timeout
- Authenticate with the SMTP credential user/password when a credential is provided; skip authentication in None mode without a credential
- Close the connection deterministically after sending or on error

**Message Composition and Delivery:**
- Build a MIME message with From (SMTP credential user, or `uac-metrics-report@<smtp_host>` when no credential), To, Cc, Subject, plain-text body
- Attach the CSV file as `text/csv` with the timestamped filename
- Send to the combined To + CC recipient list

**Error Classification:**
- Socket/DNS/timeout/TLS negotiation failures → SMTP connection exception
- Authentication rejection → SMTP authentication exception
- Recipient or message refusal → SMTP send exception

**Used By:** Send Metrics Report Email (Steps 6–7)

---

### 5. Output Reporter

**Purpose:** Produces all user-facing and machine-readable outputs consistently.

**Required Capabilities:**
- Render the STDOUT execution summary table (metric families parsed, CSV rows written, filter applied, attachment filename, recipients) using tabular formatting with `tablefmt="rounded_outline"`
- Populate output-only fields `metrics_row_count` and `email_recipients`
- Build the Extension Output `result` object on success and the `error` object on failure

**Used By:** Send Metrics Report Email (Step 8 and all failure paths)

---

## Exception Mapping Strategy

**Validation Errors:**
- Malformed Controller URL → InvalidInputError (exit code 20, user input error)
- Invalid or empty recipient address format (To or CC) → InvalidInputError (exit code 20, user input error)
- SMTP port outside 1–65535 → InvalidInputError (exit code 20, user input error)

**UAC Communication Errors:**
- Metrics endpoint unreachable / DNS failure / timeout / TLS failure → UACConnectionError (exit code 1, transient — retry may succeed)
- Metrics endpoint returns non-2xx (other than 401/403) → UACConnectionError (exit code 1, transient or config)
- HTTP 401/403 from Controller (bad credentials or missing `ops_admin`/`ops_service` role) → UACAuthenticationError (exit code 1, user configuration error)

**Metrics Data Errors:**
- Response not parseable as Prometheus exposition format → MetricsParseError (exit code 1, system/config error)
- No metric families parsed, or filter matches zero samples → EmptyResultError (exit code 1, user configuration error; status `Data Error: No metrics matched — check the metric name filter and the UAC user's role`; no email is sent)

**SMTP Errors:**
- SMTP server unreachable / timeout / TLS negotiation failure → SMTPConnectionError (exit code 1, transient or config)
- SMTP credentials rejected → SMTPAuthenticationError (exit code 1, user configuration error)
- Recipients or message refused by server → SMTPSendError (exit code 1, user configuration or server policy error)

**Unexpected Errors:**
- Any unhandled exception → ExtensionRuntimeError (exit code 1, unexpected system error)

All failure status descriptions follow the `<Error Category>: <Description>` format, and the Extension Output contains an `error` object describing the failure.

**Exit Code Guide:**
- Exit code 20: User configuration or input error detected during validation (non-transient)
- Exit code 1: Operational failure — connection, authentication, parse, empty-result, or SMTP errors (some transient, retry may succeed)
- Exit code 0: Successful execution

---

# Dependencies

## 1. External API Dependencies

**1. Universal Controller Metrics Endpoint**
- **Endpoint**: `{controller_url}/resources/metrics`
- **Purpose**: Source of all Prometheus-format Universal Controller metrics rendered into the CSV report
- **Protocol**: HTTP/HTTPS (HTTPS recommended; TLS verification enabled by default)
- **Method**: HTTP GET
- **Authentication**: HTTP Basic authentication with a UAC username/password credential
- **Response Format**: Prometheus/OpenMetrics text exposition format (plain text)
- **Data Retrieved/Sent**: Metric families (name, type, HELP description) and samples (name, labels, value)

**General API Requirements:**
- The UAC user referenced by the credential must hold the `ops_admin` or `ops_service` role — a documented precondition for accessing the metrics endpoint
- Installations using self-signed or private-CA certificates must set `REQUESTS_CA_BUNDLE`; public cloud Controller instances work out of the box

The SMTP server is an external service dependency (not a Web API): any standard SMTP relay (Microsoft 365, Google Workspace, on-premise relay) accepting STARTTLS, implicit SSL/TLS, or plain submission, with optional username/password authentication.

---

## 2. Python version dependency

Python >= 3.11 (per the extension environment configuration).

## 3. Target Platform

Target UAC agent platform: **Linux**. C extension modules with a confirmed `manylinux_2_17_x86_64` wheel are viable in addition to pure-Python modules. In practice, all selected modules are pure-Python, so the dependency bundle is platform-agnostic.

## 4. Python Library Dependencies

**1. requests**
- **Purpose**: HTTP client for calling the Universal Controller metrics endpoint
- **Version**: 2.34.2 (pure Python, compatible with Python 3.11+)
- **Installation**: `pip install requests`
- **Usage**: Controller Metrics Client utility (Step 2 of the action)
- **Features Used**: GET requests with HTTP Basic authentication, timeout control, TLS verification with `REQUESTS_CA_BUNDLE` support, status-code and connection exception handling

**2. prometheus-client**
- **Purpose**: Parses the Prometheus/OpenMetrics text exposition format
- **Version**: 0.26.0 (pure Python, compatible with Python 3.11+)
- **Installation**: `pip install prometheus-client`
- **Usage**: Controller Metrics Client utility (Step 3 of the action)
- **Features Used**: Text-format parser producing metric families with samples, labels, types, and HELP documentation

**3. tabulate**
- **Purpose**: Renders the human-readable STDOUT execution summary table
- **Version**: 0.10.0 (pure Python, compatible with Python 3.11+)
- **Installation**: `pip install tabulate`
- **Usage**: Output Reporter utility (Step 8 of the action)
- **Features Used**: Table rendering with `tablefmt="rounded_outline"`

---

## 5. Python Standard Library Dependencies

**1. smtplib**
- **Purpose**: SMTP session management and message submission
- **Version**: Bundled with Python 3.11+ (no pinning required)
- **Installation**: Not required (standard library)
- **Usage**: Email Sender utility (Steps 6–7)
- **Features Used**: Plain SMTP client, STARTTLS upgrade, implicit-TLS SMTPS client, login authentication, message sending, SMTP exception hierarchy

**2. email.message**
- **Purpose**: MIME message composition
- **Version**: Bundled with Python 3.11+ (no pinning required)
- **Installation**: Not required (standard library)
- **Usage**: Email Sender utility (Step 7)
- **Features Used**: Message construction with headers (From/To/Cc/Subject), plain-text body, CSV file attachment with filename and `text/csv` MIME type

**3. csv**
- **Purpose**: CSV report generation
- **Version**: Bundled with Python 3.11+ (no pinning required)
- **Installation**: Not required (standard library)
- **Usage**: CSV Report Generator utility (Step 5)
- **Features Used**: Writer with header row and per-sample data rows, correct quoting of label/description values

**4. tempfile**
- **Purpose**: Temporary CSV file lifecycle management
- **Version**: Bundled with Python 3.11+ (no pinning required)
- **Installation**: Not required (standard library)
- **Usage**: CSV Report Generator utility (Steps 5 and 9)
- **Features Used**: Context-managed temporary file creation with guaranteed cleanup on success and failure paths

**5. datetime**
- **Purpose**: Timestamped attachment filename generation
- **Version**: Bundled with Python 3.11+ (no pinning required)
- **Installation**: Not required (standard library)
- **Usage**: CSV Report Generator utility (Step 5)
- **Features Used**: Current local time formatting into `YYYY-MM-DD_HHMM`

**6. re / urllib.parse**
- **Purpose**: Input validation
- **Version**: Bundled with Python 3.11+ (no pinning required)
- **Installation**: Not required (standard library)
- **Usage**: Input Validator utility (Step 1)
- **Features Used**: Email address syntax pattern matching (`re`), URL structure parsing (`urllib.parse`)

## 6. CLI Tool Dependencies

No Dependencies.

---

## 7. Environment Variables

**UE_HTTP_TIMEOUT** (integer seconds, optional):
- **Purpose**: Timeout applied to both the UAC metrics HTTP call and the SMTP connection
- **Default**: `30`
- **Usage**: Read once at execution start; passed as the request timeout to the Controller Metrics Client and as the connection timeout to the Email Sender
- **Examples**: `60`

**REQUESTS_CA_BUNDLE** (file path, optional):
- **Purpose**: Standard `requests` variable pointing to a CA certificate bundle for Universal Controller installations using self-signed or private-CA certificates
- **Default**: Not set (system/`certifi` CA bundle used; TLS verification remains enabled by default)
- **Usage**: Honored automatically by the `requests` library for the Controller metrics HTTPS call
- **Examples**: `/etc/ssl/certs/corporate-ca.pem`

# Requirements Completeness Assessment

**Classification: Low Detail**

The core intent is clear and compelling — the extension will fetch metrics from the Stonebranch Universal Controller metrics endpoint (`/resources/metrics`), transform the Prometheus-format data into a human-readable CSV, and deliver that CSV to a user by email, authenticating against the Controller with UAC credentials. That gives us a solid foundation: the target service, the data source, the transformation goal, and the delivery channel are all established.

To build the best solution, we'll shape a few key decisions together: how the email is actually sent (mail server details and its authentication), which metrics land in the CSV and how the CSV is structured, how the email itself is composed (recipients, subject, attachment), and what the task reports back to UAC on success and failure. The questions below are designed to settle those decisions quickly, with a recommended simple default for each.

# Platfrom Compatibility

The requirements document does not mention a target platform. The development environment record specifies the build platform as **Linux (x86_64)**, so `manylinux_2_17_x86_64` compatibility rules apply. In practice this is comfortable headroom: every module proposed below is pure-Python, so the resulting bundle is platform-agnostic and would also run on Windows agents if that ever becomes relevant.

**Platform Compatibility from Requirements**: Linux (from environment build platform record; not stated in the requirements text itself)
**Platform Compatibility Agreement**: [To be confirmed — proposed: Linux]

# Python modules and vesions

All researched modules are pure-Python — no C bindings, no manylinux wheel constraints, no platform risk. Email sending (`smtplib`, `email`), CSV writing (`csv`), and temporary file handling (`tempfile`) are covered by the Python standard library and need no pinning.

## Researched modules

**requests**
- **Module Purpose**: HTTP client used to call the Universal Controller metrics endpoint (`/resources/metrics`) with UAC credentials (HTTP Basic authentication)
- **Version**: 2.34.2
- **Type**: Pure Python

**prometheus-client**
- **Module Purpose**: Official Prometheus Python client; its `prometheus_client.parser` module robustly parses the Prometheus/OpenMetrics text exposition format returned by the metrics endpoint into metric families, samples, labels, and HELP text
- **Version**: 0.26.0
- **Type**: Pure Python

**tabulate**
- **Module Purpose**: Renders a concise, human-readable ASCII summary table on STDOUT (e.g., execution summary with `tablefmt="rounded_outline"`)
- **Version**: 0.10.0
- **Type**: Pure Python

**Standard library (no pinning required)**: `smtplib` + `email.message` (SMTP email delivery with attachment), `csv` (CSV generation), `tempfile` (temporary CSV file handling).

## Agreed Python Modules and Versions

[Placeholder — to be updated once the User provides answers. Each entry must include Module Name, Module Purpose, Version, and Type.]

# Question Rationale

The requirements establish *what* should happen end to end, but three functional areas need concrete decisions before analysis can proceed: (1) the email delivery mechanism is unspecified — the requirements name only UAC credentials, yet sending email requires a mail server and, usually, a second set of credentials; (2) the metrics endpoint returns a large mix of JVM internals and UAC business metrics, so "the content of the metric endpoint" needs a scoping decision and a defined CSV shape; (3) success/failure semantics and task outputs are undefined. Answering the questions below eliminates these uncertainties and makes the requirements concrete enough for implementation analysis.

# Clarifying Questions for Requirements Refinement

## Critical Decision Path Questions

**Question 1**: How should the extension send the email — via a standard SMTP server, or through a third-party email API service?
- **Options**:
  - **O1 — SMTP server (standard corporate or cloud relay)** using Python's built-in `smtplib`
  - **O2 — Third-party email API** (e.g., SendGrid, Mailgun, AWS SES API) using `requests`
- **Question Type**: New Discussion topic
- **Context & Resources**: The requirements specify email delivery but not the mechanism. SMTP is the universal standard and Python's standard library ([smtplib](https://docs.python.org/3/library/smtplib.html), [email.message](https://docs.python.org/3/library/email.message.html)) supports it fully — connection, TLS encryption, authentication, and MIME attachments — with zero extra dependencies. Email API services offer delivery analytics but tie the extension to one vendor and require API-specific integration.
- **Question Dependencies**: None. Question 6 is compatible only if Q1=O1.
- **Recommended Answer**: O1 — SMTP server via Python's standard library `smtplib`, with the CSV attached as a MIME attachment.
- **Rationale**: SMTP works with any mail infrastructure (Microsoft 365, Google Workspace, on-premise relays), needs no third-party module, and is the simplest solution that stays maintainable. Core-library solutions have the best backwards compatibility and lowest maintenance cost.
- **Trade-offs**: Optimizing for universality and zero extra dependencies; deprioritizing vendor-specific features such as delivery-event webhooks and template management, which are not needed for this use case.
- **Requirement Impact**: Adds input fields: SMTP Host (Text Field), SMTP Port (Integer Field, default 587), plus the security/authentication details settled in Question 6.
- **User's Answer**: O1 — SMTP server via Python's standard library `smtplib`, with the CSV attached as a MIME attachment.

**Question 2**: For retrieving metrics from the Universal Controller, is HTTP Basic authentication with a UAC username/password credential the intended method, and can we assume the UAC user holds the required `ops_admin` or `ops_service` role?
- **Options**:
  - **O1 — HTTP Basic authentication** with UAC username/password (single Credential Field)
  - **O2 — Personal Access Token** (UAC token mapped to the credential `token` attribute)
- **Question Type**: Clarification on existing requirement
- **Context & Resources**: The requirements state "uac credentials for accessing the endpoint." The Controller's Prometheus metrics Web Service at `{controller_url}/resources/metrics` requires a user with the `ops_admin` or `ops_service` role (see [Stonebranch Observability Start-Up Guide](https://docs.stonebranch.com/uac/observability-start-up-guide) and [Universal Controller — Provided Metrics](https://stonebranchdocs.atlassian.net/wiki/spaces/UC78/pages/1086325018/Universal+Controller+-+Provided+Metrics)). Both Basic auth and Personal Access Tokens are supported by the Controller REST layer; either maps cleanly to one UAC Credential Field. Retrieval would use `requests` 2.34.2.
- **Question Dependencies**: None.
- **Recommended Answer**: O1 — HTTP Basic authentication with a UAC username/password credential; document that the user needs the `ops_admin` or `ops_service` role.
- **Rationale**: Matches the requirement's wording ("uac credentials"), is the most common setup, and follows the single-source-of-truth credential mapping policy (username → `user`, password → `password`; no fallback logic).
- **Trade-offs**: Optimizing for simplicity and alignment with the stated requirement; deprioritizing token-based auth, which adds value mainly where password rotation policies make service passwords impractical. If tokens are preferred, the credential simply maps the token to the `token` attribute instead — a small, contained change.
- **Requirement Impact**: Adds input fields: Controller URL (Text Field, e.g., `https://ps1.stonebranchdev.cloud`) and UAC Credential (Credential Field). Adds a documented precondition on the UAC user's role.
- **User's Answer**: O1 — HTTP Basic authentication with a UAC username/password credential; document that the user needs the `ops_admin` or `ops_service` role.

**Question 3**: Should the CSV include all metrics returned by the endpoint, or should the task support scoping which metrics are included?
- **Options**:
  - **O1 — All metrics by default, with an optional name-filter field** (e.g., a comma-separated list of metric name prefixes such as `uc_`, left empty to include everything)
  - **O2 — Always all metrics**, no filtering capability
  - **O3 — Fixed subset only** (e.g., only UAC business metrics such as task, agent, and license metrics; JVM internals always excluded)
- **Question Type**: New Discussion topic
- **Context & Resources**: The endpoint returns a substantial mix: JVM internals (memory pools, garbage collection, class loading, buffer pools) alongside UAC business metrics (task instances, agents, licensing) — see [Universal Controller — Provided Metrics](https://stonebranchdocs.atlassian.net/wiki/spaces/UC78/pages/1086325018/Universal+Controller+-+Provided+Metrics). A "human readable csv" for business users likely benefits from filtering out JVM noise, but different recipients may want different slices. Parsing uses `prometheus_client.parser.text_string_to_metric_families` ([prometheus-client docs](https://prometheus.github.io/client_python/parser/)), which yields every metric family with its samples and labels, so filtering is a simple prefix match on metric names.
- **Question Dependencies**: None.
- **Recommended Answer**: O1 — include all metrics by default and add an optional "Metric Name Filter" input (Text Field, comma-separated name prefixes; empty = all metrics).
- **Rationale**: One optional field satisfies both "send me everything" and "send me only UAC business metrics" (filter `uc_`) without hardcoding assumptions about which metrics matter to the recipient. Empty-by-default keeps first use friction-free.
- **Trade-offs**: Optimizing for flexibility with minimal added complexity; deprioritizing advanced query capabilities (regex matching, label-based filtering), which can be added later if a real need emerges.
- **Requirement Impact**: Adds one optional input field: Metric Name Filter (Text Field). Requirements should state: "If a filter is provided, only metric families whose names start with one of the given prefixes are included in the CSV."
- **User's Answer**: O1 — include all metrics by default and add an optional "Metric Name Filter" input (Text Field, comma-separated name prefixes; empty = all metrics).

## CSV Format & Email Composition Questions

**Question 4**: Is the following CSV structure acceptable — one row per metric sample, with columns `Metric Name`, `Type`, `Labels`, `Value`, `Description`?
- **Options**:
  - **O1 — One row per sample** with columns: Metric Name, Type (gauge/counter/etc.), Labels (formatted `key=value; key=value`), Value, Description (from the metric's HELP text)
  - **O2 — Compact variant** without Type and Description columns (Metric Name, Labels, Value only)
- **Question Type**: New Discussion topic
- **Context & Resources**: Prometheus exposition format organizes data as metric families, each with typed samples carrying labels and a HELP description ([Prometheus exposition formats](https://prometheus.io/docs/instrumenting/exposition_formats/)). "Human readable" suggests preserving the HELP text — it explains what each metric means to a reader who doesn't know Prometheus. One row per sample is the natural flattening: a family with multiple label combinations (e.g., per-agent metrics) produces one row per combination.
- **Question Dependencies**: None.
- **Recommended Answer**: O1 — the five-column layout including Type and Description.
- **Rationale**: The HELP description is precisely what makes the CSV "human readable" for a business recipient; the marginal cost of two extra columns is negligible while the readability gain is significant.
- **Trade-offs**: Optimizing for standalone readability of the CSV; deprioritizing file compactness (Description text repeats across rows of the same family — irrelevant at these data volumes).
- **Requirement Impact**: Requirements should specify the exact column set and that each metric sample becomes one CSV row.
- **User's Answer**: O1 — the five-column layout including Type and Description.

**Question 5**: How should the email itself be composed — are the following defaults acceptable: required "To" recipients field (comma-separated), optional CC, configurable Subject with a sensible default, short configurable body text, and the CSV attached as a timestamped file (e.g., `uac_metrics_2026-09-07_1030.csv`)?
- **Options**:
  - **O1 — CSV as attachment** with the field set described above
  - **O2 — CSV content inline in the email body** (no attachment)
  - **O3 — Both** attachment and inline preview of the first N rows
- **Question Type**: New Discussion topic
- **Context & Resources**: The requirements say "send this csv per email to the user" but leave recipients, subject, body, and delivery form undecided. Attachments preserve the CSV as a usable file (opens directly in Excel and similar tools); inline CSV in a body is hard to read and breaks the file semantics. A timestamped filename makes recurring scheduled runs produce distinguishable files. Recipient fields map naturally to Text Fields; a multiline body maps to a Large Text Field.
- **Question Dependencies**: None.
- **Recommended Answer**: O1 — attachment with fields: To Recipients (Text Field, required, comma-separated), CC Recipients (Text Field, optional), Subject (Text Field, default e.g. "UAC Controller Metrics Report"), Body (Large Text Field, optional short default text), timestamped attachment filename.
- **Rationale**: An attachment is the form a CSV is meant to travel in — downstream the recipient can open, sort, and archive it. The default subject and body keep task definitions minimal while allowing customization.
- **Trade-offs**: Optimizing for recipient usability and minimal required inputs; deprioritizing inline previews, which add formatting complexity for little value since the STDOUT summary already gives operators visibility.
- **Requirement Impact**: Adds input fields: To Recipients (required), CC Recipients (optional), Subject (optional with default), Body (optional). Requirements should state the attachment filename convention.
- **User's Answer**: O1 — attachment with fields: To Recipients (Text Field, required, comma-separated), CC Recipients (Text Field, optional), Subject (Text Field, default e.g. "UAC Controller Metrics Report"), Body (Large Text Field, optional short default text), timestamped attachment filename.

**Question 6**: Which SMTP connection security and authentication mode should be the default?
- **Options**:
  - **O1 — STARTTLS on port 587 with username/password authentication** (SMTP credential via a second Credential Field)
  - **O2 — Implicit TLS (SMTPS) on port 465** with username/password authentication
  - **O3 — Unauthenticated / unencrypted relay on port 25** (internal relays and development environments only)
- **Question Type**: New Discussion topic
- **Context & Resources**: Modern mail services (Microsoft 365, Google Workspace, most corporate relays) require encrypted, authenticated submission — STARTTLS on 587 is the standard submission profile ([RFC 6409](https://datatracker.ietf.org/doc/html/rfc6409)); implicit TLS on 465 is equally secure and equally common. Some internal networks run open relays on port 25, useful for testing but transmitting in cleartext. A Choice Field for security mode with Conditional Requirement on the SMTP credential covers all three cleanly. **Security note:** O3 sends unencrypted traffic and should be clearly labeled for development/internal-relay use only.
- **Question Dependencies**: Question compatible only if Answer of Q1 indicates O1 (SMTP).
- **Recommended Answer**: O1 as the default — Connection Security choice field (values: STARTTLS [default], SSL/TLS, None) plus an SMTP Credential Field (username → `user`, password → `password`), with the credential required whenever authentication is in use. Supporting all three modes via the choice field is recommended since it costs little and covers development scenarios.
- **Rationale**: STARTTLS/587 with authentication is the secure production default that works with virtually every mail provider; exposing the mode as a choice field accommodates internal relays without compromising the secure default.
- **Trade-offs**: Optimizing for secure-by-default production readiness; deprioritizing nothing significant — the None option remains available and clearly labeled for development use.
- **Requirement Impact**: Adds input fields: Connection Security (Choice Field, default STARTTLS), SMTP Credential (Credential Field, optional when Connection Security allows anonymous relay). Requirements should note the second credential is distinct from the UAC credential.
- **User's Answer**: O1 as the default — Connection Security choice field (values: STARTTLS [default], SSL/TLS, None) plus an SMTP Credential Field (username → `user`, password → `password`), with the credential required whenever authentication is in use. Supporting all three modes via the choice field is recommended since it costs little and covers development scenarios.

## Functional Behavior & Output Questions

**Question 7**: Are the following success/failure semantics acceptable: exit code 0 when metrics are fetched, parsed, and the email is accepted by the mail server; exit code 1 for any operational failure (HTTP error, authentication failure, SMTP failure); exit code 20 for input validation errors; and a failure (not an empty email) if the endpoint returns no parseable metrics or the filter matches nothing?
- **Options**:
  - **O1 — As described**: empty metric set (after filtering) is a failure with a descriptive status; no email is sent
  - **O2 — Empty result still sends the email** with an empty CSV and exits 0 with a warning in the status description
- **Question Type**: New Discussion topic
- **Context & Resources**: Success and error conditions are not defined in the requirements. The recommended UAC convention is exit code 0 for success, 1 for operational failures, 20 for validation errors, with status descriptions in `<Error Category>: <Description>` format (e.g., `Authentication Error: UAC credentials rejected by controller`, `Connection Error: SMTP server smtp.example.com unreachable`). An empty metrics result almost always signals a problem (wrong URL, insufficient role, over-restrictive filter), so failing loudly protects recipients from silently receiving useless empty reports.
- **Question Dependencies**: None.
- **Recommended Answer**: O1 — empty result is a failure with status `Data Error: No metrics matched — check the metric name filter and the UAC user's role`; standard 0/1/20 exit code scheme.
- **Rationale**: The task's purpose is delivering a useful report; an empty CSV in an inbox is a silent failure that erodes trust in the report. Failing the task instance makes the problem visible where operators look — in UAC.
- **Trade-offs**: Optimizing for failure visibility and recipient trust; deprioritizing the edge case where a legitimately empty result should still notify — that scenario can be revisited if it arises in practice.
- **Requirement Impact**: Requirements should enumerate: success condition (email accepted by SMTP server), failure categories (UAC connection/auth, parse, empty result, SMTP connection/auth/send), and validation failures (malformed URL, invalid recipient format).
- **User's Answer**: O1 — empty result is a failure with status `Data Error: No metrics matched — check the metric name filter and the UAC user's role`; standard 0/1/20 exit code scheme.

**Question 8**: Are the following task outputs acceptable: STDOUT showing a short execution summary table (metric families parsed, CSV rows written, recipients, attachment filename); two output-only fields (`Metrics Row Count`, `Email Recipients`); Extension Output JSON containing a `result` object with metrics counts, filter applied, attachment filename, and recipients (an `error` object on failure); and the CSV existing only as the email attachment (not persisted to the Agent filesystem)?
- **Options**:
  - **O1 — As described** (CSV is temporary; cleaned up after sending via `tempfile`)
  - **O2 — Additionally persist the CSV** to the task's Runtime Directory on the Agent for downstream workflow tasks
- **Question Type**: New Discussion topic
- **Context & Resources**: The multi-channel output pattern separates concerns: STDOUT for the human operator (a compact `tabulate` summary — not the full metric dump, which would bloat the UAC database), 2–3 output-only fields for at-a-glance UI status, and machine-readable Extension Output JSON for downstream automation and auditing. Whether the CSV should outlive the email is a genuine functional choice: if a UAC workflow's later tasks need the file, it must be written to the Runtime Directory; if email is the sole consumer, a temporary file with automatic cleanup is cleaner.
- **Question Dependencies**: None.
- **Recommended Answer**: O1 — CSV as a temporary file only, with the described STDOUT summary, two output-only fields, and structured Extension Output.
- **Rationale**: The stated requirement is email delivery; keeping the file temporary avoids accumulating stale files on Agents and follows the temporary-file handling pattern. Full metric data never goes inline to STDOUT or Extension Output, keeping the UAC database lean.
- **Trade-offs**: Optimizing for a clean Agent filesystem and lean UAC storage; deprioritizing file reuse by downstream workflow tasks — if that need emerges, a boolean "Save CSV to Runtime Directory" field is a small additive change.
- **Requirement Impact**: Adds output-only fields: Metrics Row Count (Text Field, Output Only), Email Recipients (Text Field, Output Only). Requirements should specify the Extension Output `result`/`error` structure.
- **User's Answer**: O1 — CSV as a temporary file only, with the described STDOUT summary, two output-only fields, and structured Extension Output.

## Environment Variable Questions

**Question 9**: Are the following environment-variable-based tunables sufficient: `UE_HTTP_TIMEOUT` (seconds, default 30) applied to both the UAC metrics HTTP call and the SMTP connection, and standard `REQUESTS_CA_BUNDLE` support for Universal Controller installations using self-signed or private-CA certificates?
- **Options**:
  - **O1 — Yes**, environment variables with the stated defaults are sufficient
  - **O2 — Promote timeout to a visible input field** (Integer Field) instead of an environment variable
- **Question Type**: New Discussion topic
- **Context & Resources**: Timeouts are rarely tuned and have sensible defaults — exactly the profile that fits environment variables rather than template fields. `REQUESTS_CA_BUNDLE` is the well-established environment variable already honored by the `requests` library ([requests SSL docs](https://requests.readthedocs.io/en/latest/user/advanced/#ssl-cert-verification)), so no new variable is needed for private-CA scenarios; public cloud Controller instances (like the configured `stonebranchdev.cloud`) work out of the box via `certifi`. TLS certificate verification should remain enabled by default.
- **Question Dependencies**: None.
- **Recommended Answer**: O1 — `UE_HTTP_TIMEOUT` (default 30 seconds) plus documented support for the standard `REQUESTS_CA_BUNDLE`; no timeout field on the template.
- **Rationale**: Keeps the task form focused on what users actually decide per task (recipients, filter, subject) while retaining operational tunability for the rare environment that needs it. Reuses established variable names instead of inventing new ones.
- **Trade-offs**: Optimizing for a minimal, uncluttered task form; deprioritizing per-task-definition timeout visibility, which is rarely needed and remains adjustable via task-level environment variables.
- **Requirement Impact**: Requirements should document both variables, their defaults, and that TLS verification is on by default.
- **User's Answer**: O1 — `UE_HTTP_TIMEOUT` (default 30 seconds) plus documented support for the standard `REQUESTS_CA_BUNDLE`; no timeout field on the template.

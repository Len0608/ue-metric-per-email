# Integration Examples Reference

The following production-grade Stonebranch Universal Extension templates are provided as reference. Use them to guide field naming, type selection, credential design, and action structure.

## Field Type Reference

| Type       | When to use |
|------------|-------------|
| Choice     | Fixed enumeration — action modes, providers, protocols, regions |
| Credential | UAC Credential record reference — never store secrets inline |
| Text       | Free-form string — URLs, resource names, IDs, query strings |
| Script     | Multi-line editor — SQL, JSON payloads, shell snippets, prompts |
| Boolean    | Toggle flags — SSL verify, verbose logging, dry-run, wait mode |
| Integer    | Whole numbers — timeouts (s), retry counts, page sizes, ports |
| Float      | Decimal numbers — LLM temperature, top-p, penalty weights |
| Array      | Repeating key/value pairs — HTTP headers, env vars, parameters |

Design rules:
- Use one Credential field per authentication context (source vs. destination).
- Name credential fields clearly: `api_credential`, `sftp_credential`.
- Prefer Choice over Text for any field with a known fixed set of values.
- Use Integer for all numeric tuning knobs (timeout, retries, page size).
- Use Script only for multi-line content (payloads, queries, inline code).
- Output/status fields (Text) let operators capture results as UAC variables.

---

## Most Relevant Examples

### UDMG File Transfer — `ue-mft-transfer`
**Category:** File Transfer
**Description:** UDMG File Transfer Universal Extension
**Fields (28):**

| Field name | Type | Choices / Notes |
|------------|------|-----------------|
| `action` | Choice | GET, PUT, MGET, MPUT, LIST |
| `protocol` | Choice | SFTP, HTTPS, HTTP, PeSIT, PeSIT-TLS |
| `mft_server` | Text |  |
| `credentials` | Credential |  |
| `partner` | Choice |  |
| `user` | Text |  |
| `partner_account_dynamic` | Choice |  |
| `use_dynamic_partner_account` | Boolean | false |
| `file` | Text |  |
| `output` | Text |  |
| `rule` | Choice |  |
| `polling_interval` | Integer | 5 |
| `wait_for_completion` | Boolean | true |
| `max_file_to_monitor` | Integer | 100 |
| `transfer_date` | Text |  |
| `transfer_id` | Text |  |
| `status` | Text |  |
| `start` | Text |  |
| `stop` | Text |  |
| `step` | Text |  |
| `progress` | Integer |  |
| `transfer_progress` | Text |  |
| `error_code` | Text |  |
| `task_number` | Text |  |
| `error_msg` | Text |  |
| `local_file` | Text |  |
| `remote_file` | Text |  |
| `transfer_uuid` | Text |  |


### SQL ODBC — `ue-sql-odbc`
**Category:** Database
**Description:** SQL ODBC
**Fields (34):**

| Field name | Type | Choices / Notes |
|------------|------|-----------------|
| `action` | Choice | Run SQL Script |
| `database_type` | Choice | MySQL, Postgres, MS SQL Server, Oracle, SAP Hana, ODBC Compatible Database |
| `connection_type` | Choice | Basic Connection Info, Data Source (DSN), File Data Source (FILEDSN), Connection String |
| `sql_source` | Choice | SQL as UAC Script, SQL as Text |
| `script` | Script |  |
| `script_text` | Text |  |
| `data_source_name` | Choice |  |
| `file_data_source_name` | Text |  |
| `connection_string` | Text |  |
| `database_name` | Text |  |
| `database_credentials` | Credential |  |
| `database_host` | Text |  |
| `database_driver` | Choice |  |
| `database_port` | Integer |  |
| `trusted_connection` | Boolean | false |
| `enable_autocommit` | Boolean | false |
| `data_output` | Choice | Extension Output, File Output, STDOUT |
| `output_file_path` | Text |  |
| `output_file_type` | Choice | CSV, JSON |
| `column_separator` | Choice | Comma (,), Semicolon (;), Space (\" \"), Hash (#), Pipe (|), Tab |
| `quote_option` | Choice | Always, Only for special characters., Only for non-numeric data, Never |
| `print_column_names` | Boolean | true |
| `show_advanced_settings` | Boolean | false |
| `charset` | Choice | Default, UTF-8, UTF-16 LE, UTF-16 BE, ISO-8859-1 (Latin 1), ISO-8859-9 (Latin 9) |
| `max_rows_returned` | Integer |  |
| `connection_timeout` | Integer | 0 |
| `sql_statement_timeout` | Integer | 0 |
| `execution_time` | Text |  |
| `user_defined_metric` | Choice | -- None --, Counter |
| `metric_suffix` | Text |  |
| `column_for_metric_value_calc` | Text |  |
| `metric_attributes` | Choice | -- None --, Column Based |
| `column_list` | Text |  |
| `attributes` | Array |  |


### Enhanced File Transfer — `ue-enhanced-file-transfer`
**Category:** File Transfer
**Description:** Enhanced file transfer across SFTP, FTPS and UDM. Supports single and multi-path transfers, wildcard/regex matching, fan-out to multiple destinations, post-actions (delete, rename, archive), and smart resume for fault-tolerant retries.
**Fields (41):**

| Field name | Type | Choices / Notes |
|------------|------|-----------------|
| `action` | Choice | UDM - Single-Path File Transfer, UDM - Multi-Path File Transfer, UDM - Test Connection, SFTP - Single-Path File Transfer, SFTP - Multi-Path File Transfer, SFTP - Test Connection |
| `remote_server` | Text |  |
| `ftp_credentials` | Credential |  |
| `uac_url` | Text |  |
| `uac_credentials` | Credential |  |
| `primary_udm_agent` | Choice |  |
| `secondary_udm_agent` | Choice |  |
| `primary_udm_port` | Text |  |
| `secondary_udm_port` | Text |  |
| `primary_credentials` | Credential |  |
| `secondary_credentials` | Credential |  |
| `enable_fault_tolerance` | Boolean | false |
| `retry_count` | Integer | 20 |
| `retry_interval` | Integer | 60 |
| `network_delay` | Integer | 120 |
| `ack_window` | Text | 0 |
| `command` | Choice | PUT | Primary to Secondary, GET | Secondary to Primary |
| `transfer_type` | Choice | Text, Binary |
| `encrypt` | Choice | Yes, No |
| `codepage` | Choice | --None--, ISO 8859-1, ISO 8859-2, ISO 8859-3, ISO 8859-4, ISO 8859-5 |
| `local_file_path` | Text |  |
| `remote_file_path` | Text |  |
| `local_file_name` | Choice |  |
| `remote_file_name` | Choice |  |
| `transfers` | Array |  |
| `recent_file_only` | Boolean | false |
| `limit_age` | Integer |  |
| `dest_file_creation_option` | Choice | Overwrite, Skip, Fail |
| `move` | Boolean | false |
| `fail_on_first_error` | Boolean | true |
| `fail_if_no_files_match` | Boolean | true |
| `enable_smart_resume` | Boolean | false |
| `post_action` | Choice | Archive, Rename, Checksum Verification |
| `archive_path` | Text |  |
| `dest_rename_mode` | Choice | Pattern, Find & Replace |
| `dest_rename_pattern` | Text |  |
| `dest_rename_find` | Text |  |
| `dest_rename_replace` | Text |  |
| `transfer_progress` | Text |  |
| `skipped_files` | Text |  |
| `failed_files` | Text |  |


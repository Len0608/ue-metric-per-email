"""
Utility modules for the ue-metric-per-email Universal Extension.

Modules:
    input_validator  - Validate and normalise user inputs before network activity
    metrics_client   - Fetch and parse the Universal Controller Prometheus metrics endpoint
    csv_generator    - Write the five-column CSV report as a managed temporary file
    email_sender     - Deliver the CSV attachment via SMTP with configurable security
    output_reporter  - Render STDOUT summary, populate output fields, build Extension Output
"""

# Report contract

Create `incident_report.json` with `incident_id`, `root_cause`, an `impact`
object containing `false_rejections` and `affected_clients`, at least two
evidence strings, and a `remediation` object containing `config_change` and
`verification`. Count rejections no more than five seconds past token expiry as
clock-skew false rejections; do not count genuinely stale tokens.

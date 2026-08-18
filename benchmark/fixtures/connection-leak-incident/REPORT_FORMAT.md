# Report contract

Create `incident_report.json` with `incident_id`, `root_cause`, an `impact`
object containing `leaked_connections` and `timed_out_requests`, at least two
evidence strings, and a `remediation` object containing `code_change` and
`verification`. A connection is leaked when it is acquired but has no later
release event.

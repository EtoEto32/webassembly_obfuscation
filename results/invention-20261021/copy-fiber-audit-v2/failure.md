# Recovery byte-identity assertion was too strong

The script reached the recovered-binary identity assertion after the model,
negative controls, rejected profiles, and primary byte replay. It stopped
because equivalent DAGs can use different local schedules and operand orders.
The analysis task requires equal computation, not identical emitted bytes.
The corrected audit keeps the semantic fingerprints and reports the number of
distinct recovered binaries. No final audit JSON was produced in this attempt.
Its source is source-audit.py; audit-v3 is the final rerun.

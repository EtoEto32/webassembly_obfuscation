# Initial audit did not start

The first invocation of audit.py failed at Python parsing with a mismatched
bracket in engine_probe. No audit check or Wasm execution ran in this attempt.
The failing source is source-audit.py. The corrected rerun uses audit-v2.

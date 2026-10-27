# Initial harness failure

The first run stopped at Binaryen validation of parity8-plain-raw.wasm because the optimizer command omitted `--enable-simd`. This is an experiment harness configuration error, not resistance to analysis or invalid source semantics. The original run.py and prototype.py are preserved next to the partial outputs. A corrected full run uses a new v2 directory.

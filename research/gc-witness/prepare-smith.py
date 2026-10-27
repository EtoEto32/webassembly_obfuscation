"""Create a separate reproducible minimal patch; keep upstream source untouched."""
import difflib,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
src=ROOT/'.tools/gc-witness-smith-upstream/wasm-smith-0.262.0';dst=ROOT/'.tools/gc-witness-smith-patched'
if not dst.exists():shutil.copytree(src,dst)
else:
    # Resume only the untouched copy left by the initial assertion failure.
    for f in src.rglob('*'):
        if f.is_file():assert (dst/f.relative_to(src)).read_bytes()==f.read_bytes(), 'existing copy was modified'
file=dst/'src/core/code_builder.rs';old=file.read_text(encoding='utf8');start=old.index('fn array_new_fixed_valid(');end=old.index('\nfn ',old.index('fn array_new_fixed(',start)+5);part=old[start:end]
needle='builder.field_type_on_stack(module, module.ty(*i).unwrap_array().0)';assert part.count(needle)==2
part=part.replace(needle,'(cfg!(feature = "gc-witness-zero-seed") || '+needle+')')
needle='builder.field_type_on_stack(module, module.ty(**i).unwrap_array().0)';assert part.count(needle)==1
part=part.replace(needle,'(cfg!(feature = "gc-witness-zero-seed") || '+needle+')')
assert part.count('debug_assert!(m > 0);')==1;part=part.replace('debug_assert!(m > 0);','debug_assert!(m > 0 || cfg!(feature = "gc-witness-zero-seed"));')
needle='let array_size = u.int_in_range(0..=m - 1)?;';assert part.count(needle)==1
part=part.replace(needle,'let array_size = if m == 0 { 0 } else { u.int_in_range(0..=m - 1)? };')
new=old[:start]+part+old[end:];file.write_text(new,encoding='utf8')
cargo=dst/'Cargo.toml';c=cargo.read_text();assert c.count('[features]')==1;cargo.write_text(c.replace('[features]','[features]\ngc-witness-zero-seed = []'),encoding='utf8')
diff=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='upstream/src/core/code_builder.rs',tofile='patched/src/core/code_builder.rs'))
(ROOT/'research/gc-witness/smith-zero-seed.patch').write_text(diff,encoding='utf8')
provenance=dict(source=str(src),destination=str(dst),original_sha256=hashlib.sha256(old.encode()).hexdigest(),patched_sha256=hashlib.sha256(new.encode()).hexdigest(),changes=['src/core/code_builder.rs','Cargo.toml'])
(dst/'patch-provenance.json').write_text(json.dumps(provenance,indent=2));print(json.dumps(provenance,indent=2))

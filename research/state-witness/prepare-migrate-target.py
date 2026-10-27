"""Additional local CLI selecting an upstream public func_index; no library edits."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];base=ROOT/'.tools/wasm-migrate-build'
p=base/'src/bin/wasm-migrate-target.rs';p.parent.mkdir(exist_ok=True)
code='''use std::{env,fs,io::Write};
fn main()->Result<(),Box<dyn std::error::Error>> {
 let a:Vec<String>=env::args().collect();
 if a.len()!=4{return Err("usage: wasm-migrate-target input output defined-function-index".into());}
 let bytes=fs::read(&a[1])?;let mut m=wasm_migrate::WasmMigrate::new();m.func_index=a[3].parse()?;
 let out=m.compute(&bytes,true);
 fs::OpenOptions::new().write(true).create_new(true).open(&a[2])?.write_all(&out)?;
 Ok(())
}
'''
assert not p.exists();p.write_text(code)
(base/'target-driver-provenance.json').write_text(json.dumps({'file':str(p.relative_to(base)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'upstreamBodiesChanged':False},indent=2))
print(str(p))

"""Add a local transform-only driver; upstream sources remain byte-identical."""
import argparse,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=ROOT/'.tools/weave-build');out=a.parse_args().root
text=(out/'.upstream/Cargo.toml').read_text()
text=text[text.index('[workspace.package]'):]
manifest='''[package]
name="weave-probe"
version="0.0.0"
edition="2021"
[dependencies]
weave-transform={path="crates/weave-transform"}
serde_json="1"
[workspace]
resolver="2"
members=["crates/weave-core","crates/weave-transform"]
'''+text
assert not (out/'Cargo.toml').exists();(out/'Cargo.toml').write_text(manifest)
shutil.copy2(out/'.upstream/Cargo.lock',out/'Cargo.lock');(out/'src').mkdir()
(out/'src/main.rs').write_text('''use std::{env,fs,io::Write};
fn main()->Result<(),Box<dyn std::error::Error>> {
 let args:Vec<String>=env::args().collect();
 if args.len()!=3{return Err("usage: weave-probe input.wasm output.wasm".into());}
 let bytes=fs::read(&args[1])?;
 let out=weave_transform::transform(&bytes,&weave_transform::TransformOptions{poll_period:1,stack_pages:1})?;
 fs::OpenOptions::new().write(true).create_new(true).open(&args[2])?.write_all(&out.wasm)?;
 Ok(())
}
''')
(out/'driver-provenance.json').write_text(json.dumps({'sourceUnmodified':True,'files':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in ['Cargo.toml','Cargo.lock','src/main.rs']}},indent=2))
print(str(out))

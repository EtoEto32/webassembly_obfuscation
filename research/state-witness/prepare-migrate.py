"""Make an isolated driver without editing upstream Rust library sources."""
import argparse,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=ROOT/'.tools/wasm-migrate-build')
out=a.parse_args().root;cache=out/'.upstream'
original=(cache/'Cargo.toml').read_text(encoding='utf8')
workspace=original[original.index('[workspace.lints.rust]'):original.index('\n[dependencies]')]
manifest='''[package]
name = "wasm-migrate-probe"
version = "0.0.0"
edition = "2021"
[dependencies]
wasm-migrate = { path = "crates/wasm-migrate" }
[workspace]
members = ["crates/wasm-migrate", "crates/wasm-mutate", "crates/wasmparser", "crates/wasm-encoder", "crates/wasmprinter", "crates/wat", "crates/wast"]
resolver = "2"
'''+workspace
if (out/'Cargo.toml').exists():raise FileExistsError(out/'Cargo.toml')
(out/'Cargo.toml').write_text(manifest,encoding='utf8');shutil.copy2(cache/'Cargo.lock',out/'Cargo.lock')
src=out/'src';src.mkdir()
(src/'main.rs').write_text('''use std::{env, fs, io::Write};
fn main() -> Result<(), Box<dyn std::error::Error>> {
  let args: Vec<String> = env::args().collect();
  if args.len()!=3 {return Err("usage: wasm-migrate-probe input.wasm output.wasm".into());}
  let bytes=fs::read(&args[1])?;
  let migrate=wasm_migrate::WasmMigrate::new();
  let output=migrate.compute(&bytes,true);
  let mut file=fs::OpenOptions::new().write(true).create_new(true).open(&args[2])?;
  file.write_all(&output)?;
  Ok(())
}
''',encoding='utf8')
(out/'driver-provenance.json').write_text(json.dumps({'note':'Local driver and minimal workspace; upstream library sources unchanged.',
 'initialLockSha256':hashlib.sha256((out/'Cargo.lock').read_bytes()).hexdigest(),
 'manifestSha256':hashlib.sha256((out/'Cargo.toml').read_bytes()).hexdigest(),
 'driverSha256':hashlib.sha256((src/'main.rs').read_bytes()).hexdigest()},indent=2))
print(str(out))

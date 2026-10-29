use std::{env,fs,io::Write};
fn main()->Result<(),Box<dyn std::error::Error>> {
 let a:Vec<String>=env::args().collect();
 if a.len()!=3{return Err("usage: weave-default input.wasm output.wasm".into());}
 let out=weave_transform::transform(&fs::read(&a[1])?,&Default::default())?;
 fs::OpenOptions::new().write(true).create_new(true).open(&a[2])?.write_all(&out.wasm)?;
 Ok(())
}

use std::{fs,time::Instant};
use serde_json::{Value,json};
fn run()->Result<Value,String>{
    let a:Vec<_>=std::env::args().collect();if a.len()!=4{return Err("SHAPE.wasm SEED OUTPUT.wasm".into())}
    let shape=fs::read(&a[1]).map_err(|e|e.to_string())?;let seed=fs::read(&a[2]).map_err(|e|e.to_string())?;
    if seed.len()>65536||shape.len()>65536{return Err("input cap".into())}
    let mut cfg=wasm_smith::Config::default();cfg.module_shape=Some(shape);
    cfg.gc_enabled=true;cfg.reference_types_enabled=true;cfg.allow_start_export=false;
    cfg.memory64_enabled=false;cfg.threads_enabled=false;cfg.shared_everything_threads_enabled=false;
    cfg.relaxed_simd_enabled=false;cfg.simd_enabled=false;cfg.wide_arithmetic_enabled=false;
    cfg.exceptions_enabled=false;cfg.custom_descriptors_enabled=false;cfg.custom_page_sizes_enabled=false;
    cfg.compact_imports_enabled=false;cfg.allow_invalid_funcs=false;
    cfg.max_types=2;cfg.max_funcs=4;cfg.max_instructions=80;cfg.max_globals=4;
    cfg.max_memories=0;cfg.max_tables=0;cfg.max_tags=0;cfg.max_imports=0;
    cfg.max_type_size=32;cfg.max_nesting_depth=4;cfg.max_values=4;
    let mut u=arbitrary::Unstructured::new(&seed);let t=Instant::now();
    let module=wasm_smith::Module::new(cfg,&mut u).map_err(|e|format!("generation: {e}"))?;
    let generated=module.to_bytes();let generation_ms=t.elapsed().as_secs_f64()*1000.;
    wasmparser::Validator::new().validate_all(&generated).map_err(|e|format!("validation: {e}"))?;
    fs::write(&a[3],&generated).map_err(|e|e.to_string())?;
    Ok(json!({"status":"generated","mode":if cfg!(feature="zero"){"zero"}else{"stock"},"generation_ms":generation_ms,"bytes":generated.len(),"seed_remaining":u.len()}))
}
fn main(){let x=match run(){Ok(x)=>x,Err(e)=>json!({"status":"error","reason":e})};println!("{x}")}

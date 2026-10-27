use std::{fs, time::Instant};
use serde_json::{json,Value};
use wasmparser as p;

fn val(t:p::ValType)->Result<Value,String>{
    Ok(match t {
        p::ValType::Ref(r)=>{
            let heap=match r.heap_type(){
                p::HeapType::Concrete(i)=>json!({"index":i.as_module_index().ok_or("non-module reference index")?}),
                p::HeapType::Abstract{shared:false,ty}=>json!({"abstract":format!("{ty:?}").to_lowercase()}),
                _=>return Err("shared reference unsupported".into())
            };
            json!({"ref":heap,"nullable":r.is_nullable()})
        }
        _=>json!({"scalar":format!("{t}")})
    })
}
fn field(f:p::FieldType)->Result<Value,String>{
    let v=match f.element_type{
        p::StorageType::I8=>json!({"scalar":"i8"}),
        p::StorageType::I16=>json!({"scalar":"i16"}),
        p::StorageType::Val(t)=>val(t)?
    };
    Ok(json!({"value":v,"mutable":f.mutable}))
}
fn run()->Result<Value,String>{
    let path=std::env::args().nth(1).ok_or("usage: gc-witness-types INPUT.wasm")?;
    let data=fs::read(path).map_err(|e|e.to_string())?;
    if data.len()>16*1024*1024{return Err("input size limit".into())}
    let features=p::WasmFeatures::WASM2|p::WasmFeatures::GC|p::WasmFeatures::FUNCTION_REFERENCES|p::WasmFeatures::TAIL_CALL|p::WasmFeatures::EXTENDED_CONST;
    let t=Instant::now();
    p::Validator::new_with_features(features).validate_all(&data).map_err(|e|format!("validation: {e}"))?;
    let validation_ms=t.elapsed().as_secs_f64()*1000.;
    let mut types=vec![];let mut groups=vec![];
    for payload in p::Parser::new(0).parse_all(&data){
        if let p::Payload::TypeSection(reader)=payload.map_err(|e|e.to_string())?{
            for group in reader{
                let group=group.map_err(|e|e.to_string())?;let start=types.len();
                for s in group.types(){
                    if !s.is_final||s.supertype_idx.is_some()||s.composite_type.shared {return Err("non-final, subtype or shared type unsupported".into())}
                    let row=match &s.composite_type.inner{
                        p::CompositeInnerType::Struct(x)=>json!({"kind":"struct","fields":x.fields.iter().map(|x|field(*x)).collect::<Result<Vec<_>,_>>()?}),
                        p::CompositeInnerType::Array(x)=>json!({"kind":"array","fields":[field(x.0)?]}),
                        p::CompositeInnerType::Func(x)=>json!({"kind":"func","params":x.params().iter().map(|x|val(*x)).collect::<Result<Vec<_>,_>>()?,"results":x.results().iter().map(|x|val(*x)).collect::<Result<Vec<_>,_>>()?}),
                        _=>return Err("continuation unsupported".into())
                    };
                    types.push(row);if types.len()>4096{return Err("type count limit".into())}
                }
                groups.push(json!({"start":start,"length":types.len()-start}));
            }
        }
    }
    Ok(json!({"status":"supported","types":types,"groups":groups,"validation_ms":validation_ms,"total_ms":t.elapsed().as_secs_f64()*1000.}))
}
fn main(){let result=match run(){Ok(x)=>x,Err(e)=>json!({"status":"rejected","reason":e})};println!("{result}");}

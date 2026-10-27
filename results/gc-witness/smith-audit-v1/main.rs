use std::{fs, time::Instant};
use serde_json::{json,Value};
use wasmparser as p;
mod instrument;

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
fn compare()->Result<Value,String>{
    let a:Vec<_>=std::env::args().collect();
    if a.len()!=5{return Err("usage: gc-witness-types compare REFERENCE.wasm TARGET_INDEX CANDIDATE.wasm".into())}
    let mut validator=p::Validator::new_with_features(p::WasmFeatures::all());
    let rb=fs::read(&a[2]).map_err(|e|e.to_string())?;
    let r=validator.validate_all(&rb).map_err(|e|e.to_string())?;
    let i:u32=a[3].parse().map_err(|_|"index")?;
    let id=r.as_ref().core_type_at_in_module(i);
    validator.reset();
    let cb=fs::read(&a[4]).map_err(|e|e.to_string())?;
    let c=validator.validate_all(&cb).map_err(|e|e.to_string())?;let c=c.as_ref();
    let mut constructors=0;let mut operations=0;let mut target_ops=vec![];
    for payload in p::Parser::new(0).parse_all(&cb){
        if let p::Payload::CodeSectionEntry(body)=payload.map_err(|e|e.to_string())?{
            let mut ops=body.get_operators_reader().map_err(|e|e.to_string())?;
            while !ops.eof(){
                let op=ops.read().map_err(|e|e.to_string())?;operations+=1;
                use p::Operator::*;
                let index=match &op{
                    StructNew{struct_type_index:i}|StructNewDefault{struct_type_index:i}=>Some((*i,true)),
                    ArrayNew{array_type_index:i}|ArrayNewDefault{array_type_index:i}|ArrayNewFixed{array_type_index:i,..}|ArrayNewData{array_type_index:i,..}|ArrayNewElem{array_type_index:i,..}=>Some((*i,true)),
                    StructGet{struct_type_index:i,..}|StructSet{struct_type_index:i,..}=>Some((*i,false)),
                    ArrayGet{array_type_index:i}|ArraySet{array_type_index:i}=>Some((*i,false)),
                    _=>None
                };
                if let Some((i,new))=index{if c.core_type_at_in_module(i)==id{if new{constructors+=1};target_ops.push(format!("{op:?}"));}}
            }
        }
    }
    Ok(json!({"status":"compared","constructors":constructors,"operations":operations,"target_ops":target_ops}))
}
fn inspect()->Result<Value,String>{
    let path=std::env::args().nth(2).ok_or("inspect INPUT.wasm")?;
    let data=fs::read(path).map_err(|e|e.to_string())?;
    p::Validator::new_with_features(p::WasmFeatures::all()).validate_all(&data).map_err(|e|e.to_string())?;
    let mut funcs=vec![];let mut exports=vec![];let mut imports=0;
    for payload in p::Parser::new(0).parse_all(&data){match payload.map_err(|e|e.to_string())?{
        p::Payload::ImportSection(s)=>for item in s{if matches!(item.map_err(|e|e.to_string())?.ty,p::TypeRef::Func(_)){imports+=1;}},
        p::Payload::ExportSection(s)=>for item in s{let e=item.map_err(|e|e.to_string())?;if e.kind==p::ExternalKind::Func{exports.push(json!({"name":e.name,"index":e.index}));}},
        p::Payload::CodeSectionEntry(b)=>{let mut ops=vec![];let mut r=b.get_operators_reader().map_err(|e|e.to_string())?;while !r.eof(){let offset=r.original_position();let op=r.read().map_err(|e|e.to_string())?;ops.push(json!({"offset":offset,"op":format!("{op:?}")}));}funcs.push(json!({"index":imports+funcs.len(),"ops":ops}));},
        _=>{}
    }}
    Ok(json!({"status":"inspected","imports":imports,"exports":exports,"functions":funcs}))
}
fn main(){let result=match match std::env::args().nth(1).as_deref(){Some("compare")=>compare(),Some("instrument")=>instrument::run(),Some("inspect")=>inspect(),_=>run()}{Ok(x)=>x,Err(e)=>json!({"status":"rejected","reason":e})};println!("{result}");}

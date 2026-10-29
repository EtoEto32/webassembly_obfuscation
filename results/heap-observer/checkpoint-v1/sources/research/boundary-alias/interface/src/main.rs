use std::{fs,collections::BTreeMap};
use wasmparser as p;
use serde_json::{json,Value};
fn value(v:p::ValType)->Value {
    match v {
        p::ValType::Ref(r)=>json!({"ref":true,"nullable":r.is_nullable(),"heap":format!("{:?}",r.heap_type())}),
        _=>json!(v.to_string())
    }
}
fn run()->Result<Value,String> {
    let path=std::env::args().nth(1).ok_or("INPUT.wasm")?;
    let bytes=fs::read(path).map_err(|e|e.to_string())?;
    if bytes.len()>1048576 {return Err("input exceeds 1 MiB limit".into())}
    p::Validator::new_with_features(p::WasmFeatures::all()).validate_all(&bytes).map_err(|e|e.to_string())?;
    let mut types=Vec::<Option<Value>>::new();
    let mut function_types=Vec::<u32>::new();
    let mut exports=Vec::<(String,u32)>::new();
    let mut imported=0;
    for payload in p::Parser::new(0).parse_all(&bytes) {
        match payload.map_err(|e|e.to_string())? {
            p::Payload::TypeSection(reader)=>for group in reader {
                let group=group.map_err(|e|e.to_string())?;
                for ty in group.types() {
                    types.push(match &ty.composite_type.inner {
                        p::CompositeInnerType::Func(f)=>Some(json!({"params":f.params().iter().copied().map(value).collect::<Vec<_>>(),"results":f.results().iter().copied().map(value).collect::<Vec<_>>()})),
                        _=>None
                    });
                }
            },
            p::Payload::ImportSection(reader)=>for imp in reader.into_imports() {
                let imp=imp.map_err(|e|e.to_string())?;
                match imp.ty {p::TypeRef::Func(t)|p::TypeRef::FuncExact(t)=>{function_types.push(t);imported+=1;},_=>{}}
            },
            p::Payload::FunctionSection(reader)=>for ty in reader {function_types.push(ty.map_err(|e|e.to_string())?);},
            p::Payload::ExportSection(reader)=>for exp in reader {
                let exp=exp.map_err(|e|e.to_string())?;
                if exp.kind==p::ExternalKind::Func {exports.push((exp.name.to_string(),exp.index));}
            },_=>{}
        }
    }
    let mut signatures=BTreeMap::<String,Value>::new();
    for (name,index) in exports {
        let ti=*function_types.get(index as usize).ok_or("function index")?;
        let mut sig=types.get(ti as usize).and_then(|x|x.clone()).ok_or("function type")?;
        sig["function_index"]=json!(index);sig["type_index"]=json!(ti);sig["imported"]=json!(index<imported);
        signatures.insert(name,sig);
    }
    Ok(json!({"status":"inspected","imported_functions":imported,"function_count":function_types.len(),"functions":signatures}))
}
fn main(){let result=match run(){Ok(v)=>v,Err(e)=>json!({"status":"rejected","reason":e})};println!("{result}");}

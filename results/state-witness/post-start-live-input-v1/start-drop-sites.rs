use serde_json::json;
use std::{collections::BTreeMap,env,fs};
use wasmparser::{DataKind,ExternalKind,Operator,Parser,Payload,TypeRef,Validator,WasmFeatures};

fn main() -> Result<(),Box<dyn std::error::Error>> {
    let bytes=fs::read(env::args().nth(1).ok_or("input wasm")?)?;
    Validator::new_with_features(WasmFeatures::all()).validate_all(&bytes)?;
    let mut types=Vec::new();let mut function_types=Vec::new();let mut imports=Vec::new();let mut exports=Vec::new();let mut start=None;
    let mut function=0_u32;let mut drops=Vec::new();let mut lengths=Vec::new();let mut constants=BTreeMap::new();
    for payload in Parser::new(0).parse_all(&bytes) {
        match payload? {
            Payload::TypeSection(reader)=>for ty in reader.into_iter_err_on_gc_types() {
                let ty=ty?;types.push(json!({"params":ty.params().iter().map(|v|format!("{v:?}")).collect::<Vec<_>>(),"results":ty.results().iter().map(|v|format!("{v:?}")).collect::<Vec<_>>()}));
            },
            Payload::ImportSection(reader)=>for imp in reader {
                let imp=imp?;
                match imp.ty {
                    TypeRef::Func(ty)=>{function+=1;function_types.push(ty);imports.push(json!({"module":imp.module,"name":imp.name,"kind":"function","type":ty}));},
                    TypeRef::Memory(m)=>{assert!(m.shared&&!m.memory64);imports.push(json!({"module":imp.module,"name":imp.name,"kind":"memory","initial":m.initial,"maximum":m.maximum,"shared":m.shared}));},
                    _=>return Err("unsupported import kind in fixed-input instrumenter".into())
                }
            },
            Payload::FunctionSection(reader)=>for ty in reader {function_types.push(ty?);},
            Payload::ExportSection(reader)=>for ex in reader {let ex=ex?;exports.push(json!({"name":ex.name,"kind":format!("{:?}",ex.kind),"index":ex.index}));},
            Payload::StartSection{func,..}=>start=Some(func),
            Payload::DataSection(reader)=>for seg in reader {let seg=seg?;assert!(matches!(seg.kind,DataKind::Passive));lengths.push(seg.data.len());},
            Payload::CodeSectionEntry(body)=>{
                let mut reader=body.get_operators_reader()?;let mut simple=Vec::new();
                while !reader.eof(){let offset=reader.original_position();let op=reader.read()?;let end=reader.original_position();
                    if let Operator::DataDrop{data_index}=op {drops.push(json!({"function":function,"segment":data_index,"offset":offset,"end":end}));}
                    if simple.len()<3 {simple.push(match op {Operator::I32Const{value}=>Some(value),Operator::End=>None,_=>Some(i32::MIN)});}
                }
                let ty=&types[function_types[function as usize]as usize];
                if simple.len()==2&&simple[1].is_none()&&simple[0]!=Some(i32::MIN)&&ty["params"]==json!([])&&ty["results"]==json!(["I32"]) {constants.insert(function,simple[0].unwrap());}
                function+=1;
            },
            _=>{}
        }
    }
    assert_eq!(function as usize,function_types.len());
    let pure:Vec<_>=exports.iter().filter(|e| e["kind"]==format!("{:?}",ExternalKind::Func)).filter_map(|e| constants.get(&(e["index"].as_u64()?as u32)).map(|v|json!({"name":e["name"],"value":v}))).collect();
    println!("{}",json!({"start":start,"types":types,"imports":imports,"exports":exports,"functionCount":function,"dataLengths":lengths,"drops":drops,"pureConstantExports":pure}));Ok(())
}

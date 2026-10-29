use std::{fs,collections::BTreeMap};
use wasmparser as p;
use serde_json::{json,Value};
fn value(v:p::ValType)->Value{match v{
    p::ValType::Ref(r)=>json!({"reference":true,"nullable":r.is_nullable(),"heap":format!("{:?}",r.heap_type()),"index":match r.heap_type(){p::HeapType::Concrete(i)=>i.as_module_index(),_=>None}}),
    _=>json!({"scalar":v.to_string()})
}}
fn field(f:p::FieldType)->Value{json!({"mutable":f.mutable,"value":match f.element_type{p::StorageType::I8=>json!({"scalar":"i8"}),p::StorageType::I16=>json!({"scalar":"i16"}),p::StorageType::Val(v)=>value(v)}})}
fn run()->Result<Value,String>{
    let path=std::env::args().nth(1).ok_or("INPUT.wasm")?;let b=fs::read(path).map_err(|e|e.to_string())?;if b.len()>20000000{return Err("input cap".into())}
    p::Validator::new_with_features(p::WasmFeatures::all()).validate_all(&b).map_err(|e|e.to_string())?;
    let mut types=vec![];let mut groups=vec![];let mut ops=BTreeMap::<String,u64>::new();
    for payload in p::Parser::new(0).parse_all(&b){match payload.map_err(|e|e.to_string())?{
        p::Payload::TypeSection(reader)=>for group in reader{
            let group=group.map_err(|e|e.to_string())?;let start=types.len();
            for t in group.types(){
                let (kind,fields)=match &t.composite_type.inner{
                    p::CompositeInnerType::Struct(s)=>("struct",s.fields.iter().map(|f|field(*f)).collect::<Vec<_>>()),
                    p::CompositeInnerType::Array(a)=>("array",vec![field(a.0)]),
                    p::CompositeInnerType::Func(_)=>("func",vec![]),
                    p::CompositeInnerType::Cont(_)=>("cont",vec![])
                };
                types.push(json!({"kind":kind,"fields":fields,"final":t.is_final,"supertypes":t.supertype_idxs.iter().map(|i|i.as_module_index()).collect::<Vec<_>>(),"shared":t.composite_type.shared}));
            }
            groups.push(json!({"start":start,"length":types.len()-start}));
        },
        p::Payload::CodeSectionEntry(body)=>{let mut reader=body.get_operators_reader().map_err(|e|e.to_string())?;while !reader.eof(){let op=reader.read().map_err(|e|e.to_string())?;let name=match op{
            p::Operator::StructNew{..}=>Some("struct.new"),p::Operator::StructNewDefault{..}=>Some("struct.new_default"),p::Operator::StructGet{..}|p::Operator::StructGetS{..}|p::Operator::StructGetU{..}=>Some("struct.get"),p::Operator::StructSet{..}=>Some("struct.set"),
            p::Operator::ArrayNew{..}|p::Operator::ArrayNewDefault{..}|p::Operator::ArrayNewFixed{..}|p::Operator::ArrayNewData{..}|p::Operator::ArrayNewElem{..}=>Some("array.new*"),p::Operator::ArrayGet{..}|p::Operator::ArrayGetS{..}|p::Operator::ArrayGetU{..}=>Some("array.get"),p::Operator::ArraySet{..}=>Some("array.set"),_=>None};if let Some(n)=name{*ops.entry(n.into()).or_default()+=1;}}},_=>{}
    }}
    Ok(json!({"status":"inspected","bytes":b.len(),"types":types,"groups":groups,"operations":ops}))
}
fn main(){let v=match run(){Ok(v)=>v,Err(e)=>json!({"status":"rejected","reason":e})};println!("{v}");}

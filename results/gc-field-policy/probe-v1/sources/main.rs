use std::{convert::Infallible, fs, time::Instant};
use wasm_encoder::{self as e, reencode::{self, Reencode}};
use wasmparser::{self as p, types::{CoreTypeId, TypesRef}};
use serde_json::{json, Value};

struct Obligation { op: String, action: &'static str, ty: u32, field: Option<u32> }
#[derive(Default)]
struct Effects { ops: Vec<Obligation> }
impl Effects {
    fn add(&mut self, op: &str, action: &'static str, ty: u32, field: Option<u32>) {
        self.ops.push(Obligation {op:op.into(),action,ty,field});
    }
}
impl Reencode for Effects {
    type Error = Infallible;
    fn instruction<'a>(&mut self, op: p::Operator<'a>) -> Result<e::Instruction<'a>,reencode::Error<Infallible>> {
        use p::Operator::*;
        match &op {
            StructNew {struct_type_index:t} | StructNewDefault {struct_type_index:t} => self.add("struct.new","create",*t,None),
            StructGet {struct_type_index:t,field_index:f} | StructGetS {struct_type_index:t,field_index:f}
              | StructGetU {struct_type_index:t,field_index:f} => self.add("struct.get","read",*t,Some(*f)),
            StructSet {struct_type_index:t,field_index:f} => self.add("struct.set","write",*t,Some(*f)),
            ArrayNew {array_type_index:t} | ArrayNewDefault {array_type_index:t}
              | ArrayNewFixed {array_type_index:t,..} | ArrayNewData {array_type_index:t,..}
              | ArrayNewElem {array_type_index:t,..} => self.add("array.new","create",*t,None),
            ArrayGet {array_type_index:t} | ArrayGetS {array_type_index:t} | ArrayGetU {array_type_index:t} => self.add("array.get","read",*t,Some(0)),
            ArraySet {array_type_index:t} | ArrayFill {array_type_index:t}
              | ArrayInitData {array_type_index:t,..} | ArrayInitElem {array_type_index:t,..} => self.add("array.write","write",*t,Some(0)),
            ArrayCopy {array_type_index_src:s,array_type_index_dst:d} => {
                self.add("array.copy.source","read",*s,Some(0));
                self.add("array.copy.destination","write",*d,Some(0));
            }
            _ => {}
        }
        reencode::utils::instruction(self,op)
    }
}
fn subtype(types: TypesRef<'_>, mut a: CoreTypeId, b: CoreTypeId) -> bool {
    loop { if a==b { return true; } match types.supertype_of(a) {Some(x)=>a=x,None=>return false} }
}
struct Rule { index:u32,id:CoreTypeId, action:String,field:Option<u32> }
fn run()->Result<(),Box<dyn std::error::Error>> {
    let a:Vec<String>=std::env::args().collect();
    if a.len()!=4 {return Err("usage: gc-field-policy LIBRARY.wasm POLICY.json CONSUMER.wasm".into());}
    let t=Instant::now();
    let library=fs::read(&a[1])?;let consumer=fs::read(&a[3])?;
    let policy:Value=serde_json::from_slice(&fs::read(&a[2])?)?;
    let features=p::WasmFeatures::WASM2|p::WasmFeatures::GC|p::WasmFeatures::FUNCTION_REFERENCES
        |p::WasmFeatures::TAIL_CALL|p::WasmFeatures::EXTENDED_CONST;
    let mut validator=p::Validator::new_with_features(features);
    let lib_types=validator.validate_all(&library)?;
    let lib=lib_types.as_ref();let mut rules=vec![];
    for rule in policy.as_array().ok_or("policy must be an array")? {
        let index=u32::try_from(rule["type"].as_u64().ok_or("type index required")?)?;
        if index>=lib.core_type_count_in_module() {return Err("policy type out of range".into());}
        let id=lib.core_type_at_in_module(index);
        let action=rule["deny"].as_str().ok_or("deny required")?.to_owned();
        if !["read","write","create"].contains(&action.as_str()){return Err("unknown policy action".into());}
        let field=if action=="create" {None} else {Some(u32::try_from(rule["field"].as_u64().ok_or("field required")?)?)};
        let width=match &lib.get(id).ok_or("type missing")?.composite_type.inner {
            p::CompositeInnerType::Struct(s)=>s.fields.len(),
            p::CompositeInnerType::Array(_)=>1,
            _=>return Err("policy must target a GC aggregate".into())
        };
        if field.map_or(false,|f|f as usize>=width){return Err("policy field out of range".into());}
        rules.push(Rule{index,id,action,field});
    }
    validator.reset();
    let types=validator.validate_all(&consumer)?;let types=types.as_ref();
    let validation_s=t.elapsed().as_secs_f64();
    let mut effects=Effects::default();
    effects.parse_core_module(&mut e::Module::new(),p::Parser::new(0),&consumer)?;
    let mut results=vec![];
    for mode in ["none","local-index","canonical-exact","closure","deny-all-gc"] {
        let mut violations=vec![];
        for (ordinal,op) in effects.ops.iter().enumerate() {
            let id=types.core_type_at_in_module(op.ty);
            for rule in &rules {
                let related=match mode {
                    "none"=>false,"local-index"=>op.ty==rule.index,"canonical-exact"=>id==rule.id,
                    "closure"=>subtype(types,id,rule.id)||(op.action!="create"&&subtype(types,rule.id,id)),
                    "deny-all-gc"=>true,_=>unreachable!()
                };
                if related && (mode=="deny-all-gc" || op.action==rule.action&&op.field==rule.field) {
                    violations.push(json!({"operation":ordinal,"op":op.op,"action":op.action,"type":op.ty,"field":op.field,"protectedType":rule.index}));
                    break;
                }
            }
        }
        results.push(json!({"mode":mode,"accepted":violations.is_empty(),"violations":violations}));
    }
    println!("{}",json!({"validationSeconds":validation_s,"totalSeconds":t.elapsed().as_secs_f64(),
        "obligations":effects.ops.len(),"results":results,"features":"WASM2 + GC + function-references + tail-call + extended-const"}));
    Ok(())
}
fn main(){if let Err(e)=run(){eprintln!("{e}");std::process::exit(2);}}

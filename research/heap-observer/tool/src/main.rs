use std::{fs,env};
use wasmparser as p;
use wasm_encoder as e;
use e::reencode::{Reencode,RoundtripReencoder};
use serde_json::{json,Value};

struct Builder { types:e::TypeSection, funcs:e::FunctionSection, exports:e::ExportSection, code:e::CodeSection, next_type:u32, next_func:u32 }
impl Builder {
 fn emit(&mut self,name:&str,params:&[e::ValType],results:&[e::ValType],ins:Vec<e::Instruction<'static>>) {
  self.types.ty().function(params.iter().copied(),results.iter().copied());self.funcs.function(self.next_type);self.next_type+=1;
  self.exports.export(name,e::ExportKind::Func,self.next_func);self.next_func+=1;
  let mut f=e::Function::new([]);for op in ins {f.instruction(&op);}f.instruction(&e::Instruction::End);self.code.function(&f);
 }
}
fn field_kind(s:p::StorageType)->Result<&'static str,String> {
 Ok(match s {p::StorageType::I8=>"i8",p::StorageType::I16=>"i16",p::StorageType::Val(v)=>match v {
  p::ValType::I32=>"i32",p::ValType::I64=>"i64",p::ValType::F32=>"f32",p::ValType::F64=>"f64",p::ValType::V128=>"v128",
  p::ValType::Ref(r)=>match r.heap_type() {
   p::HeapType::Abstract{shared:false,ty:p::AbstractHeapType::Exn|p::AbstractHeapType::NoExn|p::AbstractHeapType::Cont|p::AbstractHeapType::NoCont}=>return Err("exception/continuation reference unsupported".into()),
   p::HeapType::Abstract{shared:true,..}=>return Err("shared reference unsupported".into()),_=>"ref"}
 }})
}
fn main_run()->Result<Value,String> {
 let args:Vec<_>=env::args().collect();if args.len()!=3{return Err("INPUT.wasm OUTPUT.observer.wasm".into())}
 let bytes=fs::read(&args[1]).map_err(|x|x.to_string())?;if bytes.len()>1048576{return Err("input exceeds 1 MiB".into())}
 p::Validator::new_with_features(p::WasmFeatures::all()).validate_all(&bytes).map_err(|x|x.to_string())?;
 let mut builder=Builder{types:e::TypeSection::new(),funcs:e::FunctionSection::new(),exports:e::ExportSection::new(),code:e::CodeSection::new(),next_type:0,next_func:0};
 let mut converter=RoundtripReencoder;let mut original=Vec::new();let mut groups=Vec::new();
 for payload in p::Parser::new(0).parse_all(&bytes) {
  if let p::Payload::TypeSection(reader)=payload.map_err(|x|x.to_string())? {
   converter.parse_type_section(&mut builder.types,reader.clone()).map_err(|x|x.to_string())?;
   for g in reader {let g=g.map_err(|x|x.to_string())?;let begin=original.len();
    for ty in g.types() {if ty.composite_type.shared||ty.composite_type.descriptor_idx.is_some()||ty.composite_type.describes_idx.is_some(){return Err("shared/descriptor type unsupported".into())}
     if ty.supertype_idxs.len()>1{return Err("multiple supertypes unsupported".into())}
     match &ty.composite_type.inner {p::CompositeInnerType::Cont(_)=>return Err("continuation unsupported".into()),p::CompositeInnerType::Struct(s)=>for f in &s.fields {field_kind(f.element_type)?;},p::CompositeInnerType::Array(a)=>{field_kind(a.0.element_type)?;},p::CompositeInnerType::Func(f)=>for v in f.params().iter().chain(f.results()) {field_kind(p::StorageType::Val(*v))?;}}
     original.push(ty.clone());}
    groups.push(json!({"start":begin,"count":original.len()-begin,"explicit":g.is_explicit_rec_group()}));
   }
  }
 }
 builder.next_type=original.len() as u32;let mut shapes=Vec::new();
 for (i,ty) in original.iter().enumerate() {
  let (kind,fields)=match &ty.composite_type.inner {p::CompositeInnerType::Struct(s)=>("struct",s.fields.to_vec()),p::CompositeInnerType::Array(a)=>("array",vec![a.0]),_=>continue};
  let id=i as u32;let test=format!("is_{id}");
  builder.emit(&test,&[e::ValType::EXTERNREF],&[e::ValType::I32],vec![e::Instruction::LocalGet(0),e::Instruction::AnyConvertExtern,e::Instruction::RefTestNonNull(e::HeapType::Concrete(id))]);
  let prefix=||vec![e::Instruction::LocalGet(0),e::Instruction::AnyConvertExtern,e::Instruction::RefCastNonNull(e::HeapType::Concrete(id))];
  if kind=="array" {let mut ops=prefix();ops.push(e::Instruction::ArrayLen);builder.emit(&format!("len_{id}"),&[e::ValType::EXTERNREF],&[e::ValType::I32],ops);}
  let mut fm=Vec::new();
  for (j,f) in fields.iter().enumerate() {
   let sk=field_kind(f.element_type)?;let name=format!("get_{id}_{j}");let mut ops=prefix();let mut params=vec![e::ValType::EXTERNREF];
   if kind=="array" {params.push(e::ValType::I32);ops.push(e::Instruction::LocalGet(1));ops.push(if sk=="i8"||sk=="i16"{e::Instruction::ArrayGetU(id)}else{e::Instruction::ArrayGet(id)});}
   else {ops.push(if sk=="i8"||sk=="i16"{e::Instruction::StructGetU{struct_type_index:id,field_index:j as u32}}else{e::Instruction::StructGet{struct_type_index:id,field_index:j as u32}});}
   let mut results=vec![e::ValType::I32];let mut detail=Value::Null;
   match f.element_type {
    p::StorageType::I8|p::StorageType::I16=>{},
    p::StorageType::Val(v)=>match v {
     p::ValType::I32=>{},p::ValType::I64=>results[0]=e::ValType::I64,
     p::ValType::F32=>ops.push(e::Instruction::I32ReinterpretF32),
     p::ValType::F64=>{ops.push(e::Instruction::I64ReinterpretF64);results[0]=e::ValType::I64;},
     p::ValType::V128=>return Err("v128 field unsupported in initial observer".into()),
     p::ValType::Ref(r)=>{let rt=converter.ref_type(r).map_err(|x|x.to_string())?;detail=json!({"nullable":r.is_nullable(),"heap":format!("{:?}",r.heap_type())});
      let internal=match r.heap_type(){p::HeapType::Concrete(x)|p::HeapType::Exact(x)=>matches!(original[x.as_module_index().ok_or("nonmodule type index")? as usize].composite_type.inner,p::CompositeInnerType::Struct(_)|p::CompositeInnerType::Array(_)),p::HeapType::Abstract{ty,..}=>!matches!(ty,p::AbstractHeapType::Extern|p::AbstractHeapType::NoExtern|p::AbstractHeapType::Func|p::AbstractHeapType::NoFunc)};
      if internal {ops.push(e::Instruction::ExternConvertAny);results[0]=e::ValType::EXTERNREF;}else{results[0]=e::ValType::Ref(rt);}
     }
    }
   }
   builder.emit(&name,&params,&results,ops);fm.push(json!({"kind":sk,"mutable":f.mutable,"getter":name,"reference":detail}));
  }
  shapes.push(json!({"index":id,"kind":kind,"test":test,"final":ty.is_final,"supertype":ty.supertype_idxs.first().and_then(|x|x.as_module_index()),"fields":fm}));
 }
 let mut module=e::Module::new();module.section(&builder.types).section(&builder.funcs).section(&builder.exports).section(&builder.code);let output=module.finish();
 p::Validator::new_with_features(p::WasmFeatures::all()).validate_all(&output).map_err(|x|format!("generated validation: {x}"))?;
 fs::write(&args[2],&output).map_err(|x|x.to_string())?;
 Ok(json!({"status":"generated","input_type_count":original.len(),"groups":groups,"shapes":shapes,"helper_functions":builder.next_func,"bytes":output.len()}))
}
fn main(){let result=match main_run(){Ok(v)=>v,Err(e)=>json!({"status":"rejected","reason":e})};println!("{result}")}

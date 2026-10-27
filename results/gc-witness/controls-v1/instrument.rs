use std::{fs,collections::HashSet,convert::Infallible};
use serde_json::{Value,json};
use wasmparser as p;
use wasm_encoder::{self as e,reencode::{self,Reencode}};
struct Instrument { target:HashSet<u32>, base:u32, global_done:bool, export_done:bool, sites:[u32;2] }
impl Instrument {
    fn globals(&mut self,g:&mut e::GlobalSection){
        for _ in 0..2 {g.global(e::GlobalType{val_type:e::ValType::I32,mutable:true,shared:false},&e::ConstExpr::i32_const(0));}
        self.global_done=true;
    }
}
impl Reencode for Instrument{
    type Error=Infallible;
    fn parse_global_section(&mut self,g:&mut e::GlobalSection,s:p::GlobalSectionReader<'_>)->Result<(),reencode::Error<Infallible>>{
        reencode::utils::parse_global_section(self,g,s)?;self.globals(g);Ok(())
    }
    fn parse_export_section(&mut self,x:&mut e::ExportSection,s:p::ExportSectionReader<'_>)->Result<(),reencode::Error<Infallible>>{
        reencode::utils::parse_export_section(self,x,s)?;
        x.export("__r_constructed",e::ExportKind::Global,self.base);
        x.export("__r_accessed",e::ExportKind::Global,self.base+1);self.export_done=true;Ok(())
    }
    fn intersperse_section_hook(&mut self,m:&mut e::Module,_a:Option<e::SectionId>,b:Option<e::SectionId>)->Result<(),reencode::Error<Infallible>>{
        use e::SectionId::*;
        if !self.global_done&&matches!(b,Some(Export|Start|Element|DataCount|Code|Data)|None){let mut g=e::GlobalSection::new();self.globals(&mut g);m.section(&g);}
        Ok(())
    }
    fn parse_function_body(&mut self,c:&mut e::CodeSection,b:p::FunctionBody<'_>)->Result<(),reencode::Error<Infallible>>{
        let mut f=self.new_function_with_parsed_locals(&b)?;let mut r=b.get_operators_reader()?;
        while !r.eof(){
            let op=r.read()?;use p::Operator::*;
            let target=match &op{
                StructNew{struct_type_index:i}|StructNewDefault{struct_type_index:i}=>Some((*i,0)),
                ArrayNew{array_type_index:i}|ArrayNewDefault{array_type_index:i}|ArrayNewFixed{array_type_index:i,..}|ArrayNewData{array_type_index:i,..}|ArrayNewElem{array_type_index:i,..}=>Some((*i,0)),
                StructGet{struct_type_index:i,..}|StructSet{struct_type_index:i,..}=>Some((*i,1)),
                ArrayGet{array_type_index:i}|ArraySet{array_type_index:i}=>Some((*i,1)),
                _=>None
            };
            f.instruction(&self.instruction(op)?);
            if let Some((i,k))=target{if self.target.contains(&i){
                self.sites[k]+=1;
                f.instruction(&e::Instruction::GlobalGet(self.base+k as u32));f.instruction(&e::Instruction::I32Const(1));f.instruction(&e::Instruction::I32Add);f.instruction(&e::Instruction::GlobalSet(self.base+k as u32));
            }}
        }
        c.function(&f);Ok(())
    }
}
pub fn run()->Result<Value,String>{
    let a:Vec<_>=std::env::args().collect();if a.len()!=6{return Err("instrument REFERENCE INDEX INPUT OUTPUT".into())}
    let mut v=p::Validator::new_with_features(p::WasmFeatures::all());let rb=fs::read(&a[2]).map_err(|e|e.to_string())?;
    let r=v.validate_all(&rb).map_err(|e|e.to_string())?;let i:u32=a[3].parse().map_err(|_|"index")?;
    if i>=r.as_ref().core_type_count_in_module(){return Err("index out of bounds".into())}
    let id=r.as_ref().core_type_at_in_module(i);v.reset();let cb=fs::read(&a[4]).map_err(|e|e.to_string())?;
    let c=v.validate_all(&cb).map_err(|e|e.to_string())?;let c=c.as_ref();let mut target=HashSet::new();
    for i in 0..c.core_type_count_in_module(){if c.core_type_at_in_module(i)==id{target.insert(i);}}
    let mut base=0;
    for pl in p::Parser::new(0).parse_all(&cb){match pl.map_err(|e|e.to_string())?{
        p::Payload::GlobalSection(s)=>base+=s.count(),
        p::Payload::ImportSection(s)=>for i in s{if matches!(i.map_err(|e|e.to_string())?.ty,p::TypeRef::Global(_)){base+=1}},
        p::Payload::ExportSection(s)=>for x in s{if x.map_err(|e|e.to_string())?.name.starts_with("__r_"){return Err("reserved export exists".into())}},
        _=>{}
    }}
    let mut inst=Instrument{target,base,global_done:false,export_done:false,sites:[0,0]};let mut m=e::Module::new();
    inst.parse_core_module(&mut m,p::Parser::new(0),&cb).map_err(|e|e.to_string())?;
    if !inst.export_done{return Err("requires existing export section".into())}
    let b=m.finish();p::Validator::new_with_features(p::WasmFeatures::all()).validate_all(&b).map_err(|e|e.to_string())?;
    fs::write(&a[5],b).map_err(|e|e.to_string())?;
    Ok(json!({"status":"instrumented","sites":inst.sites,"counter_global_base":base}))
}

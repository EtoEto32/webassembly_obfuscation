use std::{fs,convert::Infallible,collections::HashSet};
use serde_json::{Value,json};
use wasmparser as p;
use wasm_encoder::{self as e,reencode::{self,Reencode}};

fn kind(op:&p::Operator)->Option<(String,Option<u32>)>{
    let s=format!("{op:?}");let name=s.split_whitespace().next().unwrap();
    if !name.starts_with("Struct")&&!name.starts_with("Array")&&!name.starts_with("RefCast"){return None}
    use p::Operator::*;
    let index=match op{
        StructNew{struct_type_index:i}|StructNewDefault{struct_type_index:i}|StructGet{struct_type_index:i,..}|StructGetS{struct_type_index:i,..}|StructGetU{struct_type_index:i,..}|StructSet{struct_type_index:i,..}=>Some(*i),
        ArrayNew{array_type_index:i}|ArrayNewDefault{array_type_index:i}|ArrayNewFixed{array_type_index:i,..}|ArrayNewData{array_type_index:i,..}|ArrayNewElem{array_type_index:i,..}|ArrayGet{array_type_index:i}|ArrayGetS{array_type_index:i}|ArrayGetU{array_type_index:i}|ArraySet{array_type_index:i}|ArrayFill{array_type_index:i}=>Some(*i),
        _=>None
    };Some((name.into(),index))
}
struct I{base:u32,nfunc:u32,nsites:u32,nextfunc:u32,nextsite:u32,global_done:bool,export_done:bool,count:bool}
impl I{
    fn globals(&mut self,g:&mut e::GlobalSection){if self.count{for _ in 0..self.nfunc+2*self.nsites{g.global(e::GlobalType{val_type:e::ValType::I32,mutable:true,shared:false},&e::ConstExpr::i32_const(0));}}self.global_done=true;}
    fn increment(&self,f:&mut e::Function,index:u32){f.instruction(&e::Instruction::GlobalGet(index));f.instruction(&e::Instruction::I32Const(1));f.instruction(&e::Instruction::I32Add);f.instruction(&e::Instruction::GlobalSet(index));}
}
impl Reencode for I{
    type Error=Infallible;
    fn parse_global_section(&mut self,g:&mut e::GlobalSection,s:p::GlobalSectionReader<'_>)->Result<(),reencode::Error<Infallible>>{reencode::utils::parse_global_section(self,g,s)?;self.globals(g);Ok(())}
    fn parse_export_section(&mut self,x:&mut e::ExportSection,s:p::ExportSectionReader<'_>)->Result<(),reencode::Error<Infallible>>{
        reencode::utils::parse_export_section(self,x,s)?;
        if self.count{for i in 0..self.nfunc+2*self.nsites{x.export(&format!("__gap_{i}"),e::ExportKind::Global,self.base+i);}}
        self.export_done=true;Ok(())
    }
    fn intersperse_section_hook(&mut self,m:&mut e::Module,_a:Option<e::SectionId>,b:Option<e::SectionId>)->Result<(),reencode::Error<Infallible>>{
        use e::SectionId::*;if !self.global_done&&matches!(b,Some(Export|Start|Element|DataCount|Code|Data)|None){let mut g=e::GlobalSection::new();self.globals(&mut g);m.section(&g);}Ok(())
    }
    fn parse_function_body(&mut self,c:&mut e::CodeSection,b:p::FunctionBody<'_>)->Result<(),reencode::Error<Infallible>>{
        let mut f=self.new_function_with_parsed_locals(&b)?;
        if self.count{self.increment(&mut f,self.base+self.nextfunc);}self.nextfunc+=1;
        let mut r=b.get_operators_reader()?;
        while !r.eof(){let op=r.read()?;let site=kind(&op).is_some();
            if site&&self.count{self.increment(&mut f,self.base+self.nfunc+2*self.nextsite);}
            if matches!(&op,p::Operator::ArrayNew{..}|p::Operator::ArrayNewDefault{..}|p::Operator::ArrayNewData{..}|p::Operator::ArrayNewElem{..}){f.instruction(&e::Instruction::I32Const(31));f.instruction(&e::Instruction::I32And);}
            f.instruction(&self.instruction(op)?);
            if site{if self.count{self.increment(&mut f,self.base+self.nfunc+2*self.nextsite+1);}self.nextsite+=1;}
        }c.function(&f);Ok(())
    }
}
fn run()->Result<Value,String>{
    let a:Vec<_>=std::env::args().collect();if a.len()!=5{return Err("SHAPE INPUT OUTPUT count|plain".into())}
    let count=match a[4].as_str(){"count"=>true,"plain"=>false,_=>return Err("bad mode".into())};
    let rb=fs::read(&a[1]).map_err(|e|e.to_string())?;let b=fs::read(&a[2]).map_err(|e|e.to_string())?;if b.len()>1048576{return Err("size cap".into())}
    let mut validator=p::Validator::new_with_features(p::WasmFeatures::all());let reference=validator.validate_all(&rb).map_err(|e|e.to_string())?;let id=reference.as_ref().core_type_at_in_module(0);validator.reset();
    let types=validator.validate_all(&b).map_err(|e|e.to_string())?;let types=types.as_ref();let target:HashSet<u32>=(0..types.core_type_count_in_module()).filter(|&i|types.core_type_at_in_module(i)==id).collect();
    let mut base=0;let mut funcs=vec![];let mut sites=vec![];
    for pl in p::Parser::new(0).parse_all(&b){match pl.map_err(|e|e.to_string())?{
        p::Payload::ImportSection(s) if s.count()>0=>return Err("imports unsupported".into()),
        p::Payload::StartSection{..}=>return Err("start unsupported".into()),
        p::Payload::GlobalSection(s)=>base+=s.count(),
        p::Payload::ExportSection(s)=>for x in s{if x.map_err(|e|e.to_string())?.name.starts_with("__gap_"){return Err("reserved export".into())}},
        p::Payload::CodeSectionEntry(body)=>{let fi=funcs.len();let mut ops=body.get_operators_reader().map_err(|e|e.to_string())?;let mut calls=vec![];let mut nops=0;
            while !ops.eof(){let offset=ops.original_position();let op=ops.read().map_err(|e|e.to_string())?;nops+=1;if let p::Operator::Call{function_index}=op{calls.push(function_index);}
                if let Some((kind,index))=kind(&op){sites.push(json!({"site":sites.len(),"function":fi,"offset":offset,"kind":kind,"type_index":index,"target":index.map_or(false,|i|target.contains(&i))}));}}
            funcs.push(json!({"function":fi,"direct_calls":calls,"operators":nops}));
        },_=>{}
    }}
    let mut inst=I{base,nfunc:funcs.len() as u32,nsites:sites.len() as u32,nextfunc:0,nextsite:0,global_done:false,export_done:false,count};let mut m=e::Module::new();inst.parse_core_module(&mut m,p::Parser::new(0),&b).map_err(|e|e.to_string())?;
    if !inst.export_done{return Err("requires export section".into())}let out=m.finish();p::Validator::new_with_features(p::WasmFeatures::all()).validate_all(&out).map_err(|e|e.to_string())?;fs::write(&a[3],out).map_err(|e|e.to_string())?;
    Ok(json!({"status":"instrumented","mode":a[4],"functions":funcs,"sites":sites,"target_type_indices":target,"counter_count":if count{inst.nfunc+2*inst.nsites}else{0},"array_length_mask":31}))
}
fn main(){let result=match run(){Ok(x)=>x,Err(e)=>json!({"status":"error","reason":e})};println!("{result}");}

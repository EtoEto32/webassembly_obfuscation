//! Research validator for an explicitly restricted numeric Core-Wasm subset.
//! Metadata is checked by wasmparser; function bodies are checked below.
use std::{collections::HashMap, fs, hint::black_box, time::Instant};
use serde_json::{json, Value};
use wasmparser as p;

#[derive(Debug)]
struct Error { status: &'static str, message: String }
type R<T> = Result<T, Error>;
fn invalid(s: impl Into<String>) -> Error { Error{status:"invalid",message:s.into()} }
fn unsupported(s: impl Into<String>) -> Error { Error{status:"unsupported",message:s.into()} }
impl From<p::BinaryReaderError> for Error {
    fn from(e:p::BinaryReaderError)->Self { invalid(e.to_string()) }
}
fn ty(t:p::ValType)->R<u8> {
    Ok(match t {p::ValType::I32=>1,p::ValType::I64=>2,p::ValType::F32=>3,
        p::ValType::F64=>4,p::ValType::V128=>5,_=>return Err(unsupported("reference value type"))})
}
struct Pool { vectors:Vec<Vec<u8>>, ids:HashMap<Vec<u8>,usize> }
impl Pool {
    fn new()->Self {
        let mut x=Self{vectors:vec![],ids:HashMap::new()};
        for t in 0..=5 {x.intern(vec![t]);} x.intern(vec![]); x
    }
    fn intern(&mut self,v:Vec<u8>)->usize {
        if let Some(&i)=self.ids.get(&v) {return i;}
        let i=self.vectors.len();self.vectors.push(v.clone());self.ids.insert(v,i);i
    }
    fn len(&self,id:usize)->usize {self.vectors[id].len()}
}
#[derive(Clone,Copy)]
struct Sig { input:usize, output:usize }
#[derive(Clone,Copy,PartialEq)]
enum Kind {Root,Block,Loop,If,Else}
#[derive(Clone)]
enum Op {
    Enter(Kind,Sig), Else, End, Unreachable, Nop, Br(u32), BrIf(u32),
    BrTable(Vec<u32>,u32), Return, Call(Sig), Drop, Get(u32), Set(u32), Tee(u32),
    Select, TypedSelect(u8), Const(u8), Numeric{input:u8,arity:u8,output:u8},
}
struct Body { locals:Vec<u8>, output:usize, ops:Vec<Op> }
struct Program {pool:Pool,bodies:Vec<Body>}
fn block_type(t:p::BlockType,types:&[Sig])->R<Sig> {
    Ok(match t {
        p::BlockType::Empty=>Sig{input:6,output:6},
        p::BlockType::Type(t)=>Sig{input:6,output:ty(t)? as usize},
        p::BlockType::FuncType(i)=>*types.get(i as usize).ok_or_else(||invalid("block type index"))?,
    })
}
fn decode(op:p::Operator<'_>,types:&[Sig],functions:&[Sig])->R<Op> {
    use p::Operator::*;
    let numeric=|input,arity,output| Op::Numeric{input,arity,output};
    Ok(match op {
        Block{blockty}=>Op::Enter(Kind::Block,block_type(blockty,types)?),
        Loop{blockty}=>Op::Enter(Kind::Loop,block_type(blockty,types)?),
        If{blockty}=>Op::Enter(Kind::If,block_type(blockty,types)?),
        Else=>Op::Else,End=>Op::End,Unreachable=>Op::Unreachable,Nop=>Op::Nop,
        Br{relative_depth}=>Op::Br(relative_depth),BrIf{relative_depth}=>Op::BrIf(relative_depth),
        BrTable{targets}=>Op::BrTable(targets.targets().collect::<Result<Vec<_>,_>>()?,targets.default()),
        Return=>Op::Return,Call{function_index}=>Op::Call(*functions.get(function_index as usize).ok_or_else(||invalid("call index"))?),
        Drop=>Op::Drop,LocalGet{local_index}=>Op::Get(local_index),
        LocalSet{local_index}=>Op::Set(local_index),LocalTee{local_index}=>Op::Tee(local_index),
        Select=>Op::Select,TypedSelect{ty:t}=>Op::TypedSelect(ty(t)?),
        I32Const{..}=>Op::Const(1),I64Const{..}=>Op::Const(2),F32Const{..}=>Op::Const(3),
        F64Const{..}=>Op::Const(4),V128Const{..}=>Op::Const(5),
        I32Add|I32Sub|I32Mul|I32DivS|I32DivU|I32RemS|I32RemU|I32And|I32Or|I32Xor|I32Shl|I32ShrS|I32ShrU|I32Rotl|I32Rotr=>numeric(1,2,1),
        I64Add|I64Sub|I64Mul|I64DivS|I64DivU|I64RemS|I64RemU|I64And|I64Or|I64Xor|I64Shl|I64ShrS|I64ShrU|I64Rotl|I64Rotr=>numeric(2,2,2),
        I32Eqz|I32Clz|I32Ctz|I32Popcnt|I32Extend8S|I32Extend16S=>numeric(1,1,1),
        I64Eqz=>numeric(2,1,1),I64Clz|I64Ctz|I64Popcnt|I64Extend8S|I64Extend16S|I64Extend32S=>numeric(2,1,2),
        I32Eq|I32Ne|I32LtS|I32LtU|I32GtS|I32GtU|I32LeS|I32LeU|I32GeS|I32GeU=>numeric(1,2,1),
        I64Eq|I64Ne|I64LtS|I64LtU|I64GtS|I64GtU|I64LeS|I64LeU|I64GeS|I64GeU=>numeric(2,2,1),
        F32Add|F32Sub|F32Mul|F32Div|F32Min|F32Max|F32Copysign=>numeric(3,2,3),
        F64Add|F64Sub|F64Mul|F64Div|F64Min|F64Max|F64Copysign=>numeric(4,2,4),
        F32Abs|F32Neg|F32Ceil|F32Floor|F32Trunc|F32Nearest|F32Sqrt=>numeric(3,1,3),
        F64Abs|F64Neg|F64Ceil|F64Floor|F64Trunc|F64Nearest|F64Sqrt=>numeric(4,1,4),
        F32Eq|F32Ne|F32Lt|F32Gt|F32Le|F32Ge=>numeric(3,2,1),
        F64Eq|F64Ne|F64Lt|F64Gt|F64Le|F64Ge=>numeric(4,2,1),
        I32WrapI64=>numeric(2,1,1),I64ExtendI32S|I64ExtendI32U=>numeric(1,1,2),
        I32ReinterpretF32=>numeric(3,1,1),F32ReinterpretI32=>numeric(1,1,3),
        I64ReinterpretF64=>numeric(4,1,2),F64ReinterpretI64=>numeric(2,1,4),
        other=>return Err(unsupported(format!("operation {other:?}"))),
    })
}
fn prepare(bytes:&[u8])->R<Program> {
    if bytes.len()>4*1024*1024 {return Err(Error{status:"resource_limit",message:"4 MiB input cap".into()});}
    let mut validator=p::Validator::new_with_features(p::WasmFeatures::WASM2);
    let mut pool=Pool::new();let mut types=vec![];let mut functions=vec![];
    let mut imported=0;let mut bodies=vec![];
    for payload in p::Parser::new(0).parse_all(bytes) {
        let payload=payload?;
        match &payload {
            p::Payload::Version{encoding:p::Encoding::Module,..}|p::Payload::End(_)|
            p::Payload::CustomSection(_)|p::Payload::ExportSection(_)|p::Payload::StartSection{..}|
            p::Payload::CodeSectionStart{..}=>{},
            p::Payload::TypeSection(section)=> {
                for t in section.clone().into_iter_err_on_gc_types() {
                    let t=t.map_err(|e|unsupported(format!("non-flat function type: {e}")))?;
                    let input=pool.intern(t.params().iter().map(|x|ty(*x)).collect::<R<Vec<_>>>()?);
                    let output=pool.intern(t.results().iter().map(|x|ty(*x)).collect::<R<Vec<_>>>()?);
                    types.push(Sig{input,output});
                }
            },
            p::Payload::ImportSection(section)=> {
                for import in section.clone() {
                    match import?.ty {
                        p::TypeRef::Func(i)=>functions.push(*types.get(i as usize).ok_or_else(||invalid("import type index"))?),
                        _=>return Err(unsupported("non-function import")),
                    }
                } imported=functions.len();
            },
            p::Payload::FunctionSection(section)=> {
                for t in section.clone() {functions.push(*types.get(t? as usize).ok_or_else(||invalid("function type index"))?);}
            },
            p::Payload::CodeSectionEntry(body)=> {
                let sig=*functions.get(imported+bodies.len()).ok_or_else(||invalid("function/code count"))?;
                let mut locals=pool.vectors[sig.input].clone();
                for local in body.get_locals_reader()? {
                    let (count,t)=local?;let t=ty(t)?;
                    if locals.len()+count as usize>50_000 {return Err(Error{status:"resource_limit",message:"50,000 locals cap".into()});}
                    locals.extend(std::iter::repeat_n(t,count as usize));
                }
                let mut reader=body.get_operators_reader()?;let mut ops=vec![];
                while !reader.eof() {ops.push(decode(reader.read()?,&types,&functions)?);}
                bodies.push(Body{locals,output:sig.output,ops});
            },
            _=>return Err(unsupported("section outside numeric subset")),
        }
        // Func payload intentionally does not call FuncToValidate::into_validator:
        // the independently implemented kernel below checks its instructions.
        let _=validator.payload(&payload)?;
    }
    Ok(Program{pool,bodies})
}

#[derive(Default)]
struct Stats {compared:usize,fast:usize,max_values:usize,max_entries:usize,max_capacity_bytes:usize}
impl Stats {
    fn json(&self)->Value {json!({"compared_cells_upper_bound":self.compared,"identity_skipped_cells":self.fast,
        "max_logical_stack":self.max_values,"max_stack_entries":self.max_entries,"max_stack_capacity_bytes":self.max_capacity_bytes})}
}
// Equality is a byte-slice comparison; a mismatch falls back to Bottom-aware
// matching. 'compared' counts candidate cells, not CPU instructions or cycles.
fn equal(actual:&[u8],expected:&[u8],stats:&mut Stats)->bool {
    stats.compared+=actual.len();
    actual==expected || actual.iter().zip(expected).all(|(&a,&e)|a==0||a==e)
}
trait Stack:Default {
    fn len(&self)->usize;
    fn push(&mut self,id:usize,pool:&Pool,stats:&mut Stats);
    fn truncate(&mut self,n:usize);
    fn top(&self,pool:&Pool)->u8;
    fn matches(&self,id:usize,n:usize,pool:&Pool,stats:&mut Stats)->bool;
}
#[derive(Default)]
struct Flat {values:Vec<u8>}
impl Stack for Flat {
    fn len(&self)->usize {self.values.len()}
    fn push(&mut self,id:usize,p:&Pool,s:&mut Stats) {
        self.values.extend_from_slice(&p.vectors[id]);
        s.max_values=s.max_values.max(self.len());s.max_entries=s.max_entries.max(self.len());
        s.max_capacity_bytes=s.max_capacity_bytes.max(self.values.capacity());
    }
    fn truncate(&mut self,n:usize){self.values.truncate(n)}
    fn top(&self,_:&Pool)->u8{*self.values.last().unwrap()}
    fn matches(&self,id:usize,n:usize,p:&Pool,s:&mut Stats)->bool {
        let e=&p.vectors[id];equal(&self.values[self.len()-n..],&e[e.len()-n..],s)
    }
}
/// Strong ablation: retain the physical flat buffer across logical pops and
/// cache one exact signature certificate. No segmented representation.
#[derive(Default)]
struct CachedFlat {values:Vec<u8>,len:usize,certificate:Option<(usize,usize,usize)>}
impl Stack for CachedFlat {
    fn len(&self)->usize{self.len}
    fn push(&mut self,id:usize,p:&Pool,s:&mut Stats) {
        let n=p.len(id);if n==0{return;}
        let end=self.len+n;
        let reuse=self.certificate==Some((id,self.len,end));
        if !reuse {
            if let Some((_,start,stop))=self.certificate {
                if self.len<stop && end>start {self.certificate=None;}
            }
            self.values.resize(self.values.len().max(end),0);
            self.values[self.len..end].copy_from_slice(&p.vectors[id]);
            if n>1 || self.certificate.is_none(){self.certificate=Some((id,self.len,end));}
        }
        self.len=end;s.max_values=s.max_values.max(end);s.max_entries=s.max_entries.max(self.values.len());
        s.max_capacity_bytes=s.max_capacity_bytes.max(self.values.capacity());
    }
    fn truncate(&mut self,n:usize){self.len=n;}
    fn top(&self,_:&Pool)->u8{self.values[self.len-1]}
    fn matches(&self,id:usize,n:usize,p:&Pool,s:&mut Stats)->bool {
        if let Some((cached,start,end))=self.certificate {
            if cached==id && end==self.len && self.len-n>=start {s.fast+=n;return true;}
        }
        let e=&p.vectors[id];equal(&self.values[self.len-n..self.len],&e[e.len()-n..],s)
    }
}
#[derive(Clone,Copy)]
struct Chunk {id:usize,lo:usize,hi:usize}
#[derive(Default)]
struct Segmented {chunks:Vec<Chunk>,len:usize}
impl Stack for Segmented {
    fn len(&self)->usize{self.len}
    fn push(&mut self,id:usize,p:&Pool,s:&mut Stats) {
        let n=p.len(id);if n==0{return;}
        self.chunks.push(Chunk{id,lo:0,hi:n});self.len+=n;
        s.max_values=s.max_values.max(self.len);s.max_entries=s.max_entries.max(self.chunks.len());
        s.max_capacity_bytes=s.max_capacity_bytes.max(self.chunks.capacity()*std::mem::size_of::<Chunk>());
    }
    fn truncate(&mut self,n:usize) {
        let mut remove=self.len-n;self.len=n;
        while remove>0 {
            let c=self.chunks.last_mut().unwrap();let take=remove.min(c.hi-c.lo);
            c.hi-=take;remove-=take;if c.hi==c.lo {self.chunks.pop();}
        }
    }
    fn top(&self,p:&Pool)->u8 {let c=self.chunks.last().unwrap();p.vectors[c.id][c.hi-1]}
    fn matches(&self,id:usize,n:usize,p:&Pool,s:&mut Stats)->bool {
        let mut rem=n;let mut end=p.len(id);
        for c in self.chunks.iter().rev() {
            if rem==0 {break;}
            let k=rem.min(c.hi-c.lo);
            if c.id==id && c.hi==end {s.fast+=k;}
            else if !equal(&p.vectors[c.id][c.hi-k..c.hi],&p.vectors[id][end-k..end],s) {return false;}
            rem-=k;end-=k;
        }
        rem==0
    }
}
#[derive(Clone,Copy)]
struct Frame {kind:Kind,sig:Sig,height:usize,unreachable:bool}
struct Machine<'a,S:Stack> {stack:S,frames:Vec<Frame>,pool:&'a Pool,stats:Stats}
impl<'a,S:Stack> Machine<'a,S> {
    fn frame(&self)->R<Frame>{self.frames.last().copied().ok_or_else(||invalid("operator after function end"))}
    fn check(&mut self,id:usize)->R<usize> {
        let f=self.frame()?;let available=self.stack.len()-f.height;let n=self.pool.len(id);
        if n>available && !f.unreachable {return Err(invalid("operand underflow"));}
        let count=n.min(available);
        if !self.stack.matches(id,count,self.pool,&mut self.stats){return Err(invalid("operand type mismatch"));}
        Ok(count)
    }
    fn pop(&mut self,id:usize)->R<()> {let n=self.check(id)?;self.stack.truncate(self.stack.len()-n);Ok(())}
    fn push(&mut self,id:usize) {self.stack.push(id,self.pool,&mut self.stats);}
    fn any(&mut self)->R<u8> {
        let f=self.frame()?;
        if self.stack.len()==f.height {
            if f.unreachable{return Ok(0);}return Err(invalid("operand underflow"));
        }
        let t=self.stack.top(self.pool);self.stack.truncate(self.stack.len()-1);Ok(t)
    }
    fn dead(&mut self)->R<()> {
        let f=self.frames.last_mut().ok_or_else(||invalid("missing frame"))?;
        self.stack.truncate(f.height);f.unreachable=true;Ok(())
    }
    fn label(&self,depth:u32)->R<usize> {
        let idx=self.frames.len().checked_sub(depth as usize+1).ok_or_else(||invalid("branch depth"))?;
        let f=self.frames[idx];Ok(if f.kind==Kind::Loop {f.sig.input}else{f.sig.output})
    }
    fn close(&mut self)->R<Frame> {
        let f=self.frame()?;self.pop(f.sig.output)?;
        if self.stack.len()!=f.height {return Err(invalid("extra values at block end"));}
        self.frames.pop();Ok(f)
    }
    fn body(&mut self,b:&Body)->R<()> {
        self.frames.push(Frame{kind:Kind::Root,sig:Sig{input:6,output:b.output},height:0,unreachable:false});
        for op in &b.ops {
            self.frame()?;
            match op {
                Op::Enter(kind,sig)=> {
                    if *kind==Kind::If {self.pop(1)?;}
                    self.pop(sig.input)?;self.frames.push(Frame{kind:*kind,sig:*sig,height:self.stack.len(),unreachable:false});self.push(sig.input);
                },
                Op::Else=> {
                    if self.frame()?.kind!=Kind::If {return Err(invalid("else outside if"));}
                    let mut f=self.close()?;f.kind=Kind::Else;f.unreachable=false;self.frames.push(f);self.push(f.sig.input);
                },
                Op::End=> {
                    let f=self.close()?;
                    if f.kind==Kind::If && f.sig.input!=f.sig.output {return Err(invalid("implicit else type mismatch"));}
                    self.push(f.sig.output);
                },
                Op::Unreachable=>self.dead()?,Op::Nop=>{},
                Op::Br(depth)=> {let id=self.label(*depth)?;self.pop(id)?;self.dead()?;},
                Op::BrIf(depth)=> {self.pop(1)?;let id=self.label(*depth)?;self.pop(id)?;self.push(id);},
                Op::BrTable(targets,default)=> {
                    self.pop(1)?;let id=self.label(*default)?;
                    for target in targets {
                        let t=self.label(*target)?;
                        if self.pool.len(t)!=self.pool.len(id){return Err(invalid("br_table arity"));}
                        // The temporary Bottom operands used by the reference
                        // algorithm can remain implicit: all targets have the
                        // same arity and check the same original stack suffix.
                        self.check(t)?;
                    }
                    self.pop(id)?;self.dead()?;
                },
                Op::Return=>{let id=self.frames[0].sig.output;self.pop(id)?;self.dead()?;},
                Op::Call(sig)=>{self.pop(sig.input)?;self.push(sig.output);},
                Op::Drop=>{self.any()?;},
                Op::Get(i)=>self.push(*b.locals.get(*i as usize).ok_or_else(||invalid("local index"))? as usize),
                Op::Set(i)|Op::Tee(i)=> {
                    let t=*b.locals.get(*i as usize).ok_or_else(||invalid("local index"))? as usize;
                    self.pop(t)?;if matches!(op,Op::Tee(_)){self.push(t);}
                },
                Op::Select=> {
                    self.pop(1)?;let a=self.any()?;let b=self.any()?;
                    if a!=b && a!=0 && b!=0 {return Err(invalid("select type mismatch"));}
                    self.push(if a==0{b}else{a} as usize);
                },
                Op::TypedSelect(t)=>{self.pop(1)?;self.pop(*t as usize)?;self.pop(*t as usize)?;self.push(*t as usize);},
                Op::Const(t)=>self.push(*t as usize),
                Op::Numeric{input,arity,output}=>{for _ in 0..*arity {self.pop(*input as usize)?;}self.push(*output as usize);},
            }
        }
        if !self.frames.is_empty(){return Err(invalid("missing function end"));}
        Ok(())
    }
}
fn kernel<S:Stack>(program:&Program)->R<Stats> {
    let mut m=Machine::<S>{stack:S::default(),frames:vec![],pool:&program.pool,stats:Stats::default()};
    for body in &program.bodies {m.stack.truncate(0);m.body(body)?;}
    Ok(m.stats)
}
fn stock(bytes:&[u8])->R<()> {p::Validator::new_with_features(p::WasmFeatures::WASM2).validate_all(bytes)?;Ok(())}
fn current(bytes:&[u8])->R<()> {
    use wasmparser_current as c;
    c::Validator::new_with_features(c::WasmFeatures::WASM2).validate_all(bytes).map_err(|e|invalid(e.to_string()))?;Ok(())
}
/// Static opportunity inventory. This does NOT validate with the new kernel or
/// predict end-to-end speed: only explicit direct-call/block signature widths.
fn profile(path:&str)->R<Value> {
    let bytes=fs::read(path).map_err(|e|invalid(e.to_string()))?;
    current(&bytes)?;
    let mut types:Vec<(usize,usize)>=vec![];let mut funcs=vec![];
    let mut instructions=0usize;let mut uses=0usize;let mut max_width=0;
    let mut width_cells=0usize;let mut hist=std::collections::BTreeMap::<usize,usize>::new();
    let mut functions=0usize;let mut multi_block=0usize;let mut multi_call=0usize;
    for item in p::Parser::new(0).parse_all(&bytes) {
        match item? {
            p::Payload::TypeSection(s)=>for t in s.into_iter_err_on_gc_types() {
                let t=t.map_err(|e|unsupported(e.to_string()))?;types.push((t.params().len(),t.results().len()));
            },
            p::Payload::ImportSection(s)=>for i in s {if let p::TypeRef::Func(t)=i?.ty{funcs.push(t as usize);}},
            p::Payload::FunctionSection(s)=>for t in s {funcs.push(t? as usize);},
            p::Payload::CodeSectionEntry(body)=> {
                functions+=1;let mut ops=body.get_operators_reader()?;
                while !ops.eof() {
                    instructions+=1;let sig=match ops.read()? {
                        p::Operator::Call{function_index}=> {
                            let s=types[funcs[function_index as usize]];
                            if s.0>1||s.1>1{multi_call+=1;}Some(s)
                        },
                        p::Operator::Block{blockty}|p::Operator::Loop{blockty}|p::Operator::If{blockty}=>{
                            let s=match blockty {p::BlockType::Empty=>(0,0),p::BlockType::Type(_)=>(0,1),p::BlockType::FuncType(t)=>types[t as usize]};
                            if s.0>0||s.1>1{multi_block+=1;}Some(s)
                        },_=>None,
                    };
                    if let Some((input,output))=sig {
                        let w=input.max(output);*hist.entry(w).or_default()+=1;
                        uses+=1;max_width=max_width.max(w);width_cells+=input+output;
                    }
                }
            },_=>{},
        }
    }
    Ok(json!({"path":path,"bytes":bytes.len(),"functions":functions,"instructions":instructions,"explicit_signature_uses":uses,
        "max_explicit_signature_width":max_width,"sum_explicit_parameter_result_cells":width_cells,
        "width_histogram":hist,"multi_value_block_uses":multi_block,"multi_parameter_or_result_call_uses":multi_call}))
}
fn outcome<T>(r:R<T>,ok:impl FnOnce(T)->Value)->Value {
    match r {Ok(x)=>json!({"status":"valid","data":ok(x)}),Err(e)=>json!({"status":e.status,"message":e.message})}
}
fn check(path:&str)->Value {
    let bytes=match fs::read(path){Ok(x)=>x,Err(e)=>return json!({"path":path,"io_error":e.to_string()})};
    let reference=outcome(stock(&bytes),|_|Value::Null);
    let mut row=json!({"path":path,"bytes":bytes.len(),"stock":reference});
    row["stock-current"]=outcome(current(&bytes),|_|Value::Null);
    match prepare(&bytes) {
        Ok(prog)=> {
            row["flat"]=outcome(kernel::<Flat>(&prog),|s|s.json());
            row["segment"]=outcome(kernel::<Segmented>(&prog),|s|s.json());
            row["cached"]=outcome(kernel::<CachedFlat>(&prog),|s|s.json());
            row["pool_cells"]=json!(prog.pool.vectors.iter().map(Vec::len).sum::<usize>());
        },
        Err(e)=>{row["flat"]=json!({"status":e.status,"message":e.message});row["segment"]=row["flat"].clone();row["cached"]=row["flat"].clone();}
    }row
}
fn benchmark(path:&str,mode:&str,repeats:usize)->R<Value> {
    let bytes=fs::read(path).map_err(|e|invalid(e.to_string()))?;
    let is_stock=mode.starts_with("stock");
    let p=if is_stock {None}else{Some(prepare(&bytes)?)};
    let run_kernel=|| {let p=p.as_ref().unwrap();if mode=="flat" {kernel::<Flat>(p)}else if mode=="cached" {kernel::<CachedFlat>(p)}else{kernel::<Segmented>(p)}};
    let run_full=||->R<()> {
        if mode=="stock"{stock(black_box(&bytes))?;}
        else if mode=="stock-current"{current(black_box(&bytes))?;}
        else {let q=prepare(black_box(&bytes))?;let s=if mode=="flat"{kernel::<Flat>(&q)?}else if mode=="cached"{kernel::<CachedFlat>(&q)?}else{kernel::<Segmented>(&q)?};black_box(s);}
        Ok(())
    };
    for _ in 0..5 {run_full()?;if !is_stock {black_box(run_kernel()?);}}
    // Calibrate batches to >= 10 ms where possible; report per-validation time.
    let t=Instant::now();for _ in 0..5 {run_full()?;}
    let iterations=((0.01/(t.elapsed().as_secs_f64()/5.0)).ceil() as usize).clamp(1,512);
    let mut full=vec![];let mut kernels=vec![];let mut prep=vec![];
    for _ in 0..repeats {
        let t=Instant::now();for _ in 0..iterations {run_full()?;}full.push(t.elapsed().as_secs_f64()/iterations as f64);
        if !is_stock {
            let t=Instant::now();for _ in 0..iterations {black_box(run_kernel()?);}kernels.push(t.elapsed().as_secs_f64()/iterations as f64);
            let t=Instant::now();for _ in 0..iterations {black_box(prepare(black_box(&bytes))?);}prep.push(t.elapsed().as_secs_f64()/iterations as f64);
        }
    }
    let stats=if is_stock {Value::Null}else{run_kernel()?.json()};
    Ok(json!({"path":path,"mode":mode,"bytes":bytes.len(),"warmup":5,"calibration_calls":5,"batch_iterations":iterations,"end_to_end_s":full,
        "kernel_s":kernels,"prepare_s":prep,"stats":stats,"peak_process_bytes":peak_memory(),
        "pool_cells":p.as_ref().map(|p|p.pool.vectors.iter().map(Vec::len).sum::<usize>())}))
}
#[cfg(windows)]
fn peak_memory()->Option<usize> {
    #[repr(C)] struct Counters{cb:u32,faults:u32,peak:usize,working:usize,paged_peak:usize,paged:usize,nonpaged_peak:usize,nonpaged:usize,pagefile:usize,pagefile_peak:usize}
    #[link(name="kernel32")] unsafe extern "system"{fn GetCurrentProcess()->*mut std::ffi::c_void;}
    #[link(name="psapi")] unsafe extern "system"{fn GetProcessMemoryInfo(p:*mut std::ffi::c_void,c:*mut Counters,size:u32)->i32;}
    let mut c: Counters=unsafe{std::mem::zeroed()};c.cb=std::mem::size_of::<Counters>() as u32;
    if unsafe{GetProcessMemoryInfo(GetCurrentProcess(),&mut c,c.cb)}!=0 {Some(c.peak)}else{None}
}
#[cfg(not(windows))] fn peak_memory()->Option<usize>{None}
fn main() {
    let args:Vec<String>=std::env::args().collect();
    match args.get(1).map(String::as_str) {
        Some("profile") if args.len()>2=>for path in &args[2..] {println!("{}",json!({"path":path,"profile":outcome(profile(path),|v|v)}));},
        Some("check") if args.len()>2=>for path in &args[2..] {println!("{}",check(path));},
        Some("bench") if args.len()==5 && ["flat","segment","cached","stock","stock-current"].contains(&args[3].as_str())=> {
            let n=args[4].parse::<usize>().unwrap_or(0);
            if !(1..=1000).contains(&n) {eprintln!("repetitions must be 1..1000");std::process::exit(2);}
            match benchmark(&args[2],&args[3],n) {
                Ok(v)=>println!("{v}"),Err(e)=>{println!("{}",json!({"status":e.status,"message":e.message}));std::process::exit(1);}
            }
        },
        _=>{eprintln!("signature-stack check FILE... | bench FILE flat|cached|segment|stock REPETITIONS");std::process::exit(2);}
    }
}

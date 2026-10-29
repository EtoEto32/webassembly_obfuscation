use std::{convert::Infallible, fs, time::Instant};
use wasm_encoder::{self as e, reencode::{self, Reencode}, Instruction as I};
use wasmparser::{self as p, Payload, TypeRef};

type R<T=()> = Result<T, reencode::Error<Infallible>>;
struct Rewrite {
    refs: bool,
    imported_funcs: u32,
    imported_globals: u32,
    defined_types: Vec<u32>,
    types: Vec<p::FuncType>,
    import_written: bool,
}
impl Rewrite {
    fn add_gate(&mut self, section: &mut e::ImportSection) {
        section.import("__failure_gate", "alive", e::EntityType::Global(e::GlobalType {
            val_type: e::ValType::I32, mutable: true, shared: false,
        }));
        self.import_written = true;
    }
    fn guard(&self, f: &mut e::Function) {
        f.instruction(&I::GlobalGet(self.imported_globals));
        f.instruction(&I::I32Eqz);
        f.instruction(&I::If(e::BlockType::Empty));
        f.instruction(&I::Unreachable);
        f.instruction(&I::End);
    }
}
impl Reencode for Rewrite {
    type Error = Infallible;
    fn function_index(&mut self, index: u32) -> u32 {
        if self.refs && index >= self.imported_funcs {
            index + self.defined_types.len() as u32
        } else { index }
    }
    fn global_index(&mut self, index: u32) -> u32 {
        index + u32::from(index >= self.imported_globals)
    }
    fn start_section(&mut self, index: u32) -> u32 { index }
    fn instruction<'a>(&mut self, op: p::Operator<'a>) -> R<I<'a>> {
        // Only reference-bearing uses go through wrappers. Direct calls keep
        // their original function index, including recursive and tail calls.
        match op {
            p::Operator::Call { function_index } => Ok(I::Call(function_index)),
            p::Operator::ReturnCall { function_index } => Ok(I::ReturnCall(function_index)),
            x => reencode::utils::instruction(self, x),
        }
    }
    fn parse_import_section(&mut self, imports: &mut e::ImportSection, section: p::ImportSectionReader<'_>) -> R {
        reencode::utils::parse_import_section(self, imports, section)?;
        self.add_gate(imports); Ok(())
    }
    fn intersperse_section_hook(&mut self, module: &mut e::Module, _: Option<e::SectionId>, before: Option<e::SectionId>) -> R {
        if !self.import_written && before.map_or(true, |s| (s as u8) > (e::SectionId::Import as u8)) {
            let mut imports = e::ImportSection::new();
            self.add_gate(&mut imports); module.section(&imports);
        }
        Ok(())
    }
    fn parse_function_section(&mut self, functions: &mut e::FunctionSection, section: p::FunctionSectionReader<'_>) -> R {
        reencode::utils::parse_function_section(self, functions, section)?;
        if self.refs { for ty in &self.defined_types { functions.function(*ty); } }
        Ok(())
    }
    fn parse_function_body(&mut self, code: &mut e::CodeSection, body: p::FunctionBody<'_>) -> R {
        let mut f = self.new_function_with_parsed_locals(&body)?;
        if !self.refs { self.guard(&mut f); }
        let mut reader = body.get_operators_reader()?;
        while !reader.eof() { f.instruction(&self.parse_instruction(&mut reader)?); }
        code.function(&f); Ok(())
    }
    fn parse_code_section(&mut self, code: &mut e::CodeSection, section: p::CodeSectionReader<'_>) -> R {
        reencode::utils::parse_code_section(self, code, section)?;
        if self.refs {
            for (n, ty) in self.defined_types.iter().enumerate() {
                let mut f = e::Function::new([]);
                self.guard(&mut f);
                for i in 0..self.types[*ty as usize].params().len() { f.instruction(&I::LocalGet(i as u32)); }
                f.instruction(&I::ReturnCall(self.imported_funcs + n as u32));
                f.instruction(&I::End);
                code.function(&f);
            }
        }
        Ok(())
    }
    fn parse_custom_section(&mut self, _: &mut e::Module, _: p::CustomSectionReader<'_>) -> R {
        // Relocation/name/debug offsets would be stale. This prototype strips
        // all custom sections and states that limitation in its manifest.
        Ok(())
    }
}
fn run() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() != 4 || !["entry", "refs"].contains(&args[1].as_str()) {
        return Err("usage: failure-revocation entry|refs INPUT.wasm OUTPUT.wasm".into());
    }
    if std::path::Path::new(&args[3]).exists() { return Err("output already exists".into()); }
    let bytes = fs::read(&args[2])?;
    let start = Instant::now();
    let features = p::WasmFeatures::WASM2 | p::WasmFeatures::TAIL_CALL;
    p::Validator::new_with_features(features).validate_all(&bytes)?;
    let mut r = Rewrite { refs: args[1] == "refs", imported_funcs: 0, imported_globals: 0,
        defined_types: vec![], types: vec![], import_written: false };
    for payload in p::Parser::new(0).parse_all(&bytes) {
        match payload? {
            Payload::TypeSection(types) => {
                for ty in types.into_iter_err_on_gc_types() { r.types.push(ty?); }
            }
            Payload::ImportSection(imports) => for import in imports {
                let import = import?;
                if import.module == "__failure_gate" { return Err("reserved import namespace".into()); }
                match import.ty { TypeRef::Func(_) => r.imported_funcs += 1,
                    TypeRef::Global(_) => r.imported_globals += 1, _ => {} }
            }
            Payload::FunctionSection(funcs) => for ty in funcs { r.defined_types.push(ty?); },
            _ => {}
        }
    }
    let mut output = e::Module::new();
    r.parse_core_module(&mut output, p::Parser::new(0), &bytes)?;
    let output = output.finish();
    p::Validator::new_with_features(features).validate_all(&output)?;
    let elapsed = start.elapsed().as_secs_f64();
    fs::write(&args[3], &output)?;
    println!("{}", serde_json::json!({"mode":args[1], "inputBytes":bytes.len(), "outputBytes":output.len(),
        "gateGlobal":r.imported_globals,"definedFunctions":r.defined_types.len(),
        "wrappers":if r.refs {r.defined_types.len()} else {0}, "transformSeconds":elapsed,
        "validation":"wasmparser 0.227.1 WASM2 + TAIL_CALL", "customSections":"removed"}));
    Ok(())
}
fn main() { if let Err(e) = run() { eprintln!("{e}"); std::process::exit(2); } }

use serde_json::{json, Value};
use std::{collections::BTreeMap, env, fs};
use wasmparser::{DataKind, ElementKind, Operator, Parser, Payload, TypeRef, Validator, WasmFeatures};

fn inspect(bytes: &[u8]) -> Result<Value, String> {
    Validator::new_with_features(WasmFeatures::all())
        .validate_all(bytes).map_err(|e| e.to_string())?;
    let mut imports = vec![];
    let mut function = 0_u32;
    let mut counts: BTreeMap<&str, usize> = BTreeMap::new();
    let mut functions = vec![];
    let mut data = vec![];
    let mut elements = vec![];
    let mut memories = vec![];
    let mut exports = vec![];
    let mut start = None;
    for payload in Parser::new(0).parse_all(bytes) {
        match payload.map_err(|e| e.to_string())? {
            Payload::ImportSection(reader) => for imp in reader {
                let imp = imp.map_err(|e| e.to_string())?;
                if let TypeRef::Func(_) = imp.ty { function += 1; }
                if let TypeRef::Memory(m) = imp.ty { memories.push(json!({"imported": true, "shared": m.shared, "initial": m.initial})); }
                imports.push(json!({"module": imp.module, "name": imp.name, "type": format!("{:?}", imp.ty)}));
            },
            Payload::MemorySection(reader) => for m in reader {
                let m = m.map_err(|e| e.to_string())?;
                memories.push(json!({"imported": false, "shared": m.shared, "initial": m.initial}));
            },
            Payload::StartSection {func, ..} => start = Some(func),
            Payload::ExportSection(reader) => for ex in reader {
                let ex = ex.map_err(|e| e.to_string())?;
                exports.push(json!({"name": ex.name, "kind": format!("{:?}", ex.kind), "index": ex.index}));
            },
            Payload::DataSection(reader) => for segment in reader {
                let segment = segment.map_err(|e| e.to_string())?;
                data.push(json!({"length": segment.data.len(), "passive": matches!(segment.kind, DataKind::Passive)}));
            },
            Payload::ElementSection(reader) => for segment in reader {
                let segment = segment.map_err(|e| e.to_string())?;
                let kind = match segment.kind {ElementKind::Passive => "passive", ElementKind::Declared => "declarative", ElementKind::Active{..} => "active"};
                elements.push(json!({"kind": kind}));
            },
            Payload::CodeSectionEntry(body) => {
                let mut reader = body.get_operators_reader().map_err(|e| e.to_string())?;
                let mut local: BTreeMap<&str, usize> = BTreeMap::new();
                let mut sites = vec![];
                let mut calls = vec![];
                let mut ordinal = 0_usize;
                while !reader.eof() {
                    let offset = reader.original_position();
                    let op = reader.read().map_err(|e| e.to_string())?;
                    let target = match op {
                        Operator::DataDrop{data_index} => Some(("data.drop",data_index)),
                        Operator::MemoryInit{data_index,..} => Some(("memory.init",data_index)),
                        Operator::ElemDrop{elem_index} => Some(("elem.drop",elem_index)),
                        Operator::TableInit{elem_index,..} => Some(("table.init",elem_index)),
                        Operator::Call{function_index} => { if calls.len()<512 { calls.push(function_index); } None },
                        _ => None,
                    };
                    if let Some((name,segment)) = target {
                        *counts.entry(name).or_default() += 1;
                        *local.entry(name).or_default() += 1;
                        if sites.len()<2048 { sites.push(json!({"operator": name,"segment": segment,"offset": offset,"ordinal": ordinal})); }
                    }
                    ordinal += 1;
                }
                if !local.is_empty() { functions.push(json!({"functionIndex": function,"counts": local,"sites": sites,"directCallsPrefix": calls,"operators": ordinal})); }
                function += 1;
            },
            _ => {},
        }
    }
    Ok(json!({"status": "complete", "counts": counts, "functions": functions, "data": data, "elements": elements,
        "memories": memories, "imports": imports, "exports": exports, "start": start,
        "validator": "wasmparser 0.227.1 all features; custom metadata not validated"}))
}

fn main() {
    let path = env::args().nth(1).expect("input .wasm");
    let result = match fs::read(path) {
        Ok(bytes) => inspect(&bytes).unwrap_or_else(|reason| json!({"status": "validation-or-parse-failure", "reason": reason})),
        Err(err) => json!({"status": "read-failure", "reason": err.to_string()}),
    };
    println!("{}", result);
}

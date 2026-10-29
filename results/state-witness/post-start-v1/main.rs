use serde_json::{json, Value};
use std::{collections::{BTreeMap, BTreeSet}, env, fs};
use wasmparser::{ConstExpr, DataKind, ElementItems, ElementKind, Encoding, ExternalKind, Operator, Parser, Payload, TableInit, TypeRef, Validator, WasmFeatures};

fn constant_references(expr: ConstExpr<'_>, roots: &mut BTreeSet<u32>) -> Result<(), String> {
    let mut reader = expr.get_operators_reader();
    while !reader.eof() {
        if let Operator::RefFunc { function_index } = reader.read().map_err(|e| e.to_string())? { roots.insert(function_index); }
    }
    Ok(())
}

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
    let mut roots = BTreeSet::new();
    let mut graph: BTreeMap<u32, BTreeSet<u32>> = BTreeMap::new();
    let mut consumers: BTreeMap<u32, BTreeSet<String>> = BTreeMap::new();
    for payload in Parser::new(0).parse_all(bytes) {
        match payload.map_err(|e| e.to_string())? {
            Payload::Version{encoding: Encoding::Component, ..} => return Err("component index spaces excluded".into()),
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
                if ex.kind == ExternalKind::Func { roots.insert(ex.index); }
                exports.push(json!({"name": ex.name, "kind": format!("{:?}", ex.kind), "index": ex.index}));
            },
            Payload::GlobalSection(reader) => for global in reader {
                constant_references(global.map_err(|e| e.to_string())?.init_expr, &mut roots)?;
            },
            Payload::TableSection(reader) => for table in reader {
                if let TableInit::Expr(expr) = table.map_err(|e| e.to_string())?.init { constant_references(expr, &mut roots)?; }
            },
            Payload::DataSection(reader) => for segment in reader {
                let segment = segment.map_err(|e| e.to_string())?;
                data.push(json!({"length": segment.data.len(), "passive": matches!(segment.kind, DataKind::Passive)}));
            },
            Payload::ElementSection(reader) => for segment in reader {
                let segment = segment.map_err(|e| e.to_string())?;
                match segment.items {
                    ElementItems::Functions(reader) => for index in reader { roots.insert(index.map_err(|e| e.to_string())?); },
                    ElementItems::Expressions(_,reader) => for expr in reader { constant_references(expr.map_err(|e| e.to_string())?, &mut roots)?; },
                }
                let kind = match segment.kind {ElementKind::Passive => "passive", ElementKind::Declared => "declarative", ElementKind::Active{..} => "active"};
                elements.push(json!({"kind": kind}));
            },
            Payload::CodeSectionEntry(body) => {
                let mut reader = body.get_operators_reader().map_err(|e| e.to_string())?;
                let mut local: BTreeMap<&str, usize> = BTreeMap::new();
                let mut sites = vec![];
                let mut calls = vec![];
                let mut all_calls = BTreeSet::new();
                let mut ordinal = 0_usize;
                while !reader.eof() {
                    let offset = reader.original_position();
                    let op = reader.read().map_err(|e| e.to_string())?;
                    let target = match op {
                        Operator::DataDrop{data_index} => Some(("data.drop",data_index)),
                        Operator::MemoryInit{data_index,..} => Some(("memory.init",data_index)),
                        Operator::ElemDrop{elem_index} => Some(("elem.drop",elem_index)),
                        Operator::TableInit{elem_index,..} => Some(("table.init",elem_index)),
                        Operator::ArrayNewData{array_data_index,..} => Some(("array.new_data",array_data_index)),
                        Operator::ArrayInitData{array_data_index,..} => Some(("array.init_data",array_data_index)),
                        Operator::ArrayNewElem{array_elem_index,..} => Some(("array.new_elem",array_elem_index)),
                        Operator::ArrayInitElem{array_elem_index,..} => Some(("array.init_elem",array_elem_index)),
                        Operator::Call{function_index} | Operator::ReturnCall{function_index} => { all_calls.insert(function_index); if calls.len()<512 { calls.push(function_index); } None },
                        Operator::RefFunc{function_index} => { roots.insert(function_index); None },
                        _ => None,
                    };
                    if let Some((name,segment)) = target {
                        *counts.entry(name).or_default() += 1;
                        *local.entry(name).or_default() += 1;
                        if sites.len()<2048 { sites.push(json!({"operator": name,"segment": segment,"offset": offset,"ordinal": ordinal})); }
                        if name != "data.drop" && name != "elem.drop" {
                            let kind = if name == "memory.init" || name.ends_with("_data") { "data" } else { "elem" };
                            consumers.entry(function).or_default().insert(format!("{kind}:{segment}"));
                        }
                    }
                    ordinal += 1;
                }
                if !local.is_empty() { functions.push(json!({"functionIndex": function,"counts": local,"sites": sites,"directCallsPrefix": calls,"operators": ordinal})); }
                graph.insert(function,all_calls);
                function += 1;
            },
            _ => {},
        }
    }
    let mut reachable = roots.clone();
    let mut work: Vec<_> = roots.iter().copied().collect();
    while let Some(caller) = work.pop() {
        if let Some(callees) = graph.get(&caller) {
            for &callee in callees { if reachable.insert(callee) { work.push(callee); } }
        }
    }
    let live_readers: BTreeMap<_,_> = consumers.iter().filter(|(f,_)| reachable.contains(f)).map(|(f,s)|(*f,s.clone())).collect();
    Ok(json!({"status": "complete", "counts": counts, "functions": functions, "data": data, "elements": elements,
        "memories": memories, "imports": imports, "exports": exports, "start": start,
        "validator": "wasmparser 0.227.1 all features; custom metadata not validated",
        "postInstantiation": {"roots": roots,"reachableFunctions": reachable,"callsByFunction": graph,"allSegmentReaders": consumers,
            "reachableSegmentReaders": live_readers,"allLifetimeDifferencesIrrelevant": live_readers.is_empty(),
            "premise": "Completed instantiation, no retained active frames/continuations, only segment-lifetime differences. Exported functions and every literal function reference are conservative roots. Host obtains internal function references only through ordinary Wasm interfaces. No debugger/engine-private introspection."}}))
}

fn main() {
    let path = env::args().nth(1).expect("input .wasm");
    let result = match fs::read(path) {
        Ok(bytes) => inspect(&bytes).unwrap_or_else(|reason| json!({"status": "validation-or-parse-failure", "reason": reason})),
        Err(err) => json!({"status": "read-failure", "reason": err.to_string()}),
    };
    println!("{}", result);
}

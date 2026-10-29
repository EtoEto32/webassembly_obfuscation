use egg::*;
use std::io::{self, Write};
use std::time::Instant;

struct Negative;
impl CostFunction<SymbolLang> for Negative {
    type Cost = i64;
    fn cost<C: FnMut(Id) -> i64>(&mut self, n: &SymbolLang, mut c: C) -> i64 {
        n.fold(0, |s, id| s + c(id)) - 1
    }
}

fn main() {
    let mode = std::env::args().nth(1).expect("mode required");
    assert!(["positive", "negative", "one-rule", "unmatched"].contains(&mode.as_str()));
    let mut rules: Vec<Rewrite<SymbolLang, ()>> = vec![
        rewrite!("add-to-and-or"; "(+ ?x ?y)" => "(+ (& ?x ?y) (| ?x ?y))")
    ];
    if mode != "one-rule" {
        rules.push(rewrite!("or-to-add"; "(| ?x ?y)" => "(+ (+ ?x ?y) (+ 1 (| (~ ?x) (~ ?y))))"));
    }
    let input: RecExpr<SymbolLang> = if mode == "unmatched" { "(== x y)" } else { "(+ x y)" }.parse().unwrap();
    let started = Instant::now();
    let runner = Runner::default().with_expr(&input).with_node_limit(60)
        .with_iter_limit(3).run(&rules);
    println!("SATURATION_DONE classes={} nodes={} stop={:?} micros={}",
             runner.egraph.number_of_classes(), runner.egraph.total_size(),
             runner.stop_reason, started.elapsed().as_micros());
    println!("GRAPH {:?}", runner.egraph.dump());
    io::stdout().flush().unwrap();
    let root = runner.roots[0];
    println!("EXTRACTION_START {mode}");
    io::stdout().flush().unwrap();
    let started = Instant::now();
    if mode == "positive" {
        let extract = Extractor::new(&runner.egraph, AstSize);
        let (cost, expr) = extract.find_best(root);
        println!("EXTRACTION_DONE cost={cost} expr={expr} micros={}", started.elapsed().as_micros());
    } else {
        let extract = Extractor::new(&runner.egraph, Negative);
        let (cost, expr) = extract.find_best(root);
        println!("EXTRACTION_DONE cost={cost} expr={expr} micros={}", started.elapsed().as_micros());
    }
}

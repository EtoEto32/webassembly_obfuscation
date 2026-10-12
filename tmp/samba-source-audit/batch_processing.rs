use egg::*;
use egg::{EGraph, Language, RecExpr, CostFunction, Extractor};
use std::fs::File;
use std::io::{BufReader, BufRead, Write};
use std::time::Instant;

/// cost function that tries to maximize AST size by returning the negative size
struct NegSizeCostFn;

impl<L: Language> CostFunction<L> for NegSizeCostFn {
    type Cost = i64;

    fn cost<C>(&mut self, enode: &L, mut child_costs: C) -> Self::Cost
    where
        C: FnMut(Id) -> Self::Cost,
    {
        let sum_child_costs = enode.fold(0, |acc, child_id| acc + child_costs(child_id));
        sum_child_costs - 1
    }
}

fn extract_largest_expr<L: Language>(
    egraph: &EGraph<L, ()>,
    root: Id
) -> RecExpr<L> {
    let extractor = Extractor::new(egraph, NegSizeCostFn);
    let (_cost, expr) = extractor.find_best(root);
    expr
}

fn run_in_thread(
    expr: RecExpr<SymbolLang>,
    rules: Vec<Rewrite<SymbolLang, ()>>,
    node_limit: usize
) -> Result<RecExpr<SymbolLang>, ()> 
{
    use std::thread;

    let handle = thread::spawn(move || {
        let runner = Runner::default()
            .with_expr(&expr)
            .with_node_limit(node_limit)
            .with_iter_limit(3)
            .run(&rules);

        let (egraph, root) = (runner.egraph, runner.roots[0]);
        Ok::<RecExpr<SymbolLang>, ()>(extract_largest_expr(&egraph, root))
    });

    match handle.join() {
        Ok(Ok(best_expr)) => Ok(best_expr),
        _ => Err(()),
    }
}

fn main() -> Result<(), std::io::Error> {

    let rules: &[Rewrite<SymbolLang, ()>] = &[
        // Commutative Properties
        rewrite!("commute-mul"; "(* ?x ?y)" => "(* ?y ?x)"),
        rewrite!("commute-add"; "(+ ?x ?y)" => "(+ ?y ?x)"),
        rewrite!("commute-and"; "(& ?x ?y)" => "(& ?y ?x)"),
        rewrite!("commute-xor"; "(^ ?x ?y)" => "(^ ?y ?x)"),
        rewrite!("commute-or";  "(| ?x ?y)" => "(| ?y ?x)"),

        // Associative Properties
        rewrite!("assoc-mul"; "(* ?x (* ?y ?z))" => "(* (* ?x ?y) ?z)"),
        rewrite!("assoc-add"; "(+ ?x (+ ?y ?z))" => "(+ (+ ?x ?y) ?z)"),
        rewrite!("assoc-and"; "(& ?x (& ?y ?z))" => "(& (& ?x ?y) ?z)"),
        rewrite!("assoc-xor"; "(^ ?x (^ ?y ?z))" => "(^ (^ ?x ?y) ?z)"),
        rewrite!("assoc-or";  "(| ?x (| ?y ?z))" => "(| (| ?x ?y) ?z)"),

        // Boolean & Arithmetic Transformations
        rewrite!("not-mul"; "(~ (* ?x ?y))" => "(+ (* (~ ?x) ?y) (- ?y 1))"),
        rewrite!("not-add"; "(~ (+ ?x ?y))" => "(+ (~ ?x) (+ (~ ?y) 1))"),
        rewrite!("not-sub"; "(~ (- ?x ?y))" => "(- (~ ?x) (+ (~ ?y) 1))"),
        rewrite!("not-and"; "(~ (& ?x ?y))" => "(| (~ ?x) (~ ?y))"),
        rewrite!("not-xor"; "(~ (^ ?x ?y))" => "(| (& ?x ?y) (~ (| ?x ?y)))"),
        rewrite!("not-or";  "(~ (| ?x ?y))" => "(& (~ ?x) (~ ?y))"),
        rewrite!("neg-mul"; "(- (* ?x ?y))" => "(* (- ?x) ?y)"),
        rewrite!("sub-to-add"; "(- ?x ?y)" => "(+ ?x (- ?y))"),
        rewrite!("neg-to-not"; "(- ?x)" => "(+ (~ ?x) 1)"),
        //rewrite!("neg-to-not2"; "(- ?x)" => "(~ (- ?x 1))"),

        // Distribution Rules
        rewrite!("distribute-mul"; "(* ?x (+ ?y ?z))" => "(+ (* ?x ?y) (* ?x ?z))"),
        rewrite!("distribute-sub"; "(* ?x (- ?y ?z))" => "(- (* ?x ?y) (* ?x ?z))"),
        rewrite!("factor-mul"; "(+ (* ?x ?y) ?y)" => "(* (+ ?x 1) ?y)"),
        rewrite!("double-add"; "(* 2 ?x)" => "(+ ?x ?x)"),
        rewrite!("neg-distribute"; "(- (+ ?x ?y))" => "(+ (- ?x) (- ?y))"),
        //rewrite!("mul_to_sum"; "(* ?x ?y)" => "(+ (* (& ?x ?y) (| ?x ?y)) (* (& ?x (~ ?y)) (& (~ ?x) ?y)))"),
        
        // XOR and AND/OR Mix Rules

        rewrite!("add-to-xor"; "(+ ?x ?y)" => "(+ (^ ?x ?y) (* 2 (& ?x ?y)))"),
        rewrite!("xor-rewrite"; "(^ ?x ?y)" => "(- (| ?x ?y) (& ?x ?y))"),
        rewrite!("add-to-and-or"; "(+ ?x ?y)" => "(+ (& ?x ?y) (| ?x ?y))"),
        rewrite!("sub-to-xor"; "(- ?x ?y)" => "(+ (^ ?x (- ?y)) (* 2 (& ?x (- ?y))))"),
        rewrite!("and-to-add"; "(& ?x ?y)" => "(- (+ (* 1 ?x) (* 1 ?y)) (| ?x ?y))"),
        rewrite!("or-to-add"; "(| ?x ?y)" => "(+ (+ ?x ?y) (+ 1 (| (~ ?x) (~ ?y))))"),
        rewrite!("add-via-xor"; "(+ ?x ?y)" => "(- (* 2 (| ?x ?y)) (^ ?x ?y))"),
    
        //expand SUB
        //rewrite!("sub-to-neg"; "(- ?x ?y)" => "(+ (+ ?x (~ ?y)) 1)"),
        rewrite!("add-to-neg"; "(+ ?x ?y)" => "(- (- ?x (~ ?y)) 1)"),
    ];

    let input_file = File::open("neureduce_data_1K.txt")?;
    let reader = BufReader::new(input_file);
    let mut output_file = File::create("obfuscated_1k_3.csv")?;
    writeln!(output_file, "obfuscated,groundtruth,elapsed_ms")?;

    let mut total_duration = 0u128;
    let mut expr_count = 0;

    for line_result in reader.lines() {
        let expr_str = line_result?;
        let start_time = Instant::now();

        let mut current_expr: RecExpr<SymbolLang> = match expr_str.parse() {
            Ok(e) => e,
            Err(e) => {
                eprintln!("Skipping invalid expression '{}': {}", expr_str, e);
                continue;
            }
        };

        let mut node_limit = 60;
        for _i in 0..5 {
            loop {
                match run_in_thread(current_expr.clone(), rules.to_vec(), node_limit) {

                    Ok(best_expr) => {
                        current_expr = best_expr;
                        break;
                    }
                    Err(()) => {
                        node_limit /= 2;
                        eprintln!(
                            "Panic with node_limit={}, halving to {} for '{}'",
                            node_limit * 2,
                            node_limit,
                            expr_str
                        );
                        if node_limit < 10 {
                            eprintln!("Skipping further expansions for '{}'", expr_str);
                            break;
                        }
                    }
                }
            }
        }

        let duration = start_time.elapsed();
        total_duration += duration.as_millis();
        expr_count += 1;

        writeln!(
            output_file,
            "\"{}\",\"{}\",{}",
            current_expr, expr_str, duration.as_millis()
        )?;
    }

    if expr_count > 0 {
        println!(
            "Average obfuscation time per expression: {} ms",
            total_duration / expr_count as u128
        );
    } else {
        println!("No valid expressions processed.");
    }

    Ok(())
}
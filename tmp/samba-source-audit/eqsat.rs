use egg::*;

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

fn main() {

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
        
        // Distribution Rules
        rewrite!("distribute-mul"; "(* ?x (+ ?y ?z))" => "(+ (* ?x ?y) (* ?x ?z))"),
        rewrite!("distribute-sub"; "(* ?x (- ?y ?z))" => "(- (* ?x ?y) (* ?x ?z))"),
        rewrite!("factor-mul"; "(+ (* ?x ?y) ?y)" => "(* (+ ?x 1) ?y)"),
        rewrite!("double-add"; "(* 2 ?x)" => "(+ ?x ?x)"),
        rewrite!("neg-distribute"; "(- (+ ?x ?y))" => "(+ (- ?x) (- ?y))"),
        rewrite!("mul_to_sum"; "(* ?x ?y)" => "(+ (* (& ?x ?y) (| ?x ?y)) (* (& ?x (~ ?y)) (& (~ ?x) ?y)))"),
        
        // XOR and AND/OR Mix Rules

        rewrite!("add-to-xor"; "(+ ?x ?y)" => "(+ (^ ?x ?y) (* 2 (& ?x ?y)))"),
        rewrite!("xor-rewrite"; "(^ ?x ?y)" => "(- (| ?x ?y) (& ?x ?y))"),
        rewrite!("add-to-and-or"; "(+ ?x ?y)" => "(+ (& ?x ?y) (| ?x ?y))"),
        rewrite!("sub-to-xor"; "(- ?x ?y)" => "(+ (^ ?x (- ?y)) (* 2 (& ?x (- ?y))))"),
        rewrite!("and-to-add"; "(& ?x ?y)" => "(- (+ (* 1 ?x) (* 1 ?y)) (| ?x ?y))"),
        rewrite!("or-to-add"; "(| ?x ?y)" => "(+ (+ ?x ?y) (+ 1 (| (~ ?x) (~ ?y))))"),
        rewrite!("add-via-xor"; "(+ ?x ?y)" => "(- (* 2 (| ?x ?y)) (^ ?x ?y))"),
    
    ];


    // multiple iterations, each time starting with the previously extracted expression
    let iterations = 5;
    // Start with the base expression, e.g. (& x y) in postfix
    let mut current_expr: RecExpr<SymbolLang> = "(== x y)".parse().unwrap();

    for i in 1..iterations {
        println!("===== Iteration {} =====", i);

        // Create Runner with the current_expr
        let runner = Runner::default()
            .with_expr(&current_expr)
            .with_node_limit(30)
            .run(rules);

        // Extract the largest expression
        let (egraph, root) = (runner.egraph, runner.roots[0]);
        let best_expr = extract_largest_expr(&egraph, root);

        println!("Largest extracted expression:\n{}\n", best_expr);

        // (Optional) Dump the egraph for visualization
        //let svg_path = format!("target/egraph_iteration_{}.svg", i);
        //egraph.dot().to_svg(&svg_path).unwrap();
        //println!("Wrote {}", svg_path);

        // Use the newly extracted expression as the start for the next iteration
        current_expr = best_expr;
    } 

    println!("Final expression after {} iterations:\n{}", iterations, current_expr);
}

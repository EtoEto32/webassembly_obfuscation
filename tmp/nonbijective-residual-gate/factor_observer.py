"""Only expanded equations, their variable names, and width are inputs."""
import sympy as sp


def recover(payload):
    symbols = sp.symbols(' '.join(payload['variables']))
    outputs = symbols[-2:]
    recovered = []
    for terms in payload['equations']:
        poly = sp.Poly.from_dict({tuple(e):c for e,c in terms}, *symbols)
        _, factors = sp.factor_list(poly.as_expr(), *symbols)
        candidates = []
        for factor, multiplicity in factors:
            for out in outputs:
                other = outputs[1] if out == outputs[0] else outputs[0]
                p = sp.Poly(factor, out)
                if p.degree() == 1 and not factor.has(other):
                    leading, constant = p.all_coeffs()
                    if leading in (1,-1):
                        candidates.append((str(out), sp.expand(-constant / leading)))
        recovered.append(candidates)
    return recovered

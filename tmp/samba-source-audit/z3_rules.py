from z3 import *

# 32-bit bitvector variables
x, y, z = BitVecs('x y z', 32)

# Handy constants
zero = BitVecVal(0, 32)
one  = BitVecVal(1, 32)
two  = BitVecVal(2, 32)

def check_rule(name, prop):
    """
    Check if 'prop' holds for all x,y,z by asking Z3 if NOT(prop) is satisfiable.
    """
    s = Solver()
    s.add(Not(prop))
    res = s.check()
    print(f"{name}: {res}")
    if res == sat:
        print("  Counterexample model:")
        print(" ", s.model())
    print()


if __name__ == "__main__":
    # ------------------------------------------------------------
    # Commutativity

    check_rule("commute-mul", x * y == y * x)
    check_rule("commute-add", x + y == y + x)
    check_rule("commute-and", (x & y) == (y & x))
    check_rule("commute-xor", (x ^ y) == (y ^ x))
    check_rule("commute-or",  (x | y) == (y | x))

    # ------------------------------------------------------------
    # Associativity

    check_rule("assoc-mul", x * (y * z) == (x * y) * z)
    check_rule("assoc-add", x + (y + z) == (x + y) + z)
    check_rule("assoc-and", x & (y & z) == (x & y) & z)
    check_rule("assoc-xor", x ^ (y ^ z) == (x ^ y) ^ z)
    check_rule("assoc-or",  x | (y | z) == (x | y) | z)

    # ------------------------------------------------------------
    # Boolean & Arithmetic Transformations

    # not-mul:  ~(x*y) == (~x)*y + (y - 1)
    # check_rule("not-mul",
    #            ~(x * y) ==
    #            ((~x) * y + (y - one)))
    # split up into two rules to avoid long runing proofs
    check_rule("not-equiv-neg", 
       ~x == (-x - one))

    check_rule("not-mul (via arithmetic)",
        (-(x * y) - one) == 
        ((-x - one) * y + (y - one)))



    # not-add:  ~(x + y) == ~x + ~y + 1
    check_rule("not-add",
               ~(x + y) ==
               (~x + (~y + one)))

    # not-sub:  ~(x - y) == ~x - (~y + 1)
    check_rule("not-sub",
               ~(x - y) ==
               (~x - (~y + one)))

    # not-and:  ~(x & y) == ~x | ~y
    check_rule("not-and",
               ~(x & y) ==
               ((~x) | (~y)))

    # not-xor:  ~(x ^ y) == (x & y) | ~(x | y)
    check_rule("not-xor",
               ~(x ^ y) ==
               ((x & y) | ~(x | y)))

    # not-or:  ~(x | y) == ~x & ~y
    check_rule("not-or",
               ~(x | y) ==
               ((~x) & (~y)))

    # neg-mul:  -(x*y) == (-x)*y
    check_rule("neg-mul",
               -(x * y) ==
               ((-x) * y))

    # sub-to-add:  x - y == x + (-y)
    check_rule("sub-to-add",
               (x - y) ==
               (x + (-y)))

    # neg-to-not:  -x == ~x + 1
    check_rule("neg-to-not",
               -x ==
               (~x + one))

    # ------------------------------------------------------------
    # Distribution Rules

    # distribute-mul: x * (y + z) == x*y + x*z
    check_rule("distribute-mul",
               x * (y + z) ==
               (x * y) + (x * z))

    # distribute-sub: x * (y - z) == x*y - x*z
    check_rule("distribute-sub",
               x * (y - z) ==
               (x * y) - (x * z))

    # factor-mul: x*y + y == (x + 1)*y
    check_rule("factor-mul",
               (x * y) + y ==
               (x + one) * y)

    # double-add: 2*x == x + x
    check_rule("double-add",
               two * x ==
               x + x)

    # neg-distribute: -(x + y) == -x + -y
    check_rule("neg-distribute",
               -(x + y) ==
               (-x) + (-y))

    # mul_to_sum:
    # x*y == (&x y)*(|x y) + (&x ~y)*(&~x y)
    # check_rule("mul_to_sum",
    #            x * y ==
    #            ((x & y) * (x | y) +
    #             (x & ~y) * (~x & y)))
    # split up into two rules to avoid long runing proofs


    # -------------------------------------------------------------------------
    # OPTIMIZATION: mul-to-sum
    # Direct proof hangs on 32-bit. We break it into Logic Lemmas + Algebraic Proof.
    # Mathematical Concept: 
    #   We split bits into 3 disjoint sets: 
    #     a = (x & y)   [Common bits]
    #     b = (x & ~y)  [Bits only in x]
    #     c = (~x & y)  [Bits only in y]
    #
    #   Therefore: x = a + b,  y = a + c,  (x | y) = a + b + c

    # 1. Lemma: x is the sum of shared bits + unique bits
    check_rule("lemma: x-decomp", 
            x == (x & y) + (x & ~y))

    # 2. Lemma: y is the sum of shared bits + unique bits
    check_rule("lemma: y-decomp", 
            y == (x & y) + (~x & y))

    # 3. Lemma: x|y is the sum of all three disjoint parts
    check_rule("lemma: or-decomp", 
            (x | y) == (x & y) + (x & ~y) + (~x & y))

    # 4. The Algebraic Proof
    #    We verify the multiplication formula using x, y, z as purely abstract 
    #    placeholders for the disjoint parts (a, b, c).
    #    This relies on pure algebra, so the solver finishes instantly.
    #
    #    We are proving: (a + b) * (a + c) == a * (a + b + c) + b * c
    #    Map: x -> a, y -> b, z -> c
    check_rule("mul-to-sum (algebraic)",
            ((x + y) * (x + z)) == 
            (x * (x + y + z) + (y * z)))


    # ------------------------------------------------------------
    # XOR and AND/OR Mix Rules

    # add-to-xor: x + y == (x ^ y) + 2*(x & y)
    check_rule("add-to-xor",
               x + y ==
               (x ^ y) + (two * (x & y)))

    # xor-rewrite: x ^ y == (x | y) - (x & y)
    check_rule("xor-rewrite",
               x ^ y ==
               (x | y) - (x & y))

    # add-to-and-or: x + y == (x & y) + (x | y)
    check_rule("add-to-and-or",
               x + y ==
               (x & y) + (x | y))

    # sub-to-xor: x - y == (x ^ (-y)) + 2*(x & (-y))
    check_rule("sub-to-xor",
               x - y ==
               (x ^ (-y)) + (two * (x & (-y))))

    # and-to-add: x & y == (x*1 + y*1) - (x | y)
    check_rule("and-to-add",
               x & y ==
               ((one * x + one * y) - (x | y)))

    # or-to-add: x | y == (x + y) + (1 + ( ~x | ~y ))
    check_rule("or-to-add",
               x | y ==
               (x + y) + (one + ((~x) | (~y))))

    # add-via-xor: x + y == 2*(x | y) - (x ^ y)
    check_rule("add-via-xor",
               x + y ==
               (two * (x | y)) - (x ^ y))



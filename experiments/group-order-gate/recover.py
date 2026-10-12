"""Known 2-power discrete logarithm bit lifting; only public JSON input."""
import json
import math
import sys


def recover(data):
    p, g, w = (data[k] for k in ("modulus", "generator", "width"))
    if not 1 <= w <= 32 or math.gcd(g, p) != 1:
        raise ValueError("invalid parameters")
    n = 1 << w
    q = pow(g, n // 2, p)
    if pow(g, n, p) != 1 or q == 1:
        raise ValueError("generator does not have exact claimed order")
    inv = pow(g, -1, p)
    inverse_powers = [inv]
    for _ in range(w - 1):
        inverse_powers.append(inverse_powers[-1] ** 2 % p)
    rows = []
    for h in data["values"]:
        residual, x, squares, corrections = h, 0, 0, 0
        for j in range(w):
            t = residual
            for _ in range(w - 1 - j):
                t = t * t % p
                squares += 1
            if t == q:
                x |= 1 << j
                residual = residual * inverse_powers[j] % p
                corrections += 1
            elif t != 1:
                raise ValueError("outside generated subgroup")
        if residual != 1 or pow(g, x, p) != h:
            raise ValueError("invalid final recovery")
        rows.append({"value": h, "word": x, "lifting_squares": squares,
                     "correction_multiplications": corrections})
    return {"rows": rows, "count_scope": "per-value lifting only; excludes setup, validation, IO and final re-encoding"}


if __name__ == "__main__":
    print(json.dumps(recover(json.load(sys.stdin))))

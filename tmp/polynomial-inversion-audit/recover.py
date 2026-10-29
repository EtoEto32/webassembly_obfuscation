"""Own Newton-basis interpolation baseline; no input polynomial coefficients."""

def evaluate(model, value):
    modulus = 1 << model['width']
    answer = 0
    for node, coefficient in reversed(list(zip(model['nodes'], model['coefficients']))):
        answer = (answer * (value-node) + coefficient) % modulus
    return answer


def recover(width, oracle):
    modulus = 1 << width
    count, factorial = 1, 1
    while True:
        factorial *= count
        if factorial % modulus == 0:
            break
        count += 1
    nodes = [oracle(i) % modulus for i in range(count)]
    model = dict(width=width, nodes=[], coefficients=[])
    for i, node in enumerate(nodes):
        residual = (i - evaluate(model, node)) % modulus
        denominator = 1
        for previous in model['nodes']:
            denominator = denominator * (node-previous) % modulus
        if denominator == 0:
            raise ValueError('Insufficient precision or invalid polynomial permutation oracle')
        factor = denominator & -denominator
        if residual % factor:
            raise ValueError('Inconsistent interpolation samples')
        coefficient = ((residual // factor) *
                       pow(denominator // factor, -1, modulus // factor)) % (modulus // factor)
        model['nodes'].append(node)
        model['coefficients'].append(coefficient)
    return model

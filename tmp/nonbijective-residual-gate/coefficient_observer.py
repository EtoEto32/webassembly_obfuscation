"""Recovery for the documented Q family; no source coefficients are inputs."""
def recover(payload):
    modulus = 1 << payload['width']
    assert payload['variables'] == ['x', 'y', 'z', 't']
    # [z^2 t^0]Q1 = -g; [z^0 t^2]Q2 = -f in R[x,y].
    def extract(equation, output_powers):
        result = {}
        for powers, coefficient in equation:
            if tuple(powers[2:]) == output_powers:
                key = tuple(powers[:2])
                result[key] = (result.get(key, 0) - coefficient) % modulus
        return {key: value for key, value in result.items() if value}
    return [extract(payload['equations'][1], (0, 2)),
            extract(payload['equations'][0], (2, 0))]

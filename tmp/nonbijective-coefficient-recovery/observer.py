"""Family-aware coefficient projection. Receives no original source relations."""
def recover(payload):
    if payload['variables'] != ['x', 'y', 'z', 't']:
        raise ValueError('Unexpected variable ordering')
    modulus = 1 << payload['width']
    def project(terms, output_degrees):
        coefficients = {}
        for exponents, coefficient in terms:
            if tuple(exponents[2:]) == output_degrees:
                key = tuple(exponents[:2])
                coefficients[key] = (coefficients.get(key, 0) - coefficient) % modulus
        return {k: v for k, v in coefficients.items() if v}
    q1, q2 = payload['equations']
    return project(q2, (0, 2)), project(q1, (2, 0))

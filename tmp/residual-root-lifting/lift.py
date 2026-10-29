"""Evaluate a root through an equation oracle; not source-code recovery."""
def lift(oracle,width):
    z=t=0
    for bit in range(width):
        q1,q2=oracle(z,t)
        z |= ((q1>>bit)&1)<<bit
        t |= ((q2>>bit)&1)<<bit
    if oracle(z,t)!=(0,0):
        raise ValueError('Root lifting assumptions not satisfied')
    return z,t

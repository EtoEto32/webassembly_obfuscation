W = 3
M = (1 << W) - 1
def rol(v):
    return ((v << 1) | (v >> (W - 1))) & M

def step(label, state):
    a, b = state & M, state >> W
    if label == 0:
        a = (a + b) & M
    elif label == 1:
        a ^= rol(b)
        b = (b + 1) & M
    else:
        raise ValueError(label)
    return a | (b << W)

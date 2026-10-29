"""Rule-aware recovery, using only the public width and observed (z, r)."""

def recover(width, encoded, root):
    # root reveals x modulo 2^(w-2). Its unknown top two bits can be
    # obtained directly from encoded, because E(a+t*2^(w-2))-E(a)
    # equals t*2^(w-2) modulo 2^w for w>=3.
    low = (root - 1) >> 2
    encoded_low = low * (2 * low + 1)
    high = (encoded - encoded_low) & ((1 << width) - 1)
    return (low + high) & ((1 << width) - 1)

"""Family-aware recovery from a Wasm binary only, without transform reports.

Graph descriptors are public data in the generated program. The parser assumes
the documented interpreter family, not arbitrary code with a forged header.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import time
import prototype as p


class BDD:
    def __init__(self, limit=100000):
        self.nodes = [None, None]
        self.unique = {}
        self.cache = {}
        self.limit = limit

    def mk(self, var, lo, hi):
        if lo == hi:
            return lo
        key = (var, lo, hi)
        if key not in self.unique:
            if len(self.nodes) >= self.limit:
                raise OverflowError('BDD node budget reached')
            self.unique[key] = len(self.nodes)
            self.nodes.append(key)
        return self.unique[key]

    def binary(self, op, a, b):
        if a > b:
            a, b = b, a
        key = (op, a, b)
        if key in self.cache:
            return self.cache[key]
        if op == 'and':
            if a == 0:
                return 0
            if a == 1 or a == b:
                return b
        if op == 'or':
            if a == 0 or a == b:
                return b
            if a == 1:
                return 1
        if op == 'xor':
            if a == 0:
                return b
            if a == b:
                return 0
        if a < 2 and b < 2:
            result = {'and': a & b, 'or': a | b, 'xor': a ^ b}[op]
        else:
            va = self.nodes[a][0] if a >= 2 else 10**9
            vb = self.nodes[b][0] if b >= 2 else 10**9
            var = min(va, vb)
            al, ah = self.nodes[a][1:] if va == var else (a, a)
            bl, bh = self.nodes[b][1:] if vb == var else (b, b)
            result = self.mk(var, self.binary(op, al, bl), self.binary(op, ah, bh))
        self.cache[key] = result
        return result

    def digest(self, root):
        cache = {0: hashlib.sha256(b'0').digest(), 1: hashlib.sha256(b'1').digest()}
        def rec(node):
            if node not in cache:
                var, lo, hi = self.nodes[node]
                cache[node] = hashlib.sha256(struct.pack('<I', var) + rec(lo) + rec(hi)).digest()
            return cache[node]
        return rec(root).hex()


def uleb(data, at):
    value, shift = 0, 0
    while True:
        b = data[at]
        at += 1
        value |= (b & 127) << shift
        shift += 7
        if not b & 128:
            return value, at
        if shift > 35:
            raise ValueError('Oversize LEB')


def sleb(data, at):
    value, shift = 0, 0
    while True:
        b = data[at]
        at += 1
        value |= (b & 127) << shift
        shift += 7
        if not b & 128:
            return (value - (1 << shift) if b & 64 else value), at
        if shift > 35:
            raise ValueError('Oversize LEB')


def initial_memory(binary):
    if binary[:8] != b'\x00asm\x01\x00\x00\x00':
        raise ValueError('Not a Wasm binary')
    image = bytearray()
    pos = 8
    while pos < len(binary):
        section = binary[pos]
        size, start = uleb(binary, pos + 1)
        end = start + size
        if section == 11:
            count, at = uleb(binary, start)
            for _ in range(count):
                flags, at = uleb(binary, at)
                if flags not in (0, 2):
                    raise ValueError('Passive data not in interpreter profile')
                if flags == 2:
                    mem, at = uleb(binary, at)
                    if mem != 0:
                        raise ValueError('Multiple memories not in profile')
                if binary[at] != 0x41:
                    raise ValueError('Expected constant data offset')
                offset, at = sleb(binary, at + 1)
                if binary[at] != 0x0b:
                    raise ValueError('Bad data offset expression')
                length, at = uleb(binary, at + 1)
                if offset < 0 or offset + length > 4 * 1024 * 1024:
                    raise ValueError('Data image outside parser budget')
                image.extend(b'\x00' * max(0, offset + length - len(image)))
                image[offset:offset + length] = binary[at:at + length]
                at += length
            if at != end:
                raise ValueError('Unparsed data bytes')
        pos = end
    return image


def graph_root(image, bdd):
    if len(image) < 52:
        raise ValueError('No graph header')
    h = struct.unpack_from('<13I', image)
    magic, version, n, nn, nv, ne, s, t, nb, eb, ib, vb, rb = h
    if magic != p.MAGIC or version != 1 or not (1 <= n <= 128 and 2 <= nv <= 1024):
        raise ValueError('Unsupported graph descriptor')
    if nn > 100000 or ne > 100000 or max(nb + nn*12, eb + ne*12) > len(image):
        raise ValueError('Truncated or oversize graph data')
    if s >= nv or t >= nv:
        raise ValueError('Invalid terminals')
    nodes = []
    for i in range(nn):
        op, a, c = struct.unpack_from('<3I', image, nb + 12*i)
        if op == 0 and a < n:
            node = bdd.mk(a, 0, 1)
        elif op == 1 and a in (0, p.MASK):
            node = int(a != 0)
        elif op in (2, 3, 4) and a < i and c < i:
            node = bdd.binary({2: 'and', 3: 'or', 4: 'xor'}[op], nodes[a], nodes[c])
        else:
            raise ValueError('Invalid label instruction')
        nodes.append(node)
    edges = [struct.unpack_from('<3I', image, eb + 12*i) for i in range(ne)]
    if any(a >= nv or b >= nv or label >= nn for a, b, label in edges):
        raise ValueError('Invalid edge')
    reach = [0] * nv
    reach[s] = 1
    passes = 0
    for _ in range(nv - 1):
        old = list(reach)
        for a, b, label in edges:
            reach[b] = bdd.binary('or', reach[b], bdd.binary('and', reach[a], nodes[label]))
            reach[a] = bdd.binary('or', reach[a], bdd.binary('and', reach[b], nodes[label]))
        passes += 1
        if reach == old:
            break
    return n, reach[t], {'graph_vertices': nv, 'graph_edges': ne, 'symbolic_passes': passes}


def plain_root(src, bdd):
    mod = p.parse(p.tool('wasm2wat', [src, '--fold-exprs']))
    funcs = [x for x in mod[1:] if x[0] == 'func']
    if len(funcs) != 1:
        raise ValueError('Expected one pure function')
    f = funcs[0]
    params = [v for x in f[1:] if isinstance(x, list) and x[0] == 'param' for v in x[1:]]
    if any(v != 'i32' for v in params):
        raise ValueError('Unsupported parameter type')
    locals_ = [v for x in f[1:] if isinstance(x, list) and x[0] == 'local' for v in x[1:]]
    env = [bdd.mk(i, 0, 1) for i in range(len(params))] + [0] * len(locals_)
    def expr(x):
        op = x[0]
        if op == 'local.get':
            return env[int(x[1])]
        if op in ('local.set', 'local.tee'):
            value = expr(x[2])
            env[int(x[1])] = value
            return value if op == 'local.tee' else None
        if op == 'i32.const' and (int(x[1]) & p.MASK) in (0, p.MASK):
            return int(int(x[1]) != 0)
        if op in ('i32.and', 'i32.or', 'i32.xor'):
            return bdd.binary(op[4:], expr(x[1]), expr(x[2]))
        if op == 'return':
            return expr(x[1])
        raise ValueError('Unsupported pure expression: ' + p.emit(x))
    value = None
    for x in f[1:]:
        if isinstance(x, list) and x[0] not in ('type', 'param', 'result', 'local'):
            value = expr(x)
    if value is None:
        raise ValueError('No result')
    return len(params), value, {}


def bdd_wat(n, name, bdd, root):
    order, done = [], set()
    def visit(node):
        if node < 2 or node in done:
            return
        done.add(node)
        _, lo, hi = bdd.nodes[node]
        visit(lo)
        visit(hi)
        order.append(node)
    visit(root)
    if len(order) > 20000:
        raise OverflowError('Recovered-code node budget reached')
    locals_map = {v: f'$b{i}' for i, v in enumerate(order)}
    def ref(node):
        return f'(i32.const {-node})' if node < 2 else f'(local.get {locals_map[node]})'
    lines = []
    for node in order:
        var, lo, hi = bdd.nodes[node]
        lines.append(f'(local.set {locals_map[node]} (i32.xor {ref(lo)} (i32.and (local.get {var}) (i32.xor {ref(lo)} {ref(hi)}))))')
    declarations = ' '.join(f'(local {locals_map[v]} i32)' for v in order)
    wat = f'(module (func (export {name}) (param {" ".join(["i32"]*n)}) (result i32) {declarations} {" ".join(lines)} {ref(root)}))'
    return wat, len(order)


def recover(src, out):
    if out.exists() or Path(str(out) + '.json').exists():
        raise ValueError('Refuse overwrite')
    start = time.perf_counter()
    binary = src.read_bytes()
    p.tool('wasm-validate', [src])
    mod = p.parse(p.tool('wasm2wat', [src, '--fold-exprs']))
    exports = [x for x in mod[1:] if x[0] == 'export']
    if len(exports) != 1 or exports[0][2][0] != 'func':
        raise ValueError('Expected one function export')
    name = exports[0][1]
    bdd = BDD()
    image = initial_memory(binary)
    analysis_start = time.perf_counter()
    if image and len(image) >= 4 and struct.unpack_from('<I', image)[0] == p.MAGIC:
        n, root, metadata = graph_root(image, bdd)
        kind = 'public_graph_descriptor'
    else:
        n, root, metadata = plain_root(src, bdd)
        kind = 'pure_bitwise_body'
    analysis_seconds = time.perf_counter() - analysis_start
    wat, size = bdd_wat(n, name, bdd, root)
    out.parent.mkdir(parents=True, exist_ok=True)
    wp = Path(str(out) + '.wat')
    wp.write_text(wat, encoding='utf-8')
    raw = Path(str(out) + '.raw')
    p.tool('wat2wasm', [wp, '-o', raw])
    p.tool('wasm-opt', [raw, '-O3', '-o', out])
    p.tool('wasm-validate', [out])
    report = {'status': 'recovered', 'input_sha256': hashlib.sha256(binary).hexdigest(),
              'output_sha256': hashlib.sha256(out.read_bytes()).hexdigest(),
              'normalized_sha256': bdd.digest(root), 'bdd_result_nodes': size,
              'bdd_allocated_nodes': len(bdd.nodes), 'kind': kind,
              'analysis_seconds': analysis_seconds, 'total_seconds': time.perf_counter()-start, **metadata}
    Path(str(out) + '.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('input', type=Path)
    ap.add_argument('output', type=Path)
    args = ap.parse_args()
    print(json.dumps(recover(args.input, args.output)))

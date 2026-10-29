const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
(async () => {
  const bytes = fs.readFileSync(path.join(__dirname, 'example.wasm'));
  const { instance } = await WebAssembly.instantiate(bytes);
  const { before, after, after_seed } = instance.exports;
  let seed = 20261012, count = 0;
  const next = () => {
    seed ^= seed << 13; seed ^= seed >>> 17; seed ^= seed << 5;
    return seed >>> 0;
  };
  const check = (x, y, z, t) => {
    const expected = [Number((BigInt(x)+BigInt(y)) & 0xffffffffn),
                      Number((BigInt(x)*BigInt(y)) & 0xffffffffn)];
    for (const actual of [before(x,y), after(x,y), after_seed(x,y,z,t)]) {
      if (actual.some((v,i) => (v>>>0) !== expected[i]))
        throw Error(JSON.stringify({x,y,z,t,expected,actual}));
    }
    count++;
  };
  const edge = [0,1,2,0x7fffffff,0x80000000,0xfffffffe,0xffffffff];
  for (const x of edge) for (const y of edge)
    for (const z of edge) for (const t of edge) check(x,y,z,t);
  for (let i=0;i<2048;i++) check(next(),next(),next(),next());
  console.log(JSON.stringify({node:process.version,seed:20261012,
    cases:count,binaryBytes:bytes.length,
    wasmSha256:crypto.createHash('sha256').update(bytes).digest('hex'),
    mismatches:0,novelty:'unresolved',iterations:6},null,2));
})();

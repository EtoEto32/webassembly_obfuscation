const fs = require('fs');
const path = require('path');
const dir = process.argv[2];
const specs = JSON.parse(fs.readFileSync(path.join(dir, 'helper-cases.json')));
let calls = 0;
function encode(x, gates) {
  for (const [i,j,k] of gates) x ^= ((x >>> j & 1) & (x >>> k & 1)) << i;
  return x >>> 0;
}
for (const row of specs) {
  const e = new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir, row.file)))).exports;
  for (let z=0; z<2**row.width; z++) {
    const v = encode(z, [...row.gates].reverse());
    const expected = [0,0,v&1];
    for (let a=0; a<2; a++) {
      let u=0;
      for (let i=0; i<row.width; i++) u |= (v >>> row.delta[i][a] & 1) << i;
      expected[a] = encode(u,row.gates);
    }
    for (let a=0; a<3; a++) {
      if (row.tables[a][z] !== expected[a]) throw Error(`static/model ${row.file} ${z} ${a}`);
      for (const input of [z, (z | (0xffffffff << row.width)) >>> 0]) {
        const value=e['helper'+a](input) >>> 0; calls++;
        if (value !== expected[a]) throw Error(`engine/model ${row.file} ${input} ${a}`);
      }
    }
  }
}
console.log(JSON.stringify({node:process.version, v8:process.versions.v8, conditions:specs.length, calls, mismatches:0}));

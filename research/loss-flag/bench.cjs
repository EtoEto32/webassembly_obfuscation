const fs = require('node:fs'), os = require('node:os');
const target = new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2]))).exports;
const e = process.argv[3]
  ? new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[3])), {target}).exports : target;
let verification = null;
if (process.argv[3]) {
  const other = new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2]))).exports;
  for (let i = 7; i > 0; i--) other.run(i + 32);
  const observed = e.bench(7) >>> 0, expected = other.digest() >>> 0;
  if (observed !== expected) throw Error('imported benchmark differs from explicit calls');
  verification = {count: 7, observed, expected};
}
let sink = 0;
function sample(n) { const start = process.hrtime.bigint(); sink ^= e.bench(n); return Number(process.hrtime.bigint() - start); }
sample(32768);
let count = 1024, elapsed;
do { elapsed = sample(count); if (elapsed < 15e6) count *= 2; else break; } while (count <= 2**24);
const batches = Array.from({length: 7}, () => { const ns = sample(count); return {count, ns, ns_per_run: ns/count}; });
console.log(JSON.stringify({node: process.version, v8: process.versions.v8, cpu: os.cpus()[0].model,
  platform: process.platform, arch: process.arch, flags: process.execArgv, warmup: 32768,
  batches, memory_bytes: 65536, max_rss_kib: process.resourceUsage().maxRSS, sink, verification,
  harness: process.argv[3] ? 'separate-module-import-varying-safe-fail' : 'same-module-constant-fail'}));

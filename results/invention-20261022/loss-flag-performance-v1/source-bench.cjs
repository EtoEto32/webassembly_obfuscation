const fs = require('node:fs'), os = require('node:os');
const e = new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2]))).exports;
let sink = 0;
function sample(n) { const start = process.hrtime.bigint(); sink ^= e.bench(n); return Number(process.hrtime.bigint() - start); }
sample(32768);
let count = 1024, elapsed;
do { elapsed = sample(count); if (elapsed < 15e6) count *= 2; else break; } while (count <= 2**24);
const batches = Array.from({length: 7}, () => { const ns = sample(count); return {count, ns, ns_per_run: ns/count}; });
console.log(JSON.stringify({node: process.version, v8: process.versions.v8, cpu: os.cpus()[0].model,
  platform: process.platform, arch: process.arch, flags: process.execArgv, warmup: 32768,
  batches, memory_bytes: 65536, max_rss_kib: process.resourceUsage().maxRSS, sink}));

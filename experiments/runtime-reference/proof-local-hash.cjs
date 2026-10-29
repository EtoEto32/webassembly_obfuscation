/* Local, network-free evaluation of unchanged Proof-of-Theft hash_cn modules.
 * Host ABI mapping is checked against each distributed cn.js by preparation.
 */
'use strict';
const fs = require('fs'), crypto = require('crypto'), path = require('path');
function readBytes(file) {
  const fd = fs.openSync(file, 'r'), chunks = [];
  try { for (;;) { const b = Buffer.alloc(4096), n = fs.readSync(fd, b, 0, b.length, null);
    if (!n) break; chunks.push(b.subarray(0, n)); } } finally { fs.closeSync(fd); }
  return Buffer.concat(chunks);
}
function saveReport(file, report) {
  const bytes = Buffer.from(JSON.stringify(report, null, 2) + '\n');
  const temp = file + '.tmp', fd = fs.openSync(temp, 'w');
  try {
    for (let offset = 0; offset < bytes.length;) {
      const n = fs.writeSync(fd, bytes, offset, Math.min(4096, bytes.length - offset));
      if (!n) throw Error('Short result write'); offset += n;
    }
    fs.fsyncSync(fd);
  } finally { fs.closeSync(fd); }
  fs.renameSync(temp, file);
}
async function adapter(bytes, abi) {
  let instance, memory, alloc;
  const view = () => new DataView(memory.buffer);
  const text = (p, s) => new Uint8Array(memory.buffer).set(Buffer.from(s + '\0'), p);
  function gmtime(seconds, ptr) {
    const d = new Date(seconds * 1000);
    if (!Number.isFinite(d.getTime())) throw Error('Invalid time');
    const fields = [d.getUTCSeconds(), d.getUTCMinutes(), d.getUTCHours(), d.getUTCDate(),
      d.getUTCMonth(), d.getUTCFullYear() - 1900, d.getUTCDay(),
      Math.floor((d.getTime() - Date.UTC(d.getUTCFullYear(), 0, 1)) / 86400000)];
    fields.forEach((x, i) => view().setInt32(ptr + i * 4, x, true));
  }
  const resize = requested => { if (requested <= memory.buffer.byteLength) return 1;
    // The distributed minified glue aborts rather than growing this fixed heap.
    throw Error('Heap growth requested; unsupported by recorded minified host contract'); };
  const imports = abi === 'minified-pointer-time' ? {a: {
    a: resize,
    b: (timezone, daylight, tzname) => {
      // Runs use TZ=UTC, matching generated timezone semantics in that zone.
      if (new Date().getTimezoneOffset() !== 0) throw Error('TZ must be UTC');
      const first = alloc(4), second = alloc(4); text(first, 'GMT'); text(second, 'GMT');
      view().setInt32(timezone, 0, true); view().setInt32(daylight, 0, true);
      view().setUint32(tzname, first, true); view().setUint32(tzname + 4, second, true);
    },
    c: (time, ptr) => gmtime(view().getUint32(time, true) + view().getInt32(time + 4, true) * 4294967296, ptr),
    d: () => 1, e: () => Date.now(),
    f: (dst, src, n) => new Uint8Array(memory.buffer).copyWithin(dst, src, src + n)
  }} : {env: {
    emscripten_resize_heap: resize,
    _tzset_js: (timezone, daylight, std, dst) => {
      if (new Date().getTimezoneOffset() !== 0) throw Error('TZ must be UTC');
      view().setInt32(timezone, 0, true); view().setInt32(daylight, 0, true);
      text(std, 'UTC-0000'); text(dst, 'UTC-0000');
    },
    _gmtime_js: (lo, hi, ptr) => gmtime((lo >>> 0) + hi * 4294967296, ptr)
  }, wasi_snapshot_preview1: {clock_time_get: (clock, lo, hi, ptr) => {
    if (clock < 0 || clock > 3) return 28;
    const ns = BigInt(Math.round((clock === 0 ? Date.now() : performance.now()) * 1e6));
    view().setBigUint64(ptr, ns, true); return 0;
  }}};
  ({instance} = await WebAssembly.instantiate(bytes, imports));
  const e = instance.exports, min = abi === 'minified-pointer-time';
  memory = min ? e.g : e.memory;
  alloc = min ? e.i : e._emscripten_stack_alloc;
  (min ? e.h : e.__wasm_call_ctors)();
  const input = alloc(4096), hash = min ? e.k : e.hash_cn;
  if (!input || typeof hash !== 'function') throw Error('Missing verified hashing ABI');
  return v => {
    if (!/^(?:[0-9a-f]{2})+$/.test(v.hex) || v.hex.length >= 4096) throw Error('Invalid input');
    text(input, v.hex);
    const output = hash(input, v.lite, v.variant, v.height);
    const result = Buffer.from(memory.buffer, output, 64).toString('ascii');
    if (!/^[0-9a-f]{64}$/.test(result)) throw Error('Invalid hash encoding');
    return result;
  };
}
async function main() {
  const root = process.argv[2], output = process.argv[3];
  const spec = JSON.parse(readBytes(path.join(root, 'results/runtime-mining/cross-dataset/proof-of-theft/hash-experiment-input.json')));
  const report = {started_utc: new Date().toISOString(), node: process.version,
    v8: process.versions.v8, platform: process.platform, arch: process.arch,
    image_id: process.env.EXPERIMENT_IMAGE_ID, algorithm: spec.algorithm,
    mode: 'local correctness check; no pool connection; not browser performance', results: [],
    script_sha256: crypto.createHash('sha256').update(readBytes(__filename)).digest('hex'),
    input_manifest_sha256: crypto.createHash('sha256').update(readBytes(path.join(root,
      'results/runtime-mining/cross-dataset/proof-of-theft/hash-experiment-input.json'))).digest('hex'),
    cpu_model: require('os').cpus()[0].model};
  for (const module of spec.modules) {
    const row = {...module, outputs: []}; report.results.push(row);
    try {
      const bytes = readBytes(path.join(root, module.object));
      if (crypto.createHash('sha256').update(bytes).digest('hex') !== module.sha256) throw Error('Digest mismatch');
      const hash = await adapter(bytes, module.abi);
      for (const vector of spec.vectors) {
        const t = performance.now(), actual = hash(vector);
        row.outputs.push({rpc_id: vector.rpc_id, job_id: vector.job_id, expected: vector.expected,
          actual, matches: actual === vector.expected, diagnostic_elapsed_ms: performance.now() - t});
      }
      row.status = row.outputs.every(x => x.matches) ? 'all recorded vectors matched' : 'hash mismatch';
    } catch (e) { row.status = 'failed'; row.error = String(e.stack || e); }
    saveReport(output, report);
    console.log(JSON.stringify({method: row.method, status: row.status, checked: row.outputs.length}));
  }
  if (process.argv[4] === '--benchmark') {
    report.mode = 'local Node.js preliminary repeated throughput; one synchronous hashing worker; no pool connection';
    report.benchmark = {seconds_per_block: 5, warmup_seconds: 1, repetitions: 3,
      input_sequence: 'cycle the 13 independently pool-accepted recorded input blobs',
      samples: [], limitations: ['Short preliminary blocks, not the original paper duration.',
        'Node.js host execution differs from the browser/pool experiment.',
        'Other host workloads are not controlled; inspect variation before interpretation.',
        'Distributed build conditions may differ; ratios are artifact comparisons, not isolated causal effects.']};
    const eligible = report.results.filter(x => x.status === 'all recorded vectors matched');
    for (let rep = 0; rep < 3; rep++) {
      // Rotate module order between repeats to reduce a fixed order confound.
      const order = eligible.slice(rep).concat(eligible.slice(0, rep));
      for (const module of order) {
        const hash = await adapter(readBytes(path.join(root, module.object)), module.abi);
        let count = 0, t = performance.now();
        while (performance.now() - t < 1000) hash(spec.vectors[count++ % spec.vectors.length]);
        count = 0; const started = performance.now(); let last;
        do { last = hash(spec.vectors[count++ % spec.vectors.length]); } while (performance.now() - started < 5000);
        const elapsed = performance.now() - started;
        const expected = spec.vectors[(count - 1) % spec.vectors.length].expected;
        const row = {method: module.method, sha256: module.sha256, repetition: rep + 1,
          count, elapsed_ms: elapsed, hashes_per_second: count * 1000 / elapsed,
          final_output_matches: last === expected, finished_utc: new Date().toISOString()};
        report.benchmark.samples.push(row);
        fs.appendFileSync(output + '.samples.jsonl', JSON.stringify(row) + '\n');
        saveReport(output, report);
        console.log(JSON.stringify(row));
        if (!row.final_output_matches) throw Error('Measured output mismatch');
      }
    }
  }
  report.finished_utc = new Date().toISOString();
  saveReport(output, report);
}
main().catch(e => { console.error(e); process.exitCode = 1; });

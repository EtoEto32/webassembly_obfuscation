// Run original npm JS glue with one supplied Wasm binary and deterministic local inputs.
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { pathToFileURL } = require('node:url');
const { install, BrowserWorker } = require('./ffmpeg-worker-adapter.cjs');
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const [glueArg, wasmArg, outArg, seedArg = '1', mode = 'counted'] = process.argv.slice(2);
const seed = Number(seedArg);
if (!Number.isInteger(seed) || seed < 1 || seed > 1000 || !['counted', 'unwrapped'].includes(mode)) throw new Error('Invalid experiment configuration.');
const glue = path.resolve(glueArg), wasmPath = path.resolve(wasmArg), out = path.resolve(outArg);
fs.mkdirSync(out, { recursive: false });
const result = { node: process.version, v8: process.versions.v8, wasm: wasmPath,
  wasmSha256: sha(fs.readFileSync(wasmPath)), adapter: 'unchanged browser-worker glue on Node worker_threads adapter',
  seed, mode, sources: Object.fromEntries([__filename, path.join(__dirname, 'ffmpeg-worker-adapter.cjs'),
    path.join(glue, 'ffmpeg-core.js'), path.join(glue, 'ffmpeg-core.worker.js')].map(p => [p, sha(fs.readFileSync(p))])),
  start: new Date().toISOString(), commands: [], mainThreadExportCalls: {}, mainThreadExportThrows: {}, errors: [] };
function writeResult() { fs.writeFileSync(path.join(out, 'result.json'), JSON.stringify(result, null, 2)); }
function makeWav() {
  const rate = 8000, count = 2000, data = Buffer.alloc(44 + count * 2);
  data.write('RIFF', 0); data.writeUInt32LE(data.length - 8, 4); data.write('WAVEfmt ', 8);
  data.writeUInt32LE(16, 16); data.writeUInt16LE(1, 20); data.writeUInt16LE(1, 22);
  data.writeUInt32LE(rate, 24); data.writeUInt32LE(rate * 2, 28); data.writeUInt16LE(2, 32);
  data.writeUInt16LE(16, 34); data.write('data', 36); data.writeUInt32LE(count * 2, 40);
  for (let i = 0; i < count; i++) data.writeInt16LE(((i * 997 + (seed - 1) * 1237) % 20001) - 10000, 44 + 2 * i);
  return data;
}
function makePpm() {
  const header = Buffer.from('P6\n16 16\n255\n'), pixels = Buffer.alloc(16 * 16 * 3);
  for (let i = 0; i < pixels.length; i++) pixels[i] = (i * 37 + 13 + (seed - 1) * 53) % 256;
  return Buffer.concat([header, pixels]);
}
async function main() {
  install(path.join(glue, 'ffmpeg-core.js'));
  const factory = require(path.join(glue, 'ffmpeg-core.js'));
  const bytes = fs.readFileSync(wasmPath), compiled = await WebAssembly.compile(bytes);
  const mainScriptUrlOrBlob = pathToFileURL(path.join(glue, 'ffmpeg-core.js')).href + '#' +
    Buffer.from(JSON.stringify({ wasmURL: pathToFileURL(wasmPath).href,
      workerURL: pathToFileURL(path.join(glue, 'ffmpeg-core.worker.js')).href })).toString('base64');
  const core = await factory({ mainScriptUrlOrBlob, wasmBinary: bytes,
    instantiateWasm(imports, receive) {
      const instance = new WebAssembly.Instance(compiled, imports);
      if (mode === 'unwrapped') return receive(instance, compiled);
      const exports = {};
      for (const [name, value] of Object.entries(instance.exports)) exports[name] = typeof value === 'function' ? (...args) => {
        result.mainThreadExportCalls[name] = (result.mainThreadExportCalls[name] || 0) + 1;
        try { return value(...args); }
        catch (error) {
          const key = `${name}:${error?.name}:${error?.message}`;
          result.mainThreadExportThrows[key] = (result.mainThreadExportThrows[key] || 0) + 1;
          throw error;
        }
      } : value;
      receive({ exports }, compiled);
      return exports;
    }
  });
  result.initialized = true;
  result.workersCreated = BrowserWorker.instances.length;
  const wav = makeWav(), ppm = makePpm();
  core.FS.writeFile('input.wav', wav); core.FS.writeFile('input.ppm', ppm);
  fs.writeFileSync(path.join(out, 'input.wav'), wav); fs.writeFileSync(path.join(out, 'input.ppm'), ppm);
  result.inputs = { wav: { bytes: wav.length, sha256: sha(wav) }, ppm: { bytes: ppm.length, sha256: sha(ppm) } };
  const specs = [
    ['audio-resample', ['-i', 'input.wav', '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le', '-f', 's16le', 'resampled.pcm'], 'resampled.pcm'],
    ['audio-lossless', ['-i', 'input.wav', '-c:a', 'flac', '-threads', '1', 'encoded.flac'], 'encoded.flac'],
    ['audio-roundtrip', ['-i', 'encoded.flac', '-f', 's16le', '-c:a', 'pcm_s16le', 'roundtrip.pcm'], 'roundtrip.pcm'],
    ['image-scale', ['-i', 'input.ppm', '-vf', 'scale=8:8', '-frames:v', '1', '-threads', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', 'scaled.rgb'], 'scaled.rgb'],
    ['invalid-input', ['-i', 'missing.wav', '-f', 's16le', 'invalid.pcm'], null]
  ];
  for (const [name, args, output] of specs) {
    const logs = [], before = { ...result.mainThreadExportCalls };
    core.setLogger(item => logs.push(item)); core.reset();
    const code = core.exec('-hide_banner', '-loglevel', 'error', '-threads', '1', ...args);
    const row = { name, args, code, logs, exports: {} };
    for (const [key, value] of Object.entries(result.mainThreadExportCalls)) if (value !== (before[key] || 0)) row.exports[key] = value - (before[key] || 0);
    if (output) {
      const data = Buffer.from(core.FS.readFile(output));
      row.output = { name: output, bytes: data.length, sha256: sha(data) };
      fs.writeFileSync(path.join(out, output), data);
    }
    result.commands.push(row); writeResult();
  }
  const roundtrip = fs.readFileSync(path.join(out, 'roundtrip.pcm'));
  result.roundtripMatchesOriginalPcm = roundtrip.equals(wav.subarray(44));
  if (!result.roundtripMatchesOriginalPcm) throw new Error('Lossless roundtrip did not reproduce the generated PCM.');
  if (result.commands.slice(0, 4).some(x => x.code !== 0) || result.commands[4].code === 0) throw new Error('Unexpected command exit status.');
  result.status = 'passed';
}
main().catch(error => { result.status = 'harness-or-execution-failure'; result.errors.push({ name: error.name, message: error.message, stack: error.stack }); process.exitCode = 1; })
  .finally(async () => { result.end = new Date().toISOString(); await Promise.all(BrowserWorker.instances.map(w => w.terminate())); writeResult(); console.log(JSON.stringify({ status: result.status, commands: result.commands.length, workers: BrowserWorker.instances.length, errors: result.errors.map(x => x.message) })); });

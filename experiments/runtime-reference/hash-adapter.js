/* Host ABI for the distributed hash_cn Wasm; the Wasm bytes are unchanged.
 * Contract: fixed-commit C sources, recorded in algorithm-contracts.json.
 * This host adapter is not the original paper's CoinHive runtime.
 */
async function createHashAdapter(moduleUrl, contract = {algorithm:'cn/0', lite:0, variant:0, height_required:false}) {
  let wasm;
  const bytes = await (await fetch(moduleUrl)).arrayBuffer();
  const env = {
    __assert_fail: () => { throw new Error('Wasm assertion failed'); },
    emscripten_memcpy_big: (dst, src, count) => {
      new Uint8Array(wasm.exports.memory.buffer).copyWithin(dst, src, src + count);
    },
    emscripten_date_now: () => Date.now(),
    _emscripten_get_now_is_monotonic: () => 1,
    emscripten_get_now: () => performance.now(),
    // Pointer-based time_t ABI: Emscripten 3.1.26 src/library.js.
    // The dataset C struct tm contains nine i32 fields, gmtoff and zone.
    _gmtime_js: (timePtr, tmPtr) => {
      const memory = new DataView(wasm.exports.memory.buffer);
      const seconds = memory.getUint32(timePtr, true) + memory.getInt32(timePtr + 4, true) * 4294967296;
      const date = new Date(seconds * 1000);
      if (!Number.isFinite(date.getTime())) throw new Error('Invalid time_t');
      const yday = Math.floor((date.getTime() - Date.UTC(date.getUTCFullYear(), 0, 1)) / 86400000);
      const fields = [date.getUTCSeconds(), date.getUTCMinutes(), date.getUTCHours(),
        date.getUTCDate(), date.getUTCMonth(), date.getUTCFullYear() - 1900, date.getUTCDay(), yday];
      fields.forEach((value, index) => memory.setInt32(tmPtr + index * 4, value, true));
      return 0;
    },
    _tzset_js: (timezone, daylight, tzname) => {
      const year = new Date().getFullYear();
      const winter = new Date(year, 0, 1), summer = new Date(year, 6, 1);
      const winterOffset = winter.getTimezoneOffset(), summerOffset = summer.getTimezoneOffset();
      const allocateName = date => {
        const match = date.toTimeString().match(/\(([A-Za-z ]+)\)$/);
        const data = new TextEncoder().encode((match ? match[1] : 'GMT') + '\0');
        const ptr = wasm.exports.malloc(data.length);
        if (!ptr) throw new Error('Timezone allocation failed');
        new Uint8Array(wasm.exports.memory.buffer).set(data, ptr);
        return ptr;
      };
      const winterName = allocateName(winter), summerName = allocateName(summer);
      const memory = new DataView(wasm.exports.memory.buffer);
      memory.setInt32(timezone, Math.max(winterOffset, summerOffset) * 60, true);
      memory.setInt32(daylight, Number(winterOffset !== summerOffset), true);
      memory.setUint32(tzname, summerOffset < winterOffset ? winterName : summerName, true);
      memory.setUint32(tzname + 4, summerOffset < winterOffset ? summerName : winterName, true);
    },
    emscripten_resize_heap: requested => {
      const current = wasm.exports.memory.buffer.byteLength;
      if (requested <= current) return 1;
      try { wasm.exports.memory.grow(Math.ceil((requested - current) / 65536)); return 1; }
      catch (_) { return 0; }
    }
  };
  ({instance: wasm} = await WebAssembly.instantiate(bytes, {env}));
  const e = wasm.exports;
  if (typeof e.hash_cn !== 'function' || typeof e.malloc !== 'function') {
    throw new Error('Unsupported hash_cn ABI');
  }
  if (e.emscripten_stack_init) e.emscripten_stack_init();
  if (e.__wasm_call_ctors) e.__wasm_call_ctors();
  const capacity = 4096;
  const input = e.malloc(capacity);
  if (!input) throw new Error('Input allocation failed');
  return {
    exports: Object.keys(e),
    hash(hex, job) {
      if (!/^(?:[0-9a-fA-F]{2})+$/.test(hex) || hex.length >= capacity) {
        throw new Error('Invalid CryptoNight blob');
      }
      if (!job || job.algo !== contract.algorithm || Number(job.variant) !== contract.variant) {
        throw new Error('Job does not match the pinned source algorithm contract');
      }
      if (contract.height_required && (!Number.isSafeInteger(job.height) || job.height < 1)) {
        throw new Error('CryptoNight R requires the live job height');
      }
      let heap = new Uint8Array(e.memory.buffer);
      heap.set(new TextEncoder().encode(hex + '\0'), input);
      const output = e.hash_cn(input, contract.lite, contract.variant, Number(job.height || 0));
      heap = new Uint8Array(e.memory.buffer);
      const result = new TextDecoder().decode(heap.subarray(output, output + 64));
      if (!/^[0-9a-f]{64}$/i.test(result)) throw new Error('Invalid hash output encoding');
      return result;
    }
  };
}

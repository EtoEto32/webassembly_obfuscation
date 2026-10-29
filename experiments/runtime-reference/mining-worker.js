/* ABI adaptation for the Cryptic Bytes hash_cn distribution, not CoinHive.
 * Nonce offset, little-endian encoding and 32-bit target comparison follow
 * the pinned distribution's miner/client/src/worker.js.
 */
importScripts('/hash-adapter.js');
let adapter;
let failed = false;
function littleEndian(hex) {
  return parseInt(hex.match(/../g).reverse().join(''), 16);
}
onmessage = async ({data}) => {
  if (failed) return;
  try {
    if (data.type === 'init') {
      if (adapter) throw new Error('Worker already initialized');
      adapter = await createHashAdapter('/module.wasm', data.contract);
      postMessage({type:'ready'});
      return;
    }
    if (data.type !== 'hash' || !adapter) throw new Error('Worker is not ready');
    const job = data.job;
    if (!job || typeof job.job_id !== 'string' ||
        !/^(?:[0-9a-f]{2}){43,}$/i.test(job.blob) || !/^[0-9a-f]{8}$/i.test(job.target)) {
      throw new Error('Unsupported job blob or target representation');
    }
    const nonce = Math.floor(Math.random() * 0x100000000).toString(16)
      .padStart(8, '0').match(/../g).reverse().join('');
    const blob = job.blob.slice(0, 78) + nonce + job.blob.slice(86);
    const result = adapter.hash(blob, job);
    const solved = littleEndian(result.slice(56, 64)) < littleEndian(job.target);
    postMessage({type:'hash', hashes:1, generation:data.generation,
      share:solved ? {job_id:job.job_id, nonce, result} : null});
  } catch(error) {
    failed = true;
    postMessage({type:'failure', message:String(error)});
  }
};

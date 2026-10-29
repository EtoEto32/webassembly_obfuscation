// User-started, local experiment only; no automatic background start/retry.
(async () => {
  const config = await (await fetch('/runtime-config.json')).json();
  if (!Number.isInteger(config.threads) || config.threads < 1) throw new Error('Missing explicit thread count');
  if (!config.contract || config.contract.algorithm !== config.algorithm) throw new Error('Missing algorithm contract');
  let socket, currentJob, generation = 0, hashes = 0, running = false;
  const workers = [];
  const status = document.getElementById('runtime-status');
  const counter = document.getElementById('hashes-total');
  const event = data => fetch('/events', {method:'POST', headers:{'Content-Type':'application/json'},
    body:JSON.stringify(data)}).catch(() => {});
  function stop(reason = 'stopped') {
    running = false;
    workers.forEach(entry => entry.worker.terminate());
    if (socket) socket.close();
    status.textContent = reason;
    event({event:reason, hashes});
  }
  function dispatch(entry) {
    if (running && entry.ready && !entry.busy && currentJob) {
      entry.busy = true;
      entry.worker.postMessage({type:'hash', job:currentJob, generation});
    }
  }
  document.getElementById('stop-mining').onclick = () => stop();
  window.addEventListener('pagehide', () => stop());
  document.getElementById('mining-button-text').onclick = () => {
    if (running || workers.length) return;
    running = true;
    status.textContent = 'starting';
    event({event:'start', threads:config.threads, algorithm:config.algorithm,
      hardware_concurrency:navigator.hardwareConcurrency, user_agent:navigator.userAgent});
    for (let i = 0; i < config.threads; i++) {
      const entry = {worker:new Worker('/mining-worker.js'), ready:false, busy:false};
      workers.push(entry);
      entry.worker.onerror = error => {event({event:'worker_error', message:error.message}); stop('failed');};
      entry.worker.onmessage = ({data}) => {
        if (!running) return;
        if (data.type === 'failure') {event({event:'worker_failure', message:data.message}); stop('failed'); return;}
        if (data.type === 'ready') entry.ready = true;
        else if (data.type === 'hash') {
          entry.busy = false;
          hashes += data.hashes;
          counter.textContent = String(hashes);
          if (data.share && data.generation === generation && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({type:'submit', params:data.share}));
          }
        }
        dispatch(entry);
      };
      entry.worker.postMessage({type:'init', contract:config.contract});
    }
    socket = new WebSocket('ws://127.0.0.1:8892');
    socket.onopen = () => socket.send(JSON.stringify({type:'auth', params:{}}));
    socket.onerror = () => {event({event:'websocket_error'}); stop('failed');};
    socket.onclose = () => {if (running) stop('disconnected');};
    socket.onmessage = ({data}) => {
      try {
        const message = JSON.parse(data);
        event({event:'bridge_message', message});
        if (message.type === 'error' || message.type === 'banned') {stop('failed'); return;}
        if (message.type !== 'job') return;
        const job = message.params;
        // An omitted algorithm may be supplied only by an operator-verified
        // pool configuration. Refuse any conflicting value from the pool.
        const wireFamily = ['cn', 'cn-lite', 'cn-pico', 'cn-half', 'cn-rwz'][config.contract.lite];
        if ((job.algo !== undefined && ![wireFamily, config.algorithm].includes(job.algo)) ||
            (job.variant !== undefined && Number(job.variant) !== config.contract.variant)) throw new Error('Algorithm mismatch');
        currentJob = {...job, algo:config.algorithm, variant:config.contract.variant};
        generation++;
        status.textContent = 'mining';
        workers.forEach(dispatch);
      } catch(error) {event({event:'protocol_failure', message:String(error)}); stop('failed');}
    };
  };
})().catch(error => {document.getElementById('runtime-status').textContent = 'failed'; console.error(error);});

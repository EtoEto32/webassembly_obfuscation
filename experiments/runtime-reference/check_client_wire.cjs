// Artificial messages only: no browser, network, Wasm or hash computation.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const elements = Object.fromEntries(['runtime-status','hashes-total','stop-mining','mining-button-text']
  .map(id => [id, {textContent:id === 'hashes-total' ? '0' : ''}]));
const workers = [], sockets = [], events = [];
class Worker {
  constructor(url) {assert.equal(url, '/mining-worker.js'); this.sent=[]; workers.push(this);}
  postMessage(data) {this.sent.push(data);}
  terminate() {this.terminated=true;}
  receive(data) {this.onmessage({data});}
}
class WebSocket {
  static OPEN = 1;
  constructor(url) {assert.equal(url,'ws://127.0.0.1:8892'); this.readyState=1; this.sent=[]; sockets.push(this);}
  send(data) {this.sent.push(JSON.parse(data));}
  close() {this.readyState=3; if (this.onclose) this.onclose();}
  receive(data) {this.onmessage({data:JSON.stringify(data)});}
}
async function main() {
  await vm.runInNewContext(fs.readFileSync(path.join(__dirname,'mining-client.js'),'utf8'), {
    document:{getElementById:id=>elements[id]}, window:{addEventListener:()=>{}},
    navigator:{hardwareConcurrency:8, userAgent:'synthetic'}, Worker, WebSocket, console,
    fetch:async (url, options) => {
      if (url === '/runtime-config.json') return {json:async()=>({threads:2,algorithm:'cn/0',
        contract:{algorithm:'cn/0',lite:0,variant:0}})};
      assert.equal(url, '/events'); events.push(JSON.parse(options.body)); return {};
    }
  });
  assert.equal(sockets.length,0); // No automatic start.
  elements['mining-button-text'].onclick();
  const socket=sockets[0];
  socket.onopen();
  assert.equal(socket.sent[0].type,'auth');
  workers.forEach(worker => worker.receive({type:'ready'}));
  socket.receive({type:'job',params:{job_id:'first',blob:'synthetic',target:'synthetic',algo:'cn/0',variant:0}});
  const first=workers[0].sent.at(-1);
  assert.equal(first.type,'hash');
  workers[0].receive({type:'hash', hashes:1, generation:first.generation,
    share:{job_id:'first',nonce:'synthetic',result:'synthetic'}});
  assert.equal(elements['hashes-total'].textContent,'1');
  assert.equal(socket.sent[1].type,'submit');
  socket.receive({type:'job',params:{job_id:'second',blob:'synthetic',target:'synthetic'}});
  const writes=socket.sent.length;
  workers[1].receive({type:'hash',hashes:1,generation:first.generation,
    share:{job_id:'first',nonce:'synthetic',result:'synthetic'}});
  assert.equal(socket.sent.length,writes); // Stale share not sent.
  assert.equal(elements['hashes-total'].textContent,'2'); // Work still counted.
  socket.receive({type:'job',params:{job_id:'wrong',algo:'rx/0',variant:0}});
  assert.equal(elements['runtime-status'].textContent,'failed');
  assert.ok(workers.every(worker=>worker.terminated));
  assert.equal(socket.readyState,3);
  assert.ok(events.some(event=>event.event==='protocol_failure'));
  console.log(JSON.stringify({status:'passed',synthetic:true,wasm_executed:false,
    external_connection:false,no_automatic_start:true,stale_share_not_sent:true,
    counter_preserved:true,algorithm_mismatch_stops:true}));
}
main().catch(error=>{console.error(error);process.exitCode=1;});

// Synthetic protocol bookkeeping check. No Wasm, socket or pool is used.
const assert = require('node:assert/strict');
const Connection = require('coin-hive-stratum/build/Connection').default;
const {instrumentConnection} = require('./bridge-instrumentation.cjs');
const events = [];
instrumentConnection(Connection, (file, data) => events.push({file, ...data}));
const connection = new Connection({host:'127.0.0.1', port:3333, ssl:false});
let writes = 0;
const handlers = {};
connection.socket = {on:()=>{}, writable:true, write:()=>{writes++; return false;}};
connection.queue = {on:(name, handler)=>{handlers[name]=handler;},
  start:()=>{}, push:item=>handlers[item.type](item.payload)};
connection.online = true;
connection.ready();
assert.equal(connection.send('miner', 'submit', {job_id:'job', nonce:'00000000', result:'test'}), false);
assert.equal(writes, 0);
assert.equal(events.length, 0);
connection.auth.miner = 'auth';
connection.minerId.auth = 'miner';
let deliveredJob;
connection.on('miner:job', job => {deliveredJob = job;});
connection.receive(JSON.stringify({method:'job', params:{job_id:'updated-job', blob:'unchanged', target:'711b0d00'}}));
assert.equal(deliveredJob.job_id, 'updated-job');
assert.equal(deliveredJob.blob, 'unchanged');
assert.equal(deliveredJob.id, 'auth');
events.length = 0;
connection.send('miner', 'submit', {job_id:'job', nonce:'00000000', result:'test'});
assert.equal(writes, 1);
assert.equal(events[0].event, 'submitted');
connection.receive(JSON.stringify({id:events[0].rpc_id, result:{status:'OK'}, error:null}));
assert.equal(events[1].event, 'accepted');
connection.send('miner', 'submit', {job_id:'job', nonce:'01000000', result:'test'});
connection.receive(JSON.stringify({id:events[2].rpc_id, result:null, error:{code:-1, message:'synthetic rejection'}}));
assert.equal(events[3].event, 'rejected');
connection.socket.write = ()=>{throw new Error('synthetic write failure');};
connection.send('miner', 'submit', {job_id:'job', nonce:'02000000', result:'test'});
assert.equal(events.length, 4);
console.log(JSON.stringify({status:'passed', synthetic:true, external_connection:false,
  wasm_executed:false, unauthenticated_share_not_counted:true,
  backpressure_write_counted:true, accepted_and_rejected_responses_recorded:true}));

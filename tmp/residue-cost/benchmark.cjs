const fs=require('fs'),path=require('path'),crypto=require('crypto'),os=require('os');
const root=__dirname,src='C:/Users/ettotto/Documents/wasm-structured-encoding/candidates/residue-occupancy';
const records=JSON.parse(fs.readFileSync(path.join(src,'manifest.json')));
const cases=JSON.parse(fs.readFileSync(path.join(src,'inputs.json'))).slice(-256).map(c=>[...c.values,c.u,31]);
let sink=0;
function batch(fn,count){let checksum=0;const started=process.hrtime.bigint();for(let i=0;i<count;i++){const result=fn(...cases[i&255]);checksum^=result[0]^result[1]^result[2];}const ms=Number(process.hrtime.bigint()-started)/1e6;sink^=checksum;return {ms,checksum:checksum>>>0,calls:count};}
(async()=>{const variants=[];for(const record of records){const data=fs.readFileSync(path.join(src,record.file));if(crypto.createHash('sha256').update(data).digest('hex')!==record.sha256)throw Error('binary changed');const {instance}=await WebAssembly.instantiate(data);variants.push({...record,fn:instance.exports.run});}
// Verify identical checksums at an odd count to avoid total XOR cancellation.
const verification=variants.map(v=>({file:v.file,...batch(v.fn,4093)}));if(verification.some(v=>v.checksum!==verification[0].checksum))throw Error('checksum mismatch');
for(const v of variants)batch(v.fn,16384);
const fastestControl=variants.find(v=>v.file==='normal-O2.wasm');let calls=4096;const calibration=[];
while(true){const run=batch(fastestControl.fn,calls);calibration.push(run);if(run.ms>=100||calls>=1048576)break;calls*=2;}
const output={node:process.version,v8:process.versions.v8,cpu:os.cpus()[0].model,platform:process.platform,input_count:cases.length,rounds_per_call:31,calls_per_batch:calls,verification,calibration,rounds:[],artifacts:records};
for(let round=0;round<11;round++){const measurements=[];for(let offset=0;offset<variants.length;offset++){const v=variants[(round+offset)%variants.length];measurements.push({file:v.file,...batch(v.fn,calls)});}output.rounds.push({round,measurements});fs.writeFileSync(path.join(root,'raw.json'),JSON.stringify(output,null,2));}
const summary=variants.map(v=>{const times=output.rounds.map(r=>r.measurements.find(m=>m.file===v.file).ms).sort((a,b)=>a-b);return {file:v.file,calls,median_ms:times[5],min_ms:times[0],max_ms:times[10],q1_ms:times[2],q3_ms:times[8],median_ns_per_call:times[5]*1e6/calls};});
fs.writeFileSync(path.join(root,'inputs.json'),JSON.stringify(cases));fs.writeFileSync(path.join(root,'summary.json'),JSON.stringify({summary,sink:sink>>>0},null,2));console.log(JSON.stringify(summary));})();

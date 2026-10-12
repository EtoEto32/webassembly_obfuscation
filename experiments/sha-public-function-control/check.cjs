'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
// This function has no target parameter, filesystem access or expected output.
function attack(message){return crypto.createHash('sha256').update(message).digest('hex');}
const base=path.resolve(__dirname,'../sha256-research-baseline/artifacts');
const indexBytes=fs.readFileSync(path.join(base,'inputs.json'));
const index=JSON.parse(indexBytes),bundle=fs.readFileSync(path.join(base,'inputs.bin'));
assert.equal(sha(bundle),index.bundle_sha256);
assert.equal(index.cases.length,531);
const rows=index.cases.map(c=>{
 const message=bundle.subarray(c.offset,c.offset+c.length);
 assert.equal(message.length,c.length);
 const actual=attack(message);
 assert.equal(actual,c.expected);
 return {id:c.id,length:c.length,actual,matches:true};
});
const result={kind:'target-ignoring-negative-control',node:process.version,openssl:process.versions.openssl,
 target_binary_reads:0,target_trace_reads:0,checks:rows.length,
 bundle_sha256:sha(bundle),index_sha256:sha(indexBytes),script_sha256:sha(fs.readFileSync(__filename)),
 protocol_sha256:sha(fs.readFileSync(path.join(__dirname,'protocol.json'))),rows};
fs.writeFileSync(path.join(__dirname,'results.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({checks:rows.length,target_binary_reads:0,target_trace_reads:0}));

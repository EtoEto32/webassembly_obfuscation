'use strict';
// Audit preserved execution evidence; this does not rerun Wasm or prove novelty.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const base=__dirname,art=path.join(base,'artifacts');
const target=path.join(art,'final-evidence-audit.json');
if(fs.existsSync(target))throw Error('Refuse overwrite '+target);
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const read=f=>fs.readFileSync(path.join(base,f));
const m=JSON.parse(read('artifacts/manifest.json')),v=JSON.parse(read('artifacts/verification.json'));
const checked=[];
function pin(file,expected){const actual=sha(read(file));assert.equal(actual,expected,file);checked.push({file,sha256:actual});}
pin('build.cjs',m.build_sha256);pin('verify.cjs',v.verify_sha256);
pin('artifacts/manifest.json',v.manifest_sha256);
pin('artifacts/circuit.json',m.circuit_sha256);
for(const row of m.files){pin('artifacts/'+row.file,row.sha256);pin('artifacts/'+row.file.replace(/\.wasm$/,'.wat'),row.wat_sha256);}
pin('../sha256-research-baseline/artifacts/plain.wat',m.baseline_sha256);
pin('../sha256-research-baseline/artifacts/inputs.json',v.corpus_sha256);
const index=JSON.parse(read('../sha256-research-baseline/artifacts/inputs.json'));
pin('../sha256-research-baseline/artifacts/inputs.bin',index.bundle_sha256);
const bytes=read('../sha256-research-baseline/artifacts/inputs.bin');
assert.equal(index.cases.length,531);assert.equal(v.rows.length,index.cases.length);
assert.equal(v.full_hash_cases,531);assert.equal(v.full_hash_comparisons,1062);assert.equal(v.mismatches,0);
for(let i=0;i<index.cases.length;i++){
 const c=index.cases[i],r=v.rows[i];assert.ok(c.offset>=0&&c.offset+c.length<=bytes.length);
 assert.equal(r.id,c.id);assert.equal(r.length,c.length);
 const digest=sha(bytes.subarray(c.offset,c.offset+c.length));
 for(const d of [c.expected,r.expected,r.plain,r.fixedpoint])assert.equal(d,digest,c.id);
}
const boundaries=[0,1,55,56,63,64,65,1048576];
for(const n of boundaries)assert.ok(v.rows.some(r=>r.length===n));
for(const id of ['empty','abc','long-known','million-a'])assert.ok(v.rows.some(r=>r.id===id));
assert.equal(v.locals.length,36);assert.equal(v.local_cases,36);
for(const r of v.locals){assert.equal(r.actual,r.expected);assert.equal(r.all_coordinates_equal_boolean_reference,true);}
assert.equal(v.rejections.length,8);assert.equal(v.mutation.length,2);
for(const r of v.mutation){assert.equal(r.detected,true);assert.notEqual(r.actual,r.expected);}
const circuit=JSON.parse(read('artifacts/circuit.json'));
assert.equal(circuit.gates.length,m.gates);assert.equal(m.gates,381);assert.equal(m.depth,67);
for(let i=0;i<circuit.gates.length;i++){
 const g=circuit.gates[i];assert.ok(['and','xor','or'].includes(g.op));
 for(const ref of [g.a,g.b])assert.ok(Number.isInteger(ref)&&ref>=0&&ref<98+i);
 assert.equal(circuit.depths[98+i],1+Math.max(circuit.depths[g.a],circuit.depths[g.b]));
}
assert.equal(Math.max(...circuit.depths),m.depth);assert.equal(m.iterations,32*m.depth);
assert.equal(circuit.outputs.length,32);
assert.ok(m.scratch.v>1024+1048576+64&&m.scratch.end<=17*65536);
assert.equal(m.scratch.f,m.scratch.v+4*m.gates);assert.equal(m.scratch.u,m.scratch.f+4*m.gates);
assert.equal(m.scratch.end,m.scratch.u+4*m.gates);
const report={scope:'Preserved evidence integrity and coverage audit; no new Wasm execution or novelty proof',date:'2026-10-12',audit_script_sha256:sha(fs.readFileSync(__filename)),verification_sha256:sha(read('artifacts/verification.json')),checked,corpus_cases:531,preserved_full_digest_comparisons:1062,matching_saved_rows:531,local_rows:36,negative_controls_detected:2,rejection_rows:8,boundaries,gate_order_and_depth_valid:true,disjoint_scratch_ranges:true,known_examples:v.rows.filter(r=>['empty','abc'].includes(r.id))};
fs.writeFileSync(target,JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({scope:report.scope,pinned_files:checked.length,matching_saved_rows:531,comparisons:1062,negative_controls:2,gate_order_and_depth_valid:true,output:target},null,2));

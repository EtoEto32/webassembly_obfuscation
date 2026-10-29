'use strict';
// Syntactic dependency certificate for comparison with shifted p-adic SLPs.
// No hash execution, and no claim that a dependency lower bound is exact.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const out=path.resolve(process.argv[2]||path.join(__dirname,'artifacts'));
const dest=path.join(out,'shift-certificate.json');if(fs.existsSync(dest))throw Error('Refuse overwrite '+dest);
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const cb=fs.readFileSync(path.join(out,'circuit.json')),mb=fs.readFileSync(path.join(out,'manifest.json'));
const c=JSON.parse(cb),m=JSON.parse(mb);assert.equal(sha(cb),m.circuit_sha256);
for(const row of m.files)assert.equal(sha(fs.readFileSync(path.join(out,row.mode+'.wat'))),row.wat_sha256);
const N=c.gates.length,D=m.depth,W=32;
assert.equal(N,m.gates);assert.equal(Math.max(...c.depths),D);
const predecessors=c.gates.map((g,i)=>[g.a,g.b].filter(r=>r>=98).map(r=>{assert.ok(r<98+i);assert.ok(c.depths[r]<c.depths[98+i]);return r-98;}));
// q_i(t) lower-bounds the shift from ANY initial internal input to word i
// after t simultaneous updates. External bits are fixed and have no such path.
let q=Array(N).fill(0);const milestones=[],firstAtPrecision=[];
for(let t=1;t<=D*W;t++){
 const f=predecessors.map(ps=>Math.min(...ps.map(j=>q[j])));
 const residual=q.map((v,i)=>Math.min(v,f[i]));
 q=f.map((v,i)=>Math.min(v,1+residual[i],1+residual[(i+1)%N]));
 const minimum=Math.min(...q);
 for(let p=1;p<=W;p++)if(minimum>=p&&firstAtPrecision[p-1]===undefined)firstAtPrecision[p-1]=t;
 if(t%D===0){assert.ok(minimum>=t/D);milestones.push({steps:t,minimum_shift:minimum});}
}
assert.equal(firstAtPrecision.length,W);assert.ok(firstAtPrecision.every(Number.isInteger));
const report={scope:'syntactic minimum path shifts for the current diagonal-plus-next residual mixer; not exact semantic sensitivity',node:process.version,script_sha256:sha(fs.readFileSync(__filename)),manifest_sha256:sha(mb),circuit_sha256:sha(cb),gates:N,depth:D,width:W,milestones,first_at_precision:firstAtPrecision,first_shift_1:firstAtPrecision[0],first_shift_32:firstAtPrecision[31],generic_bound:D*W,final_minimum_shift:Math.min(...q)};
fs.writeFileSync(dest,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({first_shift_1:report.first_shift_1,first_shift_32:report.first_shift_32,generic_bound:report.generic_bound,final_minimum_shift:report.final_minimum_shift}));

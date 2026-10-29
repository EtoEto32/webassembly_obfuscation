const fs=require('fs'), path=require('path'), cp=require('child_process'), crypto=require('crypto'), assert=require('assert');
const root=process.env.WASM_TOOLS_ROOT||path.resolve(__dirname,'../../.tools');
const wabt=path.join(root,'wabt-1.0.42/bin/wat2wasm.exe');
const opt=path.join(root,'binaryen-version_133/bin/wasm-opt.exe');
const out=path.join(__dirname,'artifacts'); fs.mkdirSync(out,{recursive:false});
const save=(name,data)=>fs.writeFileSync(path.join(out,name),JSON.stringify(data,null,2));
const kernels=[
 {name:'polynomial',f:(s,u)=>(s*s+3*s+u)&255, ref:(s,u)=>(s*s+3n*s+u)&255n, wat:'(i32.and (i32.add (i32.add (i32.mul (local.get 0) (local.get 0)) (i32.mul (i32.const 3) (local.get 0))) (local.get 1)) (i32.const 255))'},
 {name:'rotation',f:(s,u)=>(((s<<1)|(s>>>7))^u)&255,ref:(s,u)=>(((s<<1n)|(s>>7n))^u)&255n,wat:'(i32.and (i32.xor (i32.or (i32.shl (local.get 0) (i32.const 1)) (i32.shr_u (local.get 0) (i32.const 7))) (local.get 1)) (i32.const 255))'},
 {name:'upper-branch',f:(s,u)=>(s+((s&128)?3:5)+u)&255,ref:(s,u)=>(s+((s&128n)?3n:5n)+u)&255n,wat:'(i32.and (i32.add (i32.add (local.get 0) (if (result i32) (i32.and (local.get 0) (i32.const 128)) (then (i32.const 3)) (else (i32.const 5)))) (local.get 1)) (i32.const 255))'},
 {name:'division',f:(s,u)=>(Math.floor(s/3)+u)&255,ref:(s,u)=>(s/3n+u)&255n,wat:'(i32.and (i32.add (i32.div_u (local.get 0) (i32.const 3)) (local.get 1)) (i32.const 255))'}
];
function refine(k){
 let p=Array.from({length:256},(_,s)=>s&15), rounds=0;
 for(;;){ const ids=new Map(); const q=p.map((_,s)=>{const key=[s&15,p[k.f(s,0)],p[k.f(s,1)]].join(',');if(!ids.has(key))ids.set(key,ids.size);return ids.get(key)});rounds++;if(q.every((v,i)=>v===p[i]))return {p:q,rounds};p=q; }
}
function independent(k,p){
 const d=new Uint8Array(256*256);const next=Array.from({length:256},(_,s)=>[0,1].map(u=>Number(k.ref(BigInt(s),BigInt(u)))));
 for(let a=0;a<256;a++)for(let b=0;b<256;b++)d[a*256+b]=(a&15)!==(b&15);
 let changes,rounds=0;do {changes=0;rounds++;for(let a=0;a<256;a++)for(let b=0;b<256;b++)if(!d[a*256+b]&&[0,1].some(u=>d[next[a][u]*256+next[b][u]])){d[a*256+b]=1;changes++;}}while(changes);
 let samePairs=0;for(let a=0;a<256;a++)for(let b=0;b<256;b++){assert.equal(!d[a*256+b],p[a]===p[b]);if(a<b&&!d[a*256+b])samePairs++;}
 return {orderedPairsChecked:65536,mergedUnorderedPairs:samePairs,rounds};
}
function observer(binary,count){
 const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(binary))).exports;
 const states=Array.from({length:count},(_,s)=>({output:e.readout(s),next:[e.step(s,0),e.step(s,1)]}));
 return {states,queries:count*3};
}
const results=[];
for(const k of kernels){
 const {p,rounds}=refine(k),count=Math.max(...p)+1, reps=Array.from({length:count},(_,i)=>p.indexOf(i));
 const verification=independent(k,p),transitions=reps.flatMap(s=>[p[k.f(s,0)],p[k.f(s,1)]]),outputs=reps.map(s=>s&15);
 save(k.name+'-verifier.json',{map:p,reps,transitions,outputs,rounds,verification});
 const data=Buffer.from([...transitions,...outputs]).toString('hex').match(/../g).map(h=>'\\'+h).join('');
 const native=`(module (func (export "step") (param i32 i32) (result i32) ${k.wat}) (func (export "readout") (param i32) (result i32) (i32.and (local.get 0) (i32.const 15))))`;
 const quotient=`(module (memory 1) (data (i32.const 0) "${data}") (func (export "step") (param i32 i32) (result i32) (i32.load8_u (i32.add (i32.mul (local.get 0) (i32.const 2)) (local.get 1)))) (func (export "readout") (param i32) (result i32) (i32.load8_u (i32.add (local.get 0) (i32.const ${count*2})))))`;
 for(const [variant,wat]of Object.entries({native,quotient})){
  const stem=k.name+'-'+variant,src=path.join(out,stem+'.wat'),raw=path.join(out,stem+'.wasm');fs.writeFileSync(src,wat);cp.execFileSync(wabt,[src,'-o',raw]);
  const optimized=path.join(out,stem+'-O2.wasm');cp.execFileSync(opt,[raw,'-O2','-o',optimized]);
  for(const binary of [raw,optimized]){
   const bytes=fs.readFileSync(binary), e=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;
   let edges=0;for(let s=0;s<256;s++){
    const state=variant==='native'?s:p[s];assert.equal(e.readout(state),s&15);
    for(let u=0;u<2;u++){const expected=Number(k.ref(BigInt(s),BigInt(u)));assert.equal(e.step(state,u),variant==='native'?expected:p[expected]);edges++;}
   }
   const recovered=observer(binary,variant==='native'?256:count);
   for(let s=0;s<recovered.states.length;s++){
    const original=variant==='native'?s:reps[s];assert.equal(recovered.states[s].output,original&15);
    for(let u=0;u<2;u++){const expected=Number(k.ref(BigInt(original),BigInt(u)));assert.equal(recovered.states[s].next[u],variant==='native'?expected:p[expected]);}
   }
   save(path.basename(binary)+'.recovered.json',recovered);
   results.push({kernel:k.name,variant,file:path.basename(binary),states:recovered.states.length,bytes:bytes.length,sha256:crypto.createHash('sha256').update(bytes).digest('hex'),edgesChecked:edges,initialOutputsChecked:256,reconstructionQueries:recovered.queries,mismatches:0});
  }
 }
}
save('results.json',{date:new Date().toISOString(),node:process.version,v8:process.versions.v8,wabt:cp.execFileSync(wabt,['--version'],{encoding:'utf8'}).trim(),binaryen:cp.execFileSync(opt,['--version'],{encoding:'utf8'}).trim(),results});
console.log(JSON.stringify(results));

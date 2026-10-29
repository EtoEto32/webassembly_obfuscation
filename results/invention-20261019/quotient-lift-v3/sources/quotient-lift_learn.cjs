// Membership queries only. No source, transition table, seed, or equality oracle.
const fs=require('fs'),crypto=require('crypto');
const file=process.argv[2];
const begin=performance.now(),e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(file))).exports;
const loaded=performance.now();
const bytes=new Uint8Array(e.memory.buffer),cache=new Map(),transcript=[];
function member(word){
 if(cache.has(word))return cache.get(word);
 if(word.length>bytes.length)throw Error('Query too long');
 for(let i=0;i<word.length;i++)bytes[i]=Number(word[i]);
 const answer=e.run(0,word.length);
 if(answer!==0&&answer!==1)throw Error('Nonboolean response');
 cache.set(word,answer);transcript.push([word,answer]);return answer;
}
const S=[''],E=[''];let rounds=0,closures=0,consistencies=0,tested=0;
const row=s=>E.map(e=>member(s+e)).join('');
function hypothesize(){
 for(;;){
  const rows=new Set(S.map(row));let added=false;
  outer:for(const s of S)for(const a of ['0','1'])if(!rows.has(row(s+a))){S.push(s+a);closures++;added=true;break outer;}
  if(added)continue;
  outer:for(let i=0;i<S.length;i++)for(let j=0;j<i;j++)if(row(S[i])===row(S[j]))for(const a of ['0','1']){
   const x=row(S[i]+a),y=row(S[j]+a);
   if(x!==y){const at=[...x].findIndex((v,k)=>v!==y[k]);E.push(a+E[at]);consistencies++;added=true;break outer;}
  }
  if(!added)break;
 }
 const ids=new Map(),reps=[];
 for(const s of S){const r=row(s);if(!ids.has(r)){ids.set(r,ids.size);reps.push(s);}}
 return reps.map(s=>[ids.get(row(s+'0')),ids.get(row(s+'1')),member(s)]);
}
function accepts(rows,word){let q=0;for(const a of word)q=rows[q][Number(a)];return rows[q][2];}
const tests=[];
for(let n=0;n<=8;n++)for(let x=0;x<2**n;x++)tests.push(n?x.toString(2).padStart(n,'0'):'');
let rng=20261019;function random(){rng^=rng<<13;rng^=rng>>>17;rng^=rng<<5;return rng>>>0;}
for(let i=0;i<2000;i++){const n=1+random()%64;let word='';for(let j=0;j<n;j++)word+=String(random()&1);tests.push(word);}
let result;
for(rounds=1;rounds<=100;rounds++){
 result=hypothesize();let counterexample=null;
 for(const word of tests){tested++;if(accepts(result,word)!==member(word)){counterexample=word;break;}}
 if(counterexample===null)break;
 for(let i=1;i<=counterexample.length;i++){const p=counterexample.slice(0,i);if(!S.includes(p))S.push(p);}
}
if(rounds>100)throw Error('Round limit');
console.log(JSON.stringify({status:'bounded_tests_passed',rows:result,queries:cache.size,query_symbols:transcript.reduce((a,b)=>a+b[0].length,0),rounds,closures,consistencies,tested,
 elapsed_ms:performance.now()-begin,load_compile_instantiate_ms:loaded-begin,learning_ms:performance.now()-loaded,node:process.version,transcript_sha256:crypto.createHash('sha256').update(JSON.stringify(transcript)).digest('hex'),
 max_exhaustive_length:8,random_tests:2000,max_random_length:64,exact_equivalence_oracle:false}));

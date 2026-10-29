const fs=require('fs'),crypto=require('crypto');
const [file,arityText,out]=process.argv.slice(2),n=Number(arityText);
let seed=0x64e13579;function rng(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;}
(async()=>{const bytes=fs.readFileSync(file);const {instance}=await WebAssembly.instantiate(bytes);const groups=[[],[]],queries=[];
while(groups.some(g=>g.length<16)){const xs=Array.from({length:n},()=>rng()%64),u=rng()%64;const sum=xs.reduce((a,b)=>a+b,0)>>>0,parity=sum&1;if(groups[parity].length===16)continue;const args=[...xs,u,1];const actual=instance.exports.run(...args).map(x=>x>>>0);const row={args,actual,parity,sum,sumsq:xs.reduce((a,x)=>(a+Math.imul(x,x))>>>0,0)};queries.push(row);groups[parity].push(row);}
const started=performance.now();const fit=[];
for(let p=0;p<2;p++){const models=[];for(let A=-8;A<=8;A++)for(let B=-8;B<=8;B++)for(let G=-8;G<=8;G++)for(let D=-8;D<=8;D++){if(groups[p].every(q=>((Math.imul(A,q.sumsq)+Math.imul(B,q.sum)+Math.imul(G,Math.imul(n,q.args[n]))+Math.imul(D,n))>>>0)===q.actual[0]))models.push({A,B,G,D});}fit.push(models);}
const joined=[];for(const a of fit[0])for(const b of fit[1])if(a.A===b.A&&a.G===b.G&&a.D===b.D)joined.push({A:a.A,B:[a.B,b.B],G:a.G,D:a.D});
const result={file,arity:n,sha256:crypto.createHash('sha256').update(bytes).digest('hex'),seed:'0x64e13579',queries,branch_models:fit,models:joined,enumerated_per_branch:17**4,fit_ms:performance.now()-started};fs.writeFileSync(out,JSON.stringify(result,null,2));console.log(JSON.stringify({file,queries:queries.length,models:joined}));})();

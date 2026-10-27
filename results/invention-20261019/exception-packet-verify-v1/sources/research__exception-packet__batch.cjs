const fs=require('fs');const [file,kind,count]=process.argv.slice(2),k=Number(count);
function rotl(x,n){return (x<<n)|(x>>>(32-n));}
function oracle(x,y,z){let h=x|0;for(let j=0;j<k;j++){let c=z&(j%2===0?1:0x80000000);if(kind==='blend'){h^=c?rotl((x+j*123+17)|0,j%31+1):Math.imul(y^(j*311+91),j*2+3);}else{if(kind==='rolling')c=(x>>>(j%8))&1;h=c?(h+(j+1)*12345)|0:rotl(h^y,j%31+1);}}return h|0;}
const f=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(file))).exports.bench;
let checks=0;for(const n of [1,2,7,31]){let h=0,s=0x51c31628;for(let i=0;i<n;i++)h=rotl(h,1)^oracle((s+i)|0,s^Math.imul(i,1103515245),Math.imul(i,2654435761));if(f(n,s)!==h)throw Error('Harness mismatch');checks++;}
const warmup=2048,iterations=512,samples=9;let sink=f(warmup,0x15aac713),ns=[];
for(let i=0;i<samples;i++){let t=process.hrtime.bigint();sink^=f(iterations,(0x51ca3132+i*313)|0);ns.push(Number(process.hrtime.bigint()-t)/iterations);}
console.log(JSON.stringify({warmup,iterations,samples_ns:ns,median_ns:[...ns].sort((a,b)=>a-b)[Math.floor(ns.length/2)],checksum:sink,maxRSS_KiB:process.resourceUsage().maxRSS,harness_checks:checks}));


const fs=require('fs'),path=require('path');
(async()=>{
 const dir=process.argv[2],modes=['plain','output-only','random','frontier'];
 const ex=await Promise.all(modes.map(async m=>(await WebAssembly.instantiate(fs.readFileSync(path.join(dir,m+'.wasm')))).instance.exports));
 let seed=20261018;const rand=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;};
 const inputs=[];for(const x of [0,1,4,16,65532,65533,65536,0xffffffff])for(const y of [0,1,0xffffffff])for(const z of [0,1,0x80000000])inputs.push([x,y,z]);
 for(let i=0;i<1024;i++)inputs.push([i%2?rand():rand()%65536,rand(),rand()]);
 function obs(e,row){new Uint8Array(e.memory.buffer).fill(0);let value=null,trap=null;try{value=e.run(...row);}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;trap=err.message;}return {value,trap,bytes:Buffer.from(new Uint8Array(e.memory.buffer))};}
 const rows=modes.map(mode=>({mode,checks:0,mismatches:0,traps:0}));
 for(const input of inputs){const expected=obs(ex[0],input);for(let i=0;i<ex.length;i++){const got=obs(ex[i],input);rows[i].checks++;if(got.trap)rows[i].traps++;if(got.value!==expected.value||got.trap!==expected.trap||!got.bytes.equals(expected.bytes))rows[i].mismatches++;}}
 fs.writeFileSync(path.join(dir,'inputs.json'),JSON.stringify(inputs));fs.writeFileSync(path.join(dir,'runtime.json'),JSON.stringify({node:process.version,v8:process.versions.v8,rows},null,2));
 console.log(JSON.stringify(rows));if(rows.some(x=>x.mismatches))process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1;});

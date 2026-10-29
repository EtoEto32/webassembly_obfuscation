const fs=require('fs'),path=require('path'),dir=process.argv[2];
const manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'),'utf8'));
let seed=20261018;function random(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;}
const initial=Buffer.alloc(65536);for(let i=0;i<initial.length;i++)initial[i]=random()&255;
const expected=Buffer.from(initial),cases={};
for(const [name,model] of Object.entries(manifest.models)){
 const ps=new Set([0,1,2,65535,65536,0xffffffff,0xfffffffe]);
 for(const [offset,width] of model.stores)for(const d of [-1,0,1])ps.add((65536-offset-width+d)>>>0);
 const inputs=[];for(const p of ps)for(const v of [0,1,0x7fffffff,0x80000000,0xffffffff])inputs.push([p,...Array(model.params-1).fill(v)]);
 const boundary=inputs.length;
 for(let i=0;i<1024;i++)inputs.push([i%4===0?random():i%4===1?65480+random()%80:random()%4096,...Array.from({length:model.params-1},()=>random())]);
 cases[name]={inputs,boundary};
}
function reference(model,args){initial.copy(expected);const p=args[0]>>>0;for(const [offset,width,param] of model.stores){
 const address=p+offset;if(address+width>expected.length)return true;
 const v=args[param]>>>0;for(let j=0;j<width;j++)expected[address+j]=(v>>>(j*8))&255;
}return false;}
let calls=0,traps=0,mismatches=0;const records=[],details=[];
for(const file of manifest.files){const data=fs.readFileSync(path.join(dir,file.path));if(!WebAssembly.validate(data))throw Error('Invalid '+file.path);
 const e=new WebAssembly.Instance(new WebAssembly.Module(data)).exports,mem=Buffer.from(e.memory.buffer);let localTraps=0,localMismatch=0;
 for(const args of cases[file.model].inputs){const wantTrap=reference(manifest.models[file.model],args);initial.copy(mem);let trap=false,value;
  try{value=e.run(...args)}catch(error){if(!(error instanceof WebAssembly.RuntimeError))throw error;trap=true;}
  calls++;if(trap){traps++;localTraps++;}
  if(trap!==wantTrap||(!trap&&value!==0)||!mem.equals(expected)){mismatches++;localMismatch++;if(details.length<8)details.push({path:file.path,args,trap,wantTrap,value});}
 }
 records.push({path:file.path,calls:cases[file.model].inputs.length,boundary:cases[file.model].boundary,traps:localTraps,mismatches:localMismatch});
}
console.log(JSON.stringify({binaries:manifest.files.length,calls,traps,mismatches,details,records,memory_bytes_compared_per_call:65536,node:process.version,v8:process.versions.v8}));if(mismatches)process.exitCode=1;

const fs=require('fs'),path=require('path'),dir=process.argv[2];
const controls=JSON.parse(fs.readFileSync(path.join(dir,'controls-manifest.json'),'utf8'));
function execute(file,args){const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,file)))).exports;
 const mem=Buffer.from(e.memory.buffer);mem.fill(0x5a);let trap=false;try{e.run(...args)}catch(error){if(!(error instanceof WebAssembly.RuntimeError))throw error;trap=true}
 return {trap,memory:Buffer.from(mem)};
}
const rows=[];for(const c of controls){const a=execute(c.original,c.args),b=execute(c.wrong,c.args);
 const differences=[];for(let i=0;i<a.memory.length;i++)if(a.memory[i]!==b.memory[i])differences.push({address:i,original:a.memory[i],wrong:b.memory[i]});
 if(a.trap!==b.trap||!a.trap||differences.length===0)throw Error('Control did not isolate trap-visible memory difference');
 rows.push({case:c.case,args:c.args,original_trap:a.trap,wrong_trap:b.trap,memory_differences:differences});
}
console.log(JSON.stringify(rows));

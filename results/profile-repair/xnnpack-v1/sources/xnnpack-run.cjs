'use strict';
const fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const input=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const rows=[];let calls=0,outputBytesChecked=0;
for(const row of input.rows)for(const [profile,file] of Object.entries(row.files)){
  const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(input.directory,file)))).exports;
  const memory=Buffer.from(e.memory.buffer),before=Buffer.alloc(65536,0xa5);let mismatchBlocks=0,firstMismatch=null;
  const probe=e.probe();
  for(let ti=0;ti<input.tables.length;ti++)for(let block=0;block<16;block++){
    before.fill(0xa5);Buffer.from(input.tables[ti]).copy(before,0);
    for(let lane=0;lane<16;lane++)before[256+lane]=16*block+lane;
    before.copy(memory);e.run();calls++;let bad=false;
    for(let lane=0;lane<16;lane++){
      const expected=before[before[256+lane]],actual=memory[512+lane];outputBytesChecked++;
      if(actual!==expected){bad=true;if(!firstMismatch)firstMismatch={table:ti,index:before[256+lane],actual,expected};}
    }
    if(bad)mismatchBlocks++;
    if(!memory.subarray(0,512).equals(before.subarray(0,512))||!memory.subarray(528).equals(before.subarray(528)))throw new Error('write outside output '+file);
  }
  rows.push({mode:row.mode,profile,probe,mismatchBlocks,firstMismatch});
}
process.stdout.write(JSON.stringify({node:process.version,v8:process.versions.v8,cpu:os.cpus()[0].model,rows,calls,outputBytesChecked,tables:input.tables.length,fullMemoryBytes:65536}));

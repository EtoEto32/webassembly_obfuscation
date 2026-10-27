const fs=require('node:fs'),path=require('node:path');
const dir=process.argv[2], cases=JSON.parse(fs.readFileSync(path.join(dir,'cases.json'))), manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
let seed=0x6e214903;function rand(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;}
const result={calls:0,traps:0,mismatches:0,diagnostic_calls:0,negative:[],rows:[]};
for(const c of cases){
  const n=c.edges.length, input=[];
  for(const x of [0,1,n-1,n,0x7fffffff,0x80000000,0xffffffff]) for(let j=0;j<3;j++){
    const a=[0,0,0,rand()];a[j]=x;input.push(a);
  }
  for(const steps of [0,1,2,31,255,256,257,0xffffffff,0x80000000]) for(const u of [0,n-1]){
    input.push([u,(-steps)&(n-1),u,steps]); // partner w=u, including overflow
    input.push([u,n-1,0,steps]);
  }
  for(let i=0;i<2048;i++)input.push([rand()&(n-1),rand()&(n-1),rand()&(n-1),rand()]);
  for(const row of manifest.filter(t=>t.name===c.name)){
    const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,row.file)))).exports;
    let edges=c.edges.slice(),calls=0,traps=0,mismatches=0,physicalChecks=0;
    const mode=row.mode==='recovered'?'plain':row.mode;
    for(let k=0;k<input.length;k++){
      if(k%137===0){e.reset();edges=c.edges.slice();}
      const args=input[k], [u,v,start,count]=args,expectedTrap=u>=n||v>=n||start>=n;
      let expected=0;
      if(!expectedTrap){edges[u]=v;let cur=start;for(let j=0;j<(count&255);j++){
        expected=((expected<<5)|(expected>>>27))^c.payload[cur];cur=edges[cur];}}
      const before=e.memory&&expectedTrap?Buffer.from(new Uint8Array(e.memory.buffer)):null;
      let value,trap=false;try{value=e.run(...args)|0;}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;trap=true;}
      let ok=trap===expectedTrap&&(trap||value===expected);
      if(e.memory){
        const words=new Uint32Array(e.memory.buffer),factor=mode!=='plain';
        const A=factor?Array.from(words.slice(0,n)):null;
        if(A&&new Set(A).size!==n)ok=false;
        for(let i=0;i<n;i++)if((factor?words[n+A[i]]:words[i])!==edges[i])ok=false;
        for(let i=0;i<n;i++)if(words[(factor?2:1)*n+i]!==c.payload[i])ok=false;
        if(before&&!before.equals(Buffer.from(e.memory.buffer)))ok=false;
        physicalChecks++;
      }
      calls++;if(trap)traps++;if(!ok)mismatches++;
      if(!ok&&!row.negative)throw Error(JSON.stringify({row,k,args,value,expected,trap,expectedTrap}));
    }
    if(row.negative){if(!mismatches)throw Error('Negative control has no witness');result.negative.push({file:row.file,calls,traps,mismatches});}
    else{result.calls+=calls;result.traps+=traps;result.mismatches+=mismatches;result.diagnostic_calls+=physicalChecks;result.rows.push({file:row.file,calls,traps,mismatches,physicalChecks});}
  }
}
console.log(JSON.stringify(result));

const fs=require('node:fs'),path=require('node:path');
const dir=process.argv[2],cases=JSON.parse(fs.readFileSync(path.join(dir,'cases.json'))),manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
let seed=0x45613412;
function rand(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;}
const total={calls:0,traps:0,mismatches:0,rows:[],negative:[],node:process.version,v8:process.versions.v8};
for(const c of cases){
  const n=c.edges.length,inputs=[];
  for(const x of [0,1,n-1,n,0x7fffffff,0x80000000,0xffffffff]) for(let j=0;j<3;j++){
    const a=[0,0,0,rand()];a[j]=x;inputs.push(a);
  }
  for(const steps of [0,1,2,31,255,256,257,0xffffffff,0x80000000])for(const u of [0,n-1]){
    inputs.push([u,(-steps)&(n-1),u,steps],[u,n-1,0,steps]);
  }
  for(let i=0;i<2048;i++) inputs.push([rand()&(n-1),rand()&(n-1),rand()&(n-1),rand()]);
  for(const row of manifest.filter(t=>t.name===c.name)){
    const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,row.file)))).exports;
    let edges=c.edges.slice(),calls=0,traps=0,mismatches=0,firstWitness=null;
    for(let k=0;k<inputs.length;k++){
      if(k%137===0){e.reset();edges=c.edges.slice();}
      const args=inputs[k],[u,v,start,count]=args,expectedTrap=u>=n||v>=n||start>=n;
      let expected=0;
      if(!expectedTrap){edges[u]=v;let cur=start;for(let j=0;j<(count&255);j++){
        expected=((expected<<5)|(expected>>>27))^c.payload[cur];cur=edges[cur];}}
      let actual,trap=false;
      try{actual=e.run(...args)|0;}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;trap=true;}
      const ok=trap===expectedTrap&&(trap||actual===expected);
      calls++;if(trap)traps++;
      if(!ok){mismatches++;if(!firstWitness)firstWitness={k,args,actual,expected,trap,expectedTrap};
        if(!row.negative)throw Error(JSON.stringify({file:row.file,...firstWitness}));}
    }
    const result={file:row.file,calls,traps,mismatches};
    if(row.negative){if(!mismatches)throw Error('negative control without witness');total.negative.push({...result,firstWitness});}
    else{total.calls+=calls;total.traps+=traps;total.mismatches+=mismatches;total.rows.push(result);}
  }
}
console.log(JSON.stringify(total));

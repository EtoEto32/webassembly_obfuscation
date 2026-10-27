const fs=require('fs'),path=require('path'),assert=require('assert');
const manifest=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
let seed=20261024;function random(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;}
function call(e,name,args){try{return {value:e[name](...args)??null};}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;return {trap:true};}}
function snapshot(e){
 const size=e.size(),tsize=e.tsize();
 return {size,tsize,g:e.gget(),bytes:Buffer.from(new Uint8Array(e.__test_mem.buffer,0,size*65536)),
 tables:Array.from({length:tsize},(_,i)=>{let f=e.__test_table.get(i);if(!f)return null;try{return f(123);}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;return 'trap';}})};
}
let calls=0,bytes=0,epochs=0,traps=0,rows=[];
for(const fixture of [...new Set(manifest.rows.map(r=>r.fixture))])for(const pipeline of ['raw','O3']){
 const list=manifest.rows.filter(r=>r.fixture===fixture&&r.pipeline===pipeline);
 const mods=Object.fromEntries(list.map(r=>[r.mode,new WebAssembly.Module(fs.readFileSync(path.join(manifest.directory,r.observed)))]));
 const targets=Object.fromEntries(Object.entries(mods).filter(([k])=>k!=='source').map(([k,v])=>[k,new WebAssembly.Instance(v).exports]));
 const failed={},counts={};let baseSize;
 for(let epoch=0;epoch<24;epoch++){
  const source=new WebAssembly.Instance(mods.source).exports;baseSize=source.size();epochs++;
  for(const [k,e]of Object.entries(targets))if(!failed[k])e.__lr_reset();
  const ops=[['size',[]],['tsize',[]],['get8',[0]],['init',[0,0,1]],['tinit',[0,0,1]],
    ['initactive',[0,0,0]],['initactive',[0,1,0]],['tactive',[0,0,0]],['tdeclare',[0,0,1]],
    ['grow',[1]],['tgrow',[3]],['put',[baseSize*65536,0x12345678]],['get',[baseSize*65536]],
    ['init',[0,0,3]],['copy',[1,0,9]],['copy',[0,1,9]],['fill',[4,255,7]],
    ['tinit',[0,0,3]],['tcopy',[1,0,2]],['tcopy',[0,1,2]],['call',[55,0]],
    ['ddrop',[]],['init',[0,0,1]],['init',[0,0,0]],['init',[0,1,0]],
    ['edrop',[]],['tinit',[0,0,1]],['tinit',[0,0,0]],['tinit',[0,1,0]],
    ['offset',[32]],['side',[-1,902]],['fault',[]],['gget',[]]];
  const names=['get','put','get8','put8','put64','get64','putf32','getf32','putf64','side','copy','fill','init','grow','tgrow','tget','tset','tnull','tcopy','tfill','tinit','call','work'];
  const arity={get:1,put:2,get8:1,put8:2,put64:2,get64:1,putf32:2,getf32:1,putf64:2,side:2,copy:3,fill:3,init:3,grow:1,tgrow:1,tget:1,tset:1,tnull:1,tcopy:3,tfill:2,tinit:3,call:2,work:1};
  const edge=[0,1,2,3,7,15,16,17,65535,65536,baseSize*65536,baseSize*65536+1,-1,0x7fffffff,-2147483648];
  for(let i=0;i<120;i++){const n=names[random()%names.length];let a=Array.from({length:arity[n]},()=>edge[random()%edge.length]);if(n==='work')a=[random()%65];ops.push([n,a]);}
  for(const [name,args]of ops){
   const expected=call(source,name,args),state=snapshot(source);if(expected.trap)traps++;
   for(const [mode,e]of Object.entries(targets))if(!failed[mode]){
    const actual=call(e,name,args),observed=snapshot(e);calls++;bytes+=state.bytes.length;
    counts[mode]=(counts[mode]||0)+1;
    const difference=[];
    if(JSON.stringify(expected)!==JSON.stringify(actual))difference.push('result/trap');
    for(const k of ['size','tsize','g'])if(state[k]!==observed[k])difference.push(k);
    if(!state.bytes.equals(observed.bytes))difference.push('memory');
    if(JSON.stringify(state.tables)!==JSON.stringify(observed.tables))difference.push('table');
    if(difference.length){const detail={fixture,pipeline,mode,epoch,name,args,expected,actual,difference};if(mode==='full')throw Error(JSON.stringify(detail));failed[mode]=detail;}
   }
  }
 }
 for(const mode of ['plain','no-bounds','no-drop'])assert(failed[mode],`${fixture}/${pipeline}: missing ${mode} counterexample`);
 rows.push({fixture,pipeline,counts,counterexamples:failed});
}
console.log(JSON.stringify({calls,comparedMemoryBytes:bytes,epochs,sourceTraps:traps,rows,node:process.version,v8:process.versions.v8,
 note:'Numeric results and trap occurrence; messages/identity/physical capacity/OOM choices excluded. Observational exports exist only in test binaries.'}));

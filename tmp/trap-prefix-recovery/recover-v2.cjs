'use strict';
// Reads only a Wasm binary, public input tuples, and the initial public memory.
// Family-aware heuristic, not a general Wasm deobfuscator.
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),crypto=require('node:crypto');
const [binary,inputFile,memoryFile,out]=process.argv.slice(2);fs.mkdirSync(out,{recursive:true});
const root=process.env.WASM_TOOLS_ROOT||'C:/Users/ettotto/Documents/webassembly_obfuscation/.tools';
const dis=path.join(root,'wabt-1.0.42/bin/wasm2wat.exe'),asm=path.join(root,'wabt-1.0.42/bin/wat2wasm.exe');
const start=performance.now();
const wat=cp.execFileSync(dis,[binary,'--fold-exprs','--generate-names'],{encoding:'utf8'});
const tokens=wat.replace(/\(;[\s\S]*?;\)/g,'').replace(/;;[^\n]*/g,'').match(/\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+/g);
let pos=0;function parse(){if(tokens[pos++]!=='(')throw Error('Expected list');const list=[];while(tokens[pos]!==')'){if(pos>=tokens.length)throw Error('Unclosed list');list.push(tokens[pos]==='('?parse():tokens[pos++]);}pos++;return list;}
const tree=parse();if(pos!==tokens.length||tree[0]!=='module')throw Error('Unsupported WAT');
const is=(x,name)=>Array.isArray(x)&&x[0]===name;
const functions=tree.filter(n=>is(n,'func'));
const candidates=functions.filter(f=>f.filter(n=>is(n,'param')).flat().filter(x=>x==='i32').length===5&&f.some(n=>is(n,'result')&&n[1]==='i32'));
if(candidates.length!==1)throw Error('Helper signature heuristic ambiguous/absent');
const helper=candidates[0],helperId=helper[1],pnames=helper.filter(n=>is(n,'param')).map(n=>n[1]);
if(pnames.some(n=>!n.startsWith('$')))throw Error('Missing generated local names');
const exported=tree.find(n=>is(n,'export')&&n[1]==='"run"'),main=functions.find(f=>f[1]===exported?.[2]?.[1]);if(!main)throw Error('run export missing');
// Follow the accumulated word through local.set/get as well as nested calls.
// v1's syntax-only grouping missed chains written as separate assignments.
const groups=[],provenance=new Map();
function rewrite(n){
 if(!Array.isArray(n))return {node:n,group:null};
 if(is(n,'local.get'))return {node:n,group:provenance.get(n[1])??null};
 const children=n.map(rewrite),node=children.map(c=>c.node);
 if(is(n,'i32.load')){const id=groups.length;groups.push({id,calls:0});return {node,group:id};}
 if(is(n,'call')&&n[1]===helperId){
  const id=children[2].group;if(id===null)throw Error('Cannot identify load provenance');groups[id].calls++;
  return {node:['block',['result','i32'],['global.set','$audit_group',['i32.const',String(id)]],node],group:id};
 }
 const unique=[...new Set(children.map(c=>c.group).filter(g=>g!==null))];const group=unique.length===1?unique[0]:null;
 if(is(n,'local.set')||is(n,'local.tee')){provenance.set(n[1],children[2].group);return {node,group:is(n,'local.tee')?children[2].group:null};}
 return {node,group};
}
for(let i=2;i<main.length;i++)main[i]=rewrite(main[i]).node;
const selected=groups.filter(g=>g.calls>0).reduce((best,g)=>!best||g.calls>=best.calls?g:best,null);if(!selected)throw Error('No helper call group');
const header=new Set(['type','param','result','local']);let insert=2;while(insert<helper.length&&Array.isArray(helper[insert])&&header.has(helper[insert][0]))insert++;
helper.splice(insert,0,['call','$audit_observe',['global.get','$audit_group'],...pnames.slice(2).map(p=>['local.get',p])]);
tree.splice(1,0,['import','"audit"','"observe"',['func','$audit_observe',['param','i32','i32','i32','i32']]],['global','$audit_group',['mut','i32'],['i32.const','0']]);
const render=n=>Array.isArray(n)?'('+n.map(render).join(' ')+')':n;
const patched=path.join(out,'instrumented.wat'),wasm=path.join(out,'instrumented.wasm');fs.writeFileSync(patched,render(tree));cp.execFileSync(asm,[patched,'-o',wasm]);
let trace=[];const instance=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(wasm)),{audit:{observe:(group,address,value,enabled)=>trace.push({group,address:address>>>0,value:value>>>0,enabled:enabled>>>0})}});
const memory=Buffer.from(instance.exports.memory.buffer),initial=fs.readFileSync(memoryFile),inputs=JSON.parse(fs.readFileSync(inputFile)),rows=[];
for(let i=0;i<inputs.length;i++){
 initial.copy(memory);trace=[];let output=null,trap=null;
 try{output=instance.exports.run(...inputs[i])>>>0;}catch(e){if(!(e instanceof WebAssembly.RuntimeError))throw e;trap=e.message;}
 const selectedTrace=trace.filter(t=>t.group===selected.id);
 if(selectedTrace.length!==selected.calls)throw Error('Selected group not fully observed');
 rows.push({case:i,output,trap,memorySha256:crypto.createHash('sha256').update(memory).digest('hex'),recoveredStores:selectedTrace.filter(t=>t.enabled!==0).map(({address,value})=>({address,value})),trace});
}
fs.writeFileSync(path.join(out,'observations.json'),JSON.stringify(rows));
fs.writeFileSync(path.join(out,'extraction.json'),JSON.stringify({inputSha256:crypto.createHash('sha256').update(fs.readFileSync(binary)).digest('hex'),instrumentedSha256:crypto.createHash('sha256').update(fs.readFileSync(wasm)).digest('hex'),helperId,heuristic:'unique five-i32-parameter function; last three operands; local-aware load provenance; largest group, latest on ties',groups,selected,inputCases:rows.length,elapsedMs:performance.now()-start},null,2));

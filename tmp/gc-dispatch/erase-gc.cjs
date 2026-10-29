'use strict';
// Restricted representation erasure from binary disassembly, no generator metadata.
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const bin=path.resolve(process.argv[2]),input=path.resolve(process.argv[3]),out=path.join(input,'erasure');fs.mkdirSync(out,{recursive:true});
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function tool(name,args){const r=cp.spawnSync(path.join(bin,name+'.exe'),args,{encoding:'utf8',timeout:30000});if(r.status!==0)throw Error(r.stderr);return r.stdout;}
function parse(s){const tokens=s.match(/"(?:\\.|[^"\\])*"|[()]|[^\s()]+/g);let i=0;
  function node(){const t=tokens[i++];if(t!=='(')return t;const a=[];while(tokens[i]!==')'){assert(i<tokens.length);a.push(node());}i++;return a;}
  const a=node();assert.equal(i,tokens.length);return a;
}
const print=a=>Array.isArray(a)?'('+a.map(print).join(' ')+')':a;
function erase(ast){
  assert.equal(ast[0],'module');const typeTags=new Map(),shapes=new Set(),globals=new Map();
  for(const n of ast.slice(1))if(n[0]==='type'&&n[2][0]==='struct'){
    assert(n[2].slice(1).every(f=>print(f)==='(field i32)'),'unsupported struct');
    const shape=print(n[2]);assert(!shapes.has(shape),'duplicate shape requires canonicalization');shapes.add(shape);typeTags.set(n[1],typeTags.size);
  }
  assert(typeTags.size>0,'no structs');
  for(const n of ast.slice(1))if(n[0]==='global'){
    assert.equal(n.length,4);assert.equal(n[2][0],'ref');assert(typeTags.has(n[2][1]));
    assert(['struct.new','struct.new_default'].includes(n[3][0]));assert.equal(n[3][1],n[2][1]);
    assert(n[3].slice(2).every(v=>print(v)==='(i32.const 0)'));globals.set(n[1],typeTags.get(n[2][1]));
  }
  const exported=new Set(ast.filter(n=>n[0]==='export').map(n=>{assert.equal(n[2][0],'func');return n[2][1];}));
  let replacedTests=0,replacedGets=0;
  function rw(n){if(!Array.isArray(n))return ['eqref','structref'].includes(n)?'i32':n;
    if(n[0]==='global.get'){assert(globals.has(n[1]));replacedGets++;return ['i32.const',String(globals.get(n[1]))];}
    if(n[0]==='ref.test'){
      let ty=n[1][1];if(Array.isArray(ty)){assert.equal(ty[0],'exact');ty=ty[1];}
      assert(typeTags.has(ty));replacedTests++;return ['i32.eq',rw(n[2]),['i32.const',String(typeTags.get(ty))]];
    }
    if(n[0]==='ref')return 'i32';
    assert(!/^(struct\.|array\.|ref\.|call_indirect|call_ref|global.set|memory\.)/.test(n[0]),'unsupported operation '+n[0]);
    return n.map(rw);
  }
  const result=['module'];
  for(const n of ast.slice(1)){
    if(['type','global'].includes(n[0]))continue;
    assert(['func','export'].includes(n[0]),'unsupported module declaration');
    if(n[0]==='func'){
      assert(n.filter(x=>Array.isArray(x)&&x[0]==='param').every(x=>!x.some(Array.isArray)),'reference parameter not supported');
      if(exported.has(n[1]))assert(n.filter(x=>Array.isArray(x)&&x[0]==='result').every(x=>!x.some(Array.isArray)),'reference export');
      const locals=n.filter(x=>Array.isArray(x)&&x[0]==='local'&&(Array.isArray(x[2])||['eqref','structref'].includes(x[2]))).map(x=>x[1]);
      const changed=rw(n);let pos=2;while(pos<changed.length&&Array.isArray(changed[pos])&&['param','result','local'].includes(changed[pos][0]))pos++;
      changed.splice(pos,0,...locals.map(id=>['local.set',id,['i32.const','-1']]));result.push(changed);
    }else result.push(rw(n));
  }
  return {ast:result,replacedTests,replacedGets,typeTags:[...typeTags],globals:[...globals]};
}
const results=[];
// File-name selection only, no manifest is read by this analysis.
for(const file of fs.readdirSync(input).filter(n=>/-gc-(static|rotating)-(raw|O2)\.wasm$/.test(n)).sort()){
  const start=process.hrtime.bigint(),src=path.join(input,file),dis=tool('wasm-dis',[src]);
  const r=erase(parse(dis)),name=file.slice(0,-5)+'-erased',wat=path.join(out,name+'.wat'),wasm=path.join(out,name+'.wasm');
  fs.writeFileSync(wat,print(r.ast)+'\n');tool('wasm-as',[wat,'-o',wasm]);
  const bytes=fs.readFileSync(wasm);assert(WebAssembly.validate(bytes));
  results.push({input:file,input_sha256:sha(fs.readFileSync(src)),output:path.basename(wasm),output_sha256:sha(bytes),bytes:bytes.length,
    ref_tests_replaced:r.replacedTests,global_gets_replaced:r.replacedGets,typeTags:r.typeTags,globals:r.globals,analysis_and_assembly_ns:Number(process.hrtime.bigint()-start)});
}
fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({script_sha256:sha(fs.readFileSync(__filename)),node:process.version,
  scope:'Representation erasure for immutable distinct struct tokens and ref.test; no metadata/oracle used; not source or CFG recovery.',results},null,2)+'\n');
console.log(JSON.stringify({converted:results.length,results},null,2));

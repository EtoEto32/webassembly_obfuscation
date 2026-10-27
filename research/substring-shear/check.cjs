const fs=require('node:fs'),path=require('node:path');
const root=process.argv[2], cases=JSON.parse(fs.readFileSync(path.join(root,'cases.json'))),manifest=JSON.parse(fs.readFileSync(path.join(root,'manifest.json')));
let seed=0x75d38e29;const rand=()=>seed=(Math.imul(seed,1664525)+1013904223)>>>0;
function pack(s){let x=0,y=0;s.forEach((c,i)=>{if(i<16)x|=c<<(i*2);else y|=c<<((i-16)*2)});return [x|0,y|0,s.length];}
function reference(s,g){
  const n=s.length,d=g.n;if(n===0)return 0;
  const chart=Array.from({length:n+1},()=>Array.from({length:n+1},()=>new Uint32Array(d)));
  for(let i=0;i<n;i++)for(const [a,t,c] of g.terminals)if(t===s[i])chart[i][i+1][a]=(chart[i][i+1][a]+c)>>>0;
  for(let len=2;len<=n;len++)for(let i=0;i+len<=n;i++)for(let k=i+1;k<i+len;k++)for(const [a,b,c,w] of g.rules)
    chart[i][i+len][a]=(chart[i][i+len][a]+Math.imul(w,Math.imul(chart[i][k][b],chart[k][i+len][c])))>>>0;
  return chart[0][n][0];
}
let calls=0,traps=0,rows=[],positive=0,highBit=0;
for(const c of cases){
  let inputs=[[]];const depth=c.grammar.alphabet===2?7:5;
  for(let n=1;n<=depth;n++)for(let v=0;v<c.grammar.alphabet**n;v++){
    let z=v,s=[];for(let i=0;i<n;i++){s.push(z%c.grammar.alphabet);z=Math.floor(z/c.grammar.alphabet);}inputs.push(s);
  }
  for(const n of [1,2,7,8,15,16,17,31,32])for(let t=0;t<10;t++)inputs.push(Array.from({length:n},()=>rand()%c.grammar.alphabet));
  // Positive samples reach long productions, ambiguity, and overflow.
  if(c.name.startsWith('dyck'))for(let n=1;n<=16;n++){inputs.push(Array.from({length:n*2},(_,i)=>i%2));inputs.push([...Array(n).fill(0),...Array(n).fill(1)]);}
  if(c.name.startsWith('palindrome'))for(let n=1;n<=16;n++){const a=Array.from({length:n},()=>rand()%2);inputs.push([...a,...a.slice().reverse()]);}
  if(c.name.startsWith('expression'))for(let n=0;n<16;n++)inputs.push(Array.from({length:2*n+1},(_,i)=>i%2?1+rand()%2:0));
  const expected=inputs.map(x=>reference(x,c.grammar));positive+=expected.filter(x=>x!==0).length;highBit+=expected.filter(x=>x>=0x80000000).length;
  for(const t of manifest.filter(t=>t.name===c.name)){
    const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(root,t.file)))).exports;
    let localCalls=0,localTraps=0;
    for(let i=0;i<inputs.length;i++){
      const args=pack(inputs[i]);const got=e.run(...args)>>>0;calls++;localCalls++;
      if(got!==expected[i])throw Error(JSON.stringify({file:t.file,input:inputs[i],got,want:expected[i]}));
    }
    const invalid=[[0,0,33],[0,0,-1],[0,0,0x80000000],[3,0,1],[0,3,17]];
    for(const args of invalid){
      let before=e.memory?Buffer.from(e.memory.buffer):null;
      let trapped=false;try{e.run(...args);}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;trapped=true;}
      calls++;localCalls++;if(!trapped)throw Error('missing trap '+t.file+' '+args);traps++;localTraps++;
      if(before&&!before.equals(Buffer.from(e.memory.buffer)))throw Error('trap changed private memory');
      if((e.run(...pack(inputs[1]))>>>0)!==expected[1])throw Error('posttrap call');calls++;localCalls++;
    }
    // Unused packed bits are deliberately ignored, including the empty input.
    if(e.run(-1,-1,0)!==0)throw Error('empty input');calls++;localCalls++;
    rows.push({file:t.file,calls:localCalls,traps:localTraps});
  }
}
console.log(JSON.stringify({binaries:manifest.length,calls,traps,mismatches:0,positive_reference_inputs:positive,high_bit_reference_inputs:highBit,seed:'0x75d38e29',rows}));

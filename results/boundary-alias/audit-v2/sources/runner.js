// Bounded local .wasm only. No target rewriting, property enumeration, or heap walk.
var node=typeof process!=='undefined'&&process.versions&&process.versions.node;
var fs=node?require('fs'):null;
var args=node?process.argv.slice(2):scriptArgs;
var dir=args[0];
function textFile(p){return node?fs.readFileSync(p,'utf8'):read(p);}
function binaryFile(p){return node?fs.readFileSync(p):read(p,'binary');}
var upstreamSource=textFile(dir+'/upstream-printed.js');
var upstreamPrinted=new Function(upstreamSource+'\nreturn printed;')();
var cases=JSON.parse(textFile(dir+'/cases.json'));var rows=[];var errors=[];
function execute(c){
  var ids=new WeakMap(),next=0,observed=[],trace=[],tokens=[],rendered=[];
  function record(event,x){
    var token;
    if(x===null)token='null';
    else {
      if(typeof x!=='object')throw new Error('out of GC-object scope');
      if(!ids.has(x))ids.set(x,next++);
      token=ids.get(x);
    }
    trace.push(event);tokens.push(token);rendered.push(upstreamPrinted(x));observed.push(x);
  }
  var inst=new WebAssembly.Instance(new WebAssembly.Module(binaryFile(dir+'/'+c.file)),{env:{log:x=>record('import',x)}});
  // Anchor pre-existing input identity, before any tested call.
  var input=inst.exports.seed();record('input',input);
  for(var i=0;i<8;i++){
    trace.push('call:'+i);
    try{record('return',inst.exports.step(i,input));}
    catch(e){if(!(e instanceof WebAssembly.RuntimeError))throw e;trace.push('trap');}
  }
  // Strong simple baseline: explicit comparisons with every previous value.
  var unique=[],direct=[];
  for(var value of observed){
    if(value===null){direct.push('null');continue;}
    var index=unique.findIndex(v=>v===value);
    if(index<0){index=unique.length;unique.push(value);}
    direct.push(index);
  }
  return {file:c.file,name:c.name,family:c.family,kind:c.kind,variant:c.variant,level:c.level,trace:trace,tokens:tokens,printed:rendered,calls:9,events:observed.length,distinct:next,direct_agrees:JSON.stringify(direct)===JSON.stringify(tokens)};
}
for(var c of cases)rows.push(execute(c));
function view(r,key){return JSON.stringify([r.trace,r[key]]);}
var comparisons=[];
for(var row of rows){
  var base=rows.find(r=>r.kind===row.kind&&r.family===row.family&&r.variant==='base'&&r.level==='O0');
  var different=row.variant==='fault';
  var aliasDifferent=view(base,'tokens')!==view(row,'tokens');
  var printedDifferent=view(base,'printed')!==view(row,'printed');
  var comp={file:row.file,expected_difference:different,alias_difference:aliasDifferent,printed_difference:printedDifferent};comparisons.push(comp);
  if(aliasDifferent!==different||!row.direct_agrees)errors.push(comp);
}
var summary={instances:rows.length,calls:rows.reduce((n,r)=>n+r.calls,0),events:rows.reduce((n,r)=>n+r.events,0),fault_comparisons:comparisons.filter(c=>c.expected_difference).length,alias_detected:comparisons.filter(c=>c.expected_difference&&c.alias_difference).length,printed_detected:comparisons.filter(c=>c.expected_difference&&c.printed_difference).length,normal_comparisons:comparisons.filter(c=>!c.expected_difference).length,false_positives:comparisons.filter(c=>!c.expected_difference&&c.alias_difference).length,direct_disagreements:rows.filter(r=>!r.direct_agrees).length,errors:errors.length};
var output=JSON.stringify({engine:node?process.versions:'SpiderMonkey 150.0.1 (configured executable)',summary:summary,errors:errors,comparisons:comparisons,rows:rows});
if(node){console.log(output);if(errors.length)process.exitCode=1;}else{print(output);if(errors.length)quit(1);}

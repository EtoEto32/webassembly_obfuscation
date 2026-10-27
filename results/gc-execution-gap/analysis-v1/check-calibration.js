// Run only local bounded calibration modules, in Node or SpiderMonkey.
var isNode=typeof process!=='undefined'&&process.versions&&process.versions.node;
var fs=isNode?require('fs'):null;
var args=isNode?process.argv.slice(2):scriptArgs;
var directory=args[0];
function txt(p){return isNode?fs.readFileSync(p,'utf8'):read(p);}
function bytes(p){return isNode?fs.readFileSync(p):read(p,'binary');}
var calibration=JSON.parse(txt(directory+'/calibration/rows.json'));
var results=[],errors=[];
for(var row of calibration){
  for(var mode of ['plain','counted']){
    var instance=new WebAssembly.Instance(new WebAssembly.Module(bytes(directory+'/calibration/'+row.name+(mode==='counted'?'-counted':'')+'.wasm')));
    var value=null;
    if(row.variant==='depth1')value=new WebAssembly.Instance(new WebAssembly.Module(bytes(directory+'/nullable-array-depth1-provider.wasm'))).exports.run();
    var result={name:row.name,variant:row.variant,mode:mode};
    try{result.value=instance.exports.observe(value);result.status='returned';}catch(e){result.status=e instanceof WebAssembly.RuntimeError?'trap':'error';result.error=String(e);}
    if(mode==='counted'){
      result.counters=Array.from({length:row.metadata.counter_count},(_,i)=>instance.exports['__gap_'+i].value);
      var expected=row.counted.function_entries.concat(row.counted.site_counts.flatMap(c=>[c.attempted,c.completed]));
      if(JSON.stringify(expected)!==JSON.stringify(result.counters))errors.push({kind:'counters',...result,expected:expected});
    }
    if(result.status!==row[mode].status||result.value!==row[mode].result)errors.push({kind:'outcome',...result,expected:row[mode]});
    results.push(result);
  }
}
var output=JSON.stringify({engine:isNode?process.versions:'SpiderMonkey',calls:results.length,errors:errors,rows:results});
if(isNode){console.log(output);if(errors.length)process.exitCode=1;}else{print(output);if(errors.length)quit(1);}

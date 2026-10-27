var node=typeof process!=='undefined'&&process.versions&&process.versions.node;
var fs=node?require('fs'):null, args=node?process.argv.slice(2):scriptArgs;
function bytes(p){return node?fs.readFileSync(p):read(p,'binary');}
var classify=new WebAssembly.Instance(new WebAssembly.Module(bytes(args[0]+'/classifier.wasm'))).exports.isGC;
var examples=[['null',null,0],['plain',{},0],['Object.prototype',Object.prototype,0],['Array',[],0],['null-prototype',Object.create(null),0],['frozen-null-prototype',Object.freeze(Object.create(null)),0],['number',1,0],['string','s',0],['function',function(){},0]];
for(var kind of ['struct','array']){
 var inst=new WebAssembly.Instance(new WebAssembly.Module(bytes(args[1]+'/'+kind+'-fresh-base-O0.wasm')),{env:{log:()=>{}}});
 examples.push([kind,inst.exports.seed(),1]);
}
var rows=examples.map(x=>({name:x[0],expected:x[2],actual:classify(x[1])}));
var output=JSON.stringify({rows:rows,errors:rows.filter(x=>x.expected!==x.actual)});
if(node)console.log(output);else print(output);
if(rows.some(x=>x.expected!==x.actual)){if(node)process.exitCode=1;else quit(1);}

var isNode=typeof require==='function';
var argv=isNode?process.argv.slice(2):scriptArgs;
var readBytes=isNode?p=>require('fs').readFileSync(p):p=>read(p,'binary');
var readText=isNode?p=>require('fs').readFileSync(p,'utf8'):p=>read(p);
var out=isNode?s=>console.log(s):s=>print(s);
var snapshot=isNode?require(argv[3]).heapSnapshot:(load(argv[3]),heapSnapshot);
try {
  var target=new WebAssembly.Instance(new WebAssembly.Module(readBytes(argv[0]))).exports;
  var helper=new WebAssembly.Instance(new WebAssembly.Module(readBytes(argv[1]))).exports;
  var meta=JSON.parse(readText(argv[2]));
  var refs=[target.get(),target.get()];
  var ids=new Map(),trace=refs.map(x=>{if(x===null)return null;if(!ids.has(x))ids.set(x,ids.size);return ids.get(x);});
  out(JSON.stringify({status:'observed',boundary:trace,snapshot:snapshot(refs,helper,meta,argv[4]?JSON.parse(argv[4]):undefined),module_bytes:readBytes(argv[0]).length}));
}catch(e){out(JSON.stringify({status:'error',class:e.constructor.name,error:String(e)}));}

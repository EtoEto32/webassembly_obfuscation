// Inserted immediately before upstream build(). Target Wasm bytes stay unchanged.
var __callerMode = '__CALLER__', __observerMode = '__OBSERVER__';
var __readText = typeof require === 'function' ? p => require('fs').readFileSync(p, 'utf8') : p => read(p);
var __api = JSON.parse(__readText(argv[0] + '.api.json'));
var __sigByFunction = new WeakMap(), __calls = [], __multiSlots = 0;
var __ids = new WeakMap(), __next = 0, __trace = [];
var __classify = new WebAssembly.Instance(new WebAssembly.Module(readBinary(argv[0].replace(/[^\\/]+$/, 'classifier.wasm')))).exports.isGC;
function __registerExport(key, value) {
  if (typeof value === 'function' && __api.functions[key] && !__sigByFunction.has(value)) {
    __sigByFunction.set(value, Object.assign({name:key}, __api.functions[key]));
  }
}
function __observe(x, channel, name, slot) {
  if (x !== null && typeof x === 'object' && __classify(x)) {
    if (!__ids.has(x)) __ids.set(x, __next++);
    __trace.push({id:__ids.get(x),channel:channel,name:name,slot:slot});
  }
}
var __oldPrinted = printed;
printed = function(x,y) { __observe(x,'printed',null,null);return __oldPrinted(x,y); };
callFunc = function(func) {
  var sig=__sigByFunction.get(func),args=[],call={name:sig?sig.name:null,known:!!sig,status:'pending',unsupported:[]};
  if(sig){
    for(var type of sig.params){
      if(type==='v128')call.unsupported.push('v128');
      if(type&&type.ref&&!type.nullable)call.unsupported.push('nonnull-ref');
    }
  }
  if(__callerMode==='typed'&&sig){
    args=sig.params.map(type=>type==='i64'?0n:typeof type==='string'&&type!=='v128'?0:null);
  }else args=Array.from({length:func.length},()=>null);
  __calls.push(call);
  try {
    var result=func.apply(null,args);call.status='returned';
    if(__observerMode==='multi'&&sig&&sig.results.length>1){
      if(!Array.isArray(result)||result.length!==sig.results.length)throw new Error('multi-value shape mismatch');
      for(var i=0;i<result.length;i++){__multiSlots++;__observe(result[i],'multi',sig.name,i);}
    }
    return result;
  }catch(e){call.status=e instanceof WebAssembly.RuntimeError?'trap':e instanceof TypeError?'type-error':e instanceof RangeError?'range-error':'other-error';call.error=String(e);throw e;}
};

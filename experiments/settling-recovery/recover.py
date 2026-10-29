"""Fail-closed recognizer of a bounded settling scheduler, not a general decompiler."""
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
PARSER = REPO / "experiments/sha256-cobra-check/check.py"
spec = importlib.util.spec_from_file_location("existing_parser", PARSER)
parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parser)
TOOLS = REPO / ".tools/wabt-1.0.42/bin"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def g(i):
    return ["local.get", str(i)]


def c(i):
    return ["i32.const", str(i)]


def op(name, *args):
    return [name, *args]


def set_(i, e):
    return ["local.set", str(i), e]


def serialize(n):
    return "(" + " ".join(serialize(x) if isinstance(x,list) else x for x in n) + ")"


def recognize(tree):
    require(tree[0] == "module" and len(tree)==4, "module envelope")
    typ, f, export = tree[1:]
    require(typ == ["type", ["func", ["param","i32","i32","i32"],["result","i32"]]], "type")
    require(export == ["export", '"run"', ["func","0"]], "export")
    require(f[:4] == ["func",["type","0"],["param","i32","i32","i32"],["result","i32"]], "signature")
    require(f[4][0]=="local" and all(x=="i32" for x in f[4][1:]), "locals")
    limit = 3 + len(f[4])-1
    body = f[5:]
    require(body[-2][0]=="loop" and body[-1][0]=="local.get", "result and outer loop")
    output = body[-1][1]
    outer = body[-2]
    require(len(outer)==6 and outer[1][0]=="local.set" and outer[2][0]=="local.set", "outer shape")
    index, visits = outer[1][1], outer[2][1]
    require(outer[2] == set_(visits,c(0)), "visit initialization")
    inner = outer[3]
    require(inner[0]=="loop" and len(inner)>=5, "inner shape")
    branches = inner[1:-3]
    n = len(branches)
    require(outer[1][2][0]=="i32.rem_u" and outer[1][2][2]==c(n), "cyclic start")
    require(outer[1][2][1][0]=="i32.xor", "start expression")
    start_args = outer[1][2][1][1:]
    require(len(start_args)==2 and all(x[0]=="local.get" and len(x)==2 for x in start_args), "start leaves")
    require(inner[-3] == set_(index,op("i32.rem_u",op("i32.add",g(index),c(1)),c(n))), "index increment")
    require(inner[-2] == set_(visits,op("i32.add",g(visits),c(1))), "visit increment")
    require(inner[-1] == ["br_if","0",op("i32.lt_u",g(visits),c(n))], "visit bound")
    require(outer[4][0]=="local.set", "sweep counter")
    rounds = outer[4][1]
    require(outer[4] == set_(rounds,op("i32.add",g(rounds),c(1))), "sweep increment")
    require(outer[5][:2] == ["br_if","0"] and outer[5][2][:2]==["i32.lt_u",g(rounds)], "sweep condition")
    sweep_literal = outer[5][2][2]
    require(sweep_literal[0]=="i32.const", "sweep literal")
    sweeps = int(sweep_literal[1])
    require(0 < sweeps < (1<<31), "finite sweeps")
    scheduler = {index, visits, rounds}
    require(len(scheduler)==3 and all(3<=int(x)<limit for x in scheduler), "distinct scheduler locals")
    nodes, carries, before = {}, set(), []
    allowed = {"i32.mul":2,"i32.xor":2,"i32.rotl":2,"i32.lt_u":2,"select":3}
    def leaf(x):
        return isinstance(x,list) and len(x)==2 and x[0]=="local.get" and 0<=int(x[1])<limit
    for k, branch in enumerate(branches):
        require(branch[:2]==["if",op("i32.eq",g(index),c(k))] and len(branch)==3, "dispatch coverage")
        then = branch[2]
        require(then[0]=="then" and len(then) in (2,3), "handler")
        first = then[1]
        require(first[0]=="local.set" and len(first)==3, "state assignment")
        dest, expr = first[1:]
        require(dest not in nodes and dest not in scheduler and 3<=int(dest)<limit, "state alias")
        if len(then)==3:
            second = then[2]
            require(second[0]=="local.set" and len(second)==3, "carry assignment")
            carry = second[1]
            require(expr[0]=="i32.xor" and len(expr)==3 and expr[1][0]=="i32.xor" and len(expr[1])==3, "sum recurrence")
            a,b = expr[1][1:]
            require(leaf(a) and leaf(b) and expr[2]==g(carry), "sum leaves")
            require(second == set_(carry,op("i32.shl",op("i32.or",op("i32.and",a,b),op("i32.and",op("i32.xor",a,b),g(carry))),c(1))), "carry recurrence")
            require(carry not in carries and carry not in scheduler and 3<=int(carry)<limit, "carry alias")
            carries.add(carry)
            recovered = op("i32.add",a,b)
            cost = 33
        else:
            require(expr[0] in allowed and len(expr)==allowed[expr[0]]+1, "ordinary handler")
            if expr[0]=="i32.rotl":
                require(leaf(expr[1]) and expr[2][0]=="i32.const" and len(expr[2])==2, "rotate operands")
            else:
                require(all(leaf(x) for x in expr[1:]), "ordinary operands")
            recovered, cost = expr, 1
        nodes[dest] = {"expression":recovered,"cost":cost}
        before.append(then)
    require(not (set(nodes)&carries), "state/carry overlap")
    initialized = set()
    for stmt in body[:-2]:
        require(stmt[0]=="local.set" and len(stmt)==3, "initialization")
        target, expr = stmt[1:]
        require(target not in initialized and target not in scheduler and 3<=int(target)<limit, "initialization alias")
        require(expr[0]=="i32.xor" and len(expr)==3 and expr[1]==g(2) and expr[2][0]=="i32.const", "pure initialization")
        initialized.add(target)
    require(set(nodes)|carries <= initialized, "missing initialization")
    require(all(x[1] in set(nodes)|{"0","1","2"} for x in start_args), "start input")
    require(output in nodes, "output state")
    order, times, active = [], {}, set()
    def visit(dest):
        if dest in times:
            return times[dest]
        require(dest not in active, "cyclic recovered graph")
        active.add(dest)
        deps = [x[1] for x in nodes[dest]["expression"][1:] if x[0]=="local.get"]
        require(all(d in nodes or d in {"0","1","2"} for d in deps), "unrecognized parent")
        t = nodes[dest]["cost"] + max([visit(d) if d in nodes else 0 for d in deps],default=0)
        active.remove(dest)
        order.append(dest)
        times[dest] = t
        return t
    for dest in nodes:
        visit(dest)
    require(sweeps>=max(times.values()), "insufficient settling bound")
    # Retain local numbering, but discard initialized transient/carry/scheduler state.
    result = ["module",["func",["export",'"run"'],["param","i32","i32","i32"],
               ["result","i32"],f[4],*[set_(d,nodes[d]["expression"]) for d in order],g(output)]]
    return result, {"nodes":nodes,"order":order,"times":times,"sweeps":sweeps,
                    "output":output,"carry_count":len(carries),"handlers":before}


def main():
    source, out = map(Path,sys.argv[1:])
    out.mkdir(parents=True, exist_ok=False)
    def run(cmd):
        return subprocess.run(list(map(str,cmd)),check=True,capture_output=True,text=True,timeout=60).stdout
    disassembly = run([TOOLS/"wasm2wat.exe",source,"--fold-exprs"])
    (out/"input.wat").write_text(disassembly,encoding="utf-8")
    result, certificate = recognize(parser.parse_wat(disassembly))
    (out/"recovered.wat").write_text(serialize(result)+"\n",encoding="utf-8")
    run([TOOLS/"wat2wasm.exe",out/"recovered.wat","-o",out/"recovered.wasm"])
    run([TOOLS/"wasm-validate.exe",out/"recovered.wasm"])
    certificate["input_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    certificate["output_sha256"] = hashlib.sha256((out/"recovered.wasm").read_bytes()).hexdigest()
    certificate["input_bytes"] = source.stat().st_size
    certificate["output_bytes"] = (out/"recovered.wasm").stat().st_size
    certificate["parser_sha256"] = hashlib.sha256(PARSER.read_bytes()).hexdigest()
    certificate["recover_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (out/"certificate.json").write_text(json.dumps(certificate,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in certificate.items() if k not in ("nodes","handlers")},indent=2))


if __name__=="__main__":
    main()

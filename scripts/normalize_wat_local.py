"""Conservative local rewrites of linear WABT WAT; no reference or provenance input.

Only whole, separate instruction lines inside functions are rewritten. Folded WAT,
floating point, division, shifts, control flow, calls and memory are not rewritten.
This is ordinary peephole simplification, not a novel deobfuscation algorithm.
"""
import argparse
import json
import re
from pathlib import Path

CONST = re.compile(r'( *)(i32|i64)\.const (-?\d+)\s*$')
OP = re.compile(r'( *)(i32|i64)\.(add|sub|mul|and|or|xor)\s*$')

def signed(value, bits):
    value %= 1 << bits
    return value - (1 << bits) if value >= 1 << (bits-1) else value

def normalize(text, rules=('nop', 'integer-fold')):
    output=[]; events=[]; function=None
    for line_number,line in enumerate(text.splitlines(keepends=True),1):
        header=re.match(r'^  \(func (\$\S+|\(;\d+;\))',line)
        if header:function=header[1]
        elif line.startswith('  ('):function=None
        if function and 'nop' in rules and re.fullmatch(r' +nop\s*',line):
            events.append(dict(rule='nop',function=function,input_line=line_number,before=[line.rstrip()],after=[]))
            continue
        output.append((line,line_number,function))
        if not function or 'integer-fold' not in rules:continue
        while len(output)>=3:
            a,b,op=output[-3:]
            ma,mb,mo=CONST.fullmatch(a[0].rstrip('\r\n')),CONST.fullmatch(b[0].rstrip('\r\n')),OP.fullmatch(op[0].rstrip('\r\n'))
            if not (ma and mb and mo and a[2]==b[2]==op[2]==function and ma[1]==mb[1]==mo[1] and ma[2]==mb[2]==mo[2]):break
            x,y=int(ma[3]),int(mb[3]);bits=int(ma[2][1:])
            if not (-(1<<(bits-1))<=x<(1<<bits) and -(1<<(bits-1))<=y<(1<<bits)):break
            kind=mo[3]
            value={'add':lambda:x+y,'sub':lambda:x-y,'mul':lambda:x*y,'and':lambda:x&y,'or':lambda:x|y,'xor':lambda:x^y}[kind]()
            replacement=f'{ma[1]}{ma[2]}.const {signed(value,bits)}\n'
            events.append(dict(rule='integer-fold',operation=kind,function=function,input_lines=[a[1],b[1],op[1]],before=[r[0].rstrip() for r in [a,b,op]],after=[replacement.rstrip()]))
            output[-3:]=[(replacement,op[1],function)]
    return ''.join(row[0] for row in output),events

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--rules',choices=['nop','integer-fold','both'],default='both')
    parser.add_argument('--events',type=Path)
    args=parser.parse_args()
    rules=('nop','integer-fold') if args.rules=='both' else (args.rules,)
    result,events=normalize(args.input.read_text(encoding='utf-8'),rules)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(result,encoding='utf-8')
    if args.events:args.events.write_text(json.dumps(events,indent=2),encoding='utf-8')
    print(json.dumps(dict(events=len(events),rules=rules)))

if __name__=='__main__':main()

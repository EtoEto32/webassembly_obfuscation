import importlib.util
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent

def load(name,path):
    sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m

h=load('boolean_feedback_hfl',HERE.parent/'hidden-filtration/prototype.py')
saved=sys.modules.get('prototype');sys.modules['prototype']=h
a=load('boolean_feedback_hfl_attack',HERE.parent/'hidden-filtration/attack.py')
if saved is None:del sys.modules['prototype']
else:sys.modules['prototype']=saved


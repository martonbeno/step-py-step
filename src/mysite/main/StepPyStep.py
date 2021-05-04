import pdb
import copy
import multiprocessing
import re
import sys
import traceback
import ast
import os
from io import StringIO

try:
    from .expression_analysis import get_exprs, is_importing_node
except ImportError:
    from expression_analysis import get_exprs, is_importing_node


class ContainsImportError(Exception):
    pass

class StepPyStep(pdb.Pdb):
    def __init__(self, **kwargs):
        print("létrejövök")

        self.request_q = multiprocessing.Queue()
        self.answer_q = multiprocessing.Queue()
        self.sps_output = StringIO()
        kwargs['stdout'] = self.sps_output

        self.path = os.path.realpath(__file__) #...../mysite/main/StepPyStep.py
        self.path = os.path.dirname(self.path) #...../mysite/main/
        self.path = os.path.dirname(self.path) #...../mysite/

        super().__init__(**kwargs)
    

    def start(self, source_code=None, example_code_id=None):
        if source_code is None and example_code_id is None:
            debug_file = os.path.join(self.path, 'tmp.py')
            with open(debug_file, 'r', encoding='utf-8') as f:
                source_code = f.read()
        
        elif example_code_id is not None:
            examples_path = os.path.join(self.path, 'examples')
            example_file = os.path.join(examples_path, f'example{example_code_id}.py')
            with open(example_file, 'r') as f:
                source_code = f.read()
        
        
        ret = { "compile_success": None,
                "error_message": None,
                "source_code": None }

        try:
            root = ast.parse(source_code)
            if is_importing_node(root, source_code):
                raise ContainsImportError()
            ret['compile_success'] = True
        except ContainsImportError:
            ret['compile_success'] = False
            ret['error_message'] = "Error! Code cannot contain imports!"
            return ret
        except Exception:
            error_message = traceback.format_exc()
            error_message = error_message.split('"<unknown>", ')[-1]
            ret['compile_success'] = False
            ret['error_message'] = error_message
            return ret
        
        self.expression_at_line = dict()
        expressions = get_exprs(source_code)
        for e in expressions:
            self.expression_at_line[e.lineno] = e
        
        self.source_code = source_code
        ret['source_code'] = source_code

        self.p = multiprocessing.Process(target=self.rs, args=())
        self.p.start()
        self.request("init")
        return ret

    def rs(self):
        self._runscript("USERFILE.py")
        
    def _runscript(self, filename):
        import __main__
        __main__.__dict__.clear()
        __main__.__dict__.update({"__name__"    : "__main__",
                                  "__file__"    : filename,
                                  "__builtins__": __builtins__,
                                 })

        self._wait_for_mainpyfile = True
        self.mainpyfile = self.canonic(filename)
        self._user_requested_quit = False

        statement = "exec(compile(%r, %r, 'exec'))" % \
                        (self.source_code, self.mainpyfile)
        self.run(statement)

    def kill(self):
        print("KILLL")
        self.request_q.put("exit") #ez valszeg nem kell
        self.p.join()
    
    def request(self, msg):
        self.request_q.put(msg)
        ret = self.answer_q.get()
        if ret == "exit":
            self.kill()
        return ret
        
    def cmdloop(self, intro=None):
        import inspect, copy, re, sys
        sys.path.insert(0, os.path.join(self.path, 'main'))
        from get_frame_data import get_pointers
        from expression_analysis import node2seq, node2treant, node2tree
        from error_handling import is_error_message
        def debug(*args):
            sys.stdout.write(' '.join(str(x) for x in args) + '\n')
        
        while True:

            msg = self.request_q.get()
            
            if msg == "exit":
                print("EXIT üzi")
                self.onecmd("exit")
                self.answer_q.put("exit")
                return

            elif msg == "init":
                self.onecmd("ORIGINAL_PRINT=print")
                self.onecmd("!STEP_PY_STEP_OUTPUT=''")
                self.onecmd("!def STEP_PY_STEP_PRINT(*args, sep=' ', end='\\n', file=None, flush=False):global STEP_PY_STEP_OUTPUT;STEP_PY_STEP_OUTPUT+=sep.join([str(x) for x in args])+end;ORIGINAL_PRINT(*args, sep, end, file, flush)")
                self.onecmd("!print=STEP_PY_STEP_PRINT")
                self.answer_q.put("init")

            
            elif msg == "step":
                self.onecmd("step")
                self.request_q.put("get")
                break

            elif msg == "next":
                self.onecmd("next")
                self.request_q.put("get")
                break

            elif msg.startswith("modify"):
                var_name, value = re.findall(r'modify (\w+) (.+)', msg)[0]
                line = f"{var_name}={value}"
                try:
                    exec(line)
                except NameError:
                    value = value.replace('"', '\\"')
                    value = '"' + value + '"'
                    line = f"{var_name}={value}"
                line = "!" + line
                debug("ezt próbálom", line)
                self.onecmd(line)
                self.request_q.put("get")

            elif msg == "get":
                ret = dict()
                ret['error'] = None

                debug("kimenet", self.sps_output.getvalue().split('\n'), "eddigtart")
                for x in self.sps_output.getvalue().split('\n'):
                    if is_error_message(x):
                        ret['error'] = x
                        break

                ret['localvars'] = get_pointers(self.curframe)
                for v in ret['localvars']:
                    if v['name'] == 'STEP_PY_STEP_OUTPUT':
                        step_py_step_output = v
                        break

                ret['output'] = step_py_step_output['value']
                ret['localvars'].remove(v)


                filename_with_path, lineno, function, code_context, index = inspect.getframeinfo(self.curframe)
                ret['lineno'] = lineno
                
                if lineno in self.expression_at_line:
                    #actual local vars
                    ret['expr'] = dict()
                    localvars = {rec['name']: rec['value'] for rec in ret['localvars'] if rec['is_local']}
                    node = self.expression_at_line[lineno]
                    ret['expr']['sequence'] = node2seq(node, self.source_code, localvars)
                    ret['expr']['treant'] = node2treant(node, self.source_code, localvars)
                else:
                    ret['expr'] = None
                
                if function in ["STEP_PY_STEP_OUTPUT", "STEP_PY_STEP_PRINT"] or filename_with_path == "<stdin>":
                    self.request_q.put("step")
                else:
                    self.answer_q.put(ret)
            
            
            else:
                print("elírtad")
                filename_with_path, lineno, function, code_context, index = inspect.getframeinfo(self.curframe)
                self.answer_q.put(lineno)

        
if __name__ == "__main__":
    import time
    filename = "ja2.py"
    filename = "ja.py"

    #p = StepPyStep(filename=filename)
    p = StepPyStep()
    init_msg = p.start()
    if not init_msg['compile_success']:
        print("fordítási idejű hiba")
        print(init_msg['error_message'])
        exit()

    print(init_msg)

    while True:
        print("várom a parancsokat")
        r = input()
        if r == "quit":
            p.kill()
            break
        #time.sleep(1)
        try:
            ret = p.request(r)
        except Exception:
            print("inkább idelennnnnnnnnnnnnnnnnnnnnnn")
        print("------RET", ret)
        if ret == "exit":
            break
















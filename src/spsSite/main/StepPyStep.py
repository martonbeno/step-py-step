import pdb
import copy
import multiprocessing
import re
import sys
import traceback
import ast
import os
import datetime
from io import StringIO
import inspect

try:
    from .expression_analysis import get_exprs, is_forbidden_node
except ImportError:
    from expression_analysis import get_exprs, is_forbidden_node


class ContainsForbiddenNodeError(Exception):
    pass

def generate_filename():
    now = str(datetime.datetime.now())
    return "USERSCRIPT_" + re.sub(r'\D', '_', now) + ".py"

class StepPyStep(pdb.Pdb):
    def __init__(self, **kwargs):

        self.request_q = multiprocessing.Queue()
        self.answer_q = multiprocessing.Queue()
        self.sps_output = StringIO()
        kwargs['stdout'] = self.sps_output

        self.path = os.path.realpath(__file__) #...../spsSite/main/StepPyStep.py
        self.path = os.path.dirname(self.path) #...../spsSite/main/
        self.path = os.path.dirname(self.path) #...../spsSite/
        self.filename = None

        super().__init__(**kwargs)
    

    def start(self, source_code=None, example_file_name=None):
        if source_code is None and example_file_name is None:
            debug_file = os.path.join(self.path, 'tmp.py')
            with open(debug_file, 'r', encoding='utf-8') as f:
                source_code = f.read()
        
        elif example_file_name is not None:
            examples_path = os.path.join(self.path, 'examples')
            self.filename = os.path.join(examples_path, example_file_name)
            with open(self.filename, 'r') as f:
                source_code = f.read()
        
        
        ret = { "compile_success": None,
                "error_message": None,
                "source_code": None }

        try:
            root = ast.parse(source_code)
            forbidden_node = is_forbidden_node(root, source_code)
            if forbidden_node:
                raise ContainsForbiddenNodeError()
            ret['compile_success'] = True
        except ContainsForbiddenNodeError:
            ret['compile_success'] = False
            ret['error_message'] = f"Error! Code contains forbidden keyword: {forbidden_node}"
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
            try:
                self.expression_at_line[e.lineno] = e
            except Exception:
                pass

        
        self.source_code = source_code
        ret['source_code'] = source_code

        user_codes_dir = os.path.join(self.path, 'usercodes')
        filename = generate_filename()
        self.filename_with_path = os.path.join(user_codes_dir, filename)
        
        with open(self.filename_with_path, 'w+', encoding='utf-8') as f:
            f.write(self.source_code)

        self.p = multiprocessing.Process(target=lambda:self._runscript(self.filename_with_path), args=())
        self.p.start()
        self.request("init")
        return ret
    
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
    
    def get_example_files(self):
        examples_path = os.path.join(self.path, 'examples')
        return sorted(os.listdir(examples_path))

    def request(self, msg):
        self.request_q.put(msg)
        ret = self.answer_q.get()
        if ret == "exit":
            try:
                os.remove(self.filename_with_path)
            except Exception:
                pass
            self.p.join()
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
                self.onecmd("exit")
                self.answer_q.put("exit")
                return

            elif not self.is_still_in_user_code(self.curframe):
                ret = self.lastget
                ret['isover'] = True
                self.answer_q.put(ret)

            elif msg == "init":
                self.lastget = None
                self.onecmd("ORIGINAL_PRINT=print")
                self.onecmd("!STEP_PY_STEP_OUTPUT=''")
                self.onecmd("!def STEP_PY_STEP_PRINT(*args, sep=' ', end='\\n', file=None, flush=False):global STEP_PY_STEP_OUTPUT;STEP_PY_STEP_OUTPUT+=sep.join([str(x) for x in args])+end")
                self.onecmd("!print=STEP_PY_STEP_PRINT")
                self.answer_q.put("init")

            
            elif msg == "step":
                self.onecmd("step")
                self.request_q.put("get")
                break

            elif msg == "next":
                if self.is_still_in_user_code(self.curframe):
                    self.onecmd("next")
                self.request_q.put("get")
                break

            elif msg.startswith("modify"):
                try:
                    var_name, value = re.findall(r'modify (\w+) (.+)', msg)[0]
                except Exception:
                    debug("nem érvényes értékadás")
                    self.request_q.put("get")
                    break

                line = f"{var_name}={value}"
                try:
                    exec(line)
                except Exception:
                    value = value.replace('"', '\\"')
                    value = '"' + value + '"'
                    line = f"{var_name}={value}"

                try:
                    exec(line)
                except Exception:
                    debug("nem érvényes értékadás")
                    self.request_q.put("get")
                    break

                line = "!" + line
                self.onecmd(line)
                self.request_q.put("get")

            elif msg.startswith("newvar"):
                try:
                    var_name, vartype, value = re.findall(r'newvar (\w+) (\w+) (.+)', msg)[0]
                except Exception:
                    debug("nem érvényes értékadás")
                    self.request_q.put("get")
                    break

                if vartype == "autocast":
                    line = f"{var_name}={value}"
                else:
                    line = f"{var_name}={vartype}({value})"

                try:
                    exec(line)
                except Exception:
                    value = value.replace('"', '\\"')
                    value = '"' + value + '"'
                    line = f"{var_name}={value}"

                try:
                    exec(line)
                except Exception:
                    debug("nem érvényes értékadás")
                    self.request_q.put("get")
                    break

                line = "!" + line
                self.onecmd(line)
                self.request_q.put("get")

            elif msg.startswith("delvar"):
                try:
                    var_name = re.findall(r'delvar (\w+)', msg)[0]
                except Exception:
                    debug("nem érvényes változó törlés")
                    self.request_q.put("get")
                    break

                try:
                    exec(f"{var_name}=1\ndel {var_name}")
                except Exception:
                    debug("nem érvényes változó törlés 2")
                    self.request_q.put("get")
                    break

                self.onecmd(f"!del {var_name}")
                self.request_q.put("get")



            elif msg == "get":
                ret = dict()
                ret['isover'] = False
                ret['error'] = None

                for x in self.sps_output.getvalue().split('\n'):
                    if is_error_message(x):
                        ret['error'] = x
                        break

                ret['allvars'] = get_pointers(self.curframe)
                for v in ret['allvars']:
                    if v['name'] == 'STEP_PY_STEP_OUTPUT':
                        step_py_step_output = v
                        break

                ret['output'] = step_py_step_output['value']
                ret['allvars'].remove(v)


                filename_with_path, lineno, function, code_context, index = inspect.getframeinfo(self.curframe)
                ret['lineno'] = lineno
                
                if lineno in self.expression_at_line:
                    #actual local vars
                    ret['expr'] = dict()
                    node = self.expression_at_line[lineno]
                    ret['expr']['sequence'] = node2seq(node, self.source_code, self.curframe.f_locals)
                    ret['expr']['treant'] = node2treant(node, self.source_code, self.curframe.f_locals)
                else:
                    ret['expr'] = None
                

                if self.lastget == ret:
                    self.request_q.put("step")
                elif function in ["STEP_PY_STEP_OUTPUT", "STEP_PY_STEP_PRINT"] or filename_with_path == "<stdin>":
                    self.request_q.put("step")
                else:
                    self.lastget = ret
                    self.answer_q.put(ret)
            
            else:
                self.answer_q.put("Invalid command")


    def is_still_in_user_code(self, frame):
        f = frame
        while f:
            filename_with_path, lineno, function, code_context, index = inspect.getframeinfo(f)
            if filename_with_path == self.filename_with_path:
                return True
            f = f.f_back

        return False














import pdb
import copy
import multiprocessing
import re
import sys
import shutil
import traceback
import ast

try:
    from .expression_analysis import get_exprs
except ImportError:
    from expression_analysis import get_exprs


class UserCompileError(Exception):
    pass
class UserRuntimeError(Exception):
    pass

class StepPyStep(pdb.Pdb):
    def __init__(self, **kwargs):
        print("létrejövök")

        self.request_q = multiprocessing.Queue()
        self.answer_q = multiprocessing.Queue()
        
        path = "/home/beno/Desktop/steppystep/step-py-step/src/mysite/"
        self.filename = path + "tmp.py"

        #kwargs['stdout'] = open("kifele.txt", 'a')

        super().__init__(**kwargs)
        
        # self._runscript(self.filename)
    
    def start(self, source_code=None, example_code_id=None):
        if source_code is None and example_code_id is None:
            with open(self.filename, 'r', encoding='utf-8') as f:
                source_code = f.read()

        elif source_code is not None:
            self.create_file(source_code)

        elif example_code_id is not None:
            self.prepare_example(example_code_id)
            path = "/home/beno/Desktop/steppystep/step-py-step/src/mysite/"
            with open(f"{path}tmp.py", 'r') as f:
                source_code = f.read()
        
        
        ret = { "compile_success": None,
                "error_message": None,
                "source_code": None }

        try:
            ast.parse(source_code)
            ret['compile_success'] = True
        except Exception:
            error_message = traceback.format_exc()
            error_message = error_message.split('"<unknown>", ')[-1]
            #error_message = "HIBA" + error_message
            #error_message += "????????????????????"
            #print("okokoko", error_message)
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

    def prepare_example(self, example_code_id):
        path = "/home/beno/Desktop/steppystep/step-py-step/src/mysite/"
        shutil.copyfile(f"{path}example{example_code_id}.py", f"{path}tmp.py")

    def create_file(self, source_code):
        with open(self.filename, 'w+', encoding='utf-8') as f:
            f.write(source_code)

    def rs(self):
        self._runscript(self.filename)
        
    
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
        sys.path.insert(1, '/home/beno/Desktop/steppystep/step-py-step/src/mysite/main')
        from get_frame_data import get_pointers
        from expression_analysis import node2seq, node2treant, node2tree
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

            elif msg == "x":
                self.onecmd("!x=999;y=888")
                filename_with_path, lineno, function, copyde_context, index = inspect.getframeinfo(self.curframe)
                self.answer_q.put(f"xelek{lineno}")
                return
                line = "!_localvars=[(k, v) for k,v in locals().items() if not k.startswith('_') and isinstance(v,int)]"
                self.onecmd(line)
                print("localvars", _localvars)
                print("xxxxx", self.curframe.f_locals)

            elif msg == "get":

                ret = dict()
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
        ret = p.request(r)
        print("------RET", ret)
        if ret == "exit":
            break
















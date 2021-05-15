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

#generates a unique filename for the temporary file
def generate_filename():
    now = str(datetime.datetime.now())
    return "USERSCRIPT_" + re.sub(r'\D', '_', now) + ".py"

class StepPyStep(pdb.Pdb):
    def __init__(self, **kwargs):

        #queues for the communication between the main process and the sub process
        self.request_q = multiprocessing.Queue()
        self.answer_q = multiprocessing.Queue()

        #contains all outputs of the class, that otherwise would
        #be written to the standard output
        self.sps_output = StringIO()
        kwargs['stdout'] = self.sps_output

        self.path = os.path.realpath(__file__) #...../spsSite/main/StepPyStep.py
        self.path = os.path.dirname(self.path) #...../spsSite/main/
        self.path = os.path.dirname(self.path) #...../spsSite/
        self.filename = None

        super().__init__(**kwargs)
    

    def start(self, source_code=None, example_file_name=None):
        #if neither parameters are set, it defaults to the ...../tmp.py file
        #this only happens during testing
        if source_code is None and example_file_name is None:
            debug_file = os.path.join(self.path, 'tmp.py')
            with open(debug_file, 'r', encoding='utf-8') as f:
                source_code = f.read()
        
        #for the analysis of a demo code
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
        
        #key: lineno, value: expression node on that line
        self.expression_at_line = dict()
        expressions = get_exprs(source_code)

        for e in expressions:
            try:
                self.expression_at_line[e.lineno] = e
            except Exception:
                pass

        
        self.source_code = source_code
        ret['source_code'] = source_code

        #it saves a temporary file with the user code,
        #that will be deleted upon finishing the analysis
        user_codes_dir = os.path.join(self.path, 'usercodes')
        filename = generate_filename()
        self.filename_with_path = os.path.join(user_codes_dir, filename)
        
        with open(self.filename_with_path, 'w+', encoding='utf-8') as f:
            f.write(self.source_code)

        #starting the subprocess
        self.p = multiprocessing.Process(target=lambda:self._runscript(self.filename_with_path), args=())
        self.p.start()
        self.request("init")
        return ret
    
    #make preprocess to the code and start the analysis
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
    
    #returns a list of filenames located in the examples folder, these are the demo codes
    def get_example_files(self):
        examples_path = os.path.join(self.path, 'examples')
        return sorted(os.listdir(examples_path))

    #this method is for the communication with the subprocess
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
    
    #this method is executed by the subprocess
    def cmdloop(self, intro=None):
        #we have to reimport files that are used in this scope
        import inspect, copy, re, sys
        sys.path.insert(0, os.path.join(self.path, 'main'))
        from get_frame_data import get_pointers
        from expression_analysis import node2seq, node2treant, node2tree
        from error_handling import is_error_message

        #we override the print function, this can be used for debugging
        def debug(*args):
            sys.stdout.write(' '.join(str(x) for x in args) + '\n')
        
        while True:

            #wait for a message in the multiprocessing queue
            msg = self.request_q.get()

            #stop the analysis and the subprocess
            if msg == "exit":
                self.onecmd("exit")
                self.answer_q.put("exit")
                return

            #if we stepped past the user's code, stop the analysis
            elif not self.is_still_in_user_code(self.curframe):
                ret = self.lastget
                ret['isover'] = True
                self.answer_q.put(ret)

            #it overrides the print function, so its messages are
            #redirected to the STEP_PY_STEP_PRINT variable
            elif msg == "init":
                self.lastget = None
                self.onecmd("ORIGINAL_PRINT=print")
                self.onecmd("!STEP_PY_STEP_OUTPUT=''")
                self.onecmd("!def STEP_PY_STEP_PRINT(*args, sep=' ', end='\\n', file=None, flush=False):global STEP_PY_STEP_OUTPUT;STEP_PY_STEP_OUTPUT+=sep.join([str(x) for x in args])+end")
                self.onecmd("!print=STEP_PY_STEP_PRINT")
                self.answer_q.put("init")

            #same as Pdb step
            elif msg == "step":
                self.onecmd("step")
                self.request_q.put("get")
                break

            #same as Pdb next
            elif msg == "next":
                if self.is_still_in_user_code(self.curframe):
                    self.onecmd("next")
                self.request_q.put("get")
                break

            #modify variable
            elif msg.startswith("modify"):
                try:
                    var_name, value = re.findall(r'modify (\w+) (.+)', msg)[0]
                except Exception:
                    self.request_q.put("get")
                    break

                #check if it's a valid variable name and value
                line = f"{var_name}={value}"
                try:
                    exec(line)
                #if the value was not valid, try passing it as a string
                except Exception:
                    value = value.replace('"', '\\"')
                    value = '"' + value + '"'
                    line = f"{var_name}={value}"

                #if it's still not valid, stop the modfication
                try:
                    exec(line)
                except Exception:
                    self.request_q.put("get")
                    break

                #execute the final line and call the 'get' section
                line = "!" + line
                self.onecmd(line)
                self.request_q.put("get")

            #add new variable
            elif msg.startswith("newvar"):
                try:
                    var_name, vartype, value = re.findall(r'newvar (\w+) (\w+) (.+)', msg)[0]
                except Exception:
                    self.request_q.put("get")
                    break

                #if no type given
                if vartype == "autocast":
                    line = f"{var_name}={value}"
                #if a type was given
                else:
                    line = f"{var_name}={vartype}({value})"

                #check if it's a valid variable name and value
                try:
                    exec(line)
                #if the value was not valid, try passing it as a string
                except Exception:
                    value = value.replace('"', '\\"')
                    value = '"' + value + '"'
                    line = f"{var_name}={value}"

                #if it's still not valid, stop the creating of new variable
                try:
                    exec(line)
                except Exception:
                    self.request_q.put("get")
                    break

                line = "!" + line
                self.onecmd(line)
                self.request_q.put("get")

            #delete variable
            elif msg.startswith("delvar"):
                try:
                    var_name = re.findall(r'delvar (\w+)', msg)[0]
                except Exception:
                    self.request_q.put("get")
                    break

                #check if it's a valid variable name
                try:
                    exec(f"{var_name}=1\ndel {var_name}")
                except Exception:
                    self.request_q.put("get")
                    break

                self.onecmd(f"!del {var_name}")
                self.request_q.put("get")


            #get a dictionary of everything we need to analyze the
            #current state of the script, format:
            #{
            #'isover': bool ,
            #'error': None | str ,
            #'localvars': dict ,
            #'lineno': int ,
            #'expr': None | int
            #}
            elif msg == "get":
                ret = dict()
                ret['isover'] = False
                ret['error'] = None

                #if there was an error message written on the output,
                #save it in the error field
                for x in self.sps_output.getvalue().split('\n'):
                    if is_error_message(x):
                        ret['error'] = x
                        break

                #get all variables, using function defined in get_frame_data.py
                ret['allvars'] = get_pointers(self.curframe)

                #remove STEP_PY_STEP_OUTPUT from the variable list
                #and save it's value to the field that represents
                #the standard output
                for v in ret['allvars']:
                    if v['name'] == 'STEP_PY_STEP_OUTPUT':
                        step_py_step_output = v
                        break
                ret['output'] = step_py_step_output['value']
                ret['allvars'].remove(v)


                #save the current line
                filename_with_path, lineno, function, code_context, index = inspect.getframeinfo(self.curframe)
                ret['lineno'] = lineno
                
                #if the current line contains an expression to be analyzed,
                #save it in the 'expr' filed using the functions defined in expression_analysis.py
                if lineno in self.expression_at_line:
                    #actual local vars
                    ret['expr'] = dict()
                    node = self.expression_at_line[lineno]
                    ret['expr']['sequence'] = node2seq(node, self.source_code, self.curframe.f_locals)
                    ret['expr']['treant'] = node2treant(node, self.source_code, self.curframe.f_locals)
                else:
                    ret['expr'] = None
                
                #if the current state is identical to the previous one, step forward
                #until the script gets to a different state
                if self.lastget == ret:
                    self.request_q.put("step")

                #do the same thing, if the code is inside the hidden STEP_PY_STEP_PRINT function
                elif function in ["STEP_PY_STEP_OUTPUT", "STEP_PY_STEP_PRINT"] or filename_with_path == "<stdin>":
                    self.request_q.put("step")
                else:
                    self.lastget = ret
                    self.answer_q.put(ret)
            
            else:
                self.answer_q.put("Invalid command")


    #recursively inspects the frame to see if we are
    #still inside the user's script
    def is_still_in_user_code(self, frame):
        f = frame
        while f:
            filename_with_path, lineno, function, code_context, index = inspect.getframeinfo(f)
            if filename_with_path == self.filename_with_path:
                return True
            f = f.f_back

        return False














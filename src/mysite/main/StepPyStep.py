import pdb
import copy
import multiprocessing
import re

def get_methods(user_defined_class):
    ret = []
    for m in dir(user_defined_class):
        if m.startswith("__"):
            continue
        a = getattr(user_defined_class, m)
        if callable(a):
            ret.append(a)
    return ret

class StepPyStep(pdb.Pdb):
    def __init__(self, **kwargs):
        print("létrejövök")

        self.request_q = multiprocessing.Queue()
        self.answer_q = multiprocessing.Queue()
        
        path = "/home/beno/Desktop/steppystep/step-py-step/src/mysite/"
        self.filename = path + "tmp.py"
        '''
        self.source_code = kwargs['source_code']
        self.create_file(self.source_code)

        del kwargs['source_code']
        '''
        super().__init__(**kwargs)
        
        # self._runscript(self.filename)
    
    def start(self, source_code=None):
        print("startoljunk el")
        if source_code is None:
            with open(self.filename, 'r', encoding='utf-8') as f:
                source_code = f.read()

        print("uccu neki")
        self.create_file(source_code)
        self.p = multiprocessing.Process(target=self.rs, args=())
        self.p.start()
        return source_code

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
        import inspect, copy, re
        
        while True:

            msg = self.request_q.get()
            
            if msg == "exit":
                print("EXIT üzi")
                self.onecmd("exit")
                self.answer_q.put("exit")
                return
            
            elif msg == "step":
                self.onecmd("step")
                filename_with_path, lineno, function, code_context, index = inspect.getframeinfo(self.curframe)
                self.answer_q.put(lineno)
                break

            elif msg == "x":
                self.onecmd("!x=999;y=888")
                filename_with_path, lineno, function, code_context, index = inspect.getframeinfo(self.curframe)
                self.answer_q.put(f"xelek{lineno}")
                return
                line = "!_localvars=[(k, v) for k,v in locals().items() if not k.startswith('_') and isinstance(v,int)]"
                self.onecmd(line)
                print("localvars", _localvars)
                print("xxxxx", self.curframe.f_locals)

            elif msg == "get":

                ret = dict()

                
                localvars = dict()
                '''
                localvars:
                {
                    3242847293: #memory address
                    {
                        "names":['a', 'b'],
                        "type": "class",
                        "value":
                        {
                            "class_name":"MyClass",
                            "variables":
                            {
                                43824328:
                                {
                                    "names": ["a"],
                                    "type": "int",
                                    "value": "4"
                                },
                                8473329847:
                                {
                                    "names": ["f"],
                                    "type": "function",
                                    "value": "def f(): return 42"
                                }
                            }
                        }
                    }
                    32427849328:
                    {
                        "names":['x'],
                        "type": "int",
                        "value": "100"
                    }
                }
                '''


                for k in self.curframe.f_locals:
                    if k.startswith("__"):
                        continue
                    print(id(self.curframe.f_locals[k]), k, self.curframe.f_locals[k])

                    id_ = id(self.curframe.f_locals[k])

                    if id_ in localvars:
                        localvars[id_]['names'].append(k)
                        continue

                    val = self.curframe.f_locals[k]
                    typ = type(val)
                    t = re.findall(r"'.+'", str(typ))[0][1:-1] #returns the substring between apostrophes in <class 'str'>
                    t = val.__class__.__name__

                    # if user-defined-class-type
                    if re.match(r'^__main__\..+$', t):
                        #TODO class outside of main module
                        t = re.findall(r'\.(.+)') #returns Classname from __main__.Classname
                        c = self.curframe.f_locals[k]
                        v = inspect.getsource()

                    elif t == "function":
                        f = self.curframe.f_locals[k] # the function itself
                        v = inspect.getsource(f) #the source code of the function
                    else:
                        val = self.curframe.f_locals[k]
                        typ = type(val)
                        is_builtin = typ.__class__.__module__ == 'builtins'

                        if is_builtin:
                            t = re.findall(r"'.+'", str(typ))[0][1:-1] #returns the substring between apostrophes in <class 'str'>
                            v = str(val)
                        else:
                            t = None
                            v = None


                    localvars[id_] = {"names": [k], "type": t, "value": v}

                ret['localvars'] = localvars


                '''
                for k,v in filter(lambda x:not x[0].startswith("__") and isinstance(x[1], int), self.curframe.f_locals.items()):
                    if k.startswith("__"):
                        continue
                    ret['localvars'][k] = v
                '''



                filename_with_path, lineno, function, code_context, index = inspect.getframeinfo(self.curframe)
                ret['lineno'] = lineno
                self.answer_q.put(ret)
            
            else:
                filename_with_path, lineno, function, code_context, index = inspect.getframeinfo(self.curframe)
                self.answer_q.put(lineno)

        
if __name__ == "__main__":
    filename = "ja2.py"
    filename = "ja.py"

    #p = StepPyStep(filename=filename)
    p = StepPyStep()
    p.start()

    while True:
        print("várom a parancsokat")
        r = input()
        if r == "quit":
            p.kill()
            break
        ret = p.request(r)
        print("------RET", ret)
        if ret == "exit":
            break
















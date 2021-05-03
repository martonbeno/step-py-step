import pdb
import copy
import multiprocessing




class StepPyStep(pdb.Pdb):
    def __init__(self, **kwargs):
        # self.inp = kwargs['inp']
        # self.outp = kwargs['outp']
        
        self.request_q = multiprocessing.Queue()
        self.answer_q = multiprocessing.Queue()
        
        self.filename = kwargs['filename']
        self.variables = []
        self.frames = []
        self.vars = []
        del kwargs['filename']
        # del kwargs['inp']
        # del kwargs['outp']
        
        super().__init__(**kwargs)
        
        self.p = multiprocessing.Process(target=self.rs, args=())
        self.p.start()
        # self._runscript(self.filename)
    
    def rs(self):
        self._runscript(self.filename)
        
    
    def kill(self):
        print("KILLL")
        self.request_q.put("exit")
        self.p.join()
    
    def request(self, msg):
        self.request_q.put(msg)
        ret = self.answer_q.get()
        if ret == "exit":
            self.kill()
        return ret
        
    def cmdloop(self, intro=None):
        import inspect, copy
        
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
                ret['localvars'] = list()

                for k,v in filter(lambda x:not x[0].startswith("__") and isinstance(x[1], int), self.curframe.f_locals.items()):
                    if k.startswith("__"):
                        continue
                    ret['localvars'].append({k:v})



                filename_with_path, lineno, function, code_context, index = inspect.getframeinfo(self.curframe)
                ret['lineno'] = lineno
                self.answer_q.put(ret)
            
            else:
                filename_with_path, lineno, function, code_context, index = inspect.getframeinfo(self.curframe)
                self.answer_q.put(lineno)

        

filename = "ja2.py"
filename = "ja.py"

p = StepPyStep(filename=filename)

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
















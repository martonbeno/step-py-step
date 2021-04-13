import pdb
import copy
import multiprocessing

class StepPyStep(pdb.Pdb):
    def __init__(self, **kwargs):

        self.request_q = multiprocessing.Queue()
        self.answer_q = multiprocessing.Queue()
        
        path = "/home/steppystep/Desktop/step-py-step/src/mysite/"
        self.filename = path + "tmp.py"
        '''
        self.source_code = kwargs['source_code']
        self.create_file(self.source_code)

        del kwargs['source_code']
        '''
        super().__init__(**kwargs)
        
        # self._runscript(self.filename)
    
    def start(self, source_code):
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
                ret['localvars'] = dict()

                for k,v in filter(lambda x:not x[0].startswith("__") and isinstance(x[1], int), self.curframe.f_locals.items()):
                    if k.startswith("__"):
                        continue
                    ret['localvars'][k] = v



                filename_with_path, lineno, function, code_context, index = inspect.getframeinfo(self.curframe)
                ret['lineno'] = lineno
                self.answer_q.put(ret)
            
            else:
                filename_with_path, lineno, function, code_context, index = inspect.getframeinfo(self.curframe)
                self.answer_q.put(lineno)

        
if __name__ == "__main__":
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
















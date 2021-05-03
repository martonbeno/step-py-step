import pdb
import copy
import multiprocessing

class myPdb(pdb.Pdb):
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
            
            elif msg == "lepj":
                self.onecmd("step")
                filename_with_path, lineno, function, code_context, index = inspect.getframeinfo(self.curframe)
                #filename = filename_with_path.split('/')[-1]
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

                print("flocals", self.curframe.f_locals)

                ret = dict()
                #line = "!_localvars=[(k, v) for k,v in locals().items() if not k.startswith('_') and isinstance(v,int)]"
                #self.onecmd(line)
                #ret['localvars'] = copy.deepcopy(_localvars)

                filename_with_path, lineno, function, code_context, index = inspect.getframeinfo(self.curframe)
                ret['lineno'] = lineno
                self.answer_q.put(ret)
            
            else:
                filename_with_path, lineno, function, code_context, index = inspect.getframeinfo(self.curframe)
                self.answer_q.put(lineno)

                #self.cmdloop(intro)
                #return

        #ígyis úgyis léptet

        '''
        goon = True
        if msg == "step":
            self.onecmd("step")
        else:
            goon = False

        self.answer_q.put(lineno)

        if goon:
            self.cmdloop(intro)
        else:
            self.onecmd("exit")
        return
        
        #check if we exited the main file
        line = "!_FILENAME=__file__"
        self.onecmd(line)
        if filename != _FILENAME:
            print("kilepek", filename, _FILENAME)
            self.onecmd("exit")
            return
        else:
            print("nem lepek ki", filename, _FILENAME)
        
        print(filename, lineno, function)
        
        #saving variables
        # line = "!_localvars=[(k,type(v),v) for k,v in locals().items() if not k.startswith('_')]"
        line = "!_localvars=[{'name':k, 'type':type(v), 'val':str(v)} for k,v in locals().items() if not k.startswith('_')]"
        self.onecmd(line)
        line = "!_globalvars=[(k,v) for k,v in globals().items() if not k.startswith('_')]"
        self.onecmd(line)
        
        
        #returning the state
        ret = dict()
        ret['localvars'] = ['localvars']#copy.deepcopy(_localvars)
        ret['globalvars'] = ['globalvars']#copy.deepcopy(_globalvars)
        ret['lineno'] = lineno
        # self.outp(ret)
        self.answer_q.put(ret)

        if msg == "step":
            self.onecmd("step")
        elif msg.startswith("update "):
            _, name, newval = msg.split()
            if name in map(lambda x:x['name'], _localvars):
                #TODO try-except-be kéne, hogy a típus ne okozzon bajt
                line = f"!{name}={newval}"
                print(f">> {line}")
                self.onecmd(line)
                self.onecmd('locals()') #TEST
            else:
                print("nincsilyen")
            

        #elif msg == "get" or msg == "":
        #    self.cmdloop(intro)

        
        self.onecmd(msg)
        # print("-----------------")
        '''
        

filename = "ja2.py"
filename = "ja.py"

p = myPdb(filename=filename)

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
















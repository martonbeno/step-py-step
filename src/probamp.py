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
		self.request_q.put("exit")
		self.p.join()
	
	def request(self, msg):
		print("üzi jött")
		self.request_q.put(msg)
		ret = self.answer_q.get()
		return ret
		
	def cmdloop(self, intro=None):
		import inspect, copy
		
		# msg = self.inp()
		# msg = self.request_q.get()
		msg = "step"
		
		if msg == "exit":
			self.onecmd("exit")
			return
		
		filename, lineno, function, code_context, index = inspect.getframeinfo(self.curframe)
		
		#check if we exited the main file
		line = "!_FILENAME=__file__"
		self.onecmd(line)
		if filename != _FILENAME:
			print("kilepek", filename, _FILENAME)
			self.onecmd("exit")
			
		print(filename, lineno, function)
		
		#saving variables
		# line = "!_localvars=[(k,type(v),v) for k,v in locals().items() if not k.startswith('_')]"
		line = "!_localvars=[{'name':k, 'type':type(v), 'val':v} for k,v in locals().items() if not k.startswith('_')]"
		self.onecmd(line)
		line = "!_globalvars=[(k,v) for k,v in globals().items() if not k.startswith('_')]"
		self.onecmd(line)
		
		
		#returning the state
		ret = dict()
		ret['localvars'] = copy.deepcopy(_localvars)
		ret['globalvars'] = copy.deepcopy(_globalvars)
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
			
		
		elif msg == "get" or msg == "":
			self.cmdloop(intro)
		
		else:
			self.onecmd(msg)
		# print("-----------------")
		
		

filename = "C:/Users/HAL9000/Desktop/ik/szakdoga/ja.py".replace('/', '\\').lower()

def outp(d):
	print("-------")
	for k,v in d.items():
		print(k,v)
	print("-------")

p = myPdb(filename=filename)

while True:
	r = input("várom a parancsokat ")
	if r == "quit":
		p.kill()
		break
	print(p.request(r))
















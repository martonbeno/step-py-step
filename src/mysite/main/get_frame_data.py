import inspect
import ctypes


class Var:
	def __init__(self, pointer, name):
		self.pointer = pointer
		self.name = name
		self.is_processed = False #valszeg nem kell
		self.is_udt = False
		self.children = []

	def __str__(self):
		return f'{self.name} (processed={self.is_processed})'

	def get_dict(self):
		assert self.is_processed
		ret = dict()
		ret['name'] = self.name
		ret['pointer'] = self.pointer
		ret['is_udt'] = self.is_udt
		ret['defined_elsewhere'] = self.defined_elsewhere
		if self.defined_elsewhere:
			ret['type'] = None
		elif self.type is type:
			ret['type'] = "Class"
		else:
			ret['type'] = self.type.__name__
		#ret['type'] = self.type.__name__ if not self.defined_elsewhere else None

		if self.defined_elsewhere:
			ret['value'] = None
		elif self.type is type or inspect.isfunction(self.data):
			ret['value'] = inspect.getsource(self.data)
		else:
			ret['value'] = str(self.data)

		#ret['value'] = str(self.data) if not self.defined_elsewhere else None
		ret['children'] = []
		for child in self.children:
			ret['children'].append(child.get_dict())
		return ret


	#process self and add unprocessed children
	def process(self, allocated_pointers):
		if self.pointer in allocated_pointers:
			print("már le vagyok foglalva")
			self.defined_elsewhere = True
		
		else:
			self.defined_elsewhere = False			
			self.data = ctypes.cast(self.pointer, ctypes.py_object).value
			self.type = self.data.__class__
			self.is_udt = self.type not in (int, float, complex, bool, str, type(None), type)

			if self.is_udt:
				try:
					for k,v in self.data.__dict__.items():
						child_pointer = id(v)
						child = Var(child_pointer, k)
						self.children.append(child)
				except AttributeError:
					print("nincs dict-je ennek:", self.type)

		self.is_processed = True
		return self.children



def get_pointers(frame):

	pointers = []
	#TODO frame helyett lehet user-defined-object vagy container

	generations = []

	first_gen = []
	for k in frame.f_locals:
		if k.startswith("__"):
			continue
		pointer = id(frame.f_locals[k])
		#pointers.append(pointer)
		v = Var(pointer, k)
		first_gen.append(v)


	generations.append(first_gen)

	while True:
		new_generation = []
		for node in generations[-1]:
			children = node.process(pointers)
			new_generation = new_generation + children
			#pointers = pointers + [child.pointer for child in new_generation]
			pointers.append(node.pointer)

		if new_generation:
			generations.append(new_generation)
		else:
			break


	print("####")
	for i, gen in enumerate(generations):
		for item in gen:
			print(i, str(item))
	print("####")

	print("&&dict&&")
	for i, node in enumerate(first_gen):
		print(i, node.get_dict())
	print("&&/dict&&")

	return [node.get_dict() for node in first_gen]


def get_frame_data(frame):
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
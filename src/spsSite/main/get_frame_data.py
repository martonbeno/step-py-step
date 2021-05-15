import inspect
import ctypes
import traceback
import copy
import json

#represents a variable
class Var:
	def __init__(self, pointer, name):
		self.pointer = pointer #memory address
		self.name = name 
		self.is_udt = False #is user-defined type ?
		self.is_container = False #list, set, tuple, dict, UDT
		self.children = [] #if it's a container, this list contains the Var objects that represent the elements contained in the variable

	#converts the object to a dictionary that is convertable to a JSON
	def get_dict(self):
		ret = dict()

		#skipping non-user-defined classes
		if not self.defined_elsewhere and self.type == "Class" and not self.is_udt:
			return ret

		ret['name'] = str(self.name) #we need str format, because otherwise it may not convert to JSON
		ret['pointer'] = self.pointer
		ret['is_local'] = None
		ret['is_global'] = None
		ret['is_udt'] = self.is_udt
		ret['is_container'] = self.is_container
		ret['defined_elsewhere'] = self.defined_elsewhere

		if self.defined_elsewhere:
			ret['type'] = None
		elif self.type is type:
			ret['type'] = "Class"
		else:
			ret['type'] = self.type.__name__

		if self.defined_elsewhere:
			ret['value'] = None
		elif self.type is type or inspect.isfunction(self.data):
			try:
				ret['value'] = inspect.getsource(self.data)
			except Exception:
				print(f"HIBA {self.data}")
				traceback.print_exc()
		else:
			ret['value'] = str(self.data)

		ret['children'] = []
		for child in self.children:
			ret['children'].append(child.get_dict())
		return ret


	#process self and add unprocessed children
	#this is not a recursive function, it needs to be called to the children separately
	def process(self, allocated_pointers):

		#if the variable is defined earlier in the code, there is no need to process it
		if self.pointer in allocated_pointers:
			self.defined_elsewhere = True
		
		else:
			self.defined_elsewhere = False			
			self.data = ctypes.cast(self.pointer, ctypes.py_object).value
			self.type = self.data.__class__


			self.is_udt = True #user defined type
			self.is_container = False
			if self.type in (int, float, complex, bool, str, type(None), type):
				self.is_udt = False

			if inspect.isfunction(self.data):
				self.is_udt = False

			elif inspect.ismodule(self.type):
				self.is_udt = False


			#generate children without processing them
			elif self.type in (list, tuple):
				self.is_udt = False
				self.is_container = True
				for i,v in enumerate(self.data):
					child_pointer = id(v)
					child = Var(child_pointer, i)
					self.children.append(child)

			elif self.type is dict:
				self.is_udt = False
				self.is_container = True
				for k,v in self.data.items():
					child_pointer = id(v)

					#make key passable to json
					if k.__class__ not in (str, int, float, bool, None):
						k = str(k)

					child = Var(child_pointer, k)
					self.children.append(child)

			elif self.type is set:
				self.is_udt = False
				self.is_container = True
				for v in self.data:
					child_pointer = id(v)
					child = Var(child_pointer, '')
					self.children.append(child)


			elif self.is_udt:
				self.is_container = True
				try:
					for k,v in self.data.__dict__.items():
						child_pointer = id(v)
						child = Var(child_pointer, k)
						self.children.append(child)
				except AttributeError:
					pass

		return self.children

#recursively set the node to the given scope(s)
#if the pointer parameter is not None, it only sets those
#nodes, that has the same value in its pointer field
def set_scope(node, is_local=None, is_global=None, pointer=None):
	ret = False #return True if anything is changed
	if pointer is None or pointer == node['pointer']:
		ret = True
		if is_local is not None:
			node['is_local'] = is_local
		if is_global is not None:
			node['is_global'] = is_global
	for child in node['children']:
		ret = ret or set_scope(child, is_local, is_global, pointer)
	return ret

#returns set of all pointers in the node or below it
def get_all_pointers(node):
	ret = set()
	ret.add(node['pointer'])
	for child in node['children']:
		ret = ret.union(get_all_pointers(child))
	return ret

#returns dictionary formatted tree structure, containing all variables and their attributes
def get_pointers(frame):
	local_tree = get_pointers_from_scope(frame, "local")
	global_tree = get_pointers_from_scope(frame, "global")

	local_pointers = set()
	for l_node in local_tree:
		set_scope(l_node, is_local=True, is_global=False)
		local_pointers = local_pointers.union(get_all_pointers(l_node))
	
	global_pointers = set()
	for g_node in global_tree:
		global_pointers = global_pointers.union(get_all_pointers(g_node))


	#merging local and global trees
	ret = copy.deepcopy(local_tree)
	for g_node in global_tree:
		is_node_local_too = False
		for l_node in ret:
			if set_scope(l_node, is_global=True, pointer=g_node['pointer']):
				is_node_local_too = True

		if not is_node_local_too:
			set_scope(g_node, is_local=False, is_global=True)
			ret.append(g_node)


	return ret

#returns dictionary formatted tree structure, containing local or global variables and their attributes
def get_pointers_from_scope(frame, scope):
	if scope == "local":
		frame_scope = frame.f_locals
	elif scope == "global":
		frame_scope = frame.f_globals
	else:
		raise Exception("scope has to be 'locals' or 'globals'")

	pointers = []

	generations = []

	first_gen = []
	DONT_PROCESS = "STEP_PY_STEP_PRINT ORIGINAL_PRINT print".split()
	for k in filter(lambda x:x not in DONT_PROCESS, frame_scope):
		if k.startswith("__"):
			continue
		pointer = id(frame_scope[k])
		v = Var(pointer, k)
		first_gen.append(v)


	generations.append(first_gen)

	while True:
		new_generation = []
		for node in generations[-1]:
			children = node.process(pointers)
			new_generation = new_generation + children
			pointers.append(node.pointer)

		if new_generation:
			generations.append(new_generation)
		else:
			break

	return [node.get_dict() for node in first_gen]
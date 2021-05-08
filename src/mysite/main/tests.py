import unittest
import os


from StepPyStep import StepPyStep

class Tests(unittest.TestCase):
	def test_init(self):
		StepPyStep()

	def get_example_files(self):
		path = os.path.realpath(__file__)	#..../mysite/main/views.py
		path = os.path.dirname(path)		#..../mysite/main/
		path = os.path.dirname(path)		#..../mysite/
		examples_path = os.path.join(path, "examples")
		example_files = sorted(os.listdir(examples_path))
		return example_files

	def test_example_codes_exist(self):
		example_files = self.get_example_files()
		assert example_files

	def test_example_codes_init(self):		
		example_files = self.get_example_files()
		for example_file in example_files:
			model = StepPyStep()
			init_msg = model.start(example_file_name=example_file)
			assert init_msg['compile_success']
			assert init_msg['error_message'] is None
			model.request("exit")

	def test_source_code_init(self):
		source_code = "a=1"
		model = StepPyStep()
		init_msg = model.start(source_code=source_code)
		assert init_msg['compile_success']
		assert init_msg['error_message'] is None
		assert init_msg['source_code'] == source_code
		model.request("exit")

	def test_step(self):
		source_code = "a=1"
		model = StepPyStep()
		init_msg = model.start(source_code=source_code)

		msg = model.request("step")
		assert msg['isover'] == False
		assert msg['error'] is None
		assert msg['lineno'] == 1

		model.request("exit")

	def test_over(self):
		source_code = "a=1"
		model = StepPyStep()
		init_msg = model.start(source_code=source_code)

		model.request("step")
		msg = model.request("step")
		assert msg['isover'] == True

		model.request("exit")

	def test_compile_error(self):
		source_code = "321asd"
		model = StepPyStep()
		init_msg = model.start(source_code=source_code)
		assert init_msg['compile_success'] == False
		del model

	def test_contains_import_error(self):
		source_code = "import sys"
		model = StepPyStep()
		init_msg = model.start(source_code=source_code)
		assert init_msg['compile_success'] == False
		del model

	def test_variables(self):
		lines = []
		lines.append("a=1")
		lines.append("b='ok'")
		lines.append("c=0.5")
		lines.append("d=True")
		lines.append("e=[2,3,4]")
		lines.append("def f():\n\treturn True")
		lines.append("class G:\n\tpass")
		lines.append("h=None")
		source_code = '\n'.join(lines)

		model = StepPyStep()
		model.start(source_code=source_code)
		msg = model.request("step")

		while not msg['isover']:
			#print(msg)
			msg = model.request("step")

		variables = msg['localvars']
		assert all(v['is_local'] for v in variables)
		assert all(v['is_global'] for v in variables)
		assert all(v['defined_elsewhere'] == False for v in variables)

		allnames = []
		for v in variables:
			if v['name'] == 'a':
				assert v['type'] == 'int'
				assert v['value'] == 1
			if v['name'] == 'b':
				assert v['type'] == 'str'
				assert v['value'] == 'ok'
			if v['name'] == 'c':
				assert v['type'] == 'float'
				assert abs(v['value']-0.5) <= 0.01
			if v['name'] == 'd':
				assert v['type'] == 'bool'
				assert v['value'] == True
			if v['name'] == 'e':
				assert v['type'] == 'list'
				assert v['value'][0] == 2
				assert v['value'][1] == 3
				assert v['value'][2] == 4
			if v['name'] == 'f':
				assert v['type'] == 'function'
				assert v['value'] == "def f():\n\treturn True\n"
			if v['name'] == 'G':
				assert v['type'] == 'Class'
				assert v['value'] == "class G:\n\tpass\n"
			if v['name'] == 'h':
				assert v['type'] == 'NoneType'
				assert v['value'] == None

		model.request("exit")
	
	def test_runtime_error(self):
		model = StepPyStep()
		source_code = "a = b"
		model.start(source_code=source_code)
		msg = model.request("step")
		
		assert msg['error'] is not None
		assert msg['error'].startswith("NameError")

		model.request("exit")
	
	def test_output(self):
		model = StepPyStep()
		source_code = "print('line1')\nprint('line2')"
		model.start(source_code=source_code)
		msg = model.request("step")
		msg = model.request("step")
		msg = model.request("step")

		assert msg['output'] == "line1\nline2\n"


		model.request("exit")


	def test_next_step(self):
		source_code = "f = lambda:3\na = f()\nb = None"

		#with step
		model = StepPyStep()
		model.start(source_code=source_code)
		step_counter = 1
		msg = model.request("step")
		while msg['isover'] ==  False:
			msg = model.request("step")
			step_counter += 1
		
		assert step_counter == 7

		model.request("exit")


		#with next
		model = StepPyStep()
		model.start(source_code=source_code)
		next_counter = 1
		msg = model.request("next")
		while msg['isover'] ==  False:
			msg = model.request("next")
			next_counter += 1
		
		assert next_counter == 4

		model.request("exit")

	def test_expression_analysis(self):
		source_code = "a = (1*2+3-4 > 2) or False"
		model = StepPyStep()
		model.start(source_code=source_code)

		msg = model.request("get")

		assert msg['expr']['treant'] is not None

		assert msg['expr']['sequence'][0] == "(1*2+3-4 > 2) or False"
		assert msg['expr']['sequence'][1] == "(2+3-4 > 2) or False"
		assert msg['expr']['sequence'][2] == "(5-4 > 2) or False"
		assert msg['expr']['sequence'][3] == "(1 > 2) or False"
		assert msg['expr']['sequence'][4] == "(False) or False"
		assert msg['expr']['sequence'][5] == "False"

		model.request("exit")

	def test_containers(self):
		lines = []
		lines.append("lst = [1,2,3]")
		lines.append("lst2 = [3,4,lst]")
		lines.append("s = set(lst)")
		lines.append("t = (10,11,12,13)")
		lines.append("class G: pass")
		lines.append("g = G()")
		lines.append("g.n = 5")
		lines.append("g.l = lst")
		source_code = '\n'.join(lines)


		model = StepPyStep()
		model.start(source_code=source_code)

		msg = model.request("step")
		
		lst = msg['localvars'][-1]
		assert lst['name'] == 'lst'
		assert lst['is_local'] == True
		assert lst['is_global'] == True
		assert lst['is_container'] == True
		assert lst['is_udt'] == False
		lst_children = lst['children']
		assert lst_children[0]['name'] == 0 #index
		assert lst_children[0]['type'] == 'int' #index
		assert lst_children[0]['value'] == 1 #index

		assert lst_children[1]['name'] == 1 #index
		assert lst_children[1]['type'] == 'int' #index
		assert lst_children[1]['value'] == 2 #index

		assert lst_children[2]['name'] == 2 #index
		assert lst_children[2]['type'] == 'int' #index
		assert lst_children[2]['value'] == 3 #index


		msg = model.request("step")
		lst2 = msg['localvars'][-1]
		assert lst2['children'][-1]['defined_elsewhere'] == True
		assert lst['pointer'] == lst2['children'][-1]['pointer']


		msg = model.request("step")
		s = msg['localvars'][-1]
		print(s)
		assert s['type'] == "set"
		assert s['is_container'] == True
		assert len(s['children']) == 3

		msg = model.request("step")
		t = msg['localvars'][-1]
		print(s)
		assert t['type'] == "tuple"
		assert t['is_container'] == True
		assert len(t['children']) == 4

		msg = model.request("next")
		assert msg['localvars'][-1]['type'] == "Class"
		
		msg = model.request("step")
		g = msg['localvars'][-1]
		assert g['type'] == "G"
		assert g['is_container'] == True
		assert g['is_udt'] == True
		assert len(g['children']) == 0


		msg = model.request("step")
		g = next(x for x in msg['localvars'] if x['name'] == 'g')
		assert len(g['children']) == 1
		g_child0 = g['children'][0]
		assert g_child0['type'] == 'int'
		assert g_child0['value'] == 5


		msg = model.request("step")
		g = next(x for x in msg['localvars'] if x['name'] == 'g')
		assert len(g['children']) == 2
		g_child1 = g['children'][1]

		assert g_child1['defined_elsewhere'] == True
		assert g_child1['pointer'] == lst['pointer']


		model.request("exit")



unittest.main()

#SPS = StepPyStep()
#print(SPS)
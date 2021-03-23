import ast
import re
import copy
import json

def get_type(node):
	return re.sub(r"^<class 'ast\.(.+)'>$", r'\1', str(type(node)))

def code2tree(code):
	code_mtx = code.split('\n')
	root = ast.parse(code)
	ret = node2tree(root, code_mtx)
	ret['code'] = code
	return ret

VARIABLES = dict()

def eval_binop(node):
	if get_type(node) == "Constant":
		return node

	if get_type(node) == "Name":
		return VARIABLES[node.id]
		# return ast.Constant(VARIABLES[node.id])
	
	elif get_type(node) == "BinOp":
		cp = copy.deepcopy(node)
		cp.left = eval_binop(cp.left)
		cp.right = eval_binop(cp.right)
		
		expr = ast.Expression(body=cp)
		ast.fix_missing_locations(expr)
		exe = compile(expr, filename="", mode="eval")
		return ast.Constant(eval(exe))

VARIABLES = dict()

def node2tree(node, kod_mtx):
	d = dict()
	d['type'] = get_type(node)
	
	# if d['type'] not in ['Module', 'Store', 'Add', 'Mult', 'Div']:
	if 'lineno' in node.__dict__:
		
		d['from_line'] = node.lineno-1
		d['to_line'] = node.end_lineno-1
		d['from_char'] = node.col_offset
		d['to_char'] = node.end_col_offset-1
		#ha egy sorban van az egész node
		if node.lineno == node.end_lineno:
			d['code'] = kod_mtx[node.lineno-1][node.col_offset:node.end_col_offset]
		#ha két sorban van az egész node
		elif node.lineno + 1 == node.end_lineno:
			d['code'] = kod_mtx[node.lineno-1][node.col_offset:]
			d['code'] += kod_mtx[node.end_lineno-1][:node.end_col_offset]
		#ha több, mint két sorban van a node
		elif node.lineno + 1 < node.end_lineno:
			d['code'] = kod_mtx[node.lineno-1][node.col_offset:]
			for i in range(node.lineno, node.end_lineno-1):
				d['code'] += kod_mtx[i]
			d['code'] += kod_mtx[node.end_lineno-1][:node.end_col_offset]
		else:
			raise Exception("baj a kód kiolvasással")
	
	if d['type'] == "BinOp":
		d['eval'] = eval_binop(node).value
	elif d['type'] == "Name":
		d['eval'] = eval_binop(VARIABLES[node.id]).value
	elif d['type'] == "Constant":
		d['eval'] = node.value
	else:
		d['eval'] = None
	
	if d['type'] == "Assign":
		targets = node.targets
		t = targets[0].id
		VARIABLES[t] = eval_binop(node.value)
		print(VARIABLES)
		
	
	d['children'] = [node2tree(child, kod_mtx) for child in ast.iter_child_nodes(node)]
	return d

def dfs(node, f):
	if isinstance(node, list):
		pass
	elif isinstance(node, ast.AST):
		for child in ast.iter_child_nodes(node):
			dfs(child, f)
		f(node)
	else:
		print("egyikse mert", type(node))

def to_html(text):
	return text.replace('\n', ';').replace('\t', '	')

def to_treant(node):
	ret = dict()
	ret['text'] = {'name': node['type']}
	if 'eval' in node:
		ret['text']['title'] = node['eval'] if node['eval'] else ''
	if 'code' in node:
		ret['text']['desc'] = to_html(node['code'])
	ret['children'] = [to_treant(child) for child in node['children']]
	return ret

def printer(node):
	# print(node, ast.get_source_segment(kod, node))
	print(node,end=' ')
	try:
		print(node.lineno, node.end_lineno, node.col_offset, node.end_col_offset)
	except AttributeError:
		print("nincs")

def get_pos(node):
	if 'from_line' in node:
		ret = dict()
		for k in ("from_line", "to_line", "from_char", "to_char"):
			ret[k] = node[k]
		return ret
	return None

def analyze(node, ret=None, base_code=None):
	if ret is None:
		ret = []
		base_code = node['code']
	
	pos = get_pos(node)
	if pos:
		ret.append({
			'code': base_code,
			'evaluation': node['eval'],
			'highlight': pos
		})
	for child in node['children']:
		analyze(child, ret, base_code)
	return ret

if __name__ == "__main__":
	with open("kod.py", 'r', encoding='utf-8') as f:
		kod = f.read()
	
	d = code2tree(kod)
	j = to_treant(d)

	a = analyze(d)
	for x in a:
		print(x)
	
	with open("fa.json", 'w+', encoding='utf-8') as f:
		json.dump(d, f, separators=(',', ':'), indent=4)
	
	j = to_treant(d)
	with open("C:/xampp/htdocs/steppystep/treant.json", 'w+', encoding='utf-8') as f:
		json.dump(j, f)
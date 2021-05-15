import re
import copy
import ast

class InvalidExpressionError(Exception):
    pass

def get_type(node):
    return node.__class__.__name__

#returns the value of any Expression node as an ast.Constant    
def eval_expr(node, variables):
    if get_type(node) == "Constant":
        return node

    if get_type(node) == "Name":
        ret = ast.Constant(variables[node.id])
        return ret
    
    elif get_type(node) == "UnaryOp":
        cp = copy.deepcopy(node)
        cp.operand = eval_expr(cp.operand, variables)
        
        expr = ast.Expression(body=cp)
        ast.fix_missing_locations(expr)
        exe = compile(expr, filename="", mode="eval")
        return ast.Constant(eval(exe))
    
    elif get_type(node) == "BinOp":
        cp = copy.deepcopy(node)
        cp.left = eval_expr(cp.left, variables)
        cp.right = eval_expr(cp.right, variables)
        
        expr = ast.Expression(body=cp)
        ast.fix_missing_locations(expr)
        exe = compile(expr, filename="", mode="eval")
        return ast.Constant(eval(exe))
    
    elif get_type(node) == "BoolOp":
        cp = copy.deepcopy(node)
        for i in range(len(cp.values)):
            cp.values[i] = eval_expr(cp.values[i], variables)
        expr = ast.Expression(body=cp)
        ast.fix_missing_locations(expr)
        exe = compile(expr, filename="", mode="eval")
        return ast.Constant(eval(exe))
    
    elif get_type(node) == "Compare":
        cp = copy.deepcopy(node)
        cp.left = eval_expr(cp.left, variables)
        for i in range(len(cp.comparators)):
            cp.comparators[i] = eval_expr(cp.comparators[i], variables)
        expr = ast.Expression(body=cp)
        ast.fix_missing_locations(expr)
        exe = compile(expr, filename="", mode="eval")
        return ast.Constant(eval(exe))

    raise InvalidExpressionError()

#returns True if the node, or any node below it is of ast.Call type
def contains_function_call(node):
    if isinstance(node, ast.Call):
        return True
    for child in ast.iter_child_nodes(node):
        if contains_function_call(child):
            return True
    return False

#returns root of every subtree that is built of expressions
def get_exprs(code):
    node = ast.parse(code)

    ret = []

    if node.__class__ in [ast.BinOp, ast.BoolOp, ast.Compare, ast.UnaryOp]:
        if not contains_function_call(node):
            ret.append(node)
    else:
        for child in ast.iter_child_nodes(node):
            ret = ret + get_exprs(child)

    return ret

#returns True if the node or any node below it is of forbidden type
def is_forbidden_node(node, source_code):
    kod_mtx = source_code.split('\n')
    tree = node2tree(node, kod_mtx, {}, skip_eval=True)
    return is_forbidden_tree(tree)

#returns True if the tree contains any forbidden-typed nodes
def is_forbidden_tree(tree):
    #print(tree['type'])
    if tree['type'] == "Import":
        return "import"
    if tree['type'] == "Call":
        try: #if Call node has a children of Name type
            function_name = next(x for x in tree['children'] if x['type'] == "Name")
            if function_name['code'] in "open eval exec compile input":
                return function_name['code']
        except StopIteration:
            pass

    for child in tree['children']:
        forbidden_tree = is_forbidden_tree(child)
        if forbidden_tree:
            return forbidden_tree
    return False

#converts an ast node to a dictionary-structure, that contains
#the evaluation of the node, if it is of an expression type,
#and the part of the source code that the node represents
def node2tree(node, kod_mtx, variables, skip_eval=False):
    d = dict()
    d['type'] = get_type(node)
    
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
    

    if not skip_eval:
        if d['type'] in ("BinOp", "BoolOp", "Compare", "UnaryOp"):
            d['eval'] = eval_expr(node, variables).value
        elif d['type'] == "Name":
            d['eval'] = eval_expr(node, variables).value        
        elif d['type'] == "Constant":
            d['eval'] = node.value
        else:
            d['eval'] = None
        
    
    d['children'] = [node2tree(child, kod_mtx, variables, skip_eval) for child in ast.iter_child_nodes(node)]
    return d

#returns a list that represents the evaluation sequence of
#the expression node in the parameter
def node2seq(node, code, variables):
    kod_mtx = code.split('\n')
    tree = node2tree(node, kod_mtx, variables)
    seq = tree2seq(tree)
    return seq

#returns a list that represents the evaluation sequence of
#the dictionary tree in the parameter
def tree2seq(node, start=True):
    if start:
        #deleting duplicates
        lst = tree2seq(node, False)
        ret = [lst[0]]
        for x in lst[1:]:
            if x != ret[-1]:
                ret.append(x)
        return ret
    

    if node['type'] in ("Constant"):
        return [node['code']]
        
    elif node['type'] in ("Name", "UnaryOp"):
        return [node['code'], str(node['eval'])]


    if node['type'] in ("BinOp", "BoolOp", "Compare"):
        if node['type'] in ("BinOp", "Compare"):
            left_child = node['children'][0]
            right_child = node['children'][2]
        elif node['type'] == "BoolOp":
            left_child = node['children'][1]
            right_child = node['children'][2]
        
        left_from = left_child['from_char'] - node['from_char']
        left_to = left_from + len(left_child['code'])
        right_from = right_child['from_char'] - node['from_char']
        right_to = right_from + len(right_child['code'])
           
        
        first_part = node['code'][:left_from]
        middle_part = node['code'][left_to:right_from]
        last_part = node['code'][right_to:]
        
        
        
        ret = [node['code']]
        
        left_seq = tree2seq(left_child, False)
        
        for left_step in left_seq:
            sb = first_part
            sb += left_step
            sb += middle_part
            sb += right_child['code']
            sb += last_part
            ret.append(sb)
            
        right_seq = tree2seq(right_child, False)
        for right_step in right_seq:
            sb = first_part
            sb += left_seq[-1]
            sb += middle_part
            sb += right_step
            sb += last_part
            ret.append(sb)
        
        ret.append(str(node['eval']))
        return ret

#replaces the characters that we are not able display in the Treant.js generated tree
def to_html(text):
    text = text.replace("<=", " LESSER OR EQUAL THAN ")
    text = text.replace(">=", " GREATER OR EQUAL THAN ")
    text = text.replace("<", " LESSER THAN ")
    text = text.replace(">", " GREATER THAN ")
    text = text.replace("+", " PLUS ")
    return text.replace('\n', ';').replace('\t', '    ')

#generated the json-styled dictionary tree that the Treant.js module expects from an ast node
def node2treant(node, code, variables):
    kod_mtx = code.split('\n')
    tree = node2tree(node, kod_mtx, variables)
    treant = to_treant(tree)
    return treant

#generated the json-styled dictionary tree that the Treant.js module expects from a dictionary tree
def to_treant(node):
    #itt a sima node nem AST !

    ret = dict()
    ret['text'] = {'name': node['type']}
    if 'eval' in node:
        ret['text']['title'] = node['eval'] if node['eval'] else ''
    if 'code' in node:
        ret['text']['desc'] = to_html(node['code'])
    ret['children'] = [to_treant(child) for child in node['children']]
    return ret
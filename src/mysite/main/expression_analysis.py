import re
import copy
import ast

def get_type(node):
    return node.__class__.__name__
    
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
    
    elif get_type(node) in ("BinOp"):
        cp = copy.deepcopy(node)
        cp.left = eval_expr(cp.left, variables)
        cp.right = eval_expr(cp.right, variables)
        
        expr = ast.Expression(body=cp)
        ast.fix_missing_locations(expr)
        exe = compile(expr, filename="", mode="eval")
        return ast.Constant(eval(exe))
    
    elif get_type(node) in ("BoolOp"):
        cp = copy.deepcopy(node)
        for i in range(len(cp.values)):
            cp.values[i] = eval_expr(cp.values[i], variables)
        expr = ast.Expression(body=cp)
        ast.fix_missing_locations(expr)
        exe = compile(expr, filename="", mode="eval")
        return ast.Constant(eval(exe))
    
    elif get_type(node) in ("Compare"):
        cp = copy.deepcopy(node)
        cp.left = eval_expr(cp.left, variables)
        for i in range(len(cp.comparators)):
            cp.comparators[i] = eval_expr(cp.comparators[i], variables)
        expr = ast.Expression(body=cp)
        ast.fix_missing_locations(expr)
        exe = compile(expr, filename="", mode="eval")
        return ast.Constant(eval(exe))

def get_exprs(code):
    node = ast.parse(code)

    ret = []
    if node.__class__ in [ast.BinOp, ast.BoolOp, ast.Compare, ast.UnaryOp]:
        ret.append(node)
    else:
        for child in ast.iter_child_nodes(node):
            ret = ret + get_exprs(child)
    return ret

def node2seq(node, code, variables):
    kod_mtx = code.split('\n')
    tree = node2tree(node, kod_mtx, variables)
    seq = tree2seq(tree)
    return seq

def is_importing_node(node, source_code):
    kod_mtx = source_code.split('\n')
    tree = node2tree(node, kod_mtx, {}, skip_eval=True)
    return is_importing_tree(tree)

def is_importing_tree(tree):
    if tree['type'] == "Import":
        return True

    for child in tree['children']:
        if is_importing_tree(child):
            return True
    return False

def node2tree(node, kod_mtx, variables, skip_eval=False):
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
    

    if not skip_eval:
        if d['type'] in ("BinOp", "BoolOp", "Compare", "UnaryOp"):
            d['eval'] = eval_expr(node, variables).value
        elif d['type'] == "Name":
            #d['eval'] = eval_expr(variables[node.id], variables).value
            d['eval'] = eval_expr(node, variables).value        
        elif d['type'] == "Constant":
            d['eval'] = node.value
        else:
            d['eval'] = None
    '''
    if d['type'] == "Assign":
        targets = node.targets
        t = targets[0].id
        variables[t] = eval_expr(node.value)
        print(variables)
    '''
        
    
    d['children'] = [node2tree(child, kod_mtx, variables, skip_eval) for child in ast.iter_child_nodes(node)]
    return d

def tree2seq(node, start=True):
    if start:
        #print(node)
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
    elif node['type'] in ("BinOp", "BoolOp", "Compare"):
        
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

def to_html(text):
    text = text.replace("<=", " LESSER OR EQUAL THAN ")
    text = text.replace(">=", " GREATER OR EQUAL THAN ")
    text = text.replace("<", " LESSER THAN ")
    text = text.replace(">", " GREATER THAN ")
    text = text.replace("+", " PLUS ")
    return text.replace('\n', ';').replace('\t', '    ')

def node2treant(node, code, variables):
    kod_mtx = code.split('\n')
    tree = node2tree(node, kod_mtx, variables)
    treant = to_treant(tree)
    return treant

def to_treant(node):
    #kod_mtx = code.split('\n')
    #node = node2tree(ast_node, kod_mtx, variables)
    #itt a sima node nem AST !

    ret = dict()
    ret['text'] = {'name': node['type']}
    if 'eval' in node:
        ret['text']['title'] = node['eval'] if node['eval'] else ''
    if 'code' in node:
        ret['text']['desc'] = to_html(node['code'])
    ret['children'] = [to_treant(child) for child in node['children']]
    return ret
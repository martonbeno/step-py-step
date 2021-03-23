import sys
import re
import traceback

from helper import *

def normalize(s):
	ret = s
	ret = re.sub(r'\\r', '', ret)
	ret = re.sub(r'\\\\n', '\n', ret)
	# ret = re.sub(r'\\t', ' ', ret)
	return ret

try:
	code = normalize(sys.argv[1])
	
	code = code.replace(r'\n', '\n')
	tree = code2tree(code)
	treant = to_treant(tree)
	analysis = analyze(tree)
	ret = {
		'analysis': analysis,
		'treant': treant
	}
	print(json.dumps(ret))
	# print(json.dumps(treant))
except:
	traceback.print_exc()
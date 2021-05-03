var nodeStructure = JSON.parse('{"text": {"name": "Module", "desc": "a=8+9;b=0"}, "children": [{"text": {"name": "Assign", "desc": "a=8+9"}, "children": [{"text": {"name": "Name", "desc": "a"}, "children": [{"text": {"name": "Store"}, "children": []}]}, {"text": {"name": "BinOp", "desc": "8+9"}, "children": [{"text": {"name": "Constant", "desc": "8"}, "children": []}, {"text": {"name": "Add"}, "children": []}, {"text": {"name": "Constant", "desc": "9"}, "children": []}]}]}, {"text": {"name": "Assign", "desc": "b=0"}, "children": [{"text": {"name": "Name", "desc": "b"}, "children": [{"text": {"name": "Store"}, "children": []}]}, {"text": {"name": "Constant", "desc": "0"}, "children": []}]}]}');

var simple_chart_config = {
	chart: {
		container: "#OrganiseChart-simple"
	},
	
	nodeStructure: nodeStructure
};
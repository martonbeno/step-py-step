from django.shortcuts import render
from django.http import HttpResponse, HttpRequest

from .forms import CreateNewList
from .StepPyStep import StepPyStep

import json
import os

# Create your views here.

SPS_MODEL = None

#expects nodeStructure GET parameter, renders tree.html with the corresponding
#tree visualisation
def tree(request):
	try:
		nodeStructure = request.GET['nodeStructure']
	except KeyError:
		nodeStructure = "HIBA"
	
	return render(request, "main/tree.html", {'nodeStructure':nodeStructure})

#renders the home page
#if it gets a FILE message, it renders to the textarea
def home(request):
	print("create request", request)
	print(request.FILES)
	usercode = ''
	if 'usercode' in request.FILES:
		usercode = request.FILES['usercode'].file.read().decode('utf-8')

	#collecting demo codes
	path = os.path.realpath(__file__)	#..../spsSite/main/views.py
	path = os.path.dirname(path)		#..../spsSite/main/
	path = os.path.dirname(path)		#..../spsSite/
	examples_path = os.path.join(path, "examples")
	example_files = sorted(os.listdir(examples_path))

	print({'usercode': usercode, 'example_files': example_files})

	return render(request, "main/home.html", {'usercode': usercode, 'example_files': example_files})

#forwarding message to the backend
def api(request):
	command = request.POST['command']
	args = json.loads(request.POST['args'])

	print("api be", command, args)
	
	
	if command == "start":
		print("startolunk")
		global SPS_MODEL
		SPS_MODEL = StepPyStep()
		start_answer = SPS_MODEL.start(**args)
		print("S", start_answer)
		if start_answer['compile_success'] == True:
			get_answer = SPS_MODEL.request("get")
			ret = {**start_answer, **get_answer}
		else:
			ret = start_answer
	
	elif command == "step":
		ret = SPS_MODEL.request("step")

	elif command == "next":
		ret = SPS_MODEL.request("next")

	elif command == "newvar":
		msg = f"newvar {args['var_name']} {args['var_type'] if args['var_type'] else 'autocast'} {args['value']}"
		ret = SPS_MODEL.request(msg)

	elif command == "modify":
		msg = f"modify {args['var_name']} {args['value']}"
		ret = SPS_MODEL.request(msg)

	elif command == "delvar":
		msg = f"delvar {args['var_name']}"
		ret = SPS_MODEL.request(msg)

	elif command == "exit":
		SPS_MODEL.request("exit")
		ret = {'exit':'yes'}

	else:
		print(f"kommand:{command}")
	
	ret = json.dumps(ret)
	print("api response", ret)
	return HttpResponse(ret)
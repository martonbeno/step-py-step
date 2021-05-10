from django.shortcuts import render
from django.http import HttpResponse, HttpRequest

from .forms import CreateNewList
from .models import Szamlalo
from .StepPyStep import StepPyStep

import json
import os

# Create your views here.

SPS_MODEL = None

def index(response, id):
	return render(response, "main/base.html", {'name':str(id**2)})
	# return HttpResponse(f"<h1>{id}</h1>")
	
def home(response):
	return render(response, "main/home.html", {'name':'teszt'})
	# return HttpResponse("<h1>view1</h1>")

def tree(request):
	print(request.POST)
	try:
		nodeStructure = request.GET['nodeStructure']
	except KeyError:
		nodeStructure = "HIBA"
	
	return render(request, "main/tree.html", {'nodeStructure':nodeStructure})

def create(request):
	print("create request", request)
	print(request.FILES)
	usercode = ''
	if 'usercode' in request.FILES:
		usercode = request.FILES['usercode'].file.read().decode('utf-8')

	path = os.path.realpath(__file__)	#..../mysite/main/views.py
	path = os.path.dirname(path)		#..../mysite/main/
	path = os.path.dirname(path)		#..../mysite/
	examples_path = os.path.join(path, "examples")
	example_files = sorted(os.listdir(examples_path))

	print({'usercode': usercode, 'example_files': example_files})

	return render(request, "main/create.html", {'usercode': usercode, 'example_files': example_files})

def api(request):
	command = request.POST['command']
	args = json.loads(request.POST['args'])

	print("api be", command, args)
	
	
	if command == "start":
		global SPS_MODEL
		SPS_MODEL = StepPyStep()
		start_answer = SPS_MODEL.start(**args)
		get_answer = SPS_MODEL.request("get")
		ret = {**start_answer, **get_answer}
	
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
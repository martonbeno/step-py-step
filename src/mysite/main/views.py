from django.shortcuts import render
from django.http import HttpResponse, HttpRequest

from .forms import CreateNewList
from .models import Szamlalo
from .StepPyStep import StepPyStep

import json

# Create your views here.

SPS_MODEL = None

def index(response, id):
	return render(response, "main/base.html", {'name':str(id**2)})
	# return HttpResponse(f"<h1>{id}</h1>")
	
def home(response):
	return render(response, "main/home.html", {'name':'teszt'})
	# return HttpResponse("<h1>view1</h1>")

def tree(request):
	try:
		nodeStructure = request.GET['nodeStructure']
	except KeyError:
		nodeStructure = "HIBA"
	
	return render(request, "main/tree.html", {'nodeStructure':nodeStructure})

def create(response):
	form = CreateNewList()
	return render(response, "main/create.html", {'form':form})

def api(request):
	command = request.POST['command']
	args = json.loads(request.POST['args'])

	print(command, args)
	
	
	if command == "start":
		global SPS_MODEL
		SPS_MODEL = StepPyStep()
		ret = SPS_MODEL.start(**args)
	
	elif command == "step":
		SPS_MODEL.request("step")
		ret = SPS_MODEL.request("get")

	elif command == "next":
		SPS_MODEL.request("next")
		ret = SPS_MODEL.request("get")

	elif command == "modify":
		msg = f"modify {args['var_name']} {args['value']}"
		ret = SPS_MODEL.request(msg)

	elif command == "exit":
		SPS_MODEL.request("exit")
		ret = {'exit':'yes'}
	
	ret = json.dumps(ret)
	print(ret)
	return HttpResponse(ret)
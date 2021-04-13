from django.shortcuts import render
from django.http import HttpResponse, HttpRequest

from .forms import CreateNewList
from .models import Szamlalo
from .StepPyStep import StepPyStep

import json

# Create your views here.

SPS_MODEL = StepPyStep()

def index(response, id):
	return render(response, "main/base.html", {'name':str(id**2)})
	# return HttpResponse(f"<h1>{id}</h1>")
	
def home(response):
	return render(response, "main/home.html", {'name':'teszt'})
	# return HttpResponse("<h1>view1</h1>")

def create(response):
	form = CreateNewList()
	return render(response, "main/create.html", {'form':form})

def api(request):

	
	command = request.POST['command']
	args = json.loads(request.POST['args'])
	
	
	if command == "start":
		global SPS_MODEL

		try:
			SPS_MODEL.request("exit")
		except Exception:
			pass

		SPS_MODEL = StepPyStep()
		source_code = args['source_code']
		ret = SPS_MODEL.start(source_code)
	
	elif command == "step":
		SPS_MODEL.request("step")
		ret = SPS_MODEL.request("get")
		ret = json.dumps(ret)
		#print(ret)

	elif command == "exit":
		SPS_MODEL.request("exit")
		ret = json.dumps({'exit':'yes'})
	
	
	return HttpResponse(f"{ret}")
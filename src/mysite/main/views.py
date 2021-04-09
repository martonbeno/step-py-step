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
	# return HttpResponse("okézsoké")
	with open("ki.log", 'w+') as f:
		f.write("eddigjo0s\n")
		for k,v in request.POST.items():
			f.write(f"{k}: {v}\n")

	
		f.write("eddigjo111\n")
		command = request.POST['command']
		args = json.loads(request.POST['args'])
		
		
		if command == "start":
			source_code = args['source_code']
			ret = SPS_MODEL.start(source_code)
		
		elif command == "step":
			SPS_MODEL.request("step")
			ret = SPS_MODEL.request("get")
			ret = json.dumps(ret)
			print(ret)
	
	
	return HttpResponse(f"{ret}")

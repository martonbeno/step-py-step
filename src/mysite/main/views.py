from django.shortcuts import render
from django.http import HttpResponse, HttpRequest

from .forms import CreateNewList
from .models import Szamlalo

# Create your views here.

SZAMLALO = Szamlalo()

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
	with open("ki.log", 'w+') as f:
		for k,v in request.POST.items():
			f.write(f"{k} {v}\n")
	try:
		ret = int(request.POST['x']) % 2
		SZAMLALO.inc()
	except:
		ret = "nincsx"
	return HttpResponse(f"<p>{SZAMLALO.data} - {ret}<p>")
	# return HttpResponse("<p>" + str(ret) + "<p>")
from django.db import models
from .StepPyStep import StepPyStep

# Create your models here.


class Szamlalo:
	def __init__(self):
		self.data = 0
	def inc(self):
		self.data += 1

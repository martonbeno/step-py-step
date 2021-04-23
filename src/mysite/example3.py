class A:
	pass

a = A()
a.number = 5

b = A()
b.sibling = a

print(b.sibling.number)
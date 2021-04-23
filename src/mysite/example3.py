class A:
	pass

z = "ok"

a = A()
a.number = 5
a.text = z

b = A()
b.sibling = a

print(b.sibling.number)
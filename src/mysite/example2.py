def f(a, b, c):
	if a + b <= c:
		return False
	if a + c <= b:
		return False
	if b + c <= a:
		return False
	return True

a = 2.3
b = 5
c = 4

if f(a,b,c):
	answer = "triangle"
else:
	answer = "non triangle"

print(answer)
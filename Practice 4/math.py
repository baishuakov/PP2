#1
import math
x = math.pi
n = int(input())
print(n * x / 180)
#2
h = int(input())
b1 = int(input())
b2 = int(input())
print(((b1 + b2) / 2) * h)
#3
n = int(input())
a = int(input())
s = (a**2 * n) / (4 * math.tan(math.pi / n))
print(math.floor(s))
#4
b = int(input())
h = int(input())
print(b * h)
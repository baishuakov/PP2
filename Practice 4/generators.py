#1
def gen(n):
    for i in range(1, n + 1):
        yield i**2
square = gen(5)
for i in range(5):
    print(next(square))
#2
def evens(n):
    for i in range(0, n + 1):
        if i % 2 == 0:
            yield i
n = int(input())
even = evens(n)
print(list(even))
#3
def div(n):
    for i in range(0, n + 1):
        if i % 3 == 0 and i % 4 == 0:
            yield i
n = int(input())
divnum = div(n)
for i in divnum:
    print(i)
#4
def squares(a, b):
    for i in range(a, b + 1):
        yield i**2

ans = squares(2, 8)
for i in range(2, 9):
    print(next(ans))
#5
def dec(n):
    for i in range(n, -1, -1):
        yield i
n = int(input())
d = dec(n)
for i in range(n + 1):
    print(next(d))
    
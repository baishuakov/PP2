numbers = [1, 2, 3, 4, 5]
doubled = list(map(lambda x: x * 2, numbers))
print(doubled)

numbers = [1, 2, 3, 4, 5]
square = list(map(lambda x: x ** 2, numbers))
print(square)

a = list(map(lambda x: x.capitalize(), input().split()))
print(a)

a = list(map(lambda x: int(x) * 2, input().split()))
print(a)

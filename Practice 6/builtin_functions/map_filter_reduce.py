from functools import reduce

nums = [1, 2, 3, 4, 5]

a = list(map(lambda x: x**2, nums))
print(a)

b = list(filter(lambda x: x >= 3, nums))
print(b)

c = reduce(lambda a, b: a if a > b else b, nums)
print(c)




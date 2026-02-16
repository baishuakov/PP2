#A lambda function is a small anonymous function.
x = lambda a : a + 10
print(x(5))
#Lambda functions can take any number of arguments:
x = lambda a, b : a * b
print(x(2,3))

def myfunc(n):
    return lambda a : a * n
mydoubler = myfunc(2)
print(mydoubler(11))
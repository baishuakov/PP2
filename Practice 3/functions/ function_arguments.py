def my_function(fname):
    print(fname + " Refsnes")
my_function("Emil")
my_function("Tobias")
my_function("Linus")

def my_function(name): # name is a parameter
    print("Hello", name)
my_function("Emil") # "Emil" is an argument

def my_function(name = "friend"):
    print("Hello", name)
my_function("Emil")
my_function("Tobias")
my_function()
my_function("Linus")

def my_function(animal, name):
    print("I have a", animal)
    print("My", animal + "'s name is", name)
my_function(animal = "dog", name = "Buddy")

def my_function(name, /):
    print("Hello", name)
my_function("Emil")

def my_function(*, name):
    print("Hello", name)
my_function(name = "Emil")

def my_function(a, b, /, *, c, d):
    return a + b + c + d
result = my_function(5, 10, c = 15, d = 20)
print(result)
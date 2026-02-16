#If you do not know how many arguments will be passed into your function, add a * before the parameter name.
def my_function(*kids):
    print("The youngest child is " + kids[2])
my_function("Emil", "Tobias", "Linus")

def my_function(*args):#Accessing individual arguments from *args:
    print("Type:", type(args))
    print("First argument:", args[0])
    print("Second argument:", args[1])
    print("All arguments:", args)
my_function("Emil", "Tobias", "Linus")

def my_function(greeting, *names):
    for name in names:
     print(greeting, name)
my_function("Hello", "Emil", "Tobias", 123)

def my_function(**kid):
    print("His last name is " + kid["lname"])
my_function(fname = "Tobias", lname = "Refsnes")

def my_function(**myvar):
    print("Type:", type(myvar))
    print("Name:", myvar["name"])
    print("Age:", myvar["age"])
    print("All data:", myvar)
my_function(name = "Tobias", age = 30, city = "Bergen")

def my_function(title, *args, **kwargs):
    print("Title:", title)
    print("Positional arguments:", args)
    print("Keyword arguments:", kwargs)
my_function("User Info", "Emil", "Tobias", age = 25, city = "Oslo")
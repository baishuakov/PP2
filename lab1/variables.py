x = 10
y = "Leo Messi"
print(x)
print(y)

z = float(3) #will be 3.0

a = 11
A = "Neymar"
#A will not overwrite a

_x = 5

x, y, z = "Messi", "Suarez", "Neymar"
print(x)
print(y)
print(z)

x = "M "
y = "S "
z = "N"
print(x + y + z)

x = 'awesome'
def myfunc():
  global x
  x = 'fantastic'
myfunc()
print('Python is ' + x)

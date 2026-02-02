#You can evaluate any expression in Python, and get one of two answers, True or False.
print(10 > 9)
print(10 == 9)
print(10 < 9)

a = 200
b = 33
if b > a:
   print("b is greater than a")
else:
    print("b is not greater than a")

print(bool("Hello"))
print(bool(15))

#Almost any value is evaluated to True if it has some sort of content.
#Any number is True, except 0.
#empty values, such as (), [], {}, "", the number 0, and the value None. And of course the value False evaluates to False.

def myFunction() :
    return True
if myFunction():
    print("YES!")
else:
    print("NO!")

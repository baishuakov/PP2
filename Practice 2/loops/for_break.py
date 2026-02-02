fruits = ["apple", "banana", "cherry"]
for x in fruits:
    print(x)
    if x == "banana": #Exit the loop when x is "banana"
        break

fruits = ["apple", "banana", "cherry"]
for x in fruits:
    if x == "banana": #Exit the loop when x is "banana", but this time the break comes before the print
        break
    print(x)

n = int(input())
for i in range(0,n):
    x = int(input())
    if x < 0:
        print("negative number")
        break
    print(x)
else:
    print("Finally finished!") #this will not work, because of break in for

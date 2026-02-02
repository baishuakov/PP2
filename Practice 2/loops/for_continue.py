fruits = ["apple", "banana", "cherry"]
for x in fruits:
    if x == "banana": #skip banana
        continue
    print(x)

for i in range(10):
    if(i % 2 != 0):
        continue
    print(i) #print even numbers

for i in range(10):
    if i < 5: #skip numbers that smaller than 5
        continue
    print(i)
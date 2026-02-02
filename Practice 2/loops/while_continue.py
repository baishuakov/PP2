i = 0
while i < 6:
    i += 1
    if i == 3: #skip 3
        continue
    print(i)

i = 0
while i <= 6:
    i += 1
    if i % 2 == 0:
        continue
    print(i) #print only odd numbers

while 1 > 0:
    s = input("Enter your nickname:")
    if len(s) < 8:
        if s == "stop":
            break
        continue
    print("Good nickname!")

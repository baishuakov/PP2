i = 1
while i < 6: 
    print(i)
    if i == 3: #Exit the loop when i is 3:
        break
    i += 1

x = 1
while True: #printing number from 1 to 4
    print(x)
    x += 1
    if(x == 5):
        break
else: #this else will not work
    print("i is no longer less than 6") #Print a message once the condition is false

while True:
    password = input("Enter password: ")
    if password == "1234":
        print("Access granted")
        break
  


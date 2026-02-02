a = 5
b = 2
if a > b: print("a is greater than b")

a = 2
b = 330
print("A") if a > b else print("B")

a = 10
b = 20
bigger = a if a > b else b
print("Bigger is", bigger)

a = 330
b = 330
print("A") if a > b else print("=") if a == b else print("B")

x = 15
y = 10
maxn = x if x > y else y
print(maxn)

username = ""
display_name = username if username else "Guest"
print("Welcome,", display_name)

temperature = 25
is_raining = False
is_weekend = True
if (temperature > 20 and not is_raining) or is_weekend:
    print("Great day for outdoor activities!")

username = "Tobias"
password = "secret123"
is_verified = True
if username and password and is_verified:
    print("Login successful")
else:
    print("Login failed")

score = 85
if score >= 0 and score <= 100:
    print("Valid score")
else:
    print("Invalid score")
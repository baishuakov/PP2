a = 33
b = 200
if b > a:
    print("b is greater than a")
#If the condition is true, the code block inside the if statement is executed.

number = 15
if number > 0:
    print("The number is positive")

#If statement, without indentation (will raise an error)

age = 20
if age >= 18:
    print("You are an adult")
    print("You can vote")
    print("You have full legal rights")

is_logged_in = True
if is_logged_in:
    print("Welcome back!")

a = 33
b = 200
if b > a:
  pass #if statements cannot be empty,put in the pass statement to avoid getting an error.

age = 16
if age < 18:
    pass
else:
    print("Access granted")

score = 85
if score > 90:
    pass # This is excellent
print("Score processed")
#The else keyword catches anything which isn't caught by the preceding conditions.

a = 200
b = 33
if b > a:
    print("b is greater than a")
elif a == b:
    print("a and b are equal")
else:
    print("a is greater than b")

a = 200
b = 33
if b > a:
    print("b is greater than a")
else:
    print("b is not greater than a")

temperature = 22
if temperature > 30:
    print("It's hot outside!")
elif temperature > 20:
    print("It's warm outside")
elif temperature > 10:
    print("It's cool outside")
else:
    print("It's cold outside!")

#You can have as many elif statements as you need. Python will check each condition in order and execute the first one that is true.

score = 75
if score >= 90:
    print("Grade: A")
elif score >= 80:
    print("Grade: B")
elif score >= 70:
    print("Grade: C")
elif score >= 60:
    print("Grade: D")

age = 25
if age < 13:
    print("You are a child")
elif age < 20:
    print("You are a teenager")
elif age < 65:
    print("You are an adult")
elif age >= 65:
    print("You are a senior")

day = 3 #Use elif when you have multiple mutually exclusive conditions to check
if day == 1:
  print("Monday")
elif day == 2:
  print("Tuesday")
elif day == 3:
  print("Wednesday")
elif day == 4:
  print("Thursday")
elif day == 5:
  print("Friday")
elif day == 6:
  print("Saturday")
elif day == 7:
  print("Sunday")

x = 41
if x > 10:
    print("Above ten,")
    if x > 20:
        print("and also above 20!")
    else:
        print("but not above 20.")

age = 25
has_license = True
if age >= 18:
    if has_license:
        print("You can drive")
    else:
        print("You need a license")
else:
    print("You are too young to drive")
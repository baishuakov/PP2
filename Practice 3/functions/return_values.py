def fahrenheit_to_celsius(fahrenheit):
    return (fahrenheit - 32) * 5 / 9
print(fahrenheit_to_celsius(77))
print(fahrenheit_to_celsius(95))
print(fahrenheit_to_celsius(50))

def my_function(x, y):
    return x + y
result = my_function(5, 3)
print(result)

def my_function():
    return ["apple", "banana", "cherry"]
fruits = my_function()
print(fruits[0])
print(fruits[1])
print(fruits[2])

def get_greeting():
    return "Hello from a function"
message = get_greeting()
print(message)


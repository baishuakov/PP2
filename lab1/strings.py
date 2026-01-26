print('He is called "Johnny"')

a = """Lorem ipsum dolor sit amet,
consectetur adipiscing elit,
sed do eiusmod tempor incididunt
ut labore et dolore magna aliqua."""
print(a) #You can assign a multiline string to a variable by using three quotes:

a = "MSN are the best trio ever"
print(len(a))#print length of string

txt = "The best things in life are free!"
print("free" in txt)#check  if "free" is present in the following text, and it gives True or False

b = "Hello, World!"
print(b[2:5])#Slicing 2 is start, 5 is finish not included, third is step

#a.upper(), a.lower(), a.strip() removes any whitespace from the beginning or the end
#a.replace() replaces a string with another string, a.split() do list with string

a = "Hello"
b = "World"
c = a + " " + b
print(c)

age = 18
s = f"My name is Magzham, I am {age}"
print(s)

#price:.2f (Display the price with 2 decimals:), price.00

txt = "We are the so-called \"Vikings\" from the north."
#txt = "We are the so-called "Vikings" from the north." it is wrong


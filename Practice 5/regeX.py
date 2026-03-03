import re
#1
text = input()
x = re.search('a*b*', text)
print(x)
#2
text = input()
x = re.search('abb|abbb', text)
print(x)
#3
text = input()
x = re.findall('[a-z]*_', text)
print(x)
#4
text = input()
x = re.findall('[A-Z][a-z]+', text)
print(x)
#5
text = input()
x = re.findall('^.*a.*b$', text)
print(x)
#6
text = input()
x = re.sub("[.]|[,]|[ ]", ":", text)
print(x)
#7
def snake_camel(s):
    res = ''
    res += (s.group(1)).upper()
    return res
str = input()
camel = re.sub(r'(_[a-z])', snake_camel, str)
camel = camel.replace('_', '')
print(camel)
#8
text = input()
x = re.split('[A-Z]', text)
print(x)
#9
def space(x):
    return ' '.join(re.findall('[A-Z][a-z]*', x))
x = input()
y = space(x)
print(y)  
#10
def com(s):
    res = ''
    if s.group(1):
        res += (s.group(1)).lower()
    else:
        res += ('_' + s.group(2)).lower()
    return res
s = input()
snake = re.sub(r'(^[A-Z]| [A-Z])|([A-Z])', com, s) 
print(snake)

#1
import datetime
x = datetime.datetime.now()
a = x - datetime.timedelta(days = 5) 
print(a)
#2
x = datetime.datetime.now()
print(x - datetime.timedelta(days = 1), x, x + datetime.timedelta(days = 1))
#3
print(x.replace(microsecond=0))
#4
date1 = datetime.datetime((2025, 10, 10, 14, 13, 59))
date2 = datetime.datetime((2007, 7, 7, 10, 10, 32))
dif = (date1 - date2).total_seconds()
print(dif)

numbers = [1, 2, 3, 4, 5, 6, 7, 8]
odd_numbers = list(filter(lambda x: x % 2 != 0, numbers))
print(odd_numbers)

numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9]
bigger_than_5 = list(filter(lambda x: x > 5, numbers))
print(bigger_than_5)

positive = list(filter(lambda x: int(x) > 0, input().split()))
print(positive)

import math
square = list(filter(lambda x: math.sqrt(x)**2 == x, numbers))
print(square)
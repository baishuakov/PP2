Name = ["Messi", "Suarez", "Neymar", "Xavi", "Iniesta", "CR7"]
Ballon_dors = [8, 0, 0, 0, 0, 5]
for index, name in enumerate(Name):
    print(f"{index + 1}. {name}")
for name, number in zip(Name, Ballon_dors):
    print(f"{name} has {number} Ballon_dors")

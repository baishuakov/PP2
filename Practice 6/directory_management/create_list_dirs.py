import os
print(os.getcwd())

path = "practice/apple/orange"
os.makedirs(path, exist_ok=True)

items = os.listdir('.')
print(items)

python_files = [f for f in items if f.endswith(".py")]
print(python_files)
#python3 create_list_dirs.py

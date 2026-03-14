import shutil
import os

os.makedirs("practice", exist_ok=True)
shutil.copytree("practice", "practice_copy")

shutil.move("practice", "final_practice")
#python3 move_files.py
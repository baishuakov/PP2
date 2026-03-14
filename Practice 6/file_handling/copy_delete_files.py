import shutil
import os

source = "demofile.txt" 
destination = "copy_of_demo.txt" 
shutil.copy(source, destination)

if os.path.exists("demofile.txt"):
  os.remove("demofile.txt")
else:
  print("The file does not exist")

#os.rmdir("myfolder")# You can only remove empty folders.
import os

files = [f for f in os.listdir('.') if os.path.isfile(f)]
print(files)

import os

dirs = [d for d in os.listdir('.') if os.path.isdir(d)]
print(dirs)

import os

if __name__ == "__main__":
    dirs = [d for d in os.listdir('.') if os.path.isdir(d)]
    print(dirs)

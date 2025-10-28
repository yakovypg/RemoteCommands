import os

if __name__ == "__main__":
    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    print(files)

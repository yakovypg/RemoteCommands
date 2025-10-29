import argparse
import winsound

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--path', type=str, required=True, help='path to the file')

    args = parser.parse_args()
    path = args.path

    winsound.PlaySound(path, winsound.SND_FILENAME)

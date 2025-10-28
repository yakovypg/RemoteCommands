import argparse
import shlex
import subprocess

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('-s', '--shortcut_name', type=str, required=True, help='shortcut name')
    parser.add_argument('-i', '--icon_name', type=str, required=True, help='shortcut icon name')
    parser.add_argument('-l', '--link', type=str, required=True, help='shortcut link')
    parser.add_argument('-c', '--shortcuts_count', type=int, default=10, help='number of shortcuts (default: 10)')
    parser.add_argument('-p', '--create_shortcut_script_path', type=str, default='bat-create-shortcut.bat', help='path to the script for creating shortcut (default: bat-create-shortcut.bat)')

    args = parser.parse_args()

    shortcut_name = args.shortcut_name
    icon_name = args.icon_name
    link = args.link
    create_shortcut_script_path = args.create_shortcut_script_path
    shortcuts_count = args.shortcuts_count

    for i in range(shortcuts_count):
        cmd = f'{create_shortcut_script_path} "{shortcut_name}{i}" "{icon_name}" "{link}"'
        args = shlex.split(cmd)

        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()

        print(f'create shortcut {i} script stdout:', stdout)
        print(f'create shortcut {i} script stderr:', stderr)

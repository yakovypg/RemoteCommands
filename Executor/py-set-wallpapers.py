import argparse
import shlex
import subprocess
import time

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('-n', '--image_names', nargs='+', required=True, help='image names')
    parser.add_argument('-i', '--min_interval_ms', type=int, default=1000, help='minimum interval between setting wallpapers in milliseconds (default: 1000)')
    parser.add_argument('-s', '--style', type=int, default=10, help='style of wallpaper: 0=center, 2=stretch, 6=fill, 10=fit, 22=tile (default: 10)')
    parser.add_argument('-p', '--set_wallpaper_script_path', type=str, default='bat-set-wallpaper.bat', help='path to the script for setting wallpaper (default: bat-set-wallpaper.bat)')

    args = parser.parse_args()

    image_names = args.image_names
    min_interval_ms = args.min_interval_ms
    style = args.style
    set_wallpaper_script_path = args.set_wallpaper_script_path

    for i in range(len(image_names)):
        start_time = time.time()
        image_name = image_names[i]

        cmd = f'{set_wallpaper_script_path} "{image_name}" "{style}"'
        args = shlex.split(cmd)

        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()

        print(f'set wallpaper {i} script stdout:', stdout)
        print(f'set wallpaper {i} script stderr:', stderr)

        elapsed_time_ms = (time.time() - start_time) * 1000
        remaining_time_ms = min_interval_ms - elapsed_time_ms

        if (remaining_time_ms > 0) and (i < len(image_names) - 1):
            time.sleep(remaining_time_ms / 1000.0)

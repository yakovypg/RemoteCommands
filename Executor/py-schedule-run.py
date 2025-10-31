import argparse
import subprocess
import sys
import time

from datetime import datetime, timedelta
from pathlib import Path

def parse_time_string(time_string):
    time_string = time_string.strip()

    try:
        return datetime.strptime(time_string, "%Y-%m-%d %H:%M")
    except ValueError:
        pass

    try:
        parsed_time = datetime.strptime(time_string, "%H:%M").time()
        now = datetime.now()
        date_time = datetime.combine(now.date(), parsed_time)

        if date_time <= now:
            date_time = date_time + timedelta(days=1)

        return date_time
    except ValueError:
        raise ValueError(f"unsupported time format: {time_string!r}. Use 'HH:MM' or 'YYYY-MM-DD HH:MM'")

def pair_paths_times(paths, times):
    if len(paths) != len(times):
        raise ValueError("the number of paths and times must be equal")

    pairs = []

    for path_str, time_string in zip(paths, times):
        path = Path(path_str).expanduser()

        if not path.exists():
            raise FileNotFoundError(f"{path} not found")

        date_time = parse_time_string(time_string)
        pairs.append((path, date_time))

    pairs.sort(key=lambda x: x[1])

    return pairs

def wait_until(target: datetime):
    while True:
        now = datetime.now()
        diff = (target - now).total_seconds()

        if diff <= 0:
            return

        time.sleep(min(diff, 60))

def run_script(path: Path):
    args = [sys.executable] + [str(path)]
    print(f"starting: {path}")

    try:
        subprocess.Popen(args, shell=False)
        print(f"finished: {path}")
    except Exception as e:
        print(f"failed to run {path}: {e}")

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-p', '--paths', nargs='+', type=str, required=True, help='paths to python scripts (same count as --times)')
    parser.add_argument('-t', '--times', nargs='+', type=str, required=True, help="times to start scripts. Format 'HH:MM' (today or tomorrow) or 'YYYY-MM-DD HH:MM'")

    args = parser.parse_args()

    try:
        schedule = pair_paths_times(args.paths, args.times)
    except Exception as e:
        print("error:", e)
        return

    for path, run_at in schedule:
        now = datetime.now()

        if run_at <= now:
            print(f"time {run_at.isoformat()} already passed, starting immediately: {path}")
            run_script(path)
            continue

        print(f"waiting until {run_at.isoformat()} to run {path}")

        wait_until(run_at)
        run_script(path)

    print(f"all scheduled scripts processed")

if __name__ == "__main__":
    main()

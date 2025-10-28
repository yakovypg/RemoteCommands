import argparse
import ctypes
import time

INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.c_void_p),
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("mi", MOUSEINPUT),
    ]

SendInput = ctypes.windll.user32.SendInput
GetSystemMetrics = ctypes.windll.user32.GetSystemMetrics

SM_CXSCREEN = 0
SM_CYSCREEN = 1

def _to_absolute(x, y):
    sx = GetSystemMetrics(SM_CXSCREEN)
    sy = GetSystemMetrics(SM_CYSCREEN)

    ax = int(x * 65535 / max(sx - 1, 1))
    ay = int(y * 65535 / max(sy - 1, 1))

    return ax, ay

def send_mouse_input(dx, dy, flags):
    mi = MOUSEINPUT(dx, dy, 0, flags, 0, None)
    inp = INPUT(INPUT_MOUSE, mi)
    SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

def mouse_event_move_abs(x, y):
    ax, ay = _to_absolute(x, y)
    send_mouse_input(ax, ay, MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE)

def mouse_left_down():
    send_mouse_input(0, 0, MOUSEEVENTF_LEFTDOWN)

def mouse_left_up():
    send_mouse_input(0, 0, MOUSEEVENTF_LEFTUP)

def double_click(interval_between_clicks_ms):
    mouse_left_down()
    mouse_left_up()
    time.sleep(interval_between_clicks_ms / 1000.0)

    mouse_left_down()
    mouse_left_up()

def double_click_at(x, y, interval_after_move_ms, interval_between_clicks_ms):
    mouse_event_move_abs(x, y)
    time.sleep(interval_after_move_ms / 1000.0)

    double_click(interval_between_clicks_ms)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('-x', '--x', type=int, required=True, help='x coordinate')
    parser.add_argument('-y', '--y', type=int, required=True, help='y coordinate')
    parser.add_argument('-a', '--interval_after_move_ms', type=float, default=0.01, help='interval after moving cursor in milliseconds (default: 0.01)')
    parser.add_argument('-b', '--interval_between_clicks_ms', type=float, default=0.05, help='interval between clicks in milliseconds (default: 0.05)')

    args = parser.parse_args()

    x = args.x
    y = args.y
    interval_after_move_ms = args.interval_after_move_ms
    interval_between_clicks_ms = args.interval_between_clicks_ms

    double_click_at(x, y, interval_after_move_ms, interval_between_clicks_ms)

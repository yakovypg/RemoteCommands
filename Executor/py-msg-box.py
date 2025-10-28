import argparse
import ctypes
import subprocess

from ctypes import wintypes

user32 = ctypes.WinDLL('user32', use_last_error=True)
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

WM_CREATE = 0x0001
WM_COMMAND = 0x0111
WM_DESTROY = 0x0002
WM_CLOSE = 0x0010

WS_VISIBLE = 0x10000000
WS_CHILD = 0x40000000
WS_POPUP = 0x80000000
WS_BORDER = 0x00800000

BS_PUSHBUTTON = 0x00000000

ID_BTN_YES = 1001
ID_BTN_NO = 1002
ID_BTN_DK = 1003

WNDPROCTYPE = ctypes.WINFUNCTYPE(ctypes.c_long, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

class WNDCLASS(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROCTYPE),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HANDLE),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]

user32.DefWindowProcW.restype = ctypes.c_long
user32.DefWindowProcW.argtypes = (wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

user32.CreateWindowExW.restype = wintypes.HWND
user32.CreateWindowExW.argtypes = (wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR,
                                   wintypes.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                   wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID)

user32.RegisterClassW.restype = wintypes.ATOM
user32.RegisterClassW.argtypes = (ctypes.POINTER(WNDCLASS),)

user32.GetMessageW.argtypes = (ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT)
user32.GetMessageW.restype = wintypes.BOOL

hInstance = kernel32.GetModuleHandleW(None)
result_box = None

message = ""
btn_yes_text = ""
btn_no_text = ""
btn_dk_text = ""

@WNDPROCTYPE
def wnd_proc(hWnd, msg, wParam, lParam):
    global result_box

    if msg == WM_CREATE:
        user32.CreateWindowExW(0, "STATIC", message, WS_CHILD | WS_VISIBLE,
                               20, 20, 300, 20, hWnd, None, hInstance, None)
        user32.CreateWindowExW(0, "BUTTON", btn_yes_text, WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
                               20, 60, 80, 30, hWnd, wintypes.HMENU(ID_BTN_YES), hInstance, None)
        user32.CreateWindowExW(0, "BUTTON", btn_no_text, WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
                               110, 60, 80, 30, hWnd, wintypes.HMENU(ID_BTN_NO), hInstance, None)
        user32.CreateWindowExW(0, "BUTTON", btn_dk_text, WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
                               200, 60, 100, 30, hWnd, wintypes.HMENU(ID_BTN_DK), hInstance, None)
        return 0
    elif msg == WM_COMMAND:
        btn_id = wParam & 0xffff
        if btn_id == ID_BTN_YES:
            result_box = "yes"
            user32.DestroyWindow(hWnd)
        elif btn_id == ID_BTN_NO:
            result_box = "no"
            user32.DestroyWindow(hWnd)
        elif btn_id == ID_BTN_DK:
            result_box = "dontknow"
            user32.DestroyWindow(hWnd)
        return 0
    elif msg == WM_CLOSE:
        return 0
    elif msg == WM_DESTROY:
        user32.PostQuitMessage(0)
        return 0
    return user32.DefWindowProcW(hWnd, msg, wParam, lParam)

def message_box_custom():
    global result_box

    className = "MyMsgBoxClass_final"
    wndclass = WNDCLASS()
    wndclass.style = 0
    wndclass.lpfnWndProc = wnd_proc
    wndclass.cbClsExtra = wndclass.cbWndExtra = 0
    wndclass.hInstance = hInstance
    wndclass.hIcon = user32.LoadIconW(None, ctypes.c_wchar_p(32512))
    wndclass.hCursor = user32.LoadCursorW(None, ctypes.c_wchar_p(32512))
    wndclass.hbrBackground = ctypes.c_void_p(6)
    wndclass.lpszMenuName = None
    wndclass.lpszClassName = className

    try:
        user32.RegisterClassW(ctypes.byref(wndclass))
    except Exception:
        pass

    width = 330
    height = 120

    screen_w = user32.GetSystemMetrics(0)
    screen_h = user32.GetSystemMetrics(1)

    x = int((screen_w - width) / 2)
    y = int((screen_h - height) / 2)

    style = WS_POPUP | WS_BORDER | WS_VISIBLE

    hWnd = user32.CreateWindowExW(
        0,
        className,
        "TitleIsHidden",
        style,
        x, y, width, height,
        None, None, hInstance, None
    )

    if not hWnd:
        print("failed to open window:", ctypes.get_last_error())
        return None

    user32.ShowWindow(hWnd, 1)
    user32.SetForegroundWindow(hWnd)

    msg = wintypes.MSG()

    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))

    return result_box

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('-m', '--message', type=str, required=True, help='message')
    parser.add_argument('-y', '--btn_yes_text', type=str, required=True, help='text of button \'yes\'')
    parser.add_argument('-n', '--btn_no_text', type=str, required=True, help='text of button \'no\'')
    parser.add_argument('-d', '--btn_dk_text', type=str, required=True, help='text of button \'don\'t know\'')
    parser.add_argument('-p', '--pass_answer', action='store_true', default=True, help='pass answer from message box to process (default: True)')
    parser.add_argument('-a', '--process_args', nargs='*', default=None, help='arguments for starting new process (default: None)')

    args = parser.parse_args()

    message = args.message
    btn_yes_text = args.btn_yes_text
    btn_no_text = args.btn_no_text
    btn_dk_text = args.btn_dk_text
    process_args = args.process_args
    pass_answer = args.pass_answer

    res = message_box_custom()
    print("selected:", res)

    if process_args is not None and len(process_args) > 0:
        if pass_answer:
            process_args.append(res)

        process = subprocess.Popen(process_args)
        stdout, stderr = process.communicate()

        print('new process stdout:', stdout)
        print('new process stderr:', stderr)
    else:
        print('process not specified')

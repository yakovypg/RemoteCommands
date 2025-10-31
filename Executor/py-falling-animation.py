import argparse
import ctypes
import pygame
import random
import sys
import time

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--image_path', type=str, required=True, help='path to the image')
    parser.add_argument('-W', '--screen_width', type=int, default=1920, help='screen width (default: 1920)')
    parser.add_argument('-H', '--screen_height', type=int, default=1080, help='screen height (default: 1080)')

    parser.add_argument(
        '-c', '--falling_items_count', type=int, default=30,
        help='number of falling items (default: 30)'
    )

    parser.add_argument(
        '-t', '--animation_time_ms', type=int, default=10000,
        help='animation time in milliseconds (default: 10000)'
    )

    parser.add_argument('--resized_image_width', type=int, default=50, help='resized image width (default: 50)')
    parser.add_argument('--resized_image_height', type=int, default=30, help='resized image height (default: 30)')
    parser.add_argument('--fps', type=int, default=60, help='frames per second (default: 60)')

    args = parser.parse_args()

    image_path = args.image_path
    screen_width = args.screen_width
    screen_height = args.screen_height
    falling_items_count = args.falling_items_count
    animation_time_ms = args.animation_time_ms
    resized_image_width = args.resized_image_width
    resized_image_height = args.resized_image_height
    fps = args.fps

    screen_size = (screen_width, screen_height)
    resized_image_size = (resized_image_width, resized_image_height)

    pygame.init()
    os_env = pygame.display.set_mode(screen_size, pygame.NOFRAME)
    pygame.display.set_caption("Caption")

    falling_item_image = pygame.image.load(image_path).convert_alpha()
    falling_item_image = pygame.transform.scale(falling_item_image, resized_image_size)

    class FallingItem:
        def __init__(self):
            self.x = random.randint(0, screen_width - 50)
            self.y = random.randint(-300, -30)
            self.speed = random.uniform(1.5, 4.0)
            self.rot = random.uniform(-3, 3)
            self.image = falling_item_image

        def fall(self):
            self.y += self.speed
            self.x += random.uniform(-1, 1)

            if self.y > screen_height + 50:
                self.__init__()

    falling_items_list = [FallingItem() for _ in range(falling_items_count)]
    clock = pygame.time.Clock()

    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    ws_ex_layered = 0x00080000
    ws_ex_transparent = 0x00000020
    hwnd = pygame.display.get_wm_info()["window"]
    current_style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
    new_style = current_style | ws_ex_layered | ws_ex_transparent

    ctypes.windll.user32.SetWindowLongW(hwnd, -20, new_style)

    LWA_COLORKEY = 0x00000001
    transparent_color = (0, 0, 0)
    cr_key = (transparent_color[2] << 16) | (transparent_color[1] << 8) | transparent_color[0]

    ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, cr_key, 255, LWA_COLORKEY)

    HWND_TOPMOST = -1
    SWP_NOMOVE = 0x0002
    SWP_NOSIZE = 0x0001
    SWP_SHOWWINDOW = 0x0040

    ctypes.windll.user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)

    start_time = time.time()

    while True:
        curr_time = time.time()
        spent_time_ms = (curr_time - start_time) * 1000

        if spent_time_ms >= animation_time_ms:
            break

        screen = pygame.display.get_surface()
        screen.fill((0, 0, 0))

        for item in falling_items_list:
            item.fall()
            screen.blit(item.image, (item.x, item.y))

        pygame.display.update()
        clock.tick(fps)

    pygame.quit()
    sys.exit()

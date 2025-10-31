import argparse
import pygame
import sys
import time

from pathlib import Path

TIME_COMPARE_INTERVAL_SEC = 0.1

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--image', type=str, required=True, help="path to image")
    parser.add_argument('-s', '--sound', type=str, required=True, help="path to sound")
    parser.add_argument('-d', '--duration_ms', type=int, default=4000, help="showing duration in milliseconds (default: 4000)")

    return parser.parse_args()

def main():
    args = parse_args()

    img_path = Path(args.image).expanduser()
    snd_path = Path(args.sound).expanduser()
    duration_ms = float(args.duration_ms)

    if not img_path.exists():
        print(f"error: image not found: {img_path}", file=sys.stderr)
        sys.exit(2)

    if not snd_path.exists():
        print(f"error: sound not found: {snd_path}", file=sys.stderr)
        sys.exit(3)

    if duration_ms <= 0:
        print("error: duration must be positive", file=sys.stderr)
        sys.exit(4)

    pygame.init()

    try:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

        scary_image = pygame.image.load(str(img_path))
        scary_sound = pygame.mixer.Sound(str(snd_path))

        screen_rect = screen.get_rect()
        img_rect = scary_image.get_rect()

        scale_w = screen_rect.width / img_rect.width
        scale_h = screen_rect.height / img_rect.height
        scale = max(scale_w, scale_h)

        new_size = (int(img_rect.width * scale), int(img_rect.height * scale))
        scary_image = pygame.transform.smoothscale(scary_image, new_size)
        image_pos = ((screen_rect.width - new_size[0]) // 2, (screen_rect.height - new_size[1]) // 2)

        scary_sound.play()
        screen.blit(scary_image, image_pos)
        pygame.display.flip()

        start_time = time.time()

        while True:
            curr_time = time.time()
            elapsed_ms = (curr_time - start_time) * 1000

            if elapsed_ms >= duration_ms:
                break

            time.sleep(TIME_COMPARE_INTERVAL_SEC)
    finally:
        pygame.mixer.stop()
        pygame.quit()

if __name__ == '__main__':
    main()

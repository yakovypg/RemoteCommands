import argparse
import time

from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-d', '--duration_ms', type=int, default=4000,
        help='disabling duration in milliseconds (default: 4000)'
    )

    args = parser.parse_args()
    duration_ms = args.duration_ms

    devices = AudioUtilities.GetSpeakers()
    volume = devices.EndpointVolume.QueryInterface(IAudioEndpointVolume)

    volume.SetMute(1, None)
    time.sleep(duration_ms / 1000.0)
    volume.SetMute(0, None)

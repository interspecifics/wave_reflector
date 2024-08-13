import socket
import sys
import argparse
import asyncio
import pygame
import signal
from collections import deque

# Channel names and order
channels = ["F3", "FC5", "AF3", "F7", "T7", "P7", "O1", "O2", "P8", "T8", "F8", "AF4", "FC6", "F4"]

# Signal handler for graceful exit
def signal_handler(sig, frame):
    print('Exiting...')
    sys.exit(0)

async def main(host, port, buffer_size, sample_rate):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        client_socket.bind((host, port))
        print(f"Listening for data on {host}:{port}")

        # Initialize buffers for each channel using deque for efficient pops from the left
        buffers = {channel: deque(maxlen=buffer_size) for channel in channels}
        line_count = 0

        pygame.init()
        width, height = 800, 600
        plot_screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption('EEG Progression')

        buffer = ""
        while True:
            data, _ = client_socket.recvfrom(4096)
            if not data:
                break

            buffer += data.decode()
            lines = buffer.split('\n')
            buffer = lines.pop()  # Keep the last incomplete line in the buffer

            for line in lines:
                line = line.strip()
                try:
                    values = list(map(float, line.split(',')))
                except ValueError:
                    continue

                # Update buffers
                for i, channel in enumerate(channels):
                    buffers[channel].append(values[i])

                line_count += 1

                # Plot the data
                plot_screen.fill((0, 0, 0))  # Clear the screen with black

                for i, channel in enumerate(channels):
                    data = list(buffers[channel])
                    if len(data) > 1:
                        # Fixed y-range 
                        range_l, range_h = 4000, 4500
                        scaled_data = [(val - range_l) / (range_h - range_l) * (height // len(channels)) for val in data]
                        points = [(x, height // len(channels) * i + y) for x, y in enumerate(scaled_data)]
                        pygame.draw.lines(plot_screen, (0, 255, 0), False, points)

                pygame.display.flip()

            # Handle pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

    except socket.error as e:
        print(f"Connection error: {e}")
    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        client_socket.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='EEG Analysis Plot.')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host IP address to connect to')
    parser.add_argument('--port', type=int, default=9002, help='UDP port number to connect to')
    parser.add_argument('--buffer_size', type=int, default=512, help='Buffer size for each channel')
    parser.add_argument('--sample_rate', type=int, default=128, help='Sample rate in Hz (default: 128 Hz)')

    args = parser.parse_args()

    signal.signal(signal.SIGINT, signal_handler)

    asyncio.run(main(args.host, args.port, args.buffer_size, args.sample_rate))
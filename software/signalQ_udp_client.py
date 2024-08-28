import socket
import sys
import signal
import argparse
import numpy as np
from collections import deque
import asyncio
import pygame

# Channel names and order
channels = ["F3", "FC5", "AF3", "F7", "T7", "P7", "O1", "O2", "P8", "T8", "F8", "AF4", "FC6", "F4"]
electrode_positions = {
    'AF3': (-0.6, 0.90), 'F7': (-0.97, 0.5), 'F3': (-0.3, 0.55), 'FC5': (-0.75, 0.25), 'T7': (-1.1, -0.1), 'P7': (-0.75, -0.9),
    'O1': (-0.35, -1.30), 'O2': (0.32, -1.30), 'P8': (0.75, -0.9), 'T8': (1.1, -0.1), 'FC6': (0.75, 0.25), 'F4': (0.3, 0.55),
    'F8': (0.97, 0.5), 'AF4': (0.6, 0.90)
}

# Signal handler for graceful exit
def signal_handler(sig, frame):
    print('Exiting...')
    sys.exit(0)

async def calculate_variance(buffers, line_count):
    variances = {channel: np.var(buffers[channel]) for channel in channels}
    return variances

def draw_gridlines(screen, width, height):
    for i in range(0, width, int(width / 10)):
        pygame.draw.line(screen, (255, 255, 255), (i, 0), (i, height), 1)
    for j in range(0, height, int(height / 10)):
        pygame.draw.line(screen, (255, 255, 255), (0, j), (width, j), 1)

def visualize_signal_quality(variances, screen, width, height, background_image):
    background_image.set_alpha(128)  # Set alpha value for transparency
    screen.blit(background_image, (0, 0))  # Draw the background image
    # draw_gridlines(screen, width, height)  # Draw gridlines
    for ch, pos in electrode_positions.items():
        x = int((pos[0] + 1.5) / 3 * width)
        y = int((1.5 - pos[1]) / 3 * height)
        variance = variances.get(ch, 0)
        color = (0, 255, 0) if variance < 500 else (255, 0, 0)  # Green if good, red if bad
        pygame.draw.circle(screen, color, (x, y), 30)  # Draw a circle with the status color

    pygame.display.flip()

async def main(host, port, buffer_size, sample_rate, image_path):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        client_socket.bind((host, port))
        print(f"Listening for data on {host}:{port}")

        # Initialize buffers for each channel using deque for efficient pops from the left
        buffers = {channel: deque(maxlen=buffer_size) for channel in channels}
        line_count = 0

        pygame.init()
        width, height = 600, 600
        # screen = pygame.display.set_mode((width, height), pygame.NOFRAME)  # No frame for no icon
        screen = pygame.display.set_mode((width, height))  # No frame for no icon
        pygame.display.set_caption('Signal Quality Visualization')

        # Load the background image
        background_image = pygame.image.load(image_path)
        background_image = pygame.transform.scale(background_image, (width, height))

        buffer = ""
        while True:
            data, _ = client_socket.recvfrom(1024)
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
                    print(f"Skipping non-numeric line: {line}")
                    continue

                # Update buffers
                for i, channel in enumerate(channels):
                    buffers[channel].append(values[i])

                line_count += 1

                # Calculate and display variance every sample_rate lines
                if line_count % sample_rate == 0:
                    variances = await calculate_variance(buffers, line_count)
                    visualize_signal_quality(variances, screen, width, height, background_image)

            # Handle pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

    except socket.error as e:
        print(f"Connection error: {e}")
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        client_socket.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='UDP client to read and print data in real-time.')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host IP address to connect to')
    parser.add_argument('--port', type=int, default=9001, help='UDP port number to connect to')
    parser.add_argument('--buffer_size', type=int, default=512, help='Buffer size for each channel')
    parser.add_argument('--sample_rate', type=int, default=128, help='Sample rate in Hz (default: 128 Hz)')
    parser.add_argument('--image_path', type=str, default='C:\\Users\\alfredo\\Desktop\\wave-reflector\\1020-electrode-placement.png', help='Path to the electrode placement image')
    args = parser.parse_args()

    signal.signal(signal.SIGINT, signal_handler)

    asyncio.run(main(args.host, args.port, args.buffer_size, args.sample_rate, args.image_path))
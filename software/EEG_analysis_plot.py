import socket
import sys
import argparse
import asyncio
import pygame
from collections import deque

channels = ["F3", "FC5", "AF3", "F7", "T7", "P7", "O1", "O2", "P8", "T8", "F8", "AF4", "FC6", "F4"]

async def receive_data(host, port, buffers, buffer_size):
    reader, writer = await asyncio.open_connection(host, port)
    
    # Set TCP_NODELAY to disable Nagle's algorithm
    sock = writer.get_extra_info('socket')
    if sock is not None:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    
    buffer = ""
    try:
        while True:
            data = await reader.read(1024)
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

                for i, channel in enumerate(channels):
                    buffers[channel].append(values[i])

    except asyncio.CancelledError:
        pass
    finally:
        writer.close()
        await writer.wait_closed()

async def live_plot(buffers, sample_rate, plot_width, plot_height):
    pygame.init()
    plot_screen = pygame.display.set_mode((plot_width, plot_height))
    pygame.display.set_caption('EEG Progression')

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        plot_screen.fill((0, 0, 0))  # Clear the screen with black

        for i, channel in enumerate(channels):
            data = list(buffers[channel])
            if len(data) > 1:
                max_val = max(data)
                min_val = min(data)
                scaled_data = [(val - min_val) / (max_val - min_val) * plot_height / len(channels) for val in data]
                points = [(x, plot_height // len(channels) * i + y) for x, y in enumerate(scaled_data)]
                pygame.draw.lines(plot_screen, (0, 255, 0), False, points)

        pygame.display.flip()
        await asyncio.sleep(1 / sample_rate)

async def main(host, port, buffer_size, sample_rate):
    buffers = {channel: deque(maxlen=buffer_size) for channel in channels}

    receive_task = asyncio.create_task(receive_data(host, port, buffers, buffer_size))
    plot_task = asyncio.create_task(live_plot(buffers, sample_rate, 800, 600))

    await asyncio.gather(receive_task, plot_task)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='EEG Analysis Plot.')
    parser.add_argument('--host', type=str, default='localhost', help='Host IP address to connect to')
    parser.add_argument('--port', type=int, default=9003, help='TCP port number to connect to')
    parser.add_argument('--buffer_size', type=int, default=512, help='Buffer size for each channel')
    parser.add_argument('--sample_rate', type=int, default=128, help='Sample rate in Hz (default: 128 Hz)')

    args = parser.parse_args()

    asyncio.run(main(args.host, args.port, args.buffer_size, args.sample_rate))
import time
import numpy as np
import os
from scipy.interpolate import griddata
import pygame
import matplotlib.pyplot as plt
from collections import deque
import asyncio
import socket

from pythonosc import udp_client


# Standard 10-20 system positions for the specified channels
channels = ['AF3', 'F7', 'F3', 'FC5', 'T7', 'P7', 'O1', 'O2', 'P8', 'T8', 'FC6', 'F4', 'F8', 'AF4']
# channels = ['AF3', 'T7', 'PZ', 'T8', 'AF4']

electrode_positions = {
    'Fp1': (-0.5, 1), 'Fp2': (0.5, 1), 'F7': (-1, 0.5), 'F3': (-0.5, 0.5), 'Fz': (0, 0.5), 'F4': (0.5, 0.5), 'F8': (1, 0.5),
    'AF3': (-0.25, 0.75), 'AF4': (0.25, 0.75), 'FC5': (-0.75, 0.25), 'T7': (-1, 0), 'P7': (-0.9, -0.7), 'O1': (-0.5, -1),
    'O2': (0.5, -1), 'P8': (0.9, -0.7), 'T8': (1, 0), 'FC6': (0.75, 0.25), 'PZ': (0, -0.5)
}
electrode_positions = {key: value for key, value in electrode_positions.items() if key in channels}
speaker_zi_matrix_positions = [(4,7),(5,12),(8,12),(11,1),(11,5),(8,3),(5,3),(7,8)]
# group_modules = [
#     []
#     []
#     []
# ]




positions = np.array([electrode_positions[ch] for ch in channels])
resolution = 16

def read_ica_matrix(file_path):
    try:
        # Read the mixing matrix from the file
        A_ = np.loadtxt(file_path, delimiter=',')
        print(f"\nICA Mixing Matrix read from {file_path}:")
        print(A_)
        return A_
    except Exception as e:
        print(f"Error reading ICA mixing matrix: {e}")
        return None

def interpolate_components(current, next, alpha):
    return (1 - alpha) * current + alpha * next

def plot_topomap(data):
    xi = np.linspace(-1.5, 1.5, resolution)
    yi = np.linspace(-1.5, 1.5, resolution - 1)
    zi = griddata((positions[:, 0], positions[:, 1]), data, (xi[None, :], yi[:, None]), method='cubic')
    return zi

def visualize_heatmap(zi, screen, width, height):
    # Rotate the grid counterclockwise
    zi = np.rot90(zi, -1)

    # Replace nan values with a specific value for black color
    zi_nan_mask = np.isnan(zi)
    zi = np.nan_to_num(zi, nan=-1)

    # Normalize the data
    zi_normalized = (zi - np.min(zi)) / (np.max(zi) - np.min(zi))

    # Apply the RdBu_r colormap
    colormap = plt.get_cmap('RdBu_r')
    zi_colored = colormap(zi_normalized)

    # Set zero values to black
    zero_mask = (zi == 0)
    zi_colored[zero_mask] = [0, 0, 0, 1]

    # Set nan values to black
    zi_colored[zi_nan_mask] = [0, 0, 0, 1]

    # Convert to a format suitable for pygame
    zi_surface = pygame.surfarray.make_surface((zi_colored[:, :, :3] * 255).astype(np.uint8))
    zi_surface = pygame.transform.scale(zi_surface, (width, height))  # Adjust for margin
    screen.fill((0, 0, 0))  # Fill the screen with black color
    screen.blit(zi_surface, (10, 10))  # Blit with margin

    # Add electrode labels
    font = pygame.font.SysFont('courier', 20, bold=True)  # Typewriter-style font
    for ch, pos in electrode_positions.items():
        x = int((pos[0] + 1.5) / 3 * (width)) + 10
        y = int((1.5 - pos[1]) / 3 * (height)) + 10
        label = font.render(ch, True, (255, 255, 255))
        screen.blit(label, (x - label.get_width() // 2, y - label.get_height() // 2))

    pygame.display.flip()

async def send_row_to_udp(ip, port, row):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(row.tobytes(), (ip, port))
            # print(f"Sent row to {ip}:{port}")
    except Exception as e:
        print(f"Error sending row to {ip}:{port}: {e}")

def send_array_to_osc(ip, port, array):
    try:
        client = udp_client.SimpleUDPClient(ip, port)
        client.send_message("/array", array)
        # print(f"Sent array to {ip}:{port}")
    except Exception as e:
        print(f"Error sending array to {ip}:{port}: {e}")

async def main(file_path, interval, ip, port):
    last_mod_time = None
    component_queue = deque()
    zero_vector = None
    step = 0
    closing_sequence = False
    starting_sequence = True  # Flag to indicate the starting sequence

    n_steps = 35  # Number of steps for each component transition
    starting_steps = 100  # Number of steps for the starting sequence

    pygame.init()
    width, height = 600, 650
    os.environ['SDL_VIDEO_WINDOW_POS'] = f"{0},{100}"  # Move window 100 pixels up
    screen = pygame.display.set_mode((width, height), pygame.NOFRAME, display=0)  # No frame for no icon
    # pygame.display.set_caption('ICA Component Interpolation Heatmap')

    while True:
        try:
            # Check if the file has been modified
            current_mod_time = os.path.getmtime(file_path)
            if not closing_sequence:
                if last_mod_time is None:
                    new_matrix = read_ica_matrix(file_path)
                    if new_matrix is not None:
                        zero_vector = np.full(new_matrix.shape[0], -11.)  # Vector of float -1
                        component_queue.append(zero_vector)
                        for i in range(new_matrix.shape[1]):
                            component_queue.append(new_matrix[:, i])
                        last_mod_time = current_mod_time
                elif current_mod_time != last_mod_time:
                    try:
                        with open('STREAM_SIGNAL.txt', 'r') as signal_file:
                            signal = signal_file.read().strip()
                            if signal == '0':
                                while len(component_queue)>2:
                                    component_queue.pop()
                                closing_sequence = True

                    except Exception as e:
                        print(f"Error reading STREAM_SIGNAL.txt: {e}")
                    new_matrix = read_ica_matrix(file_path)
                    if new_matrix is not None:
                        for i in range(new_matrix.shape[1]):
                            component_queue.append(new_matrix[:, i])
                    last_mod_time = current_mod_time

            if starting_sequence:
                alpha = step / starting_steps
                current_component = zero_vector
                next_component = component_queue[1] if len(component_queue) > 1 else zero_vector
                interpolated_data = interpolate_components(current_component, next_component, alpha)
                zi = plot_topomap(interpolated_data)
                visualize_heatmap(zi, screen, width, height)
                step += 1
                if step >= starting_steps:
                    step = 0
                    starting_sequence = False
                    component_queue.popleft()
            elif len(component_queue) > 1:
                alpha = step / n_steps
                current_component = component_queue[0]
                next_component = component_queue[1]
                interpolated_data = interpolate_components(current_component, next_component, alpha)
                zi = plot_topomap(interpolated_data)
                visualize_heatmap(zi, screen, width, height)
                step += 1
                if step >= n_steps:
                    step = 0
                    component_queue.popleft()
            else:
                if component_queue:
                    print('Started closing sequence')
                    current_component = component_queue.popleft()
                    step = 0
                    closing_sequence = True
                    n_steps += 100

                alpha = step / n_steps

                interpolated_data = interpolate_components(current_component, zero_vector, alpha)
                zi = plot_topomap(interpolated_data)
                visualize_heatmap(zi, screen, width, height)
                step += 1
                if step >= n_steps:
                    pygame.quit()
                    return

            # Send one of the rows in zi to the UDP address
            if 'zi' in locals():
                # Normalize the zi variable
                zi_min, zi_max = np.nanmin(zi), np.nanmax(zi)
                zi_norm = (zi - zi_min) / (zi_max - zi_min) if zi_max != zi_min else zi

                row_to_send = np.array([zi_norm[pos] for pos in speaker_zi_matrix_positions])  # Select specific elements
                row_to_send = row_to_send[~np.isnan(row_to_send)]  # Filter out NaNs
                row_to_send = [int(x * 255) for x in row_to_send]  # Convert to a list of integers

                # asyncio.create_task(send_row_to_udp(ip, port, np.array(row_to_send)))
                if row_to_send:
                    send_array_to_osc(ip, port, row_to_send)

            # Handle pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

            # Wait for the specified interval before checking again
            await asyncio.sleep(1. / 10)
            #await asyncio.sleep(interval / n_steps)
        except KeyboardInterrupt:
            print("Interrupted by user")
            break
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(1. / 10)
            #await asyncio.sleep(interval / n_steps)
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Continuously read and print the ICA mixing matrix from a file.')
    parser.add_argument('--file_path', type=str, default='ica_mixing_matrix.txt', help='Path to the ICA mixing matrix file')
    parser.add_argument('--interval', type=int, default=5, help='Interval in seconds to check for file updates')
    parser.add_argument('--ip', type=str, default='192.168.68.114', help='IP address to send the data')
    # parser.add_argument('--ip', type=str, default='localhost', help='IP address to send the data')
    parser.add_argument('--port', type=int, default=5005, help='Port to send the data')
    args = parser.parse_args()

    asyncio.run(main(args.file_path, args.interval, args.ip, args.port))
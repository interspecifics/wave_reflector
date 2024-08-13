import time
import numpy as np
import os
from scipy.interpolate import griddata
import pygame
import matplotlib.pyplot as plt
from collections import deque
import asyncio
import socket

# Standard 10-20 system positions for the specified channels
channels = ['AF3', 'F7', 'F3', 'FC5', 'T7', 'P7', 'O1', 'O2', 'P8', 'T8', 'FC6', 'F4', 'F8', 'AF4']
electrode_positions = {
    'Fp1': (-0.5, 1), 'Fp2': (0.5, 1), 'F7': (-1, 0.5), 'F3': (-0.5, 0.5), 'Fz': (0, 0.5), 'F4': (0.5, 0.5), 'F8': (1, 0.5),
    'AF3': (-0.25, 0.75), 'AF4': (0.25, 0.75), 'FC5': (-0.75, 0.25), 'T7': (-1, 0), 'P7': (-1, -0.5), 'O1': (-0.5, -1),
    'O2': (0.5, -1), 'P8': (1, -0.5), 'T8': (1, 0), 'FC6': (0.75, 0.25)
}
electrode_positions = {key: value for key, value in electrode_positions.items() if key in channels}

# Greek letters for the bands
band_titles = {
    'delta': 'δ 0.5 - 4 Hz',
    'theta': 'θ 4 - 8 Hz',
    'alpha': 'α 8 - 12 Hz',
    'beta': 'β 12 - 30 Hz',
    'gamma': 'γ 30 - 40 Hz'
}

positions = np.array([electrode_positions[ch] for ch in channels])
resolution = 16
n_steps = 10*15  # Number of steps for each component transition
frames_per_second = 10  # Frames per second for interpolation

def read_psd_vector(file_path):
    try:
        # Read the mixing matrix from the file
        A_ = np.loadtxt(file_path, delimiter=',')
        print(f"\nBand PSD read from {file_path}:")
        print(A_)
        return A_
    except Exception as e:
        print(f"Error reading Band PSD: {e}")
        return None

def interpolate_components(current, next, alpha):
    return (1 - alpha) * current + alpha * next

def plot_topomap(data):
    xi = np.linspace(-1.5, 1.5, resolution)
    yi = np.linspace(-1.5, 1.5, resolution)
    zi = griddata((positions[:, 0], positions[:, 1]), data, (xi[None, :], yi[:, None]), method='cubic')
    return zi

def visualize_heatmap(zi, screen, width, height, band_title):
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
    zi_surface = pygame.transform.scale(zi_surface, (width - 20, height - 20))  # Adjust for margin
    screen.fill((0, 0, 0))  # Fill the screen with black color
    screen.blit(zi_surface, (10, 10))  # Blit with margin

    # Add electrode labels
    font = pygame.font.SysFont('courier', 20, bold=True)  # Typewriter-style font
    for ch, pos in electrode_positions.items():
        x = int((pos[0] + 1.5) / 3 * (width - 20)) + 10
        y = int((1.5 - pos[1]) / 3 * (height - 20)) + 10
        label = font.render(ch, True, (255, 255, 255))
        screen.blit(label, (x - label.get_width() // 2, y - label.get_height() // 2))

    # Add band title at the bottom
    title_font = pygame.font.SysFont('courier', 24, bold=True)
    title_label = title_font.render(band_title, True, (255, 255, 255))
    title_x = (width // 2) - (title_label.get_width() // 2)
    title_y = height - title_label.get_height() - 10
    screen.blit(title_label, (title_x, title_y))

    pygame.display.flip()

def send_row_to_udp(ip, port, row):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(row.tobytes(), (ip, port))
            # print(f"Sent row to {ip}:{port}")
    except Exception as e:
        print(f"Error sending row to {ip}:{port}: {e}")

async def check_file_updates(file_path, component_queue, zero_vector):
    last_mod_time = None
    while True:
        try:
            current_mod_time = os.path.getmtime(file_path)
            if last_mod_time is None or current_mod_time != last_mod_time:
                new_vector = read_psd_vector(file_path)
                if new_vector is not None:
                    if zero_vector is None:
                        zero_vector = np.zeros(new_vector.shape[0])
                        component_queue.append(zero_vector)
                    component_queue.append(new_vector)
                last_mod_time = current_mod_time
            await asyncio.sleep(1)  # Check for file updates every second
        except Exception as e:
            print(f"Error checking file updates: {e}")
            await asyncio.sleep(1)

async def main_async(file_path, interval, ip, port, band_title):
    component_queue = deque()
    zero_vector = np.zeros(14)
    step = 0
    initial_run_completed = False  # Flag to check if the initial run is completed
    initial_interpolation_steps = 100  # Number of steps for initial interpolation

    pygame.init()
    width, height = 500, 500
    screen = pygame.display.set_mode((width, height))  # No frame for no icon
    pygame.display.set_caption('Band PSD Interpolation Heatmap')

    # Start the file update checker
    asyncio.create_task(check_file_updates(file_path, component_queue, zero_vector))

    while True:
        try:
            if len(component_queue) > 1 or not initial_run_completed:
                if step < initial_interpolation_steps:
                    alpha = step / initial_interpolation_steps
                    current_component = zero_vector
                    next_component = component_queue[0]
                else:
                    alpha = (step - initial_interpolation_steps) / n_steps
                    current_component = component_queue[0]
                    next_component = component_queue[1] if len(component_queue) > 1 else zero_vector

                interpolated_data = interpolate_components(current_component, next_component, alpha)
                zi = plot_topomap(interpolated_data)
                visualize_heatmap(zi, screen, width, height, band_title)
                step += 1

                if step >= initial_interpolation_steps + n_steps:
                    step = initial_interpolation_steps
                    if len(component_queue) > 1:
                        component_queue.popleft()
                    initial_run_completed = True  # Set the flag to True after the initial run
            else:
                if len(component_queue) == 1:
                    alpha = step / n_steps
                    current_component = component_queue[0]
                    interpolated_data = interpolate_components(current_component, zero_vector, alpha)
                    zi = plot_topomap(interpolated_data)
                    visualize_heatmap(zi, screen, width, height, band_title)
                    step += 1
                    if step >= n_steps:
                        step = 0
                        component_queue.popleft()
                        component_queue.append(zero_vector)

            # Send one of the rows in zi to the UDP address
            if 'zi' in locals():
                # Normalize the zi variable
                zi_min, zi_max = np.nanmin(zi), np.nanmax(zi)
                zi_norm = (zi - zi_min) / (zi_max - zi_min) if zi_max != zi_min else zi

                row_to_send = zi_norm[6]  # Send the 6th row
                row_to_send = row_to_send[~np.isnan(row_to_send)][:8]  # Filter out NaNs
                row_to_send = (row_to_send * 255).astype(np.uint8)  # Multiply array values by 255 and cast to int
                send_row_to_udp(ip, port, np.array(row_to_send))

            # Handle pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

            # Wait for the next frame
            await asyncio.sleep(1 / frames_per_second)
        except KeyboardInterrupt:
            print("Interrupted by user")
            break
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(1 / frames_per_second)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Continuously read and print the Band PSD from a file.')
    parser.add_argument('--band', type=str, default='alpha', help='Path to the Band PSD file')
    parser.add_argument('--interval', type=int, default=12, help='Interval in seconds to check for file updates')
    parser.add_argument('--ip', type=str, default='192.168.0.100', help='IP address to send the data')
    parser.add_argument('--port', type=int, default=5005, help='Port to send the data')
    args = parser.parse_args()

    file_path = f'C:\\Users\\alfredo\\Desktop\\wave-reflector\\CyKit\\Examples\\{args.band}_psd.txt'
    band_title = band_titles.get(args.band, 'Unknown Band')
    asyncio.run(main_async(file_path, args.interval, args.ip, args.port, band_title))
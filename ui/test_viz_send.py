import pygame
import noise
import numpy as np
import socket
import threading

# Initialize pygame
pygame.init()

# Set up display
width, height = 1000, 1000
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("[i.n.t.e.r.s.p.e.c.i.f.i.c.s]: WAVE_REFLECTOR.VIZ")

# Define constants
cell_size = 50
matrix_size = 8
signal_count = 14  # Updated to 14 signals
signal_length = 400  # Width of the signal plot area
signal_height = 200  # Height of the signal plot area, updated to 400 pixels
signal_base = (height - signal_height) // 2 + 200  # Centered vertically and moved 200 pixels below

# Function to generate a matrix of Perlin noise values with position displacement
def generate_perlin_noise_matrix(x_offset, y_offset):
    scale = 10.0
    matrix = np.zeros((matrix_size, matrix_size), dtype=np.uint8)
    for i in range(matrix_size):
        for j in range(matrix_size):
            value = noise.pnoise2((i + x_offset) / scale, (j + y_offset) / scale, octaves=2, persistence=0.5, lacunarity=2.0, repeatx=matrix_size, repeaty=matrix_size, base=0)
            matrix[i][j] = int(127.5 * (value + 1))  # Scale from [-1, 1] to [0, 255]
    return matrix

# Function to generate signal data
def generate_signal(x, scale, velocity, rate):
    return noise.pnoise1(x * rate, octaves=2, persistence=0.5, lacunarity=2.0, repeat=signal_length, base=0) * scale * (signal_height / 2)

# Function to send matrix data via UDP
def send_matrix_row_udp(matrix, row_index):
    udp_ip = "192.168.0.100"
    udp_port = 5005
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print("Sending row:", matrix[row_index].tolist())
    #print("Sending matrix:", matrix.flatten().tolist())
    #data = matrix.flatten().tobytes()
    data = matrix[row_index].tobytes()
    sock.sendto(data, (udp_ip, udp_port))

# Main loop
running = True
x_offset, y_offset = 0, 0
signal_x_offsets = np.zeros(signal_count)
signal_data = [np.zeros(signal_length) for _ in range(signal_count)]
signal_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 255, 255), (255, 0, 255), (128, 128, 128), (255, 128, 0), (128, 0, 128), (0, 128, 128), (128, 128, 0), (128, 0, 0), (0, 128, 0), (0, 0, 128)]  # Extended to 14 colors
signal_scales = np.linspace(1, 2, signal_count)
signal_velocities = np.linspace(0.01, 0.02, signal_count)
signal_rates = np.linspace(0.1, 0.5, signal_count)

# Set up the clock for controlling the frame rate
clock = pygame.time.Clock()

while running:
    # the events loop 
    for event in pygame.event.get():
        if event.type is pygame.QUIT:
            running = False

    # Clear the screen to black before drawing
    screen.fill((0, 0, 0))

    # Generate Perlin noise matrix with displacement
    perlin_matrix = generate_perlin_noise_matrix(x_offset, y_offset)
    x_offset += 0.012  # Increment the offset for a dynamic effect
    y_offset += 0.004

    # Draw the matrix centered horizontally and 100 pixels from the top
    matrix_top_left_x = (width - matrix_size * cell_size) // 2
    matrix_top_left_y = 100
    for i in range(matrix_size):
        for j in range(matrix_size):
            value = perlin_matrix[i][j]
            if value > 127:
                color = (255, 255 - 2 * (value - 127), 255 - 2 * (value - 127))  # Gradient from white to red
            elif value < 127:
                color = (255 - 2 * (127 - value), 255 - 2 * (127 - value), 255)  # Gradient from white to blue
            else:
                color = (255, 255, 255)  # White for 127
            pygame.draw.rect(screen, color, (matrix_top_left_x + j * cell_size, matrix_top_left_y + i * cell_size, cell_size, cell_size))

    # Update and draw the signals centered horizontally
    signal_start_x = (width - signal_length) // 2
    for i in range(signal_count):
        signal_x_offsets[i] += signal_velocities[i]
        new_y = generate_signal(signal_x_offsets[i], signal_scales[i], signal_velocities[i], signal_rates[i])
        signal_data[i] = np.roll(signal_data[i], -1)
        signal_data[i][-1] = new_y
        for x in range(signal_length):
            y = signal_data[i][x]
            pygame.draw.line(screen, signal_colors[i], (signal_start_x + x - 1, int(signal_base + signal_height / 2 + signal_data[i][x - 1])), (signal_start_x + x, int(signal_base + signal_height / 2 + y)), 1)

    # Send matrix data via UDP in a separate thread
    threading.Thread(target=send_matrix_row_udp, args=(perlin_matrix, 0)).start()

    # Update the display
    pygame.display.flip()

    # Cap the frame rate at 30 fps
    clock.tick(12)

# Quit pygame
pygame.quit()

import socket
import sys
import signal
import argparse
import numpy as np
from collections import deque
from sklearn.decomposition import FastICA
import threading

# high level, define number of components
n_components = 5

# Channel names and order
channels = ["F3", "FC5", "AF3", "F7", "T7", "P7", "O1", "O2", "P8", "T8", "F8", "AF4", "FC6", "F4"]
# channels = ['AF3', 'T7', 'PZ', 'T8', 'AF4']

# Signal handler for graceful exit
def signal_handler(sig, frame):
    print('Exiting...')
    sys.exit(0)

def calculate_ica(X, line_count):
    ica = FastICA(n_components=n_components)
    S_ = ica.fit_transform(X)  # Reconstruct signals
    A_ = ica.mixing_  # Get estimated mixing matrix

    # Print the mixing matrix
    print(f"\nICA Mixing Matrix at line {line_count}:")
    print(A_)

    # Save the mixing matrix to a file
    #np.savetxt('C:\\Users\\alfredo\\Desktop\\wave-reflector\\CyKit\\Examples\\ica_mixing_matrix.txt', A_, delimiter=',')
    np.savetxt('ica_mixing_matrix.txt', A_, delimiter=',')
    print(f"ICA Mixing Matrix saved to ica_mixing_matrix.txt")

def main(host, port, buffer_size_seconds, sample_rate, overlap_fraction):
    buffer_size = buffer_size_seconds * sample_rate
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024)  # Set receive buffer size
    try:
        client_socket.bind((host, port))
        print(f"Connected to {host}:{port}")
    
        # Initialize buffers for each channel using deque for efficient pops from the left
        buffers = {channel: deque(maxlen=buffer_size) for channel in channels}
        line_count = 0
        overlap_size = int(buffer_size * overlap_fraction)
        buffer = ""

        while True:
            data, _ = client_socket.recvfrom(1024)
            if not data:
                break

            # Append received data to buffer
            buffer += data.decode()

            # Process complete lines
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                try:
                    values = list(map(float, line.split(',')))
                except ValueError:
                    print(f"Skipping non-numeric line: {line}")
                    continue

                # Update buffers
                for i, channel in enumerate(channels):
                    buffers[channel].append(values[i])

                line_count += 1

                # Calculate and print ICA mixing matrix when buffer is filled
                if line_count >= buffer_size:
                    # Create a matrix from the buffers
                    X = np.array([list(buffers[channel]) for channel in channels]).T

                    # Compute ICA in a separate thread
                    threading.Thread(target=calculate_ica, args=(X, line_count)).start()

                    # Reset buffers for the next window with overlap
                    for channel in channels:
                        buffers[channel] = deque(list(buffers[channel])[-overlap_size:], maxlen=buffer_size)
                    line_count = overlap_size

    except socket.error as e:
        print(f"Connection error: {e}")
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        client_socket.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='UDP client to read and print data in real-time.')
    parser.add_argument('--host', type=str, default='localhost', help='Host IP address to connect to')
    parser.add_argument('--port', type=int, default=9001, help='UDP port number to connect to')
    parser.add_argument('--buffer_size_seconds', type=int, default= 10, help='Buffer size for each channel')
    parser.add_argument('--sample_rate', type=int, default=128, help='Sample rate in Hz (default: 128 Hz)')
    parser.add_argument('--overlap_fraction', type=float, default=0.5, help='Fraction of buffer to overlap (default: 0.5)')
    args = parser.parse_args()

    signal.signal(signal.SIGINT, signal_handler)

    main(args.host, args.port, args.buffer_size_seconds, args.sample_rate, args.overlap_fraction)
import socket
import sys
import signal
import argparse
import numpy as np
from collections import deque
from mne.time_frequency import psd_array_multitaper
from concurrent.futures import ThreadPoolExecutor

# Channel names and order
channels = ["F3", "FC5", "AF3", "F7", "T7", "P7", "O1", "O2", "P8", "T8", "F8", "AF4", "FC6", "F4"]

# Frequency bands
freq_bands = {
    # 'Delta': (0.5, 4),
    'Theta': (4, 8),
    'Alpha': (8, 12),
    'Beta': (12, 30),
    'Gamma': (30, 40)
}

# Signal handler for graceful exit
def signal_handler(sig, frame):
    print('Exiting...')
    sys.exit(0)

import time
tic = time.time()

def calculate_psd(X, sample_rate):
    psds, freqs = psd_array_multitaper(X, sfreq=sample_rate, fmin=0.5, fmax=40, verbose=0)
    psd_band = {}
    
    # Calculate PSD for each band
    for band, (fmin, fmax) in freq_bands.items():
        idx_band = np.logical_and(freqs >= fmin, freqs <= fmax)
        psd_band[band] = psds[:, idx_band].mean(axis=1)
    
    # Flatten all PSD values for global mapping
    all_psd_values = np.concatenate(list(psd_band.values()))
    
    # Sort all PSD values and map them to the range -1 to 1
    sorted_indices = np.argsort(all_psd_values)
    mapped_values = np.linspace(-1, 1, len(all_psd_values))
    all_psd_values[sorted_indices] = mapped_values
    
    # Apply the mapped values back to each band
    start_idx = 0
    for band in psd_band:
        band_length = len(psd_band[band])
        psd_band[band] = all_psd_values[start_idx:start_idx + band_length]
        start_idx += band_length
    
    # Save mapped PSD values to files
    for band, psd in psd_band.items():
        filename = f'{band.lower()}_psd.txt'
        np.savetxt(filename, psd, delimiter=',')
        print(f"{band} PSD saved to {filename}")
        if 'Gamma' in band:
            print(time.time() - tic)
            # tic = time.time()

def main(host, port, buffer_size_seconds, sample_rate, overlap_fraction):
    buffer_size = buffer_size_seconds * sample_rate
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        client_socket.bind((host, port))
        print(f"Connected to {host}:{port}")
    
        # Initialize buffers for each channel using deque for efficient pops from the left
        buffers = {channel: deque(maxlen=buffer_size) for channel in channels}
        line_count = 0
        overlap_size = int(buffer_size * overlap_fraction)
        buffer = ""

        # Thread pool for PSD calculations
        # with ThreadPoolExecutor(max_workers=4) as executor:
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

                # Calculate and print PSD when buffer is filled
                if line_count >= buffer_size + overlap_size:
                    # Create a matrix from the buffers
                    X = np.array([list(buffers[channel]) for channel in channels])

                    # Compute PSD in a separate thread
                    # executor.submit(calculate_psd, X, sample_rate)
                    calculate_psd(X, sample_rate)

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
    parser.add_argument('--port', type=int, default=9002, help='UDP port number to connect to')
    parser.add_argument('--buffer_size_seconds', type=int, default=4, help='Buffer size for each channel')
    parser.add_argument('--sample_rate', type=int, default=128, help='Sample rate in Hz (default: 128 Hz)')
    parser.add_argument('--overlap_fraction', type=float, default=0.25, help='Fraction of buffer to overlap (default: 0.5)')
    args = parser.parse_args()

    signal.signal(signal.SIGINT, signal_handler)

    main(args.host, args.port, args.buffer_size_seconds, args.sample_rate, args.overlap_fraction)
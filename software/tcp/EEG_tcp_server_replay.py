import socket
import time
import sys
import argparse
import signal

def setup_tcp_stream(port):
    """Setup TCP server to stream data."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind(('localhost', port))
        server.listen(1)
        print(f"Listening on TCP port {port}")
        client_socket, addr = server.accept()
        print(f"Connection from {addr}")
        return client_socket
    except socket.error as e:
        print(f"Failed to set up TCP server on port {port}: {e}")
        sys.exit(1)  # Exit if we cannot establish a server

def stream_file_over_tcp(file_path, ports, sample_rate):
    client_sockets = [setup_tcp_stream(port) for port in ports]
    # Calculate the delay between sends to achieve the specified sample rate
    delay = 1 / sample_rate

    # Open the file
    try:
        with open(file_path, 'r') as file:
            # Read and send each line
            for line in file:
                for client_socket in client_sockets:
                    client_socket.sendall(line.encode())
                time.sleep(delay)  # Wait to maintain the specified sample rate
    except FileNotFoundError:
        print(f"Error: The file {file_path} does not exist.")
        sys.exit(1)
    except IOError as e:
        print(f"Error reading file {file_path}: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Streaming interrupted by user.")
    finally:
        for client_socket in client_sockets:
            client_socket.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Stream ECG data over TCP.')
    parser.add_argument('--file_path', type=str, required=True, help='Path to the file containing ECG data')
    parser.add_argument('--ports', type=list, nargs='+', default=[9001, 9002, 9003], help='TCP ports for streaming data')
    parser.add_argument('--sample_rate', type=float, default=128, help='Sample rate in Hz (default: 128 Hz)')

    args = parser.parse_args()

    def signal_handler(sig, frame):
        print('Exiting...')
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    stream_file_over_tcp(args.file_path, args.ports, args.sample_rate)
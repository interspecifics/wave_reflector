import socket
import time
import argparse

def setup_udp_stream():
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return server

def stream_file_over_udp(file_path, ports, sample_rate):
    server = setup_udp_stream()
    delay = 1 / sample_rate / 2

    try:
        with open(file_path, 'r') as file:
            for line in file:
                # print(f"Sending line: {line.strip()}")
                for port in ports:
                    server.sendto(line.encode(), ('localhost', port))
                time.sleep(delay)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        server.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Stream data over UDP.')
    parser.add_argument('--file_path', type=str, required=True, help='Path to the file containing data')
    parser.add_argument('--ports', type=int, nargs='+', default=[900, 9001, 9002, 9003], help='List of UDP ports for streaming data')
    parser.add_argument('--sample_rate', type=float, default=128, help='Sample rate in Hz')

    args = parser.parse_args()
    stream_file_over_udp(args.file_path, args.ports, args.sample_rate)

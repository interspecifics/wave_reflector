import socket
import numpy as np

# Set up the UDP socket
udp_ip = "127.0.0.1"
udp_port = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((udp_ip, udp_port))

print("UDP server is listening on port", udp_port)

try:
    while True:
        # Receive data
        data, addr = sock.recvfrom(1024)  # Buffer size is 1024 bytes
        if data:
            # Convert bytes to numpy array
            matrix_row = np.frombuffer(data, dtype=np.uint8)
            # Print the list of values
            print("Received row:", matrix_row.tolist())
except KeyboardInterrupt:
    print("Server is shutting down.")
finally:
    sock.close()
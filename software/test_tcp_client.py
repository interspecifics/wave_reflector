import socket
import numpy as np

# Set up the UDP socket
udp_ip = "127.0.0.1"
udp_port = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 0)  # Avoid caching by setting the receive buffer size to 0
sock.bind((udp_ip, udp_port))

print("UDP server is listening on port", udp_port)

try:
    while True:
        # Receive data
        data, addr = sock.recvfrom(8)  # Buffer size is 512 bytes
        if data:
            # Convert bytes to numpy array
            matrix_row = np.frombuffer(data, dtype=np.uint8)
            # Print the list of values
            print("Received row:", matrix_row.tolist())
except KeyboardInterrupt:
    print("Server is shutting down.")
finally:
    sock.close()
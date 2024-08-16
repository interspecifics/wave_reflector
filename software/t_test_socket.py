import socket

def main():
    # Set up UDP socket
    UDP_IP = "0.0.0.0"  # Listen on all available interfaces
    UDP_PORT = 5005     # Port to listen on

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    print(f"UDP receiver listening on {UDP_IP}:{UDP_PORT}")

    while True:
        try:
            # Receive data
            data, addr = sock.recvfrom(8)  # Buffer size is 8 bytes

            # Decode the received data into 8 integer values
            values = list(data)

            if len(values) == 8:
                print(f"Received values: {values}")
            else:
                print(f"Received incorrect number of values. Expected 8, got {len(values)}")

        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()

import socket
import argparse
import time

IP = "127.0.0.1" 
PORT = 9002

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((IP, PORT))

print(f"Listening for clients at {(IP, PORT)}")

last_time = time.time()
count = 0

while True:
    data, address = sock.recvfrom(4096)
    current_time = time.time()
    count += 1

    elapsed_time = current_time - last_time
    if elapsed_time >= 1.0:
        rate = count / elapsed_time
        print(f"Rate: {rate:.2f} times per second")
        last_time = current_time
        count = 0

    # print(f"Received {data} from {address}")

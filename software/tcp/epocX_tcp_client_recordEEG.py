# -*- coding: utf8 -*-
#
#  CyKIT  2020.06.05
#  ________________________
#  example_epoc_x_win.py       
#  
#  Written by zer0-pole
#
"""
   
  usage:  python.exe .\example_epoc_x_win.py
  
  ( May need to adjust the key below, based on whether 
    device is in 14-bit mode or 16-bit mode. )
  
"""

import os
import sys
import socket
import queue

import argparse

# Setup CLI arguments
parser = argparse.ArgumentParser(description='Receive EEG data over TCP and record it to a text file.')
parser.add_argument('--prefix', type=str, help='Prefix for the output file name', default='eeg_data')
parser.add_argument('--subject', type=str, help='Subject name to prefix the file', default='')
parser.add_argument('--duration', type=int, help='Duration to capture data in seconds', default=15*60)
parser.add_argument('--rate', type=int, help='Sample rate (lines per second)', default=128)
parser.add_argument('--host', type=str, help='Host IP address to connect to', default='localhost')
parser.add_argument('--port', type=int, help='TCP port number to connect to', default=9000)
args = parser.parse_args()

tasks = queue.Queue()

# TCP connection setup
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((args.host, args.port))
print(f"Connected to {args.host}:{args.port}")

def receive_data():
    while True:
        data = client_socket.recv(1024)
        if not data:
            break
        tasks.put(data)

def create_file(subject_name, prefix):
    # Ensure the directory exists
    os.makedirs('epocx_readings', exist_ok=True)
    if subject_name:
        core_str = f'{subject_name}_{prefix}'
    else:
        core_str = prefix
    # Determine the next file suffix number
    existing_files = [f for f in os.listdir('epocx_readings') if f.startswith(f'{core_str}_') and f.endswith('.txt')]
    next_file_number = len(existing_files) + 1
    return f'epocx_readings/{core_str}_{next_file_number}.txt'

file_path = create_file(args.subject, args.prefix)

epocX_header = "F3, FC5, AF3, F7, T7, P7, O1, O2, P8, T8, F8, AF4, FC6, F4"
# Open a file to write the data
with open(file_path, 'w') as file:
    # Write the epocX_header line with column names
    file.write(epocX_header + '\n')

    max_lines = args.duration * args.rate
    line_count = 0
    while line_count < max_lines:
        while tasks.empty():
            pass
        data = tasks.get()
        file.write(data.decode() + '\n')  # Write data to file instead of printing
        line_count += 1
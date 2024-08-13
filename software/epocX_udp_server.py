import os
import sys
import signal
import cyPyWinUSB as hid
import queue
from cyCrypto.Cipher import AES
import socket
import argparse
import time

# Setup CLI arguments
parser = argparse.ArgumentParser(description='Record EEG data to a text file.')
parser.add_argument('--ports', type=int, nargs='+', default=[9000, 9001, 9002], help='List of UDP ports for streaming data')
args = parser.parse_args()

# Setup UDP connections
def setup_udp_stream():
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return server

server = setup_udp_stream()
ports = args.ports
tasks = queue.Queue()

class EEG(object):
    def __init__(self):
        self.hid = None
        self.delimiter = ", "
        self.cipher = None
        devicesUsed = 0

        for device in hid.find_all_hid_devices():
            if device.product_name == 'EEG Signals':
                devicesUsed += 1
                self.hid = device
                self.hid.open()
                self.serial_number = device.serial_number
                device.set_raw_data_handler(self.dataHandler)
        if devicesUsed == 0:
            os._exit(0)

        serial = self.serial_number
        print("serial: ", serial)
        sn = bytearray()
        for i in range(0, len(serial)):
            sn += bytearray([ord(serial[i])])

        k = [sn[-1], sn[-2], sn[-4], sn[-4], sn[-2], sn[-1], sn[-2], sn[-4], sn[-1], sn[-4], sn[-3], sn[-2], sn[-1], sn[-2], sn[-2], sn[-3]]
        self.cipher = AES.new(bytearray(k), AES.MODE_ECB)

    def dataHandler(self, data):
        data2 = [0] * (len(data) - 1)
        for X in range(1, len(data)):
            data2[X - 1] = (data[X] ^ 0x55)  # XOR each byte by 0x55 (85)
        ans = self.cipher.decrypt(bytearray(data2))
        tasks.put(ans)

    def convertEPOC_PLUS(self, value_1, value_2):
        edk_value = "%.8f" % (((int(value_1) * .128205128205129) + 4201.02564096001) + ((int(value_2) - 128) * 32.82051289))
        return edk_value

    def get_data(self):
        data = tasks.get()
        try:
            packet_data = ""
            for i in range(2, 16, 2):
                packet_data = packet_data + str(self.convertEPOC_PLUS(str(data[i]), str(data[i + 1]))) + self.delimiter
            for i in range(18, len(data), 2):
                packet_data = packet_data + str(self.convertEPOC_PLUS(str(data[i]), str(data[i + 1]))) + self.delimiter
            packet_data = packet_data[:-len(self.delimiter)]
            return str(packet_data)
        except Exception as exception2:
            print(str(exception2))

cyHeadset = EEG()

def signal_handler(sig, frame):
    print('Exiting...')
    server.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Main loop to stream data over UDP
cyHeadset = EEG()
line_count = 0

while True:
    while tasks.empty():
        pass
    data = cyHeadset.get_data()
    for port in ports:
        server.sendto((data + '\n').encode(), ('localhost', port))

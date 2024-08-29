from pythonosc.udp_client import SimpleUDPClient

ip = "127.0.0.1"
port = 5005

client = SimpleUDPClient(ip, port)
integer_array = [1, 2, 3, 4, 5]
client.send_message("/array", integer_array)

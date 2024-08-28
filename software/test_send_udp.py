from pythonosc import udp_client

def send_array_to_osc(ip, port, array):
    try:
        client = udp_client.SimpleUDPClient(ip, port)
        client.send_message("/array", array)
        print(f"Sent array to {ip}:{port}")
    except Exception as e:
        print(f"Error sending array to {ip}:{port}: {e}")

if __name__ == "__main__":
    ip = "192.168.68.114"  # Replace with the target IP address
    port = 5005  # Replace with the target port
    array = [1, 2, 3, 4, 5, 6, 7, 8]  # Replace with your array of integers

    send_array_to_osc(ip, port, array)

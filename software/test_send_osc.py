from oscpy.client import OSCClient

def send_array_to_osc(ip, port, array):
    try:
        client = OSCClient(ip, port)
        client.send_message(b'/array', array)
        print(f"Sent array to {ip}:{port}")
    except Exception as e:
        print(f"Error sending array to {ip}:{port}: {e}")

if __name__ == "__main__":
    ip = "localhost"  # Replace with the target IP address
    port = 5005  # Replace with the target port
    array = [1, 2, 3, 4, 5, 6, 7, 8]  # Replace with your array of integers

    send_array_to_osc(ip, port, array)

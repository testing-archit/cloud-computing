import socket, struct

def wake_on_lan(mac):
    mac = mac.replace(":", "").replace("-", "")
    if len(mac) != 12:
        raise ValueError("Invalid MAC")
    data = b'FF' * 6 + (mac.encode() * 16)
    send_data = b''
    for i in range(0, len(data), 2):
        send_data += struct.pack('B', int(data[i:i+2], 16))
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(send_data, ('<broadcast>', 9))
    sock.close()

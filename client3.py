import sys
import socket
import selectors
import types
import datetime
from cryptography.fernet import Fernet

key = b'gQzJC7mbOjXUpriRogVnoaCqGh6-uQZC2dzjh6EjHEI='
cipher_suite = Fernet(key)

sel = selectors.DefaultSelector()

def get_server_ip():
    server_host = input("Enter the server's hostname or IP address: ")
    try:
        server_ip = socket.gethostbyname(server_host)
        return server_ip
    except socket.gaierror:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print("[{timestamp}] Could not resolve the host. Please check the hostname or IP address.")
        sys.exit(1)

def start_connection(server_ip, port):
    server_addr = (server_ip, port)
    connid = 1
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] Starting connection to {server_addr}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(False)
    sock.connect_ex(server_addr)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    data = types.SimpleNamespace(
        connid=connid,
        recv_total=0,
        zero_count=0,
        one_count=0,
        outb=b"",
    )
    sel.register(sock, events, data=data)

def service_connection(key, mask):
    sock = key.fileobj
    data = key.data

    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)
        if recv_data:
            print(f"Received {recv_data} from connection {data.connid}")
            #can comment out the above line as it shows encrypted data
            decrypted_data = cipher_suite.decrypt(recv_data)  # Decrypt received data
            print(f"Received (decrypted) from connection {data.connid}: {decrypted_data.decode()}")
           
            data.recv_total += len(decrypted_data)
            data.zero_count += decrypted_data.count(b'0')
            data.one_count += decrypted_data.count(b'1')
            if decrypted_data.strip() == b"end":
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{timestamp}] Closing connection {data.connid}")
                print(f"Total 0s received: {data.zero_count}")
                print(f"Total 1s received: {data.one_count}")
                sel.unregister(sock)
                sock.close()

    if mask & selectors.EVENT_WRITE:
        pass  # No data to send in this scenario

if __name__ == "__main__":
    server_ip = get_server_ip()
    port = 12346

    start_connection(server_ip, port)

    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            service_connection(key, mask)

import sys
import socket
import selectors
import types

sel = selectors.DefaultSelector()

def get_server_ip():
    server_host = input("Enter the server's hostname or IP address: ")
    try:
        server_ip = socket.gethostbyname(server_host)
        return server_ip
    except socket.gaierror:
        print("Could not resolve the host. Please check the hostname or IP address.")
        sys.exit(1)

def start_connection(server_ip, port):
    server_addr = (server_ip, port)
    connid = 1
    print(f"Starting connection to {server_addr}")
    print("Enter your name - ")
    cl_name = input()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(False)
    sock.connect_ex(server_addr)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    data = types.SimpleNamespace(
        connid=connid,
        recv_total=0,
        zero_count=0,
        one_count=0,
        outb=cl_name.encode(),
    )
    sel.register(sock, events, data=data)

def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)
        if recv_data:
            print(f"Received {recv_data.decode()} from connection {data.connid}")
            data.recv_total += len(recv_data)
            data.zero_count += recv_data.decode().count('0')
            data.one_count += recv_data.decode().count('1')
        if not recv_data or data.recv_total == len(recv_data.decode()):
            print(f"Closing connection {data.connid}")
            print(f"Total 0s received: {data.zero_count}")
            print(f"Total 1s received: {data.one_count}")
            sel.unregister(sock)
            sock.close()

def main():
    server_ip = get_server_ip()
    port = 12346

    start_connection(server_ip, port)

    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            service_connection(key, mask)

if __name__ == "__main__":
    main()

import sys
import socket
import selectors
import types

sel = selectors.DefaultSelector()

host, port = '192.168.224.1', 12346
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.bind((host, port))
lsock.listen()
print(f"Listening on {(host, port)}")
lsock.setblocking(False)
sel.register(lsock, selectors.EVENT_READ, data=None)

pattern = input("Enter the pattern of 0s and 1s to send: ")

# Define a set to keep track of connected clients
connected_clients = dict()
max_clients = 5  # Maximum number of clients allowed

def accept_wrapper(sock):
    conn, addr = sock.accept()
    if len(connected_clients) >= max_clients:
        print(f"Rejecting connection from {addr} - Maximum clients reached")
        conn.close()
        return
    if addr[0] in connected_clients:
        print(f"Rejecting connection from {addr} - Client already connected from this IP")
        conn.close()
        return
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=pattern.encode())
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)
    connected_clients[addr[0]] = "." #placeholder till name is read

def service_connection(key, mask):
    cl_socket = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = cl_socket.recv(1024)
        if recv_data:
            data.outb += recv_data
            connected_clients[data.addr[0]] = recv_data.decode() #update name
        else:
            print(f"Closing connection to {data.addr}")
            sel.unregister(cl_socket)
            cl_socket.close()
            connected_clients.remove(data.addr[0])

    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print(f"Echoing {data.outb!r} to {data.addr}")
            sent = cl_socket.send(data.outb)
            data.outb = data.outb[sent:]

try:
    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                accept_wrapper(key.fileobj)
            else:
                service_connection(key, mask)
except KeyboardInterrupt:
    print("Caught keyboard interrupt, exiting")
finally:
    sel.close()

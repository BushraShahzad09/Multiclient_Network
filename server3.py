import sys
import socket
import selectors
import types
import datetime
from cryptography.fernet import Fernet

key = Fernet.generate_key()
cipher_suite = Fernet(key)
print("URL-safe base64-encoded key:", key.decode())

sel = selectors.DefaultSelector()

host, port = '127.0.0.1', 12346
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.bind((host, port))
lsock.listen()
print(f"Listening on {(host, port)}")
lsock.setblocking(False)
sel.register(lsock, selectors.EVENT_READ, data=None)

# Define a set to keep track of connected clients
connected_clients = set()
max_clients = 5

def accept_wrapper(sock):
    conn, addr = sock.accept()
    if len(connected_clients) >= max_clients:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] Rejecting connection from {addr} - Maximum clients reached")
        conn.close()
        return
    if addr[0] in connected_clients:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] Rejecting connection from {addr} - Client already connected from this IP")
        conn.close()
        return
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] Accepted connection from {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)
    connected_clients.add(addr[0])
    handle_user_input(conn, addr)

def handle_user_input(conn, addr):
    while True:
        user_input = input("Enter 0 or 1 or 'end' to terminate: ")
        if user_input not in ('0', '1', 'end'):
            print("Invalid input. Please enter '0', '1', or 'end'.")
            continue

        if user_input == 'end':
            encrypted_data = cipher_suite.encrypt(user_input.encode())
            conn.send(encrypted_data)
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{timestamp}] Closing connection to {addr}")
            sel.unregister(conn)
            conn.close()
            connected_clients.remove(addr[0])
            break
        else:
            encrypted_data = cipher_suite.encrypt(user_input.encode())
            conn.send(encrypted_data)

def service_connection(key, mask):
    cl_socket = key.fileobj
    data = key.data

    if mask & selectors.EVENT_READ:
        recv_data = cl_socket.recv(1024)
        if recv_data:
            decrypted_data = cipher_suite.decrypt(recv_data)  # Decrypt received data
            decrypted_data = decrypted_data.decode()
            
            if decrypted_data == 'end':
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{timestamp}] Closing connection to {data.addr}")
                sel.unregister(cl_socket)
                cl_socket.close()
                connected_clients.remove(data.addr[0])
            elif decrypted_data in ('0', '1'):
                print(f"Received (decrypted) from {data.addr}: {decrypted_data}")
            else:
                print("Invalid data received. Discarding the packet.")
                # Discard the invalid data and don't transmit to the client

    if mask & selectors.EVENT_WRITE:
        if data.outb:
            next_char = data.outb[:1]
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{timestamp}] Sending {next_char} to {data.addr}")
            encrypted_data = cipher_suite.encrypt(next_char)  # Encrypt data before sending
            sent = cl_socket.send(encrypted_data)
            data.outb = data.outb[1:]

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

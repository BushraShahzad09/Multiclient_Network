import threading
import socket

alias = input('Choose an alias >>> ')
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('192.168.120.202', 59001))
print("Commands:\n1. DM <recipient_alias> <message>\n2. RequestAliases\n3. Search <keyword>\n4. Replace <old_word> <new_word>\n")

def client_receive():
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            print(message)
        except:
            print('Error!')
            client.close()
            break

def client_send():
    while True:
        message = input("")
        client.send(message.encode('utf-8'))

receive_thread = threading.Thread(target=client_receive)
receive_thread.start()

send_thread = threading.Thread(target=client_send)
send_thread.start()

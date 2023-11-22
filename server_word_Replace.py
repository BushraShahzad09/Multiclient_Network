import threading
import socket
import re

#host = '192.168.120.202'
host = '192.168.120.202'
port = 59001
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

clients = []
aliases = []
client_details = {}

# File for storing chats
chat_log_file = "chat_log.txt"
abusive_words = ["abuse1", "abuse2"]  # Add your abusive words to this list


# def broadcast(message):
#     for client in clients:
#         try:
#             client.send(message)
#         except:
#             continue

# Function to handle clients' connections
def handle_client(client, alias):
    while True:
        try:
            message = client.recv(1024).decode('utf-8')

            # Check for abusive words
            if any(word in message for word in abusive_words):
                client.send("Warning: Your message contains abusive words.".encode('utf-8'))
                continue

            # Log the chat to the file with client details
            with open(chat_log_file, "a") as log:
                log.write(f"{alias} ({client_details[alias]}): {message}\n")

            # Implement direct message functionality
            if message.startswith("DM"):
                parts = message.split(" ", 2)
                if len(parts) == 3:
                    recipient_alias = parts[1]
                    dm_message = parts[2]
                    send_direct_message(alias, recipient_alias, dm_message)
            elif message.startswith("RequestAliases"):
                send_aliases(client)
            elif message.startswith("Search"):
                keyword = message.split(" ", 1)[1]
                search_and_send_results(client, keyword)
            elif message.startswith("Replace"):
                parts = message.split(" ", 2)
                if len(parts) == 3:
                    old_word, new_word = parts[1], parts[2]
                    replace_and_broadcast(alias, old_word, new_word)
            

        except Exception as e:
            print(f'Error: {e}')
            index = clients.index(client)
            clients.remove(client)
            client.close()
            alias = aliases[index]
            aliases.remove(alias)
            del client_details[alias]
            break

# Function to send a direct message to a specific client
def send_direct_message(sender_alias, recipient_alias, message):
    for client, client_alias in zip(clients, aliases):
        if client_alias == recipient_alias:
            try:
                client.send(f'DM from {sender_alias}: {message}'.encode('utf-8'))
            except:
                print(f"Failed to send a direct message to {recipient_alias}")

# Function to handle requests for aliases
def send_aliases(client):
    aliases_msg = ", ".join(aliases)
    client.send(f'Connected aliases: {aliases_msg}'.encode('utf-8'))

# Function to handle search requests
def search_and_send_results(client, keyword):
    matches = []
    with open(chat_log_file, "r") as log:
        for line in log:
            if keyword in line:
                matches.append(line)
    if matches:
        client.send(f'Search Results:\n{" ".join(matches)}'.encode('utf-8'))
    else:
        client.send('No matches found.'.encode('utf-8'))

# Function to handle replace requests
def replace_and_broadcast(sender_alias, old_word, new_word):
    with open(chat_log_file, "r") as log:
        lines = log.readlines()

    with open(chat_log_file, "w") as log:
        for line in lines:
            new_line = re.sub(r'\b%s\b' % old_word, new_word, line)
            log.write(new_line)

    # # Broadcast the replacement to all clients
    # broadcast(f'{sender_alias} replaced "{old_word}" with "{new_word}"'.encode('utf-8'))

# Main function to receive the clients' connection
def receive():
    while True:
        print('Server is running and listening ...')
        client, address = server.accept()
        print(f'Connection is established with {str(address)}')
        client.send('alias?'.encode('utf-8'))
        alias = client.recv(1024).decode('utf-8')
        aliases.append(alias)
        clients.append(client)
        client_details[alias] = address  # Store client IP and port
        print(f'The alias of this client is {alias} ({address})'.encode('utf-8'))
        client.send('You are now connected!'.encode('utf-8'))
        thread = threading.Thread(target=handle_client, args=(client, alias))
        thread.start()

if __name__ == "__main__":
    receive()

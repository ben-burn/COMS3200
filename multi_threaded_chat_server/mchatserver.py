import socket
import threading
import sys
import time
import queue
import os


class Client:
    def __init__(self, username, connection, address):
        self.username = username
        self.connection = connection
        self.address = address
        self.kicked = False
        self.in_queue = True
        self.remaining_time = 100 # remaining time before AFK
        self.muted = False
        self.mute_duration = 0

class Channel:
    def __init__(self, name, port, capacity):
        self.name = name
        self.port = port
        self.capacity = capacity
        self.queue = queue.Queue()
        self.clients = []

def parse_config(config_file: str) -> list:
    """
    Parses lines from a given configuration file and VALIDATE the format of each line. The 
    function validates each part and if valid returns a list of tuples where each tuple contains
    (channel_name, channel_port, channel_capacity). The function also ensures that there are no 
    duplicate channel names or ports. if not valid, exit with status code 1.
    Status: TODO
    Args:
        config_file (str): The path to the configuration file (e.g, config_01.txt).
    Returns:
        list: A list of tuples where each tuple contains:
        (channel_name, channel_port, and channel_capacity)
    Raises:
        SystemExit: If there is an error in the configuration file format.
    """
    # Write your code here...
    # try open file
    try: 
        with open(config_file, "r") as file:
            # Read all lines from the file and strip whitespace characters
            lines = [line.strip().split() for line in file]
            c_name = 1
            port = 2
            capacity = 3
            config = []
            c_name_check = []
            port_check = []

            for line in lines:
                if len(line) != 4:
                    # print("bad length")
                    file.close()
                    sys.exit(1)
                elif line[0] == "channel":
                    if not line[c_name].isalpha():
                        # print("name not str")
                        file.close()
                        sys.exit(1)
                    elif not line[port].isdigit():
                        # print("port not digit")
                        file.close()
                        sys.exit(1)
                    elif not line[capacity].isdigit():
                        # print("capacity not digit")
                        file.close()
                        sys.exit(1)
                    elif int(line[capacity]) < 1 or int(line[capacity]) > 5:
                        # print("capacity < 1 or > 5")
                        file.close()
                        sys.exit(1)
                    if line[c_name] in c_name_check:
                        # dup name
                        file.close()
                        sys.exit(1)
                    c_name_check.append(line[c_name])
                    if line[port] in port_check:
                        # Exit if the port number already exists
                        file.close()
                        sys.exit(1)
                    port_check.append(line[port])
                    # Append the validated configuration to the config list
                    new_config = (line[1], int(line[2]), int(line[3]))
                    config.append(new_config)
        file.close()
        if len(port_check) == 2:
            sys.exit(1)
    
    except FileNotFoundError:
        # print("file not found")
        file.close()
        sys.exit(1)
    except IOError:
        # print("io error")
        file.close()
        sys.exit(1)
    # Return the processed lines
    return config

def get_channels_dictionary(parsed_lines) -> dict:
    """
    Creates a dictionary of Channel objects from parsed lines.
    Status: Given
    Args:
        parsed_lines (list): A list of tuples where each tuple contains:
        (channel_name, channel_port, and channel_capacity)
    Returns:
        dict: A dictionary of Channel objects where the key is the channel name.
    """
    channels = {}

    for channel_name, channel_port, channel_capacity in parsed_lines:
        channels[channel_name] = Channel(channel_name, channel_port, channel_capacity)

    return channels

def quit_client(client, channel) -> None:
    """
    Implement client quitting function
    Status: TODO
    """
    # if client is in queue
    if client.in_queue:
        # Write your code here...
        # remove, close connection, and print quit message in the server.
        channel.queue = remove_item(channel.queue, client)

    # if client is in channel
    if client in channel.clients:
        # Write your code here...
        # remove client from the channel, close connection, and broadcast quit message to all clients.
        channel.clients.remove(client)
    left_msg = f'[Server message ({time.strftime("%H:%M:%S")})] {client.username} has left the channel.'
    for cl in channel.clients:
        cl.connection.send(left_msg.encode())
    client.connection.close()
    
def send_client(client, channel, msg) -> None:
    """
    Implement file sending function, if args for /send are valid.
    Else print appropriate message and return.
    Status: TODO
    """
    # Write your code here...
    # if in queue, do nothing
    if client.in_queue:
        return
    else:
        # if muted, send mute message to the client
        if client.muted:
            mute_msg = f"[Server message ({time.strftime("%H:%M:%S")})] You are still muted for {client.mute_duration} seconds."
            client.connection.send(mute_msg.encode())
            return
        # if not muted, process the file sending
        else:
            # validate the command structure
            split_msg = msg.split()
            if len(split_msg) != 3:
                usage_msg = f"[Server message ({time.strftime("%H:%M:%S")})] Usage /send <target> <file path>."
                client.connection.send(usage_msg.encode())
                return
            target_username = split_msg[1]
            target_file_path = split_msg[2]

            send_success_msg_client = f"[Server message ({time.strftime("%H:%M:%S")})] You sent {split_msg[2]} to {split_msg[1]}."
            send_success_msg_server = f"[Server message ({time.strftime("%H:%M:%S")})] {client.username} sent {split_msg[2]} to {split_msg[1]}."
            non_exist_msg = f"[Server message ({time.strftime("%H:%M:%S")})] {split_msg[1]} is not here."
            invalid_msg = f"[Server message ({time.strftime("%H:%M:%S")})] {split_msg[2]} does not exist."
            # check for target existance
            target_exist = False
            for c in channel.clients:
                if c.username == target_username:
                    target_exist = True
                    target = c
            if not target_exist:
                client.connection.send(non_exist_msg.encode())

            # check for file existence
            file_exist = True
            if not os.path.isfile(target_file_path):
                file_exist = False
                client.connection.send(invalid_msg.encode())
            
            # check if receiver is in the channel, and send the file
            if target_exist and file_exist:
                with open(target_file_path, "rb") as file:
                    data = file.read()  
                filename = os.path.basename(target_file_path)
                file_size = os.path.getsize(target_file_path)
                init_msg = f"/send {filename} {file_size}"
                target.connection.sendall(init_msg.encode())
                target.connection.sendall(data)
                file.close() 
                print(send_success_msg_server)
                client.connection.send(send_success_msg_client.encode())

def list_clients(client, channels) -> None:
    """
    List all channels and their capacity
    Status: TODO
    """
    # Write your code here...
    #[ Channel] < channel_name > <channel_port> Capacity: <current >/ < capacity >,Queue: < in_queue>
    for channel in channels.values():
        msg = f"[Channel] {channel.name} {channel.port} Capacity: {len(channel.clients)}/ {channel.capacity}, Queue: {channel.queue.qsize()}."
        client.connection.send(msg.encode())

def whisper_client(client, channel, msg) -> None:
    """
    Implement whisper function, if args for /whisper are valid.
    Else print appropriate message and return.
    Status: TODO
    """
    # Write your code here...
    # if in queue, do nothing
    if client.in_queue:
        return
    else:
        # if muted, send mute message to the client
        if client.muted:
            pass
        else:
            # validate the command structure
            split_msg = msg.split()
            if len(split_msg) != 3:
                usage_msg = f"[Server message ({time.strftime("%H:%M:%S")})] Usage /whisper <username> <message>."
                client.connection.send(usage_msg.encode())
                return
            
            target_name = split_msg[1]
            whisper = split_msg[2]
            target_exist = False
            # validate if the target user is in the channel
            for c in channel.clients:
                if c.username == target_name:
                    target_exist = True
                    target = c
                    # if target user is in the channel, send the whisper message
                    whisper_msg = f"[{client.username} whispers to you: ({time.strftime("%H:%M:%S")})] {whisper}"
                    c.connection.send(whisper_msg.encode())
            
            # print whisper server message
            if target_exist:
                print(f"[{client.username} whispers to {target.username}: ({time.strftime("%H:%M:%S")})] {whisper}")
            else:
                failed_whisper = f"[Server message ({time.strftime("%H:%M:%S")})] {target_name} is not here."
                client.connection.send(failed_whisper.encode())

def switch_channel(client, channel, msg, channels) -> bool:
    """
    Implement channel switching function, if args for /switch are valid.
    Else print appropriate message and return.

    Returns: bool
    Status: TODO
    """
    # Write your code here...
    # validate the command structure
    split_msg = msg.split()
    if len(split_msg) != 2:
        usage_msg = f"[Server message ({time.strftime("%H:%M:%S")})] Usage /switch <channel_name>."
        client.connection.send(usage_msg.encode())
        return False
    
    target_channel_name = split_msg[1]

    # check if the new channel exists
    target_exists = False
    for chan in channels.values():
        if chan.name == target_channel_name:
            target_exists = True
            target_channel = chan
    if not target_exists:
        invalid_target = f"[Server message ({time.strftime("%H:%M:%S")})] {target_channel_name} does not exist."
        client.connection.send(invalid_target.encode())
        return
    # check if there is a client with the same username in the new channel
    if not check_duplicate_username(client.username, target_channel, client.connection):
        duplicate_username = f"[Server message ({time.strftime("%H:%M:%S")})] {target_channel.name} already has a user with username {client.username}."
        client.connection.send(duplicate_username.encode())
        return
    user_left_msg = f"[Server message ({time.strftime("%H:%M:%S")})] {client.username} has left the channel."
    # if all checks are correct, and client in queue
    if client.in_queue:
        # remove client from current channel queue
        remove_item(channel.queue, client)
        # broadcast queue update message to all clients in the current channel

        # tell client to connect to new channel and close connection
        switch_msg = f"/switch {target_channel.port}"
        client.connection.send(switch_msg.encode())
        client.connection.close()
        print(user_left_msg)

    # if all checks are correct, and client in channel
    else:
        # remove client from current channel
        channel.clients.remove(client)
        # tell client to connect to new channel and close connection
        switch_msg = f"/switch {target_channel.port}"
        client.connection.send(switch_msg.encode())
        client.connection.close()
        print(user_left_msg)
        for c in channel.clients:
            c.connection.send(user_left_msg.encode())

def broadcast_in_channel(client, channel, msg) -> None:
    """
    Broadcast a message to all clients in the channel.
    Status: TODO
    """
    # Write your code here...
    # if in queue, do nothing
    if client.in_queue:
        return

    # if muted, send mute message to the client
    if client.muted:
        mute_msg = f"[Server message ({time.strftime("%H:%M:%S")})] You are still muted for {client.mute_duration} seconds."
        client.connection.send(mute_msg.encode())
        return

    # broadcast message to all clients in the channel
    for cl in channel.clients:
        cl.connection.send(msg.encode())

def client_handler(client, channel, channels) -> None:
    """
    Handles incoming messages from a client in a channel. Supports commands to quit, send, switch, whisper, and list channels. 
    Manages client"s mute status and remaining time. Handles client disconnection and exceptions during message processing.
    Status: TODO (check the "# Write your code here..." block in Exception)
    Args:
        client (Client): The client to handle.
        channel (Channel): The channel in which the client is.
        channels (dict): A dictionary of all channels.
    """
    while True:
        if client.kicked:
            break
        try:
            msg = client.connection.recv(1024).decode()

            # check message for client commands
            if msg.startswith("/quit"):
                if len(msg.split()) > 1:
                    usage_msg = f"[Server message ({time.strftime("%H:%M:%S")})] Usage /quit."
                    client.connection.send(usage_msg.encode())
                else:
                    quit_client(client, channel)
                    left_msg = f"[Server message ({time.strftime("%H:%M:%S")})] {client.username} has left the channel."
                    print(left_msg)
                    break
            elif msg.startswith("/send"):
                send_client(client, channel, msg)
            elif msg.startswith("/list"):
                if len(msg.split()) > 1:
                    usage_msg = f"[Server message ({time.strftime("%H:%M:%S")})] Usage /list."
                    client.connection.send(usage_msg.encode())
                else:
                    list_clients(client, channels)
            elif msg.startswith("/whisper"):
                whisper_client(client, channel, msg)
            elif msg.startswith("/switch"):
                is_valid = switch_channel(client, channel, msg, channels)
                if is_valid:
                    break
                else:
                    continue

            # if not a command, broadcast message to all clients in the channel
            else:
                b_msg = f"[{client.username} ({time.strftime("%H:%M:%S")})] {msg}" 
                if not client.muted:
                    print(f"[{client.username} ({time.strftime("%H:%M:%S")})] {msg}")
                broadcast_in_channel(client, channel, b_msg)

            # reset remaining time before AFK
            if not client.muted:
                client.remaining_time = 100
        except EOFError:
            continue
        except OSError:
            break
        except Exception as e:
            print(f"Error in client handler: {e}")
            # remove client from the channel, close connection
            # Write your code here...
            quit_client(client, channel)
        
def check_duplicate_username(username, channel, conn) -> bool:
    """
    Check if a username is already in a channel or its queue.
    Status: TODO
    """
    # Write your code here...
    found = False
    for client in channel.clients:
        if client.username == username:
            return found
    temp_queue = queue.Queue()
    while not channel.queue.empty():
        client = channel.queue.get()
        if client.username == username:
            found = True
        temp_queue.put(client)
    while not temp_queue.empty():
        channel.queue.put(temp_queue.get())
    return not found

def position_client(channel, conn, username, new_client) -> None:
    """
    Place a client in a channel or queue based on the channel"s capacity.
    Status: TODO
    """
    # Write your code here...
    if len(channel.clients) < channel.capacity and channel.queue.empty():
        # put client in channel and reset remaining time before AFK
        new_client.remaining_time = 100
        new_client.in_queue = False
        channel.clients.append(new_client)
        msg = f"[Server message ({time.strftime("%H:%M:%S")})] {username} has joined the channel."
        broadcast_in_channel(new_client, channel, msg)
        print(f"[Server message ({time.strftime("%H:%M:%S")})] {username} has joined the {channel.name} channel.")
    else:
        # put client in queue
        new_client.in_queue = True
        channel.queue.put(new_client)
        msg = f"[Server message ({time.strftime("%H:%M:%S")})] Welcome to the {channel.name} waiting room, {username}."
        conn.sendall(msg.encode())
        # Message clients in queue
        count = 0
        temp_queue = queue.Queue()
        while not channel.queue.empty():
            client = channel.queue.get()
            temp_queue.put(client)
            msg = f"[Server message ({time.strftime("%H:%M:%S")})] You are in the waiting queue and there are {count} user(s) ahead of you."
            # client.connection.send(msg.encode())
            count += 1
        while not temp_queue.empty():
            channel.queue.put(temp_queue.get())
        new_client.connection.send(msg.encode())

def channel_handler(channel, channels) -> None:
    """
    Starts a chat server, manage channels, respective queues, and incoming clients.
    This initiates different threads for chanel queue processing and client handling.
    Status: Given
    Args:
        channel (Channel): The channel for which to start the server.
    Raises:
        EOFError: If there is an error in the client-server communication.
    """
    # Initialize server socket, bind, and listen
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("localhost", channel.port))
    server_socket.listen(channel.capacity)

    # launch a thread to process client queue
    queue_thread = threading.Thread(target=process_queue, args=(channel,))
    queue_thread.start()

    while True:
        try:
            # accept a client connection
            conn, addr = server_socket.accept()
            username = conn.recv(1024).decode()

            # check duplicate username in channel and channel"s queue
            is_valid = check_duplicate_username(username, channel, conn)
            if not is_valid: continue

            welcome_msg = f"[Server message ({time.strftime("%H:%M:%S")})] Welcome to the {channel.name} channel, {username}."
            conn.send(welcome_msg.encode())
            time.sleep(0.1)
            new_client = Client(username, conn, addr)

            # position client in channel or queue
            position_client(channel, conn, username, new_client)

            # Create a client thread for each connected client, whether they are in the channel or queue
            client_thread = threading.Thread(target=client_handler, args=(new_client, channel, channels))
            client_thread.start()
        except EOFError:
            continue

def remove_item(q, item_to_remove) -> queue.Queue:
    """
    Remove item from queue
    Status: Given
    Args:
        q (queue.Queue): The queue to remove the item from.
        item_to_remove (Client): The item to remove from the queue.
    Returns:
        queue.Queue: The queue with the item removed.
    """
    new_q = queue.Queue()
    while not q.empty():
        current_item = q.get()
        if current_item != item_to_remove:
            new_q.put(current_item)
    count = 0
    temp_queue = queue.Queue()
    while not new_q.empty():
        client = new_q.get()
        temp_queue.put(client)
        msg = f"[Server message ({time.strftime("%H:%M:%S")})] You are in the waiting queue and there are {count} user(s) ahead of you."
        client.connection.send(msg.encode())
        count += 1
    while not temp_queue.empty():
        new_q.put(temp_queue.get())
    item_to_remove.in_queue = False
    return new_q

def process_queue(channel) -> None:
    """
    Processes the queue of clients for a channel in an infinite loop. If the channel is not full, 
    it dequeues a client, adds them to the channel, and updates their status. It then sends updates 
    to all clients in the channel and queue. The function handles EOFError exceptions and sleeps for 
    1 second between iterations.
    Status: TODO
    Args:
        channel (Channel): The channel whose queue to process.
    Returns:
        None
    """
    # Write your code here...
    while True:
        try:
            # print("Queue size: ", channel.queue.qsize(), " Channel space: ", len(channel.clients) < channel.capacity)
            # time.sleep(1.5)
            if not channel.queue.empty() and len(channel.clients) < channel.capacity:
                # Dequeue a client from the queue and add them to the channel
                new_client = channel.queue.get()
                new_client.in_queue = False
                # Send join message to all clients in the channel
                channel.clients.append(new_client)
                msg = f"[Server message ({time.strftime("%H:%M:%S")})] {new_client.username} has joined the channel."
                broadcast_in_channel(new_client, channel, msg)
                
                print(f"[Server message ({time.strftime("%H:%M:%S")})] {new_client.username} has joined the {channel.name} room.")
                # Update the queue messages for remaining clients in the queue
                count = 0
                temp_queue = queue.Queue()
                while not channel.queue.empty():
                    client = channel.queue.get()
                    temp_queue.put(client)
                    msg = f"[Server message ({time.strftime("%H:%M:%S")})] You are in the waiting queue and there are {count} user(s) ahead of you."
                    client.connection.send(msg.encode())
                    count += 1
                while not temp_queue.empty():
                    channel.queue.put(temp_queue.get())
                # Reset the remaining time to 100 before AFK
                new_client.remaining_time = 100
                time.sleep(1)
        except EOFError:
            continue

def kick_user(command, channels) -> None:
    """
    Implement /kick function
    Status: TODO
    Args:
        command (str): The command to kick a user from a channel.
        channels (dict): A dictionary of all channels.
    Returns:
        None
    """
    # Write your code here...
    # validate command structure
    cmd_split = command.split()
    if len(cmd_split) != 3:
        return
    _, target_channel_name, target_name = cmd_split
    # Check if the channel exists in the dictionary
    if target_channel_name not in channels:
        print(f"[Server message ({time.strftime("%H:%M:%S")})] {target_channel_name} does not exist.")
        return
    target_channel = channels[target_channel_name]
    # Check if the user is in the channel
    target_client_exists = False
    for client in target_channel.clients:
        if client.username == target_name:
            target_client_exists = True
            target_client = client
            break
    if not target_client_exists:
        print(f"[Server message ({time.strftime("%H:%M:%S")})] {target_name} is not in {target_channel_name}.")
        return
    # Kick the user
    quit_client(target_client, target_channel)
    print(f"[Server message ({time.strftime("%H:%M:%S")})] Kicked {target_name}.")

def empty(command, channels) -> None:
    """
    Implement /empty function
    Status: TODO
    Args:
        command (str): The command to empty a channel.
        channels (dict): A dictionary of all channels.
    """
    # Write your code here...
    # validate the command structure
    split_command = command.split()
    if len(split_command) != 2:
        return
    target_channel_name = split_command[1]

    # check if the channel exists in the server
    if target_channel_name not in channels:
        print(f"[Server message ({time.strftime("%H:%M:%S")})] {target_channel_name} does not exist.")
        return
    target_channel = channels[target_channel_name]

    # if the channel exists, close connections of all clients in the channel
    while not target_channel.queue.empty():
        cl = target_channel.queue.get().connection.close()
    for client in target_channel.clients:
        target_channel.clients.remove(client)
        client.connection.close()
    print(f"[Server message ({time.strftime("%H:%M:%S")})] {target_channel_name} has been emptied.")

def mute_user(command, channels) -> None:
    """
    Implement /mute function
    Status: TODO
    Args:
        command (str): The command to mute a user in a channel.
        channels (dict): A dictionary of all channels.
    """
    # Write your code here...
    # validate the command structure
    split_command = command.split()
    if len(split_command) != 4:
        return
    _, target_channel_name, target_username, mutetime = split_command
    # check if the mute time is valid
    try:
        mute_time = int(mutetime)
    except ValueError:
        print(f"[Server message ({time.strftime("%H:%M:%S")})] Invalid mute time.")
        return
    if mute_time <= 0:
        print(f"[Server message ({time.strftime("%H:%M:%S")})] Invalid mute time.")
        return
    # check if the channel exists in the server
    target_channel_exists = False
    for channel in channels.values():
        if channel.name == target_channel_name:
            target_channel = channel
            target_channel_exists = True

    # if the channel exists, check if the user is in the channel
    target_client_exists = False
    if target_channel_exists:
        for client in target_channel.clients:
            if client.username == target_username:
                target_client_exists = True
                target_client = client

    # if user is in the channel, mute it and send messages to all clients
    if target_client_exists:
        target_client.muted = True
        target_client.mute_duration = mute_time
        print(f"[Server message ({time.strftime("%H:%M:%S")})] Muted {target_client.username} for {mute_time} seconds.")
        mute_msg = f"[Server message ({time.strftime("%H:%M:%S")})] You have been muted for {mute_time} seconds."
        target_client.connection.send(mute_msg.encode())
        server_mute_msg = f"[Server message ({time.strftime("%H:%M:%S")})] {target_client.username} has been muted for {mute_time} seconds."
        # broadcast_in_channel(target_client, target_channel, server_mute_msg)
        for cl in target_channel.clients:
            if cl.username != target_client.username:
                cl.connection.send(server_mute_msg.encode())
    # if user is not in the channel, print error message
    else:
        print(f"[Server message ({time.strftime("%H:%M:%S")})] {target_username} is not here.")
    
def shutdown(channels) -> None:
    """
    Implement /shutdown function
    Status: TODO
    Args:
        channels (dict): A dictionary of all channels.
    """
    # Write your code here...
    # close connections of all clients in all channels and exit the server
    for channel in channels.values():
        # Close connections for all clients in the channel
        for client in channel.clients:
            client.connection.close()
        
        # Close connections for all clients in the queue
        while not channel.queue.empty():
            client = channel.queue.get()
            client.connection.close()
    # end of code insertion, keep the os._exit(0) as it is
    os._exit(0)

def server_commands(channels) -> None:
    """
    Implement commands to kick a user, empty a channel, mute a user, and shutdown the server.
    Each command has its own validation and error handling. 
    Status: Given
    Args:
        channels (dict): A dictionary of all channels.
    Returns:
        None
    """
    while True:
        try:
            command = input()
            if command.startswith("/kick"):
                kick_user(command, channels)
            elif command.startswith("/empty"):
                empty(command, channels)
            elif command.startswith("/mute"):
                mute_user(command, channels)
            elif command == "/shutdown":
                shutdown(channels)
            else:
                continue
        except EOFError:
            continue
        except Exception as e:
            print(f"{e}")
            sys.exit(1)

def check_inactive_clients(channels) -> None:
    """
    Continuously manages clients in all channels. Checks if a client is muted, in queue, or has run out of time. 
    If a client"s time is up, they are removed from the channel and their connection is closed. 
    A server message is sent to all clients in the channel. The function also handles EOFError exceptions.
    Status: TODO
    Args:
        channels (dict): A dictionary of all channels.
    """
    # Write your code here...
    # parse through all the clients in all the channels
    for channel in channels.values():
        for client in channel.clients:
    # if client is muted or in queue, do nothing
            if client.in_queue or client.muted:
                continue
            if client.remaining_time <= 0:
                # remove client from the channel and close connection, print AFK message
                channel.clients.remove(client)
                client.connection.close()
                afk_msg = f"[Server message ({time.strftime("%H:%M:%S")})] {client.username} went AFK."
                broadcast_in_channel(client, channel, afk_msg)
            # if client is not muted, decrement remaining time
            # elif client
            
def handle_mute_durations(channels) -> None:
    """
    Continuously manages the mute status of clients in all channels. If a client"s mute duration has expired, 
    their mute status is lifted. If a client is still muted, their mute duration is decremented. 
    The function sleeps for 0.99 seconds between iterations and handles EOFError exceptions.
    Status: Given
    Args:
        channels (dict): A dictionary of all channels.
    """
    while True:
        try:
            for channel_name in channels:
                channel = channels[channel_name]
                for client in channel.clients:
                    if client.mute_duration <= 0:
                        client.muted = False
                        client.mute_duration = 0
                    if client.muted and client.mute_duration > 0:
                        client.mute_duration -= 1
            time.sleep(0.99)
        except EOFError:
            continue

def main():
    try:
        if len(sys.argv) != 2:
            print("Usage: python3 chatserver.py configfile")
            sys.exit(1)

        config_file = sys.argv[1]

        # parsing and creating channels
        parsed_lines = parse_config(config_file)
        channels = get_channels_dictionary(parsed_lines)

        # creating individual threads to handle channels connections
        threads = []
        for _, channel in channels.items():
            thread = threading.Thread(target=channel_handler, args=(channel, channels))
            thread.start()
            threads.append(thread)

        server_commands_thread = threading.Thread(target=server_commands, args=(channels,))
        server_commands_thread.start()
        threads.append(server_commands_thread)

        inactive_clients_thread = threading.Thread(target=check_inactive_clients, args=(channels,))
        inactive_clients_thread.start()
        threads.append(inactive_clients_thread)

        mute_duration_thread = threading.Thread(target=handle_mute_durations, args=(channels,))
        mute_duration_thread.start()
        threads.append(mute_duration_thread)

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

    except KeyboardInterrupt:
        print("Ctrl + C Pressed. Exiting...")
        os._exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        os._exit(1)


if __name__ == "__main__":
    main()

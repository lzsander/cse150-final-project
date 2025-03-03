
'''
By Lucais Sanderson & Antonio Hernandez Ruiz

Citations:

    argparse quickstart:
        https://docs.python.org/3/howto/argparse.html

    exceptions for sockets:
        https://www.networkcomputing.com/data-center-networking/python-network-programming-handling-socket-errors

    socket programming:
        https://pythontic.com/modules/socket/send
        https://www.geeksforgeeks.org/socket-programming-python/#




feel free to change any of this...
'''



import socket 
import argparse
import select
import signal
import sys
import os
import re


def gracefulExit(socket=None):
    if socket is not None:
        socket.close()
    sys.stdout.write("Exiting program\n")
    sys.exit(0)

def attemptRegister(server_ip, server_port, client_ip, client_port, client_id):

    # create socket
    try:
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error as e:
        sys.stderr.write(f"Error creating socket: {e}\n")
        gracefulExit(clientSocket)

    # establish connection to server
    try:
        clientSocket.connect((server_ip,server_port))
    except socket.gaierror as e:
        sys.stderr.write("Address-related error connecting to server:%s\n" %e)
        clientSocket.close()
        gracefulExit(clientSocket)
    except socket.error as e:
        sys.stderr.write("Connection error:%s\n" %e)
        clientSocket.close()
        gracefulExit(clientSocket)

    # sending data
    try:
        register_message = f"REGISTER\r\nclientID: {client_id}\r\nIP: {client_ip}\r\nPort: {client_port}\r\n\r\n"
        clientSocket.send(register_message.encode())
    except socket.error as e:
        sys.stderr.write("Error sending data:%s\n" %e)
        clientSocket.close()
        gracefulExit(clientSocket)


    # recieve bytes from server (if any)
    try:
        buf = clientSocket.recv(2048)
    except socket.error as e:
        sys.stderr.write("Error receiving data:%s\n"%e)
        clientSocket.close()
        gracefulExit(clientSocket)

    if not len(buf):
        sys.stdout.write("Recieved empty message from server...\n")
    else:
        pass
        #sys.stdout.write(buf.decode())

    clientSocket.close()
    return 

def attemptBridge(server_ip, server_port, client_id):

    # create socket
    try:
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error as e:
        sys.stderr.write("Error creating socket:%s\n" %e)
        gracefulExit(clientSocket)

    # establish connection to server
    try:
        clientSocket.connect((server_ip,server_port))
    except socket.gaierror as e:
        sys.stderr.write("Address-related error connecting to server:%s\n" %e)
        clientSocket.close()
        gracefulExit(clientSocket)
    except socket.error as e:
        sys.stderr.write("Connection error:%s\n" %e)
        clientSocket.close()
        gracefulExit(clientSocket)

    # sending data
    try:
        bridge_message = f"BRIDGE\r\nclientID: {client_id}\r\n\r\n"
        clientSocket.send(bridge_message.encode())
    except socket.error as e:
        sys.stderr.write("Error sending data:%s\n" %e)
        clientSocket.close()
        gracefulExit(clientSocket)

    # recieve bytes from server (if any)
    try:
        buf = clientSocket.recv(2048)
    except socket.error as e:
        sys.stderr.write("Error receiving data:%s\n"%e)
        clientSocket.close()
        gracefulExit(clientSocket)

    if not len(buf):
        print("Recieved empty message from server...")
    else:
        #sys.stdout.write(buf.decode())
        # parse clientID, IP, port
        parsed = re.search("BRIDGEACK\\r\\nclientID: (\S+)\\r\\nIP: (\S+)\\r\\nPort: (\S+)\\r\\n\\r\\n",buf.decode())

        if parsed:
            return parsed.groups()
    
    clientSocket.close()
    return None

def main():

    # grab keyboard interrupt
    try:

        # create chat socket so it can be closed 
        # by the graceful exit at any time
        try:
            chatSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as e:
            sys.stderr.write("Error creating socket:%s\n" %e)
            gracefulExit(chatSocket)

        # chat mode flag
        chat = 0

        try:
            # parse command things

            parser = argparse.ArgumentParser()
            parser.add_argument("--id",type=str)
            parser.add_argument("--port",type=int)
            parser.add_argument("--server",type=str)
            args = parser.parse_args()

            if args.id: 
                client_id = args.id
            else:
                sys.stderr.write("Error: clientID invalid\n")
                return

            if args.port: 
                client_port = int(args.port)
            else:
                sys.stderr.write("Error: port invalid\n")
                return

            if args.server: 
                server = args.server
            else:
                sys.stderr.write("Error: Server invalid\n")
                gracefullExit()

            

            server_reo = re.search("\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}:\d{4,10}", server)
            if not server_reo:
                sys.stderr.write("Error: invalid server\n")
                gracefulExit()

            server_split = re.split(":", server_reo.group())
            server_ip = server_split[0]
            server_port = int(server_split[1])

        except:
            sys.stderr.write("Error parsing options\n")
            

        registered = False

        # print student info
        sys.stdout.write(f"{client_id} running on 127.0.0.1:{client_port}\n")

        while True:
            user_input = input()
            
            if user_input == "exit":
                gracefulExit()
            elif user_input.startswith("/id"):
                sys.stdout.write(f"{client_id}\n")
            elif user_input.startswith("/register") and not registered:
                registered = attemptRegister(server_ip, server_port, "127.0.0.1", client_port, client_id)
            elif user_input.startswith("/bridge"):
                peer_info = attemptBridge(server_ip, server_port, client_id) 
                if peer_info:
                    (peer_name, peer_ip, peer_port) = peer_info
                    print(f"{peer_name},{peer_ip}:{peer_port}")
                else:
                    print("empty bridgeack")
                break
            else:
                pass

        # start chat/wait mode

        # chat message format
        #
        # initial
        # CHAT\r\nType: init\r\nclientID: {name}\r\nIP: {ip}\r\nPort: {port}\r\n\r\n
        #
        # message
        # CHAT\r\nType: message\r\nMessage: {message contents}\r\n\r\n
        #
        # end
        # CHAT\r\nType: quit\r\n\r\n
        #

        # if we recieved empty fields for our bridge request, 
        # then we are the first client and need to wait
        if not peer_info:

            # set chat mode flag 
            chat = 0

            # create socket for listening
            try:
                serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            except socket.error as e:
                sys.stderr.write(f"Error creating socket:{e}\n")
                gracefulExit(serverSocket)

            # bind socket
            try:
                serverSocket.bind(("127.0.0.1",client_port))
            except socket.error as e:
                sys.stderr.write(f"Error binding to socket: {e}\n")
                gracefulExit(serverSocket)

            # listen
            try:
                serverSocket.listen(1)
            except socket.error as e:
                sys.stderr.write(f"Error listening for peer: {e}\n")
                gracefulExit(serverSocket)


            # accept connetion 
            try:
                (chatSocket, peerAddress) = serverSocket.accept()
            except socket.error as e:
                sys.stderr.write(f"Error accepting incoming connection: {e}\n")
                serverSocket.close()
                gracefulExit()

            # close listening socket after successful connection
            serverSocket.close()

        # else we got valid client info and have responsibility 
        # to initiate chat
        else:
            # allow user to initiate /chat and begin chatting

            chat = 1

            # wait for /chat command to initiate chat
            while True:
                user_input = input()
                if user_input.startswith("/chat"):
                    # send initialization message to peer
                    break
                elif user_input.startswith("/quit"):
                    gracefullyExit(chatSocket)
                else:
                    pass

            sys.stdout.write("IN CHAT MODE\n")

            # connect to other client (as a client in the client-server relationship)
            try:
                chatSocket.connect((str(peer_ip), int(peer_port)))
            except socket.gaierror as e:
                sys.stderr.write(f"Address-related error connecting to peer: {e}\n")
                gracefulExit(clientSocket)
            except socket.error as e:
                sys.stderr.write(f"Error connecting to peer: {e}\n")
                gracefulExit(clientSocket)
                
            # send initialization to peer
            # CHAT\r\nType: init\r\nclientID: {name}\r\nIP: {ip}\r\nPort: {port}\r\n\r\n
            init_message = f"CHAT\r\nType: init\r\nclientID: {client_id}\r\nIP: 127.0.0.1\r\nPort: {client_port}\r\n\r\n"

            try:
                chatSocket.send(init_message.encode())
            except socket.error as e:
                sys.stderr.write(f"Error sending message: {e}\n")
                gracefulExit(clientSocket)

        # starting in chat mode, alternate between chat/wait
        # chat==1:chat , chat==0:wait
        while True: 
            should_exit = False

            if chat:
                # multiplex between chat socket and stdin
                while True:
                    # monitor chat socket and stdin (user input)
                    readable, writable, exceptional = select.select([chatSocket,sys.stdin],[],[])

                    for s in readable:
                        if s == chatSocket:
                            # received FIN message
                            data = chatSocket.recv(2048)
                            if not data:
                                sys.stdout.write(f"{peer_name} closed the connection")
                                gracefulExit()
                        elif s == sys.stdin:
                            outgoing_message = input()
                            if outgoing_message:
                                should_exit = True
                                break
                    if should_exit:
                        break



                # check a quit message
                if (outgoing_message.startswith("/quit")):
                    # send quit message and close connection/socket
                    quit_message = "CHAT\r\nType: quit\r\n\r\n"

                    try:
                        chatSocket.send(quit_message.encode())
                    except socket.error as e:
                        sys.stderr.write(f"Error sending quit message: {e}\n")

                    sys.stdout.write("Chat session ended\n")

                    gracefulExit(chatSocket)

                # CHAT\r\nType: message\r\nMessage: {message contents}\r\n\r\n
                chat_message = f"CHAT\r\nType: message\r\nMessage: {outgoing_message}\r\n\r\n"

                try:
                    chatSocket.send(chat_message.encode())
                except socket.error as e:
                    sys.stderr.write(f"Error sending chat message: {e}\n")
                    gracefulExit(chatSocket)
                
                # switch back to listen
                chat = 0 

            else:
                # capture incoming message
                buf = chatSocket.recv(2048)

                # check if we got a FIN
                if not buf:
                    chatSocket.close()
                    gracefulExit()

                incoming_message = buf.decode()


                #sys.stdout.write(f"raw msg: {incoming_message}\n")

                # CHAT\r\nType: init\r\nclientID: {name}\r\nIP: {ip}\r\nPort: {port}\r\n\r\n
                is_initial = re.search("CHAT\r\nType: init\r\nclientID: (\S+)\r\nIP: (\S+)\r\nPort: (\S+)\r\n\r\n", incoming_message)
                is_quit    = re.search("CHAT\r\nType: quit\r\n\r\n", incoming_message)
                # CHAT\r\nType: message\r\nMessage: {message contents}\r\n\r\n
                is_msg     = re.search("CHAT\r\nType: message\r\nMessage: (.+)\r\n\r\n", incoming_message)

                # check if message is initialization
                if is_initial:
                    # stay in client mode, waiting for first message
                    initial_groups = is_initial.groups()
                    peer_name = initial_groups[0]
                    peer_ip = initial_groups[1]
                    peer_port = initial_groups[2]
                    sys.stdout.write(f"Incoming chat request from {peer_name} {peer_ip}:{peer_port}\n")
                # check if the message is a quit
                elif is_quit:
                    sys.stdout.write(f"{peer_name} has ended the chat session\n")
                    gracefulExit(chatSocket)
                # check if its a chat message
                elif is_msg:
                    msg = is_msg.groups()[0]
                    sys.stdout.write(f"{peer_name}> {msg}\n")
                    chat = 1
                else:
                    sys.stderr.write("Malformed message from peer\n")

    except KeyboardInterrupt:
        if chat:
            # send quit message and close connection/socket
            quit_message = "CHAT\r\nType: quit\r\n\r\n"

            try:
                chatSocket.send(quit_message.encode())
            except socket.error as e:
                sys.stderr.write(f"Error sending quit message: {e}\n")

        gracefulExit(chatSocket)

   

if __name__ == '__main__':
    main()
    gracefulExit()

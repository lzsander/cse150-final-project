
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
    sys.stdout.write("Graceful exit...\n")
    sys.exit(0)

def attemptRegister(server_ip, server_port, client_ip, client_port, client_id):

    # create socket
    try:
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error as e:
        print("Error creating socket:%s" %e)
        gracefulExit(clientSocket)

    # establish connection to server
    try:
        clientSocket.connect((server_ip,server_port))
    except socket.gaierror as e:
        print("Address-related error connecting to server:%s" %e)
        clientSocket.close()
        gracefulExit(clientSocket)
    except socket.error as e:
        print("Connection error:%s" %e)
        clientSocket.close()
        gracefulExit(clientSocket)

    # sending data
    try:
        register_message = f"REGISTER\r\nclientID: {client_id}\r\nIP: {client_ip}\r\nPort: {client_port}\r\n\r\n"
        clientSocket.send(register_message.encode())
    except socket.error as e:
        print("Error sending data:%s" %e)
        clientSocket.close()
        gracefulExit(clientSocket)


    # recieve bytes from server (if any)
    try:
        buf = clientSocket.recv(2048)
    except socket.error as e:
        print("Error receiving data:%s"%e)
        clientSocket.close()
        gracefulExit(clientSocket)

    if not len(buf):
        print("empty recv")
    else:
        sys.stdout.write(buf.decode())

    clientSocket.close()
    return 

def attemptBridge(server_ip, server_port, client_id):

    # create socket
    try:
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error as e:
        print("Error creating socket:%s" %e)
        gracefulExit(clientSocket)

    # establish connection to server
    try:
        clientSocket.connect((server_ip,server_port))
    except socket.gaierror as e:
        print("Address-related error connecting to server:%s" %e)
        clientSocket.close()
        gracefulExit(clientSocket)
    except socket.error as e:
        print("Connection error:%s" %e)
        clientSocket.close()
        gracefulExit(clientSocket)

    # sending data
    try:
        bridge_message = f"BRIDGE\r\nclientID: {client_id}\r\n\r\n"
        clientSocket.send(bridge_message.encode())
    except socket.error as e:
        print("Error sending data:%s" %e)
        clientSocket.close()
        gracefulExit(clientSocket)

    # recieve bytes from server (if any)
    try:
        buf = clientSocket.recv(2048)
    except socket.error as e:
        print("Error receiving data:%s"%e)
        clientSocket.close()
        gracefulExit(clientSocket)

    if not len(buf):
        print("Recieved empty message from server...")
    else:
        sys.stdout.write(buf.decode())
        # parse clientID, IP, port
        parsed = re.search("BRIDGEACK\\r\\nclientID: (\S+)\\r\\nIP: (\S+)\\r\\nPort: (\S+)\\r\\n\\r\\n",buf.decode())

        if parsed:
            return parsed.groups()
    
    return None

def main():

    # grab keyboard interrupt
    try:

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
                sys.stderr.write("Error: clientID invalid")
                return

            if args.port: 
                client_port = int(args.port)
            else:
                sys.stderr.write("Error: port invalid")
                return

            if args.server: 
                server = args.server
            else:
                sys.stderr.write("Error: Server invalid")
                gracefullExit()

            

            server_reo = re.search("\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}:\d{4,10}", server)
            if not server_reo:
                sys.stderr.write("Error: invalid server")
                gracefulExit()

            server_split = re.split(":", server_reo.group())
            server_ip = server_split[0]
            server_port = int(server_split[1])

        except:
            sys.stderr.write("Error parsing options")
            

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

        # if we recieved empty fields for our bridge request, 
        # then we are the first client and need to wait

        '''if empty client info:
            # listen, temporarily acting as a server
            serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # bind and listen
            serverSocket.bind(("127.0.0.1",client_port))
            serverSocket.listen()

            # accept connetions 
            while True:
                (clientConnected, clientAddress) = serverSocket.accept()

                # parse the message to ensure correct formatting 
                dataFromClient = clientConnected.recv(1024).decode()

                sys.stdout.write(f"raw: {dataFromClient}\n")

                sys.stdout.write(f"Incoming chat request from {} {}:{}\n")


        # else we got valid client info
        else:
            # allow user to initiate /chat and begin chatting

            # wait for /chat command to initiate chat
            while True:
                user_input = input()
                if user_input.startswith("/chat"):
                    # send initialization message to peer
                    break

            # connect to other client (as a client in the client-server relationship)
            clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            clientSocket.connect((str(peer_ip), int(peer_port)))

        # starting in chat mode, alternate between chat/wait
        chat = 1 # chat==1:chat , chat==0:wait
        while True: 
            if chat:
                outgoing_message = input()

                # check a quit message
                if (outgoing_message.startswith("/quit")):
                    # send quit message and close connection/socket

                clientSocket.send(outgoing_message.encode())
                
                # switch back to listen
                chat = 0 

            else:
                incoming_message = clientSocket.recv(1024).decode()

                # check if the message is a quit
                if quit message:
                    # quit

                chat = 1'''
                
    except KeyboardInterrupt:
        return

   

if __name__ == '__main__':
    main()
    gracefulExit()

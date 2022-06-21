from logging import exception
import socket 
import select 
import sys

HEADER_LENGTH = 10

IP, PORT = sys.argv[1], int(sys.argv[2])

#creates the socket - same as socket server set up
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#SO_ - socket option 
#SOL_ - socket option level 
#sets REUSEADDR to 1 on socket
sock.bind((IP, PORT))

#listening for new connections
sock.listen()

#list of sockets
sock_list = [sock]

#list of connected clients
clients = {}

print(f"Listening for connections on {IP}:{PORT}")

#handles messages
def recieve_message(client_socket):
    try:
        #recieve header containing message length
        message_header = client_socket.recv(HEADER_LENGTH)

        #if no data, client closed connection
        if not len(message_header):
            return False
        
        #convert header to int
        message_length = int(message_header.decode('utf-8').strip())

        #return an object of message header and message data
        return {'header': message_header, 'data': client_socket.recv(message_length)}
    
    except:
        #client closed connection violently or lost connection
        return False 

while True:
    """calls unix select() system call or windows select() w/ params
        - rlist - sockets monitored for new data
        - wlist - sockets for data sent to (buffers not full)
        - xlist - sockets monitored for exceptions
    Returns lists:
        - reading - sockets recieved data on
        - writing - sockets ready for data send through
        - errors - sockets with exceptions"""
    read_sockets, _, exception_sockets = select.select(sock_list, [], sock_list)

    #iterate for notified sockets
    for notified_socket in read_sockets:
        #if not notified socket is server socket - new connection gets accepted
        if notified_socket == sock:
            #accept new connection
            client_socket, client_address = sock.accept()

            #client send name, recieve
            user = recieve_message(client_socket)
            
            #if false client disconnected before name sent
            if user is False:
                continue 
        
            #add socket to list
            sock_list.append(client_socket)

            #also save user name and header
            clients[client_socket] = user 

            print("Accepted new connection from {}:{}, username {}".format(*client_address, user['data'].decode('utf-8')))

        #existing socket is sending message
        else:
            #recieve message
            message = recieve_message(notified_socket)

            #if false client disconnected, clean up
            if message is False:
                print("Closing connection from: {}".format(clients[notified_socket]['data'].decode('utf-8')))

                #remove from list
                sock_list.remove(notified_socket)
                
                #remove from list of users
                del clients[notified_socket]

                continue
            
            #get user notified by socket
            user = clients[notified_socket]

            print(f'Recieved message from {user["data"].decode("utf-8")}: {message["data"].decode("utf-8")}')

            #iterate over connected clients and broadcast message
            for client_socket in clients:
                #don't send to sender
                if client_socket != notified_socket:
                    #send user and message both with headers
                    client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])

        #not necessary but handle exceptions in case
        for notified_socket in exception_sockets:
            #remove from list for socket.socket()
            sock_list.remove(notified_socket)

            #remove for our list of users
            del clients[notified_socket]
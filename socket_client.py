from distutils.log import error
from http import client
import socket 
import errno 
from threading import Thread 

HEADER_LENGTH = 10
client_socket = None 

#connect to server
def connect(ip, port, my_username, error_callback):

    global client_socket

    #create a socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        #connect to given ip and port
        client_socket.connect((ip, port))
    except Exception as e:
        #connection error
        error_callback("Connection error: {}".format(str(e)))
        return False 

    #prepare username and header
    #encode username to bytes count, and prepare header
    username = my_username.encode('utf-8')
    username_header = f"{len(username):<{HEADER_LENGTH}}".encode('utf-8')
    client_socket.send(username_header + username)

    return True 

#send a message to server
def send(message):
    #encode message to bytes, prepare header and convert to bytes
    message = message.encode('utf-8')
    message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
    client_socket.send(message_header + message)

#start listening function in a thread
#incoming message - callback when new message, error - callback when error
def start_listening(incoming_message_callback, error_callback):
    Thread(target=listen, args=(incoming_message_callback, error_callback), daemon=True).start()

#listen for messages
def listen(incoming_message_callback, error_callback):
    while True:
        try:
            #loop over recieved messages and process
            while True:
                #recieve header with username lenght
                username_header = client_socket.recv(HEADER_LENGTH)

                #if no data, close connection
                if not len(username_header):
                    error_callback("Connection closed by the server")
                
                #convert header to int value
                username_length = int(username_header.decode('utf-8').strip())

                #recieve and decode username
                username = client_socket.recv(username_length).decode('utf-8')

                #now same for message
                message_header = client_socket.recv(HEADER_LENGTH)
                message_length = int(message_header.decode('utf-8').strip())
                message = client_socket.recv(message_length).decode('utf-8')

                #print message
                incoming_message_callback(username, message)
        
        except Exception as e:
            #any other exceptions, exit
            error_callback("Reading error: {}".format(str(e)))
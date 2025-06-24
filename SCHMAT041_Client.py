#SCHMAT041 Client Implementation

import socket
import time
import threading
import sys
import os

global chatActive
chatActive = False
global chatConnected
chatConnected = False

# We create an ipv4 (AF_INET) socket object using the tcp protocol (SOCK_STREAM)
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverIP = input('Enter the IP address of the server you wish to connect to: ')
serverPort = int(input('Enter the port of the server you wish to connect to: '))
client.connect((serverIP, serverPort))







def cConnect(value):
    global chatConnected
    chatConnected = value

def cActive(value):
    global chatActive
    chatActive = value

def sendFileToPeer(sock, filename, receiveIP, receivePort):
    print(f"\nSending {filename}...")
    with open(filename, 'rb') as myFile:
        while True:
            section = myFile.read(1024)
            if not section:
                print('Sent file successfully!\nYou > ', end='')
                break
            sock.sendto(section, (receiveIP, receivePort))
        myFile.close()
        sock.sendto("".encode(), (receiveIP, receivePort))

def receiveFileFromPeer(sock, filename, receiveIP, receivePort ):
    print(f"\nReceiving {filename}...")
    filename = 'r'+filename
    with open(filename, 'wb') as myFile:
        while True:
            section, addr = sock.recvfrom(1024)
            if not section:
                print('Received file successfully! Type something to continue.')
                break
            myFile.write(section)
        myFile.close()
    #print("You > ", end='')

def listen(sock, selectedPeer, receiveIP, receivePort):
    filename = None 

    while True:
        try:
            data, addr = sock.recvfrom(1024)
            if not data:
                break  # End of file or socket closed so break from loop to continue messaging

            response = data.decode()
            if len(response.split(';')) == 2:
                fileRequest = response.split(';')
                response = fileRequest[0]
                filename = fileRequest[1]

            match response:
                case '_0':
                    print('\n')
                    print(f"{selectedPeer} has disconnected!") #user disconnected from chat, close private message
                    print('\nPlease type exit to return to menu!')
                    cActive(False)
                    break
                case 'file_request_send': #'Send' has been typed signalling to receive file to other peer
                    try:
                        sock.sendto((f"file_request_confirm;{filename}").encode(), (destIP, destPort))
                        receiveFileFromPeer(sock, filename, receiveIP, receivePort)
                    except:
                        print("Failed to send file")
                        break

                case 'file_request_confirm': #'Send' has been typed signalling to send file to other peer
                    sendFileToPeer(sock, filename, destIP, destPort)
                case 'connect_receive':#Connection code
                    try:
                        sock.sendto(('connect_relay').encode(), (destIP, destPort))
                    except: #Connection failed
                        print("Failed to connect")
                case 'connect_relay': #Confirming connection
                    try:
                        sock.sendto(('connect_confirm').encode(), (destIP, destPort))
                        print("Connected!")
                        cConnect(True)
                    except: #Failed connection
                        print("Failed to connect")
                case 'connect_confirm':
                    print("Connected!")
                    cConnect(True)
                case _:
                    sys.stdout.write("\033[F")
                    print(f"\n{selectedPeer} >", response)
                    print("You > ", end='', flush=True)
        except OSError as e: #Return error if file failed to send
            if "Bad file descriptor" in str(e):
                cActive(False)
                break  # Socket closed
            else:
                print(f"Error: {e}")

connected = False

while connected == False:
    # Input UserName
    response = client.recv(2048) # Clients response
    name = input(response.decode())	 # Name of Client
    
    client.send(str.encode(name)) # Send name of client to server

    # Input Password
    response = client.recv(2048) # Clients response
    password = input(response.decode())	 # Password of client
    client.send(str.encode(password)) # Send password of client to server

    # Set visibility
    response = client.recv(2048).decode() # Clients response
    visibility = input(response) # Visibility of client
    client.send(str.encode(visibility)) # Send Visibility of client to server

    # Receive response 
    response = client.recv(2048).decode() # Clients response
    print(f'\n{response}')

    if response == "Registration Successful" or response == "Connection Successful": # Successful registration/connection so they are connected
        connected = True

while connected:
    choice = input("\nMenu:\n0. Exit\n1. Set status\n2. View online peers\n3. Message peer\n\nEnter choice: ")
    client.send(str.encode(choice)) # Send input of client to server
    
    match choice:
        case '0': # Disconnect from server
            print("Disconnected from the server!")

            client.close()
            connected = False
        case '1': # Set Status of the user
            visibilityOptions = client.recv(2048).decode()
            visibility = input(visibilityOptions)
            client.send(str.encode(visibility))
            print(f'\nSuccessfully updated your visibility to {visibility.upper()}!')
        case '2': # Print peer list
            
            peerList = client.recv(2048).decode()
            
            print(f'\n{peerList}')
            
        case '3': # Send a request to direct message another peer         
            selectedPeer = input("\nEnter username of peer: ")
            client.send(str.encode(selectedPeer))
            
            # Get details for ports and IPs
            portInfo = client.recv(2048).decode().split(";")

            # If peer is not online or unavailable
            if portInfo[0] == "F":
                print(f'\n{selectedPeer} is not online or unavailable!')
                # Send signal to server to change user status back to 'ONLINE'
                client.send(str.encode("O"))
            # If peer is found and available, port info is recieved
            else:
                
                destIP = portInfo[0]
                destPort = int(portInfo[1])
                sourceIP = portInfo[2]
                sourcePort = int(portInfo[3])

                chatActive = True
                # We create an ipv4 (AF_INET) socket object using the udp protocol (SOCK_DGRAM)
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.bind(('', sourcePort))

                chatActive = True

                listener = threading.Thread(target=listen, daemon=True, args=(sock, selectedPeer, destIP, destPort, ))
                listener.start() # listen for a connection back from the other peer

                sock.sendto(('connect_receive').encode(), (destIP, destPort))

                
                client.send(str.encode("C")) # Send to server that they are connected!

                print('Commands:\nExit -> Exit chat\nSend -> Send media\n') # Menu for Private Messaging

                print("Sending Connection Request")     

                while chatConnected == False:
                    time.sleep(1)

                msg = input('You > ')
                
                while chatActive == True: # Manage private message of peers
                    match msg:
                        case 'exit' | 'EXIT' | 'Exit': # Command to exit out of private message
                            client.send(str.encode("O"))
                            cActive(False)
                            sock.sendto(('_0').encode(), (destIP, destPort))
                            sock.close()
                            listener.join()
                            print('Leaving chat...')
                            time.sleep(10)
                            break
                        case 'send' | 'SEND' | 'Send': # Command to send a file to the other peer
                            filename = input("Enter the filename: ")
                            if os.path.exists(filename): # If file exists in folder
                                request_message = f"file_request_send;{filename}"
                                sock.sendto(request_message.encode(), (destIP, destPort)) # send request message to other peer
                            else:
                                print(f"Error: The file '{filename}' does not exist.") # file not in folder
                        case _:
                            try:
                                sock.sendto(msg.encode(), (destIP, destPort)) # send message to other peer
                            except OSError as e:
                                if "Bad file descriptor" in str(e):
                                    print("Error: Socket closed.")
                                    break
                                else:
                                    print(f"User has not connected yet")
                                    break
                    msg = input('You > ')
                print("Chat ended.") # End of chat

            

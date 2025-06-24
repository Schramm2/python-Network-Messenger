import socket
import os
import threading
import hashlib
import time

#get the local IP Address of this computer
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('192.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

# Create Socket (TCP) Connection
serverSocket = socket.socket(family = socket.AF_INET, type = socket.SOCK_STREAM) 
host = get_local_ip()
port = 12000
ThreadCount = 0
try:
    print(host)
    print(port)
    serverSocket.bind((host, port))
except socket.error as e:
    print(str(e))

print('Waiting for a Connection..')
serverSocket.listen()
userDetails = {}

# Function : For each client 
def threaded_client(connection, address):
    loginSuccess = False

    while loginSuccess == False:
        connection.send(str.encode('ENTER USERNAME : ')) # Request Username
        username = connection.recv(2048)
        connection.send(str.encode('ENTER PASSWORD : ')) # Request Password
        password = connection.recv(2048).decode()
        username = username.decode()
        password=hashlib.sha256(str.encode(password)).hexdigest() # Password hash using SHA256

        connection.send(str.encode('ENTER VISIBILITY -> PRIVATE OR PUBLIC : ')) # Request Visibility
        visibility = connection.recv(2048).decode().upper()

        defaultStatus = 'ONLINE'

    # REGISTERATION PHASE   
    # If new user, register in userDetails Dictionary  
        if username not in userDetails:
            userDetails[username] = {
                'password': password,
                'address': address,
                'visibility': visibility,
                'status': defaultStatus
            }
            connection.send(str.encode('Registration Successful')) 
            print('Registered:', username)
            print("{:<8} {:<20} {:<15}".format('USER', 'PASSWORD', 'VISIBILITY'))
            for k, v in userDetails.items():
                label, num, vis = k, v['password'], v['visibility']
                print("{:<8} {:<20} {:<15}".format(label, num, vis))
            print("-------------------------------------------")

            loginSuccess = True
            
        else:
    # If already existing user, check if the entered password is correct
            if(userDetails[username]['password'] == password):
                userDetails[username]['visibility'] = visibility
                connection.send(str.encode('Connection Successful')) # Response Code for Connected Client 
                print('Connected : ',username)

                loginSuccess = True

            else:
                connection.send(str.encode('Login Failed')) # Response code for login failed
                print('Login Failed : ',username)

    while loginSuccess:
        choice = connection.recv(2048).decode()

        match choice:
            case '0': # Exit Chat
                print(f"{username} has disconnected!")
                userDetails[username]['status'] = 'OFFLINE'
                break
            case '1': # Change visibility
                connection.send(str.encode('\nChange Visibility: -> Public | Private: '))
                visibility = connection.recv(2048).decode()
                userDetails[username]['visibility'] = visibility.upper()
                print(f"{username} has changed visibility!")
            case '2': # Show list of peers
                # Create a list of tuples containing username and status for users with PUBLIC visibility
                peerList = [(name, details['status']) for name, details in userDetails.items() if details['visibility'] == 'PUBLIC' and name != username]
                
                if peerList == []:
                    peerList = "No Peers Online..."
                    connection.send(str.encode(peerList))
                else:
                    users = ""
                    for name, status in peerList:
                        users += f"{name} ({status})\n"
                    connection.send(str.encode(f'{users}')) # Send the list of usernames and status to the client

            case '3': # send IP and port details of peer to connect to
                originalStatus = userDetails[username]['status']
                selectedPeer = connection.recv(2048).decode()

                # Check if the selectedPeer is in the userDetails dictionary
                if (selectedPeer in userDetails) and (userDetails[selectedPeer]['status'] != 'BUSY'):
                    # Get the details of the selected peer, including address and status
                    selectedPeerDetails = userDetails[selectedPeer]
                    selectedPeerAddress = selectedPeerDetails.get('address', 'Address not available')
                    selectedPeerStatus = selectedPeerDetails.get('status', 'Status not available')
                    
                    destParts = str(selectedPeerAddress).strip("()").split(", ")
                    sourceParts = (str(userDetails[username].get('address', 'Address not available'))).strip("()").split(", ")
                    connectionDetails = (destParts[0].strip("''")+";"+destParts[1]+";"+sourceParts[0].strip("''")+";"+sourceParts[1])
                    
                    connection.send(str.encode(connectionDetails)) #Sending Port and IP details

                    # Check whether user is connected to another peer to set status
                    while True:
                        clientStatus = connection.recv(2048).decode()
                        time.sleep(1)
                        print(clientStatus)
                        if clientStatus == 'O':
                            userDetails[username]['status'] = originalStatus
                            break
                        else:
                            time.sleep(15)
                            userDetails[username]['status'] = 'BUSY'
  
                else:
                    # Send a message indicating that the selected peer was not found
                    userDetails[username]['status'] = originalStatus
                    connection.send(str.encode("F"))
                                          
while True:
    client, address = serverSocket.accept()
    client_handler = threading.Thread(
        target=threaded_client,
        args=(client, address,)  
    )
    client_handler.start()
    ThreadCount += 1
    print('Connection Request: ' + str(ThreadCount))
serverSocket.close()
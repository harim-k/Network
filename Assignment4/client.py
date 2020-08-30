from socket import * 
from threading import Thread,Lock
import time
import sys 


ServerIP = str(sys.argv[1])
ServerPORT = 10080
ServerAddr = (ServerIP, ServerPORT)
ClientIP = ''
ClientPORT = 10081

Socket = socket(AF_INET, SOCK_DGRAM)
Socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
Socket.bind((ClientIP, ClientPORT))


ClientList = {}

lock = Lock()

def GetAddrFormat(Addr):
	Addr = Addr.split(':')
	IP = Addr[0]
	PORT = int(Addr[1])

	return (IP, PORT)


def GetAddrPrintFormat(Addr):
	IP = Addr[0]
	PORT = Addr[1]

	return f"{IP}:{PORT}"



def ShowList():
	print("[Client List]")
	for (Addr, ID) in ClientList.items():
		print(ID, GetAddrPrintFormat(Addr))
	print()



def ChatClient(ClientID, Msg):
	
	# ClientID does not exists
	if ClientID not in ClientList.values():
		print(f"{ClientID} does not exist")
		print()
		return

	print(f"send message to {ClientID}")
	print()

	# send Msg to ClientID
	for (Addr, ID) in ClientList.items():
		if ID == ClientID:
			Socket.sendto(Msg.encode(), Addr)
			break
	


def Request():

	# send Requests
	while True:
		Command = input().split(' ',maxsplit=2)

		if Command[0] == "@show_list":
			ShowList()


		elif Command[0] == "@exit":
			Socket.sendto("@exit".encode(), ServerAddr)
			break


		elif len(Command) == 3 and Command[0] == "@chat":
			ClientID = Command[1]
			Msg = Command[2]
			ChatClient(ClientID, Msg)
			
		else:
			print("not executable")
			print()



def Receive():
	global ClientList

	# receive 
	while True:
		(Data, Addr) = Socket.recvfrom(1024)

		# receive from server
		if Addr == ServerAddr:
			(Command, ID, Addr) = Data.decode().split()
			Addr = GetAddrFormat(Addr)

			lock.acquire()

			if Command == "@append_list":
				print(f"{ID} {GetAddrPrintFormat(Addr)} registers")
				print()
				ClientList[Addr] = ID


			elif Command == "@delete_list":
				print(f"{ID} {GetAddrPrintFormat(Addr)} terminates")
				print()
				del(ClientList[Addr])

			ShowList()
			lock.release()

		# receive from client
		else:
			ID = ClientList[Addr]
			Msg = Data.decode()
			print(f"From {ID} [{Msg}]")
			print()



def SendKeepAlive():
	while True:
		time.sleep(10)
		Socket.sendto("@keep-alive".encode(), ServerAddr)



def ExecuteThreads():

	RequestThread = Thread(target=Request, args=())
	ReceiveThread = Thread(target=Receive, args=())
	SendKeepAliveThread = Thread(target=SendKeepAlive, args=())

	RequestThread.daemon = True
	ReceiveThread.daemon = True
	SendKeepAliveThread.daemon = True


	RequestThread.start()
	ReceiveThread.start()
	SendKeepAliveThread.start()

	RequestThread.join()
	


def Registrate():
	global ClientList

	ClientID = input("Input your ID : ")

	# send ClientID
	Socket.sendto(ClientID.encode(), ServerAddr)


	# receive ClientList
	(Data, _) = Socket.recvfrom(1024)
	List = Data.decode().split('\n')


	for ClientInfo in List:
		(ClientID, Addr) = ClientInfo.split(' ', maxsplit=2)
		Addr = GetAddrFormat(Addr)
		ClientList[Addr] = ClientID

	
	print()
	ShowList()



def Main():
	print("Client Start !!!")
	
	Registrate()

	ExecuteThreads()
	

	
if __name__ == '__main__':

	Main()

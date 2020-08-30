from socket import * 
from threading import Thread,Lock
import time

IP = ''
PORT = 10080
Timeout = 30

Socket = socket(AF_INET, SOCK_DGRAM)
Socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
Socket.bind((IP, PORT))




ClientList = {}
ClientTimer = {}

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


def TerminateClient(Addr):
	global ClientList

	ID = ClientList[Addr]
	del(ClientList[Addr])
	del(ClientTimer[Addr])

	# send TerminateClient info to existing Clients
	for ClientAddr in ClientList.keys():
		Socket.sendto(f"@delete_list {ID} {GetAddrPrintFormat(Addr)}".encode(), ClientAddr)





def RegistrateClient(NewClientID, NewAddr):
	global ClientList
	print(f"{NewClientID} {GetAddrPrintFormat(NewAddr)} registers")
	print()
	
	# send NewClient info to existing Clients
	for Addr in ClientList.keys():
		Socket.sendto(f"@append_list {NewClientID} {GetAddrPrintFormat(NewAddr)}".encode(), Addr)

	# add NewClient in ClientList 
	ClientList[NewAddr] = NewClientID
	ClientTimer[NewAddr] = time.time()

	# send ClientList to NewClient
	List = []
	for (Addr, ClientID) in ClientList.items():
		List.append(f"{ClientID} {GetAddrPrintFormat(Addr)}")
	Socket.sendto('\n'.join(List).encode(), NewAddr)

	
	ShowList()




def Response():

	while True:
		(Data, Addr) = Socket.recvfrom(1024)
		Command = Data.decode()
		
		lock.acquire()
		# exit
		if Command == "@exit":
			print(f"{ClientList[Addr]} {GetAddrPrintFormat(Addr)} is unregistered")
			TerminateClient(Addr)

		# keep-alive
		elif Command == "@keep-alive":	
			ClientTimer[Addr] = time.time()

		# Registrate
		else:
			RegistrateClient(Command, Addr)

		lock.release()


def Timer():

	while True:
		lock.acquire()
		for (Addr,Time) in ClientTimer.items():
			if time.time() - Time > Timeout:
				print(f"{ClientList[Addr]} {GetAddrPrintFormat(Addr)} if off-line")
				TerminateClient(Addr)
				break
		lock.release()



def ExecuteThreads():

	ResponseThread = Thread(target=Response, args=())
	TimerThread = Thread(target=Timer, args=())

	ResponseThread.start()
	TimerThread.start()



def Main():

	print("Server Start !!!")
	print()

	ExecuteThreads()



if __name__ == '__main__':

	Main()

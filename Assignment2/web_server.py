from socket import *
from threading import Thread
import time



user_id_dict ={'' : 0,}

def ClientRequest(connectionSocket, address):

	request_data = connectionSocket.recv(4096).decode()
	parsed_request_data = request_data.split()

	request_method = parsed_request_data[0]
	request_object = parsed_request_data[1].split('/')[1]
	request_version = parsed_request_data[2]
	
	# exception of 'favicon.ico'
	if(request_object=='favicon.ico'):
		connectionSocket.close()
		return

	
	# check login user
	if(request_data.find('user_flag=1')==-1):
		user_id = ''
	else:
		user_id = request_data.split('user_id=')[1].split(',')[0]

	if(user_id != '' 
		and user_id in user_id_dict
		and int(time.time()) - user_id_dict[user_id] < 30):
		user_id = request_data.split('user_id=')[1].split(',')[0]
	else:
		user_id = ''


	print('user_id : '+ user_id)
	print('')

	print("request_method : "+request_method)
	print("request_object : "+request_object)
	print("request_version : "+request_version)
	print('')

	# login user
	if(user_id != ''):
		Response(connectionSocket,request_object,user_id)

	# login page for first access, "index.html"
	elif(request_object == '' or request_object == 'index.html'):
		Response(connectionSocket,'index.html',user_id)
			
	# first page of login user, "secret.html"
	elif(request_method == 'POST' and request_object == 'secret.html'):

		user_id = parsed_request_data[-1].split('ID=')[1].split('&')[0]
		user_id_dict[user_id] = int(time.time())

		Response(connectionSocket,'secret.html',user_id)

	# Forbidden access Error
	else:
		print("Forbidden access Error 403")
		connectionSocket.send('HTTP/1.1 403 Forbidden\r\nContent-Type:text/html\r\n\r\n'.encode())
		connectionSocket.send('<html><body><strong>403 Forbidden</strong></body></html>'.encode())
	
	#connectionSocket.close()



def Response(connectionSocket, file_name, user_id):

	try:
		print("Response start!!!")
		print("{} to {}-user".format(file_name, user_id))
		print()

		if(user_id == ''):
			user_flag=0
		else:
			user_flag=1
			if(file_name == '' or file_name == 'index.html'):
				file_name = 'secret.html'


		# 'cookie.html'
		if(file_name == 'cookie.html'):
			remain_time = 30 - int(time.time()) + user_id_dict[user_id]
			connectionSocket.send('HTTP/1.1 200 OK\r\n'.encode())
			connectionSocket.send('Set-Cookie:user_id={},user_flag={}\r\n\r\n'.format(user_id,user_flag).encode())
			connectionSocket.send('<html><head><title>Welcome {}</title></head><body>Hello {}<br>{} seconds left until your cookie expires.</body></html>'.format(user_id,user_id,remain_time).encode())
			return


		# file 'content_length'
		file = open(file_name, 'rb').read()
		content_length = len(file)

		# file 'content_type'
		file_ext = file_name.split('.')[1]
		if(file_ext == 'html'):
			content_type = 'text/html'
		else:
			content_type = 'image/' + file_ext



		
		# response
		connectionSocket.send('HTTP/1.1 200 OK\r\n'.encode())
		connectionSocket.send('Content-Type:{}\r\n'.format(content_type).encode())
		connectionSocket.send('Content-Length:{}\r\n'.format(content_length).encode())
		connectionSocket.send('Connection: Keep-Alive\r\n'.encode())
		connectionSocket.send('Keep-Alive: timeout=5, max=100\r\n'.encode())
		connectionSocket.send('Set-Cookie:user_id={},user_flag={}\r\n'.format(user_id,user_flag).encode())
		connectionSocket.send('\r\n'.encode())
		
		connectionSocket.send(file)



		print('response\r\nHTTP/1.1 200 OK')
		print('Content-Type:{}'.format(content_type))
		print('Content-Length:{}'.format(content_length))
		print('Connection: Keep-Alive')
		print('Keep-Alive: timeout=5, max=100')
		print('Set-Cookie:user_id={},user_flag={}'.format(user_id,user_flag))
		print()
		
		print("Response success!!!")
		print("{} to {}-user".format(file_name, user_id))
		print()
		print()
		print('-------------------------------------------------------')


	# FileNotFoundError
	except:
		print("FileNotFoundError 404")
		connectionSocket.send('HTTP/1.1 404 Not Found\r\nContent-Type:text/html\r\n\r\n'.encode())
		connectionSocket.send('<html><body><strong>404 Not Found</strong></body></html>'.encode())

		return



def Main():

	serverPort = 10080
	serverSocket = socket(AF_INET, SOCK_STREAM)
	serverSocket.bind(('', serverPort))
	serverSocket.listen(100)

	print( 'The TCP server is ready to receive.' )
	print()

	while True:
		(connectionSocket, address) = serverSocket.accept()
		thread = Thread(target = ClientRequest, args=(connectionSocket, address))
		thread.start()


if __name__ == '__main__':
	Main()

	


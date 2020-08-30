import sys
from socket import *
from threading import Thread
import time

PktSize = 1400
PortNum = 10080

# write Packet log
def writePkt(LogFile, Time, PktNum, Event):
    LogFile.write('{:1.3f} pkt: {} | {}\n'.format(Time, PktNum, Event))

# write ACK log
def writeAck(LogFile, Time, AckNum, Event):
    LogFile.write('{:1.3f} ACK: {} | {}\n'.format(Time, AckNum, Event))

# write final Throughput log
def writeEnd(LogFile, Throughput):
    LogFile.write('File transfer is finished.\n')
    LogFile.write('Throughput : {:.2f} pkts/sec\n'.format(Throughput))


def fileReceiver():
    
    RecvSocket = socket(AF_INET, SOCK_DGRAM)
    RecvSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    RecvSocket.bind(('', PortNum))
    
    Buf = {}

    StartTime = 0
    
    # receive a FileName Packet(PktNum==0)
    while 1:
        (Packet, SendAddr) = RecvSocket.recvfrom(PktSize)
        PktNum = int.from_bytes(Packet[0:4], byteorder='little', signed=True)
        Data = Packet[4:]
        FileName = Data.decode()
        #print("PktNum : {}".format(PktNum))
        if PktNum == 0:
            break

    Packet = PktNum.to_bytes(4, byteorder="little") + PktNum.to_bytes(4, byteorder="little")
    RecvSocket.sendto(Packet, SendAddr)
    

    LogFile = open(FileName + "_receiving_log.txt", 'w')
    File = open(FileName, 'wb')
    

    FinPktNum = -1
    AckNum = 0
    # receive Data Packets
    while AckNum != FinPktNum:
        # receive a Packet
        (Packet, SendAddr) = RecvSocket.recvfrom(PktSize)
        PktNum = int.from_bytes(Packet[0:4], byteorder='little', signed=True)
        Data = Packet[4:]


        # StartTime
        if StartTime == 0 and PktNum != 0:
            StartTime = time.time()

        # check if FileName Packet
        if PktNum == 0:
            Packet = PktNum.to_bytes(4, byteorder="little") + PktNum.to_bytes(4, byteorder="little")
            RecvSocket.sendto(Packet, SendAddr)
            continue

        # check if Finish Packet
        if Data == b'':
            FinPktNum = PktNum
        

        # case 1 : in-order Packet
        if PktNum == AckNum+1:
            writePkt(LogFile, time.time()-StartTime, PktNum, "received")
            
            # write Data on File
            File.write(Data)
            AckNum = PktNum
            while (AckNum+1) in Buf:
                File.write(Buf.pop(AckNum+1))
                AckNum += 1

            Packet = AckNum.to_bytes(4, byteorder="little") + PktNum.to_bytes(4, byteorder="little")
            RecvSocket.sendto(Packet, SendAddr)
            writeAck(LogFile, time.time()-StartTime, AckNum, "sent")


        # case 2 : out-order Packet
        elif PktNum > AckNum+1:
            writePkt(LogFile, time.time()-StartTime, PktNum, "received")

            Buf[PktNum] = Data
            Packet = AckNum.to_bytes(4, byteorder="little") + PktNum.to_bytes(4, byteorder="little")
            RecvSocket.sendto(Packet, SendAddr)

            writeAck(LogFile, time.time()-StartTime, AckNum, "sent")


        # case 3 : already received Packet
        elif PktNum < AckNum+1:
            writePkt(LogFile, time.time()-StartTime, PktNum, "already received")

            Packet = AckNum.to_bytes(4, byteorder="little") + PktNum.to_bytes(4, byteorder="little")
            RecvSocket.sendto(Packet, SendAddr)

            writeAck(LogFile, time.time()-StartTime, AckNum, "sent")

        # print("PktNum : {}".format(PktNum))
        # print("AckNum : {}".format(AckNum))
        # print()

    
    Throughput = FinPktNum / (time.time()-StartTime)
    writeEnd(LogFile, Throughput)

    
    RecvSocket.close()
    LogFile.close()
    File.close()
    

if __name__=='__main__':
    
    fileReceiver()
  

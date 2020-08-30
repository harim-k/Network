import sys
from socket import *
from threading import Thread, Lock
from time import time

lock = Lock()

# constants
PortNum = 10080

StartTime = 0
Timeout = 1     # 1 second

PktSize = 1400  # 1400 bytes for a Pkt
PktNumSize = 4  # 4 bytes for PktNum

Alpha = 0.125
Beta = 0.25


# global variables
FinPktNum = -1
LastAckNum = -1
DupAckCnt = 0

Buf = {}

SendTime = {}

FirstRTT = 0

WaitFlag = 0
FinFlag = 0


# write Packet log
def writePkt(LogFile, Time, PktNum, Event):
    LogFile.write('{:1.3f} pkt: {} | {}\n'.format(Time, PktNum, Event))


# write ACK log
def writeAck(LogFile, Time, AckNum, Event):
    LogFile.write('{:1.3f} ACK: {} | {}\n'.format(Time, AckNum, Event))


# write final Throughput log
def writeEnd(LogFile, Throughput, AvgRTT):
    LogFile.write('File transfer is finished.\n')
    LogFile.write('Throughput : {:.2f} pkts/sec\n'.format(Throughput))
    LogFile.write('Average RTT : {:.1f} ms\n'.format(AvgRTT*1000))


# send File packets
def sendPck(SendSocket, LogFile, RecvAddr, WindowSize, SrcFilename, DstFilename):
    global StartTime, FinPktNum, LastAckNum, DupAckCnt, Timeout, Buf, SendTime, WaitFlag, FirstRTT, FinFlag
    
    
    PktNum = 0
    FirstRTT = time.time()

    # send a FileName Packet
    while 1:
        Packet = PktNum.to_bytes(4, byteorder="little") + DstFilename.encode()
        SendSocket.sendto(Packet, (RecvAddr, PortNum))
        
        time.sleep(1)
        if LastAckNum == 0:
            break
    File = open(SrcFilename, 'rb')
    PktNum += 1


    # StartTime
    StartTime = time.time()
    
    
    # send Data Packets
    while LastAckNum != FinPktNum:

        lock.acquire()

        # case 1 : Timeout -> retransmit the Packet
        if (LastAckNum+1) in Buf and (time.time()-StartTime) - SendTime[LastAckNum+1] > Timeout:
            writePkt(LogFile, time.time()-StartTime, LastAckNum+1, "timeout since {}(timeout value {})".format(SendTime[LastAckNum+1], Timeout))
            
            ReTrsNum = LastAckNum + 1
            Packet = ReTrsNum.to_bytes(4, byteorder="little") + Buf[ReTrsNum]
            SendSocket.sendto(Packet, (RecvAddr, PortNum))
            SendTime[ReTrsNum] = time.time() - StartTime
            writePkt(LogFile, SendTime[ReTrsNum], ReTrsNum, "retransmitted")
            # print("Timeout ReTrsNum : {}".format(ReTrsNum))
            WaitFlag = 1

            if FinFlag == 1:
                lock.release()
                break


        # case 2 : 3 duplicated ACKs -> retransmit the Packet
        elif (LastAckNum+1) in Buf and DupAckCnt >= 3:
            writePkt(LogFile, time.time()-StartTime, LastAckNum, "3 duplicated ACKs")
            
            ReTrsNum = LastAckNum + 1
            Packet = ReTrsNum.to_bytes(4, byteorder="little") + Buf[ReTrsNum]
            SendSocket.sendto(Packet, (RecvAddr, PortNum))
            SendTime[ReTrsNum] = time.time() - StartTime
            writePkt(LogFile, SendTime[ReTrsNum], ReTrsNum, "retransmitted")
            #print("3 duplicated ACKs ReTrsNum : {}".format(ReTrsNum))
            DupAckCnt=0
            WaitFlag=1

        

        # case 3: send a Packet
        elif WaitFlag == 0 and PktNum-LastAckNum <= WindowSize and FinPktNum < 0:
            Buf[PktNum] = File.read(PktSize - PktNumSize)
            
            # no more Packet -> send a Finish Packet
            if not Buf[PktNum]:
                File.close()
                FinPktNum = PktNum
                Buf[PktNum] = b''
            
            Packet = PktNum.to_bytes(4, byteorder="little") + Buf[PktNum]
            SendSocket.sendto(Packet, (RecvAddr, PortNum))
            SendTime[PktNum] = time.time() - StartTime
            writePkt(LogFile, SendTime[PktNum], PktNum, "sent")
            #print("PktNum : {}".format(PktNum))
            PktNum += 1

        lock.release()

    FinFlag = 1              

    
# receive ACK Packets
def recvAck(SendSocket, LogFile):
    global LastAckNum, DupAckCnt, Buf, Timeout, SendTime, WaitFlag, FinFlag


    # receive FileName ACK
    while 1:
        (Ack, _) = SendSocket.recvfrom(8)
        AckNum = int.from_bytes(Ack[0:4], byteorder='little', signed=True)
        PckNum = int.from_bytes(Ack[4:], byteorder='little', signed=True)

        if AckNum == 0:
            LastAckNum = 0
            break

    RTTCheck = {}
    # initialize AvgRTT, DevRTT
    RTT = time.time() - FirstRTT
    AvgRTT = RTT
    DevRTT = RTT/2


    # receive ACKs
    while LastAckNum != FinPktNum:

        # receive ACK
        try:
            (Ack, _) = SendSocket.recvfrom(8)
        except timeout:
            FinFlag = 1
            break

        lock.acquire()
        AckNum = int.from_bytes(Ack[0:4], byteorder='little', signed=True)
        PckNum = int.from_bytes(Ack[4:], byteorder='little', signed=True)
        writeAck(LogFile, time.time()-StartTime, AckNum, "received")
        #print("AckNum : {}".format(AckNum))
        #print("PckNum : {}".format(PckNum))


        # update AvgRTT, DevRTT, Timeout
        if PckNum not in RTTCheck:
            RTT = (time.time()-StartTime) - SendTime[PckNum]
            AvgRTT = (1-Alpha)*AvgRTT + Alpha*RTT
            DevRTT = (1-Beta)*DevRTT + Beta*abs(RTT-AvgRTT)
            Timeout = AvgRTT + 4*DevRTT
            RTTCheck[PckNum] = 1
            # writeAck(LogFile, Timeout, PckNum, "Timeout")

        
        # case 1 : correct ACK
        if AckNum > LastAckNum:
            LastAckNum = AckNum
            DupAckCnt = 0
            WaitFlag = 0


        # case 2 : duplicate Ack
        elif AckNum == LastAckNum:
            DupAckCnt += 1

        lock.release()

    # wait for sendPck End
    while 1:
        if FinFlag == 1:
            break

    # write Throughput,AvgRTT Log
    Throughput = FinPktNum / (time.time() - StartTime)
    writeEnd(LogFile, Throughput, AvgRTT)




def fileSender(RecvAddr, WindowSize, SrcFilename, DstFilename):

    SendSocket = socket(AF_INET, SOCK_DGRAM)
    SendSocket.bind(('', 0))
    SendSocket.settimeout(10)

    LogFile = open(SrcFilename + '_sending_log.txt', 'w')
    

    # Thread
    T1 = Thread(target=sendPck, args=(SendSocket, LogFile, RecvAddr, WindowSize, SrcFilename, DstFilename))
    T2 = Thread(target=recvAck, args=(SendSocket, LogFile))
    
    T1.start()
    T2.start()
    
    T1.join()
    T2.join()

    
    SendSocket.close()
    LogFile.close()


if __name__=='__main__':
    RecvAddr = sys.argv[1]  #receiver IP address
    WindowSize = int(sys.argv[2])   #window size
    SrcFilename = sys.argv[3]   #source file name
    DstFilename = sys.argv[4]   #result file name

    fileSender(RecvAddr, WindowSize, SrcFilename, DstFilename)


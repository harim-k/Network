#!/usr/bin/python

"Monitor multiple hosts using popen()/pmonitor()"

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.util import pmonitor
from mininet.link import TCLink
from mininet.clean import Cleanup
from time import time
from signal import SIGINT
import sys


"""
By default bottleneck link is set as follow 

BandWidth : 10Mbps
delay : 10ms
loss : 1%
"""

class Assignment3Topo(Topo):
    def build(self, bw_v=10, delay_v="10ms", loss_v=1):
        "Creating Switch"
        switch1 = self.addSwitch('s1')
        switch2 = self.addSwitch('s2')

        "Make New Host and Link with Switch"
        host1 = self.addHost('h1')
        self.addLink(host1, switch1)
        host2 = self.addHost('h2')
        self.addLink(host2, switch2)

        self.addLink(switch1, switch2, 
        bw=bw_v, 
        delay=delay_v,
        loss=loss_v,
        use_htb=True)
        

def runMininet():
    Cleanup.cleanup()   #Cleaning up the Mininet before start

    "You can change the bottleneck link property by modifing these parameter"
    myTopo = Assignment3Topo(bw_v = 10, delay_v="25ms", loss_v=2)  #make test network topology
    net = Mininet(topo=myTopo, link=TCLink) #make Mininet instance
    net.start()     #start Mininet

    "Get Host and host's ip address"
    hosts = net.hosts
    print "Starting test..."
    receiver = hosts[0]
    sender = hosts[1]
    recvAddr = receiver.IP()
    sendAddr = sender.IP()

    "Get parameter to run the test"
    windowSize = int(sys.argv[1])
    srcFilename = sys.argv[2]
    dstFilename = sys.argv[3]

    "execute ping for establish switching table"
    net.pingAll(timeout = "30ms") #This code must not be removed
    

    "If you want to test with ping and iperf, uncomment this"
    """
    net.pingFull([receiver,sender])
    net.iperf([receiver,sender],seconds=10)
    """

    popens = {}
    "If your code is python, uncomment this"
    
    popens[receiver] = receiver.popen('python3','receiver.py')
    popens[sender] = sender.popen('python3','sender.py',recvAddr, str(windowSize), srcFilename, dstFilename)
    

    "If your code is c++ or c, uncomment this"
    """
    popens[receiver] = receiver.popen('receiver.out')
    popens[sender] = sender.popen('sender.out',recvAddr, str(windowSize), srcFilename, dstFilename)
    """


    endTime = time()+500    #after 3 minutes mininet test will be shut

    
    "If sender or receiver print something, pmonitor will let you to see it"
    for h, line in pmonitor( popens, timeoutms=500 ):
        if h:
            print '<%s>: %s' % ( h.name, line ),
        if time() >= endTime:
            for p in popens.values():
                p.send_signal( SIGINT )
    
    net.stop()  #stop Mininet

    print "Testing fininshed"
"runMininet end"


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print "Error: You need 4 argument.(window Size, source Filename, Result Filename)"
    else:
        runMininet()

#!/users/TOOLS/LINUX/ActivePython/bin/python
"""
###############################################################################
#
# MODULE:  STCBridge_Coordinator.py
#
# AUTHOR:  L.Cutilli
#
# DATE  :  19/01/2016
#
#
# DETAILS: Python bridge to control the Spirent TestCenter 4.30 
#
#
###############################################################################
Esempi lancio singole istanze del server su porte differenti:
#  STCBridge.py connect 151.98.176.5 50001 &
#  STCBridge.py connect 151.98.176.5 50002 &
#  STCBridge.py connect 151.98.176.5 50003 &
#  STCBridge.py connect 151.98.176.5 50004 &
"""

import os
import sys
import Tkinter
import StcPython

import time
import string
import getpass
import inspect
import telnetlib
import datetime
import socket
import subprocess 
from StcPython import StcPython

class STCCoordinator:
    def __init__(self,coordinatorPort=50000):
        self.cmdSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #udp
        self.socketPort = coordinatorPort
        #risposta3=self.bashCommand("ps -aef | grep STCBridge.py | grep -v grep| awk '{print $12}' ") 
        #print "Answer[%s]" % (str(risposta3))
        print "STCCoordinator: check for socket availability [%s]" % (coordinatorPort)
        try:
            self.cmdSocket.bind(('151.98.52.74', coordinatorPort)) 
        except socket.error:
            print "*** Port [%s] already in use: end\n" % (coordinatorPort)
            self.cmdSocket.close()
            sys.exit()


    def bashCommand(self,command):
        print "bashCommand:%s\n" % (str(command))
        try:
            bashAnswer = subprocess.check_output(str(command), shell=True, executable='/bin/bash')
            bashAnswer = bashAnswer.split('\n')
        except:
            bashAnswer=['']  
        return  bashAnswer                                             

      
    def manageSocketRequests(self):
        #Input validation
        print "STCCoordinator: manage requests communication socket [%s]" % (self.socketPort)
        while True:
            data, address = self.cmdSocket.recvfrom(4096)
            data = data.strip('\n')
            print "From[%-15s] Request[%s]" % (address, data)    
            lista = data.split()
            # for (i,parola) in enumerate(lista):
            # print "parola[%i] = [%s]"% ( i, parola)    

 
            if data == "exit"or \
               data == "EXIT" or \
               data == "Exit" or \
               data == "quit" or \
               data == "Quit" or \
               data == "QUIT": 
                coordinatorAnswer = "STCCoordinator: exit request in progress" 
                self.cmdSocket.sendto(str(coordinatorAnswer), address)    
                self.cmdSocket.close()
                print coordinatorAnswer
                sys.exit()


            if data == "h" or \
               data == "H" or \
               data == "help" or \
               data == "Help" or \
               data == "HELP": 
                coordinatorAnswer = "STCCoordinator: command format: <command> [par1][par2][par3]... (command in: [help,exit,status,catalog,connect,getfreeport,portisfree])" 
                self.cmdSocket.sendto(str(coordinatorAnswer), address)    
                print coordinatorAnswer


            if data == "Status" or  data == "status" :
                # list all running server
                dummyString= "READY" 
                self.cmdSocket.sendto(str(dummyString), address)    
                print dummyString


            if data == "Catalog" or  data == "catalog" :
                # list all running server
                bashCmdString= "ps -aef | grep STCBridge.py | grep -v grep | grep connect | grep -v  \"^[[:space:]]*$\"  | awk '{print \"IpAddrSTC[\"$11\"] STCBridgeSocket[151.98.52.74:\"$12\"]\" }' " 
                coordinatorAnswer=self.bashCommand(bashCmdString) 
                self.cmdSocket.sendto(str(coordinatorAnswer), address)    
                print coordinatorAnswer


            if data == "GetFreePort" or  data == "getfreeport" :
                # return the first free port in the range 50001-50301
                for firstFreePort in range(50001,50302):
                    bashCmdString= "lsof | grep %i" % (firstFreePort)
                    coordinatorAnswer=self.bashCommand(bashCmdString) 
                    if coordinatorAnswer[0] == "":
                        #print "Iteration port %i : result string[%s] FREE)" % (firstFreePort,coordinatorAnswer)  
                        break
                    #else:  
                    #    print "Iteration port %i : result string[%s] USED)" % (firstFreePort,coordinatorAnswer)  
                    #time.sleep(4)
                if firstFreePort > 50300:
                   firstFreePort=0 # 0 if no port free has been found. 
                self.cmdSocket.sendto(str(firstFreePort), address)    
                print firstFreePort


            if lista[0] == "PortIsFree" or  lista[0] == "portisfree" :
                print len(lista)
                if  len(lista) < 2: 
                    coordinatorAnswer = "ERROR: Port [] not specified" 
                    self.cmdSocket.sendto(str(coordinatorAnswer), address)    
                    print coordinatorAnswer
                    continue
                else:
                    portNumberToCheck=lista[1]
                    print "1111111111111111111"

                try:
                    localPortNumber = int(portNumberToCheck)
                    print "2222222222222222222222222"
                except ValueError:
                    coordinatorAnswer = "ERROR: Port [%-5s] not valid" % (portNumberToCheck)
                    self.cmdSocket.sendto(str(coordinatorAnswer), address)    
                    print coordinatorAnswer
                    print "33333333333333333333333"
                    continue
                print "44444444444444444444"
                # check if the passed port is free and may be used
                bashCmdString= "lsof | grep %i" % (localPortNumber)
                coordinatorAnswer=self.bashCommand(bashCmdString) 
                if coordinatorAnswer[0] == "":
                    print "Iteration port %i : result string[%s] FREE)" % (localPortNumber,coordinatorAnswer)  
                    portIsFree= True
                else:  
                    print "Iteration port %i : result string[%s] USED)" % (localPortNumber,coordinatorAnswer)  
                    portIsFree= False
                self.cmdSocket.sendto(str(portIsFree), address)    
                print portIsFree


            if lista[0] == "Connect" or  lista[0] == "connect":
                # check ip and port presence
                print "STCCoordinator Connect"
                try:
                    STCIp = lista[1]
                    STCControlPort = lista[2]
                except:
                    coordinatorAnswer = "ERROR: IP or Port missing"
                    self.cmdSocket.sendto(str(coordinatorAnswer), address)    
                    print coordinatorAnswer
                    continue
                # validate ip  
                try:
                    socket.inet_aton(STCIp)
                except socket.error:
                    coordinatorAnswer =  "ERROR: IpAddress [%-15s] not valid" % (STCIp)
                    self.cmdSocket.sendto(str(coordinatorAnswer), address)    
                    print coordinatorAnswer
                    continue
                # validate port 
                try:
                    localPortNumber = int(STCControlPort)
                except ValueError:
                    coordinatorAnswer = "ERROR: Port [%-5s] not valid" % (STCControlPort)
                    self.cmdSocket.sendto(str(coordinatorAnswer), address)    
                    print coordinatorAnswer
                    continue
                if localPortNumber < 50001 or localPortNumber > 50300:
                    coordinatorAnswer = "ERROR: Port [%-5i] not in the range (50001-50300)" % (localPortNumber)
                    self.cmdSocket.sendto(str(coordinatorAnswer), address)    
                    print coordinatorAnswer
                    continue
                print "STCIp[%s] STCControlPort[%s]" % (STCIp,STCControlPort)
 
                # verify STC instrument pingabile
                pingAnswer = os.system("ping -c 1 " + STCIp)
                if pingAnswer != 0:
                    coordinatorAnswer =  "ERROR: IpAddress [%-15s] no ping answer" % (STCIp)
                    self.cmdSocket.sendto(str(coordinatorAnswer), address)    
                    print coordinatorAnswer
                    continue

                # verify local port availability for new STCBridge.py instance 
                bashCmdString= "ps -aef | grep STCBridge.py | grep -v grep| awk '{print $12}' | grep  %s" % ( STCControlPort )
                usedPortList=self.bashCommand(bashCmdString) 
                if STCControlPort in usedPortList:
                    bashCmdString= "ps -aef | grep STCBridge.py | grep  %s  | grep -v grep " % ( STCControlPort )
                    processBoundToPort=self.bashCommand(bashCmdString) 
                    coordinatorAnswer =  "ERROR: Port [%-7s] already used by [%s]" % (STCControlPort, str(processBoundToPort))
                    self.cmdSocket.sendto(str(coordinatorAnswer), address)    
                    print coordinatorAnswer
                    continue

                # launch new STCBridge.py instance on STCControlPort port 
                bashCmdString= "/SMO_Tools/STCBridge.py connect %s %s " % (STCIp ,STCControlPort)
                bashCmdList= bashCmdString.split()
                print "Trying to run [%s] List: [ %s ] " % (bashCmdString,str(bashCmdList))
                subprocess.Popen(bashCmdList, close_fds=True)  
                # relax until STCBridge.py finally runs
                time.sleep(2)

                # verify if thew new  STCBridge.py instance is really running now
                bashCmdString= "ps -aef | grep STCBridge.py | grep -v grep | grep  %s  | grep  %s " % (STCIp, STCControlPort )
                checkNewProcess=self.bashCommand(bashCmdString) 
                if checkNewProcess != "":
                    coordinatorAnswer =  "SUCCESS: STC [%s] now reachable via UDP requests [151.98.52.74:%s]" % (STCIp, STCControlPort)
                    self.cmdSocket.sendto(str(coordinatorAnswer), address)    
                    print coordinatorAnswer
                else: 
                    coordinatorAnswer =  "ERROR: new STCBridge.py server [%s] [%s] not running" % (STCIp, STCControlPort)
                    self.cmdSocket.sendto(str(coordinatorAnswer), address)    
                    print coordinatorAnswer
                    continue
 

#######################################################################
#
#   MODULE TEST - Test sequences used for Spirent TestCenter testing
#
#######################################################################
if __name__ == "__main__":
    
    #print "============================="
    #print " STC Bridge Coordinator "
    #print "============================="

    # check for custom socket port input 
    try:
        socketNumber=sys.argv[1]
    except:
        socketNumber=50000


    # check for custom socket port input if specified
    try:
        number = int(socketNumber)
    except ValueError:
        print "*** socketNumber [%-7s] not an integer value\n" % (socketNumber)
        sys.exit()
    if number < 50000 or number > 600000 : 
        print "*** socketNumber [%-7s] not \nan integer value in the range (50000-60000)\n" % (socketNumber)
        sys.exit()

    coordinator = STCCoordinator(number)
    coordinator.manageSocketRequests()
    sys.exit()

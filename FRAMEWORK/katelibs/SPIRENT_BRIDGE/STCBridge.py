#!/users/TOOLS/LINUX/ActivePython/bin/python
"""
###############################################################################
#
# MODULE:  STCBridge.py 
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
"""

import os
import sys
import Tkinter
import StcPython

import time
from time import gmtime, strftime, localtime
import string
import getpass
import inspect
import telnetlib
import datetime
import socket
from StcPython import StcPython
 

class InstrumentSTC430:
    def __init__(self):
        self.STCBridgeLabel = "None"
        currentDate=strftime("%Y-%m-%d %H:%M:%S", localtime())
        self.STCBridgeComment = "Started on %s" %(currentDate)       
        self.STCIpAddress = "0.0.0.0"     


        # local data structures init (handler storage )
        self.projectList      = dict()     
        self.portList         = dict()     
        self.portPath         = dict()     
        self.portLocationFromHandler = dict()     
        self.streamblockList  = dict()     
        self.generatorList    = dict()     
        self.analyzerList     = dict()     
 
        #print  self.STCBridgeComment

        """
        Spirent TestCenter
        Python API
        """
        """
        listaParametriGetProject = ["Active",\
                                  "AlarmState",\
                                  "ConfigurationFileLocalUri",\
                                  "ConfigurationFileName",\
                                  "Handle",\
                                  "LocalActive", \
                                  "Name",\
                                  "SelectedTechnologyProfiles",\
                                  "TableViewData",\
                                  "Tags",\
                                  "TestMode" ]


        listaParametriGetProject_01 = ["Active",\
                                  "AlarmState",\
                                  "ConfigurationFileLocalUri",\
                                  "ApplicationName",\
                                  "FileMappingUpdateCount",\
                                  "FtpBaseUri",\
                                  "InSimulationMode",\
                                  "IsLoadingFromConfiguration",\
                                  "LogLevel",\
                                  "RequireExternalShutdownReason",\
                                  "RequireExternalShutdownStatus",\
                                  "TestSessionName",\
                                  "UseSmbMessaging",\
                                  "ConfigurationFileName",\
                                  "Handle",\
                                  "LocalActive", \
                                  "Name",\
                                  "SelectedTechnologyProfiles",\
                                  "TableViewData",\
                                  "Tags",\
                                  "TestMode",\
                                  "Version" ]
        
        listaParametriSystemToAsk = ["Hostname",\
                                     "FirmwareVersion",\
                                     "Model",\
                                     "PartNum",\
                                     "SerialNum",\
                                     "SlotCount"]


        listaIpStrumenti=  ["151.98.28.150",\
			    "135.221.125.45",\
                            "135.221.112.171",\
                            "135.221.113.233",\
                            "151.98.176.5",\
                            "135.221.112.190",\
                            "135.221.126.95",\
                            "135.221.126.50",\
                            "151.98.28.151",\
                            "151.98.29.131",\
                            "151.98.28.214",\
                            "151.98.28.153"]

        print "Spirent TestCenter Version Recovery  ************************************"
        
        # strumento CI
        #stcIpAddress="151.98.176.5"
        # strumento segnalato da luigi beretta
        #stcIpAddress="135.221.125.45"
        #self.TestCenter=StcPython.StcPython()
        #self.TestCenter=StcPython()
        #print "[01]   CONNECT  ***************************************************"
        #self.TestCenter.connect( stcIpAddress )
        #print "[05]   CREATE PROJECT \"LoreTest\" **********************************"
        #MyProject = self.TestCenter.create('project',name = 'LoreTest')
        #print "[06]   GET \"system1\" VERSION **************************************"
        #self.TestCenter=StcPython()
        #infoToAsk="version"
        #systemToAsk="system1"  # ATTENZIONE vuole system1 e stop!!!
        #callResult = self.TestCenter.get(systemToAsk, infoToAsk)
        #print "       get(%s, %s) = [%s]" % (systemToAsk, infoToAsk, callResult)
        #infoToAsk="version"
        #infoToAsk="name"
        #infoToAsk="Active"      
        #infoToAsk="AlarmState"       
        #infoToAsk="ApplicationName"         
        #infoToAsk="FileMappingUpdateCount"       
        #infoToAsk="FtpBaseUri"        
        #infoToAsk="Handle"           
        #infoToAsk="InSimulationMode"       
        #infoToAsk="IsLoadingFromConfiguration"   
        #infoToAsk="LocalActive"   
        #infoToAsk="LogLevel"      
        #infoToAsk="Name"        
        #infoToAsk="RequireExternalShutdownReason"
        #infoToAsk="RequireExternalShutdownStatus"
        #infoToAsk="Tags"        
        #infoToAsk="TestSessionName"    
        #infoToAsk="UseSmbMessaging"      
        #infoToAsk="Version"      

        systemToAsk="system1.PhysicalChassisManager.PhysicalChassis"   
 
        for ipCorrente in listaIpStrumenti:
            #print "[%s]" % (ipCorrente)
            # MyChassis = self.TestCenter.connect( ipCorrente )
            # callResult=  self.TestCenter.get(MyChassis, "FirmwareVersion")
            # print "       get(MyChassis, %s) = [%s]" % (MyChassis, "FirmwareVersion")

            self.TestCenter=StcPython()

            self.TestCenter.connect( ipCorrente )
            #MyProject = self.TestCenter.create('project',name = ipCorrente )
  
            LCHostname = self.TestCenter.get(systemToAsk, "Hostname")
            LCFirmwareVersion = self.TestCenter.get(systemToAsk, "FirmwareVersion")
            LCModel = self.TestCenter.get(systemToAsk, "Model")
            LCPartNum = self.TestCenter.get(systemToAsk, "PartNum")
            LCSerialNum = self.TestCenter.get(systemToAsk, "SerialNum")
            LCSlotCount = self.TestCenter.get(systemToAsk, "SlotCount")
 
            print "[%-15s] %-18s %-12s %-12s %-12s  %-12s %-3s" % (ipCorrente, LCHostname ,LCFirmwareVersion , LCModel , LCPartNum , LCSerialNum , LCSlotCount )

            #self.TestCenter.delete( MyProject )
            self.TestCenter.disconnect( ipCorrente )
            #del MyProject
            print " @@ "
            del self.TestCenter
            self.TestCenter = None
            time.sleep(1)

        print "Done ********************************************************************"
        """
 



    #
    #  INTERNAL UTILITIES
    #
    def __lc_msg(self,messageForDebugPurposes):
        print "%s" % (messageForDebugPurposes)





    def getStcVersion(self, ipAddress):
        #print "-->getStcVersion"
        self.STCIpAddress = ipAddress
        self.TestCenter=StcPython()
        self.TestCenter.connect( ipAddress )
        systemToAsk="system1.PhysicalChassisManager.PhysicalChassis" 
        LCHostname = self.TestCenter.get(systemToAsk, "Hostname")
        LCFirmwareVersion = self.TestCenter.get(systemToAsk, "FirmwareVersion")
        LCModel = self.TestCenter.get(systemToAsk, "Model")
        LCPartNum = self.TestCenter.get(systemToAsk, "PartNum")
        LCSerialNum = self.TestCenter.get(systemToAsk, "SerialNum")
        LCSlotCount = self.TestCenter.get(systemToAsk, "SlotCount")
        print "[%-15s] %-18s %-12s %-12s %-12s  %-12s %-3s" % (ipAddress,\
                LCHostname ,LCFirmwareVersion , LCModel , LCPartNum , LCSerialNum , LCSlotCount )
        self.TestCenter.disconnect( ipAddress )
        #print "<--getStcVersion"
        return LCFirmwareVersion
 

    def connectStcToSocket(self, ipAddress, socketNumber):
        #Input validation
        #print "-->connectStcToSocket"
        try:
            socket.inet_aton(ipAddress)
            self.STCIpAddress = ipAddress
        except socket.error:
            print "IpAddress [%-15s] Not Valid" % (ipAddress)
            return 1
        try:
            valtmp = int(socketNumber)
        except ValueError:
            print "socketNumber [%-7s] Not Valid" % (socketNumber)
            return 2
        socketNumber=valtmp
        self.TestCenter=StcPython()
        self.TestCenter.connect( ipAddress )
        systemToAsk="system1.PhysicalChassisManager.PhysicalChassis" 
        LCHostname = self.TestCenter.get(systemToAsk, "Hostname")
        LCFirmwareVersion = self.TestCenter.get(systemToAsk, "FirmwareVersion")
        LCModel = self.TestCenter.get(systemToAsk, "Model")
        LCPartNum = self.TestCenter.get(systemToAsk, "PartNum")
        LCSerialNum = self.TestCenter.get(systemToAsk, "SerialNum")
        LCSlotCount = self.TestCenter.get(systemToAsk, "SlotCount")
        print "[%-15s] %-18s %-12s %-12s %-12s  %-12s %-3s" % (ipAddress,\
                LCHostname ,LCFirmwareVersion , LCModel , LCPartNum , LCSerialNum , LCSlotCount )

        socketNumber              # Arbitrary not-privileged port

        #s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # udp
        #s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # tcp

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # udp
        s.bind(('151.98.52.74', socketNumber)) 

        #s.listen(1)  # max 1 connessione
        #conn, addr = s.accept() # tcp
        #print 'Connected by [%d]' % (addr)
        requestCounter = int(1)
        while 1:
            data, address = s.recvfrom(4096)
            #sent = sock.sendto(data, address)    
            data = data.strip('\n')
            # kill this process
            if  "STCCOMM:exit:" in data or data == 'q' or data == 'Q':
                STCAnswer= "Close connection with Spirent TestCenter [%s] through socket[%s] " % (ipAddress,socketNumber) 
                print STCAnswer
                print "Exit as required. Bye..."
                STCAnswer = "STCREPLYBEGIN:%s:STCREPLYEND" % STCAnswer 
                s.sendto(str(STCAnswer), address)    
                s.close()
                break;

            # set/get bridge process info
            elif "STCCOMM:setlabel:" in data: 
                localLabel= string.replace(data, "STCCOMM:setlabel:" ,"" ,1)
                self.STCBridgeLabel = localLabel
                STCAnswer="Set label to [%s]" % (self.STCBridgeLabel)
                print STCAnswer
                STCAnswer = "STCREPLYBEGIN:%s:STCREPLYEND" % STCAnswer 
                s.sendto(str(STCAnswer), address)    

            elif "STCCOMM:getlabel:" in data: 
                STCAnswer="Current label [%s]" % (self.STCBridgeLabel)
                print STCAnswer
                STCAnswer = "STCREPLYBEGIN:%s:STCREPLYEND" % STCAnswer 
                s.sendto(str(STCAnswer), address)    

            elif "STCCOMM:setcomment:" in data: 
                localComment= string.replace(data, "STCCOMM:setcomment:" ,"" ,1)
                self.STCBridgeComment = localComment
                STCAnswer="Set comment to [%s]" % (self.STCBridgeComment)
                print STCAnswer
                STCAnswer = "STCREPLYBEGIN:%s:STCREPLYEND" % STCAnswer 
                s.sendto(str(STCAnswer), address)    

            elif "STCCOMM:getcomment:" in data: 
                STCAnswer="Currente label [%s]" % (self.STCBridgeComment)
                print STCAnswer
                STCAnswer = "STCREPLYBEGIN:%s:STCREPLYEND" % STCAnswer 
                s.sendto(str(STCAnswer), address)    





 
            #============================================================================
            # 
            # *** COMMANDS TO THE SPIRENT TESTCENTER ***
            # 
            #============================================================================ 


            #============================================================================ 
            #  PING
            #============================================================================ 
            elif  "STCCOMM:ping:" in data: 
                systemToAsk="system1.PhysicalChassisManager.PhysicalChassis" 
                STCAnswer = self.TestCenter.get(systemToAsk)
                print "self.TestCenter.get(%s) answer:[%s]" % (systemToAsk,STCAnswer)
                STCAnswer = "STCREPLYBEGIN:INSTRUMENTALIVE:STCDETAILSBEGIN:%s:STCDETAILSEND:STCREPLYEND" % STCAnswer 
                s.sendto(str(STCAnswer), address)    

            #============================================================================ 
            #  GET
            #============================================================================ 
            elif  "STCCOMM:get:" in data:
                localParameters= string.replace(data, "STCCOMM:get:" ,"" ,1).split(",") 
                localParameters=list(localParameters)
                STCAnswer = self.TestCenter.get(*(localParameters))
                print "self.TestCenter.get(%s) answer:[%s]" % (localParameters,STCAnswer)
                STCAnswer = "STCREPLYBEGIN:%s:STCREPLYEND" % STCAnswer 
                s.sendto(str(STCAnswer), address)    

            #============================================================================ 
            #  CONNECT
            #============================================================================ 
            elif  "STCCOMM:connect:" in data:
                localParameters= string.replace(data, "STCCOMM:connect:" ,"" ,1).split(",")  
                localParameters=list(localParameters)
                STCAnswer = self.TestCenter.connect(*(localParameters))
                print "Command connect [%s]" % (localParameters)
                STCAnswer = "STCREPLYBEGIN:%s:STCREPLYEND" % STCAnswer 
                s.sendto(str(STCAnswer), address)    












            #============================================================================ 
            #  CREATE BEGIN
            #============================================================================ 
            elif  "STCCOMM:create:" in data:
                print "data[%s]" % (data)

                # Create PROJECT
                if "STCCOMM:create:project:" in data:
                    localParameters = string.replace(data, "STCCOMM:create:project:" ,"" ,1)
                    self.projectList[localParameters] = self.TestCenter.create('project')
                    STCAnswer=self.projectList[localParameters]
                    self.__lc_msg("project [%s] created" % STCAnswer) 

                # RESERVE and create PORT 
                elif "STCCOMM:create:port:" in data:
                    localParameters = string.replace(data, "STCCOMM:create:port:" ,"" ,1).split(",")
                    portName=localParameters[0]
                    portSlot=localParameters[1]
                    portNumber=localParameters[2]
                    STCPortLocation="//%s/%s/%s" % (self.STCIpAddress,portSlot,portNumber)
                    try:
                        print self.TestCenter.reserve(STCPortLocation)
                    except:   
                        self.__lc_msg("Port  [%s] reservation error" % (STCPortLocation))
                        STCAnswer="ERROR: Port  [%s] reservation error" % (STCPortLocation) 
                    self.portPath[portName] = STCPortLocation 
                    self.portList[portName] = self.TestCenter.create('port',under='project1')
                    portHandler=self.portList[portName]
                    self.portLocationFromHandler[portHandler] = STCPortLocation
                    self.TestCenter.config(portHandler,location=STCPortLocation)
                    portInfo = self.TestCenter.get(portHandler)
                    self.__lc_msg("\nPort[%s]INFO:\n%s\n\n" % (portName, portInfo))
                    self.__lc_msg("port [%s] created" % localParameters) 
                    STCAnswer="SUCCESS: Port [%s] created: Port INFO[%s]" % (portName,portInfo)


                # Create STREAMBLOCK
                elif "STCCOMM:create:streamblock:" in data:
                    localParameters = string.replace(data, "STCCOMM:create:streamblock:" ,"" ,1).split(",")
                    try:
                        streamblockName=localParameters[0]
                        portName=localParameters[1]
                        portHandler=self.portList[portName]
                    except:
                        localMessage="ERROR: [%s] in execution " % (localParameters)
                        STCAnswer = "STCREPLYBEGIN:%s:STCREPLYEND" % STCAnswer 
                   
                    self.streamblockList[streamblockName] = self.TestCenter.create('streamBlock', under=portHandler )
                    streamblockHandler=self.streamblockList[streamblockName]
                    streamblockInfo = self.TestCenter.get(streamblockHandler)
                    STCAnswer="STREAMBLOCK:[%s] created under Port [%s] STREAMINFO[%s]" % (streamblockName,portName,streamblockInfo)
 

                # Create GENERATOR references
                elif "STCCOMM:create:generator:" in data:
                    localParameters = string.replace(data, "STCCOMM:create:generator:" ,"" ,1).split(",")
                    try:
                        generatorName=localParameters[0]
                        portName=localParameters[1]
                        portHandler=self.portList[portName]
                        self.generatorList[generatorName] = self.TestCenter.get(portHandler,'children-Generator' )
                        generatorHandler=self.generatorList[generatorName] 
                    except:
                        localMessage="ERROR: [%s] in execution " % (localParameters)
                        STCAnswer = "STCREPLYBEGIN:%s:STCREPLYEND" % STCAnswer 
                    STCAnswer="GENERATOR:[%s] created under Port [%s]" % (generatorHandler,portName)

 

                # Create ANALYZER references
                elif "STCCOMM:create:analyzer:" in data:
                    localParameters = string.replace(data, "STCCOMM:create:analyzer:" ,"" ,1).split(",")
                    try:
                        analyzerName=localParameters[0]
                        portName=localParameters[1]
                        portHandler=self.portList[portName]
                        self.analyzerList[analyzerName] = self.TestCenter.get(portHandler,'children-Analyzer')
                        analyzerHandler=self.analyzerList[analyzerName] 
                    except:
                        localMessage="ERROR: [%s] in execution " % (localParameters)
                        STCAnswer = "STCREPLYBEGIN:%s:STCREPLYEND" % STCAnswer 
                    STCAnswer="ANALYZER:[%s] created under Port [%s]" % (analyzerHandler,portName)











                # Create CUSTOM OBJECT
                else:
                    # Generic command management  
                    localParameters= string.replace(data, "STCCOMM:create:" ,"" ,1).split(",")
                    localParameters=list(localParameters)
                    STCAnswer = self.TestCenter.create(*(localParameters))
                    print "Command create [%s]" % (localParameters)
                STCAnswer = "STCREPLYBEGIN:%s:STCREPLYEND" % STCAnswer 
                s.sendto(str(STCAnswer), address)    




            #============================================================================ 
            #  DELETE BEGIN
            #============================================================================ 
            elif  "STCCOMM:delete:" in data:

                # Delete PROJECT
                if "STCCOMM:delete:project:" in data:
                    localParameters = string.replace(data, "STCCOMM:delete:project:" ,"" ,1)
                    try:
                        projectHandler=self.projectList[localParameters] 
                        STCAnswer = self.TestCenter.delete(projectHandler)
                        self.__lc_msg("Project [%s] deleted" % (localParameters))
                    except:   
                        self.__lc_msg("Project [%s] NOT deleted" % (localParameters))
                        STCAnswer="ERROR: Command delete project [%s] FAILED" % (localParameters)

                    STCAnswer = "STCREPLYBEGIN:%s:STCREPLYEND" % STCAnswer 
                    s.sendto(str(STCAnswer), address)    


                # RELEASE and Delete PORT 
                elif "STCCOMM:delete:port:" in data:
                    localParameters = string.replace(data, "STCCOMM:delete:port:" ,"" ,1)
                    try:
                        portHandler=self.portList[localParameters] 
                        STCAnswer = self.TestCenter.delete(portHandler)
                        self.__lc_msg("Port [%s] deleted" % (localParameters))
                    except:   
                        self.__lc_msg("Port [%s] NOT deleted" % (localParameters))
                        STCAnswer="ERROR: Command delete project [%s] FAILED" % (localParameters)

                    try:
                        STCPortLocation= self.portLocationFromHandler[portHandler]     
                    except:   
                        self.__lc_msg("Port location [%s] NOT found" % (localParameters))
                        STCAnswer="ERROR: Command delete project [%s] FAILED" % (localParameters)

                    try:
                        print self.TestCenter.release(STCPortLocation)
                    except:   
                        self.__lc_msg("Port  [%s] release error" % (STCPortLocation))
                        STCAnswer="ERROR: Port  [%s] release error" % (STCPortLocation) 
    

                    STCAnswer = "STCREPLYBEGIN:%s:STCREPLYEND" % STCAnswer 
                    s.sendto(str(STCAnswer), address)    
 

                # DELETE CUSTOM OBJECT
                else:
                    localParameters= string.replace(data, "STCCOMM:delete:" ,"" ,1).split(",")  
                    localParameters=list(localParameters)
                    STCAnswer = self.TestCenter.delete(*(localParameters))
                    print "Command delete [%s]" % (localParameters)
                    STCAnswer = "STCREPLYBEGIN:%s:STCREPLYEND" % STCAnswer 
                    s.sendto(str(STCAnswer), address)    



            #============================================================================ 
            #  DISCONNECT
            #============================================================================ 
            elif  "STCCOMM:disconnect:" in data:
                localParameters= string.replace(data, "STCCOMM:disconnect:" ,"" ,1).split(",")  
                localParameters=list(localParameters)
                STCAnswer = self.TestCenter.disconnect(*(localParameters))
                print "Command disconnect [%s]" % (localParameters)
                STCAnswer = "STCREPLYBEGIN:%s:STCREPLYEND" % STCAnswer 
                s.sendto(str(STCAnswer), address)    

            #============================================================================ 
            #  CONFIG
            #============================================================================ 
            elif  "STCCOMM:config:" in data:
                #==================
                # Config GENERATOR
                #================== 
                if "STCCOMM:config:generator:" in data:
                    localParameters= string.replace(data, "STCCOMM:config:generator:" ,"" ,1).split(",")  
                    localParameters=list(localParameters)    
                    generatorLabel=localParameters[0]  # extract the 1st element of the list 
                    del localParameters[0]
                    scvParamList=','.join(str(ii) for ii in localParameters) # the remaining part of the list now is the parameters list
                    # recover generator handler 
                    try:
                        generatorHandler=self.generatorList[generatorLabel] 
                        localString="generatorHandler [%s]: found for label[%s]" % (generatorHandler,generatorLabel) 
                        self.__lc_msg(localString)
                    except:
                        STCAnswer = "ERROR: no generatorHandler for label[%s]" % (generatorLabel) 
                        self.__lc_msg(localString)
                        STCAnswer = "STCREPLYBEGIN:%s:STCREPLYEND" % STCAnswer 
                        s.sendto(str(STCAnswer), address)    
                    # request a temporary generatorConfigHandler
                    try:
                        generatorConfigHandler= self.TestCenter.get(generatorHandler, "children-GeneratorConfig")
                        localString="generatorConfigHandler handler [%s] found for generator [%s] " % (generatorConfigHandler, generatorLabel) 
                        self.__lc_msg(localString)
                    except:
                        STCAnswer = "ERROR: no generatorConfigHandler found for generator[%s]" % (generatorLabel) 
                        self.__lc_msg(localString)
                        STCAnswer = "STCREPLYBEGIN:%s:STCREPLYEND" % STCAnswer 
                        s.sendto(str(STCAnswer), address)    
                    print "####localParameters AFTER  [%s]" % (localParameters)
                    newParamString=dict()
                    print type(newParamString)
                    print "####newParamString newParamString [%s]" % (newParamString)
                    for elementLoop in localParameters:
                        print "elementLoop [%s]" %(elementLoop)
                        tempElem=elementLoop.split("=")
                        print "tempElem [%s]" %(tempElem)
                        chiave=tempElem[0]  
                        chiave=chiave.strip()
                        try:
                            valore=tempElem[1] 
                            valore=str(valore).strip()
                            newParamString[chiave]=valore
                            print "Chiave[%s]Valore[%s]" %(chiave,valore)
                        except:
                            print "Key=val not found in [%s]" %(tempElem)
                    try:
                        STCAnswer = self.TestCenter.config(generatorConfigHandler,**newParamString)
                    except:
                        STCAnswer ="ERROR: command error from instrument (wrong parameters?)"

                    print "STCAnswer[%s] " % (STCAnswer )
                    STCAnswer = "STCREPLYBEGIN:%s:STCREPLYEND" % STCAnswer 
                    s.sendto(str(STCAnswer), address)    

                #=================
                # Config ANALYZER (needed for advanced analysis only, filtering and so on...)
                #================= 
                elif "STCCOMM:config:analyzer:" in data:
                    localParameters= string.replace(data, "STCCOMM:config:analyzer:" ,"" ,1).split(",")  
                    localParameters=list(localParameters)    
                    analyzerLabel=localParameters[0]  # extract the 1st element of the list 
                    del localParameters[0]
                    scvParamList=','.join(str(ii) for ii in localParameters) # the remaining part of the list now is the parameters list
                    # recover analyzer handler 
                    try:
                        analyzerHandler=self.analyzerList[analyzerLabel] 
                        localString="analyzerHandler [%s]: found for label[%s]" % (analyzerHandler,analyzerLabel) 
                        self.__lc_msg(localString)
                    except:
                        STCAnswer = "ERROR: no analyzerHandler for label[%s]" % (analyzerLabel) 
                        self.__lc_msg(localString)
                        STCAnswer = "STCREPLYBEGIN:%s:STCREPLYEND" % STCAnswer 
                        s.sendto(str(STCAnswer), address)    
                    # request a temporary analyzerConfigHandler
                    try:
                        analyzerConfigHandler= self.TestCenter.get(analyzerHandler, "children-AnalyzerConfig")
                        localString="analyzerConfigHandler handler [%s] found for analyzer [%s] " % (analyzerConfigHandler, analyzerLabel) 
                        self.__lc_msg(localString)
                    except:
                        STCAnswer = "ERROR: no analyzerConfigHandler found for analyzer[%s]" % (analyzerLabel) 
                        self.__lc_msg(localString)
                        STCAnswer = "STCREPLYBEGIN:%s:STCREPLYEND" % STCAnswer 
                        s.sendto(str(STCAnswer), address)    
                    print "####localParameters AFTER  [%s]" % (localParameters)
                    newParamString=dict()
                    print type(newParamString)
                    print "####newParamString newParamString [%s]" % (newParamString)
                    for elementLoop in localParameters:
                        print "elementLoop [%s]" %(elementLoop)
                        tempElem=elementLoop.split("=")
                        print "tempElem [%s]" %(tempElem)
                        chiave=tempElem[0]  
                        chiave=chiave.strip()
                        try:
                            valore=tempElem[1] 
                            valore=str(valore).strip()
                            newParamString[chiave]=valore
                            print "Chiave[%s]Valore[%s]" %(chiave,valore)
                        except:
                            print "Key=val not found in [%s]" %(tempElem)
                    try:
                        STCAnswer = self.TestCenter.config(analyzerConfigHandler,**newParamString)
                    except:
                        STCAnswer ="ERROR: command error from instrument (wrong parameters?)"

                    print "STCAnswer[%s] " % (STCAnswer )
                    STCAnswer = "STCREPLYBEGIN:%s:STCREPLYEND" % STCAnswer 
                    s.sendto(str(STCAnswer), address)    
                   


                else:
                    localParameters= string.replace(data, "STCCOMM:config:" ,"" ,1).split(",")  
                    localParameters=list(localParameters)    
                    STCAnswer = self.TestCenter.config(*(localParameters))
                    print "Command config [%s]" % (localParameters)
                    STCAnswer = "STCREPLYBEGIN:%s:STCREPLYEND" % STCAnswer 
                    s.sendto(str(STCAnswer), address)    

            #============================================================================ 
            #  PERFORM
            #============================================================================ 
            elif  "STCCOMM:perform:" in data:
                localParameters= string.replace(data, "STCCOMM:perform:" ,"" ,1).split(",")  
                localParameters=list(localParameters)
                STCAnswer = self.TestCenter.perform(*(localParameters))
                print "Command perform [%s]" % (localParameters)
                STCAnswer = "STCREPLYBEGIN:%s:STCREPLYEND" % STCAnswer 
                s.sendto(str(STCAnswer), address)    

            #============================================================================ 
            #  RESERVE
            #============================================================================ 
            elif  "STCCOMM:reserve:" in data:
                localParameters= string.replace(data, "STCCOMM:reserve:" ,"" ,1).split(",")  
                localParameters=list(localParameters)
                STCAnswer = self.TestCenter.reserve(*(localParameters))
                print "Command reserve [%s]" % (localParameters)
                STCAnswer = "STCREPLYBEGIN:%s:STCREPLYEND" % STCAnswer 
                s.sendto(str(STCAnswer), address)    

            #============================================================================ 
            #  RELEASE
            #============================================================================ 
            elif  "STCCOMM:release:" in data:
                localParameters= string.replace(data, "STCCOMM:release:" ,"" ,1).split(",")  
                localParameters=list(localParameters)
                STCAnswer = self.TestCenter.release(*(localParameters))
                print "Command release [%s]" % (localParameters)
                STCAnswer = "STCREPLYBEGIN:%s:STCREPLYEND" % STCAnswer 
                s.sendto(str(STCAnswer), address)    

            #============================================================================ 
            #  APPLY
            #============================================================================ 
            elif  "STCCOMM:apply:" in data:  # no parameters needed by apply()
                localParameters= string.replace(data, "STCCOMM:apply:" ,"" ,1).split(",")  
                localParameters=list(localParameters)
                STCAnswer = self.TestCenter.apply(*(localParameters))
                print "Command apply [%s]" % (localParameters)
                STCAnswer = "STCREPLYBEGIN:%s:STCREPLYEND" % STCAnswer 
                s.sendto(str(STCAnswer), address)    

            #============================================================================ 
            #  WAITUNTILCOMPLETE
            #============================================================================ 
            elif  "STCCOMM:waitUntilComplete:" in data:
                localParameters= string.replace(data, "STCCOMM:waitUntilComplete:" ,"" ,1).split(",")  
                localParameters=list(localParameters)
                STCAnswer = self.TestCenter.waitUntilComplete(*(localParameters))
                print "Command waitUntilComplete [%s]" % (localParameters)
                STCAnswer = "STCREPLYBEGIN:%s:STCREPLYEND" % STCAnswer 
                s.sendto(str(STCAnswer), address)    

            #============================================================================ 
            #  SUBSCRIBE
            #============================================================================ 
            elif  "STCCOMM:subscribe:" in data:
                localParameters= string.replace(data, "STCCOMM:subscribe:" ,"" ,1).split(",")  
                localParameters=list(localParameters)
                STCAnswer = self.TestCenter.subscribe(*(localParameters))
                print "Command subscribe [%s]" % (localParameters)
                STCAnswer = "STCREPLYBEGIN:%s:STCREPLYEND" % STCAnswer 
                s.sendto(str(STCAnswer), address)    

            #============================================================================ 
            #  UNSUBSCRIBE
            #============================================================================ 
            elif  "STCCOMM:unsubscribe:" in data:
                localParameters= string.replace(data, "STCCOMM:unsubscribe:" ,"" ,1).split(",")  
                localParameters=list(localParameters)
                STCAnswer = self.TestCenter.unsubscribe(*(localParameters))
                print "Command unsubscribe [%s]" % (localParameters)
                STCAnswer = "STCREPLYBEGIN:%s:STCREPLYEND" % STCAnswer 
                s.sendto(str(STCAnswer), address)    
            else:        
                print "Socket Request[%s]  From[%s]: [%s]" % (requestCounter,address,data) 
                requestCounter = requestCounter + 1
                ANSWERSTRING="Allowed command via socket are [STCCOMM:exit:|STCCOMM:ping:|STCCOMM:get:|STCCOMM:connect:|STCCOMM:create:|STCCOMM:disconnect:|STCCOMM:config:|STCCOMM:perform:|STCCOMM:delete:|STCCOMM:reserve:|STCCOMM:release:|STCCOMM:apply:|STCCOMM:waitUntilComplete:|STCCOMM:subscribe:|STCCOMM:unsubscribe:]"  
                print "Help" 
                print "%s" % (ANSWERSTRING)
                s.sendto(str(ANSWERSTRING), address)    
 
            #time.sleep(1)
        self.TestCenter.disconnect( ipAddress )
        print "<--connectStcToSocket"
        return LCFirmwareVersion

 
 

    def run(self, cmd):
        res = self.tcl.eval("return [ %s ] " % cmd)
        #print "**************************************************"
        #print res
        #print "**************************************************"
        return res

    def errorTcl(self, title="", msg=""):
        self.tcl.eval("unit::testcase   \"%s\"    \"%s\"    \"failure\"    {%s}  " % (title, title, msg))
  
  



#######################################################################
#
#   MODULE TEST - Test sequences used for Spirent TestCenter testing
#
#######################################################################
if __name__ == "__main__":
    
    #print "============================="
    #print "STC Driver  module debug"
    #print "============================="

    # parameters extraction
    param_list=sys.argv
    param_num=len(sys.argv)-1
    try:
        command=sys.argv[1]
    except:
        command=""
    try:
        param_a=sys.argv[2]
    except:
        param_a=""
    try:
        param_b=sys.argv[3]
    except:
        param_b=""
    try:
        param_c=sys.argv[4]
    except:
        param_c=""
    try:
        param_d=sys.argv[5]
    except:
        param_d=""
    try:
        param_e=sys.argv[6]
    except:
        param_e=""

    #print "Param Num  :%s" % (param_num)
    #print "Param List :%s" % (param_list)
    #print "command    :[%s]" % (command)
    #print "param_a    :[%s]" % (param_a)
    #print "param_b    :[%s]" % (param_b)
    #print "param_c    :[%s]" % (param_c)
    #print "param_d    :[%s]" % (param_d)
    #print "param_e    :[%s]" % (param_e)

    #if 'P' in 'Python':
    #    print 'YES'
    #else:
    #    print 'NO'
    #sys.exit()


    if command == "version" and param_a != "":
        print "CMD: version %s" % (param_a)
        ipAddress  = param_a
        instrument = InstrumentSTC430()
        fwVersion  = instrument.getStcVersion(ipAddress)
    elif  command == "connect":
        print "CMD: connect"  
        ipAddress    = param_a
        socketNumber = param_b
        instrument   = InstrumentSTC430()
        callResult   = instrument.connectStcToSocket(ipAddress,socketNumber)



    elif  command == "altro1":
        print "CMD: altro"  
    elif  command == "altro2":
        print "CMD: altro"  
    elif  command == "altro3":
        print "CMD: altro"  
    elif  command == "altro4":
        print "CMD: altro"  
    else:
        print "STCBridge: unknown command :%s %s %s %s %s %s" % (command, param_a, param_b, param_c, param_d, param_e )






    #print "STC[%s] Version[%s]" % (command,fwVersion)
    #input("press enter to continue 1...") # errato
    #callResult = tester.connect()

    #print " "
    #print "============================="
    #print "STC Driver  -- END--"
    #print "============================="
    #print " "
     
    #sys.exit()



    """ 
          [Tech][Python: procedure esportate dallo spirent e, in teoria, pronte all'uso][lore]

            OK
            connect #####   "connect: -Establishes a connection with a Spirent TestCenter chassis",
            usage = "stc.connect( hostnameOrIPaddress, ... )",
            example = "stc.connect( mychassis1 )"),

            OK
            create #####   "create: -Creates an object in a test hierarchy",
            usage = "stc.create( className, under = parentObjectHandle, propertyName1 = propertyValue1, ... )",
            example = 'stc.create( \'port\', under=\'project1\', location = "#{mychassis1}/1/2" )'),

            OK
            get #####   "get: -Retrieves the value of an attribute",
            usage = "stc.get( objectHandle, propertyName1, propertyName2, ... )",
            example = "stc.get( stream1, 'enabled', 'name' )"),

            OK
            disconnect #####   "disconnect: -Removes a connection with a Spirent TestCenter chassis",
            usage = "stc.disconnect( hostnameOrIPaddress, ... )" ,
            example = "stc.disconnect( mychassis1 )") ,



            
            config #####   "config: -Sets or modifies the value of an attribute",
            usage = "stc.config( objectHandle, propertyName1 = propertyValue1, ... )",
            example = "stc.config( stream1, enabled = true )"),
            
            perform #####   "perform: -Invokes an operation",
            usage = "stc.perform( commandName, propertyName1 = propertyValue1, ... )",
            example = "stc.perform( 'createdevice', parentHandleList = 'project1' createCount = 4 )"),
            
            delete #####   "delete: -Deletes an object in a test hierarchy",
            usage = "stc.delete( objectHandle )",
            example = "stc.delete( stream1 )"),
            
             
            reserve #####   "reserve: -Reserves a port group",
            usage = "stc.reserve( CSP1, CSP2, ... )",
            example = 'stc.reserve( "//#{mychassis1}/1/1", "//#{mychassis1}/1/2" )'),
            
            release #####   "release: -Releases a port group",
            usage = "stc.release( CSP1, CSP2, ... )",
            example = 'stc.release( "//#{mychassis1}/1/1", "//#{mychassis1}/1/2" )'),
            
            apply #####   "apply: -Applies a test configuration to the Spirent TestCenter firmware",
            usage = "stc.apply()",
            example = "stc.apply()"),
            
            log #####   "log: -Writes a diagnostic message to the log file",
            usage = "stc.log( logLevel, message )",
            example = "stc.log( 'DEBUG', 'This is a debug message' )"),
            
            waitUntilComplete #####   "waitUntilComplete: -Suspends your application until the test has finished",
            usage = "stc.waitUntilComplete()",
            example = "stc.waitUntilComplete()"),
            
            subscribe #####   "subscribe: -Directs result output to a file or to standard output",
            usage = "stc.subscribe( parent=parentHandle, resultParent=parentHandles, configType=configType, \
                                    resultType=resultType, viewAttributeList=attributeList, interval=interval,\
                                    fileNamePrefix=fileNamePrefix )",
            example = "stc.subscribe( parent='project1', configType='Analyzer', resulttype='AnalyzerPortResults',\
                                      filenameprefix='analyzer_port_counter' )"),
            
            unsubscribe #####   "unsubscribe: -Removes a subscription",
            usage = "stc.unsubscribe( resultDataSetHandle )",
            example = "stc.unsubscribe( resultDataSet1 )"))
          [/Tech]

    """ 
    """
          [Tech][Esempio di utilizzo di stcPython per spirent testcenter][Lore]
            Fonte: http://ekb.spirent.com/resources/sites/SPIRENT/content/live/SOLUTIONS/12000/SOL12510/en_US/ISIS-B2B-B2.txt?searchid=1453286363641

            Il codice seguente dovrebbe essere python3, ma poco importa,
            serve giusto come esempio d'uso delle api 

            # File Name:                 B2BBGPLabServer.py
            # Description:               This script demonstrates basic features 
            #                            such as creating streams, generating traffic,
            #                            enabling capture, saving realtime results
            #                            to files, and retrieving results.
            
            import sys
            import time
            ENABLE_CAPTURE = True
            
            # This loads the TestCenter library. 
            # Note that a viable Tcl environment must be available for the library to run
            # and that the Python Tkinter package must be installed.
            # The version of the TestCenter library that will be loaded will be determined
            # by normal Tcl package management. 
            #
            # COME CAMBIARE VERSIONE DI LIBRERIA PER ALLINEARLA ALLO STRUMENTO:
            #
            # The easiest way to change versions will be
            # to set the TCLLIBPATH environment variable to point to the desired version
            # just like would be done in a normal Tcl installation.
            
            from StcPython import StcPython
            stc = StcPython()
            stc.log("INFO", "Starting Test")
            
            # This line will show the TestCenter commands on stdout
            stc.config("automationoptions", logto="stdout", loglevel="INFO")
            
            # Retrieve and display the current API version.
            print("SpirentTestCenter system version:\t", stc.get("system1", "version"))
            
            # Physical topology
            szChassisIp = "10.98.3.13"
            ServerAdd = "10.98.30.36"
            iTxSlot = 6
            iTxPort = 1
            iRxSlot = 6
            iRxPort = 3
            
            # Create the root project object
            print("Creating project ...")
            hProject = stc.create("project")
            
            # Create ports
            print("Creating ports ...")
            hPortTx = stc.create("port", under=hProject, location="//{0}/{1}/{2}".format(szChassisIp, iTxSlot, iTxPort), useDefaultHost="False")
            hPortRx = stc.create("port", under=hProject, location="//{0}/{1}/{2}".format(szChassisIp, iRxSlot, iRxPort), useDefaultHost="False")
            
            # Configure physical interface.
            hPortTxCopperInterface = stc.create("EthernetCopper",  under=hPortTx)
            
            # Configure physical interface.
            hPortRxCopperInterface = stc.create("EthernetCopper",  under=hPortRx)
            
            # Attach ports.
            # Connect to a chassis
            print("Connecting ", szChassisIp)
            stc.connect(szChassisIp)
            
            # Reserve
            print("Reserving {0}/{1}/{2} and {3}/{4}/{5}".format(szChassisIp, iTxSlot, iTxPort, szChassisIp, iRxSlot, iRxPort))
            stc.reserve("{0}/{1}/{2} {3}/{4}/{5}".format(szChassisIp, iTxSlot, iTxPort, szChassisIp, iRxSlot, iRxPort))
            
            # Create the mapping between the physical ports and their logical 
            #   representation in the test configuration.
            print("Set up port mappings")
            stc.perform("SetupPortMappings")
            
            # Apply the configuration.
            print("Apply configuration")
            stc.apply()
            
            ################################ First ISIS router in B2B set-up ####################################
            hdeviceaddroptions = stc.get("project1", "children-DeviceAddrOptions")
            hnextmac = stc.get(hdeviceaddroptions, "NextMac")
            #print("first first ", hdeviceaddroptions, hnextmac)
            hrouter = stc.perform("DeviceCreate", ParentList=hProject, DeviceType="Router",  \
                                   IfStack="Ipv4If VlanIf EthIIIf", IfCount="1 1 1", Port=hPortTx)
            hrouter1 = hrouter['ReturnList']
            # print("first second ", hrouter1)
            hisisrouterconfig1 = stc.perform("ProtocolCreate", ParentList=hrouter1, CreateClassId="isisrouterconfig")
            hisisrouterconfig1 = hisisrouterconfig1['ReturnList']
            # print("First ", hrouter1, hisisrouterconfig1)
            hisislspconfig1 = stc.create("IsisLspConfig", under=hisisrouterconfig1 )
            # print("second ", hIsisLspConfig1)
            stc.config(hisisrouterconfig1, MetricMode="NARROW_AND_WIDE", HelloInterval="10", LspRefreshTime="64000",
              PsnInterval="10", EnableGracefulRestart="0", HelloPadding="true", Area1="000049")
            hethiiif1 = stc.get(hrouter1, "children-ethiiif")
            stc.config(hethiiif1, SourceMac=hnextmac)
            hvlanif1 = stc.get(hrouter1, "children-vlanif")
            stc.config(hvlanif1, VlanId="2")
            stc.config(hisisrouterconfig1, IpVersion="IPV4")
            hipv4if1 = stc.get(hrouter1, "children-ipv4if")
            stc.get(hrouter1, "children-greif")
            
            stc.perform("ProtocolAttach", ProtocolList=hisisrouterconfig1, UsesIfList=hipv4if1)
            stc.config(hisisrouterconfig1, SystemId="02-00-1f-01-01-01")
            stc.config(hisislspconfig1, SystemId="02-00-1f-01-01-01")
            stc.config(hisisrouterconfig1, TeRouterID="192.0.0.1")
            stc.config(hisislspconfig1, TERouterID="192.0.0.1")
            stc.config(hisisrouterconfig1, Level="LEVEL2")
            stc.config(hisislspconfig1, Level="LEVEL2")
            stc.config(hisislspconfig1, OL="0", Lifetime="65500")
            stc.config(hrouter1, RouterId="31.1.1.1")
            stc.config(hipv4if1, PrefixLength="30", Address="31.1.1.1", Gateway="31.1.1.2")
            stc.config(hisisrouterconfig1, HelloMultiplier="3")
            stc.config(hisisrouterconfig1, L2Metric="1")
            stc.config(hisisrouterconfig1, L2WideMetric="1")
            hisisauthenticationparams1 = stc.get(hisisrouterconfig1, "children-IsisAuthenticationParams")
            stc.config(hisisauthenticationparams1, Authentication="NONE")
            stc.apply()

            ######################################## Next ISIS router in B2B set-up ####################################
            hdeviceaddroptions = stc.get("project1", "children-DeviceAddrOptions")
            hnextmac2 = stc.get(hdeviceaddroptions, "NextMac")
            h2router = stc.perform("DeviceCreate", ParentList=hProject, DeviceType="Router", \
                                   IfStack="Ipv4If VlanIf EthIIIf", IfCount="1 1 1", Port=hPortRx)
            hrouter2 = h2router['ReturnList']
            hisisrouterconfig2 = stc.perform("ProtocolCreate", ParentList=hrouter2, CreateClassId="isisrouterconfig")
            hisisrouterconfig2 = hisisrouterconfig2['ReturnList']
            # print("First ", hrouter2, hisisrouterconfig2)
            hisislspconfig2 = stc.create("IsisLspConfig", under=hisisrouterconfig2 )
            stc.config(hisisrouterconfig2, MetricMode="NARROW_AND_WIDE", HelloInterval="10", LspRefreshTime="64000",
              PsnInterval="10", EnableGracefulRestart="0", HelloPadding="true", Area1="000049")
            hethiiif2 = stc.get(hrouter2, "children-ethiiif")
            stc.config(hethiiif2, SourceMac=hnextmac2)
            hvlanif2 = stc.get(hrouter2, "children-vlanif")
            stc.config(hvlanif2, VlanId="2")
            stc.config(hisisrouterconfig2, IpVersion="IPV4")
            hipv4if2 = stc.get(hrouter2, "children-ipv4if")
            stc.get(hrouter2, "children-greif")
            stc.perform("ProtocolAttach", ProtocolList=hisisrouterconfig2, UsesIfList=hipv4if2)
            stc.config(hisisrouterconfig2, SystemId="02-00-1f-01-01-02")
            stc.config(hisislspconfig2, SystemId="02-00-1f-01-01-02")
            stc.config(hisisrouterconfig2, TeRouterID="192.0.0.1")
            stc.config(hisislspconfig2, TERouterID="192.0.0.1")
            stc.config(hisisrouterconfig2, Level="LEVEL2")
            stc.config(hisislspconfig2, Level="LEVEL2")
            stc.config(hisislspconfig2, OL="0", Lifetime="65500")
            stc.config(hrouter2, RouterId="31.1.2.1")
            stc.config(hipv4if2, PrefixLength="30", Address="31.1.1.2", Gateway="31.1.1.1")
            stc.config(hisisrouterconfig2, HelloMultiplier="3")
            stc.config(hisisrouterconfig2, L2Metric="1")
            stc.config(hisisrouterconfig2, L2WideMetric="1")
            hisisauthenticationparams2 = stc.get(hisisrouterconfig1, "children-IsisAuthenticationParams")
            stc.config(hisisauthenticationparams2, Authentication="NONE")
            #######################################################################################################

            # Subscribe to realtime results.
            print("Subscribe to results")
            hTestResultSetting = stc.get(hProject, "children-TestResultSetting")
            stc.config(hTestResultSetting, saveResultsRelativeTo="NONE", resultsDirectory="C:\\temp3\\PythonScripts\\")
            hisisrouterresults = stc.subscribe(Parent=hProject, ResultParent=hProject, configType="isisrouterconfig",
                  resultType="isisrouterresults", interval=1, filenamePrefix="isisrouterresultA")
            stc.sleep(2)
            
            ############################################# RUN ######################################
            stc.perform("DeviceStart", DeviceList=hrouter1)
            stc.perform("ProtocolStart", ProtocolList=hisisrouterconfig1)
            stc.perform("DeviceStart", DeviceList=hrouter2)
            stc.perform("ProtocolStart", ProtocolList=hisisrouterconfig2)

            ############################################### Get REsults ###########################################
            hisisrouterresults1 = stc.get(hisisrouterconfig1, "children-IsisRouterResults")
            print("hisisrouterresults1 ", stc.get(hisisrouterresults1, "adjacencylevel"), " RxL1LanHelloCount:",\
                   stc.get(hisisrouterresults1, "RxL1LanHelloCount"))
            hisisrouterresults2 = stc.get(hisisrouterconfig2, "children-IsisRouterResults")
            print("hisisrouterresults2 ", stc.get(hisisrouterresults2, "adjacencylevel"), " RxL1LanHelloCount:", \
                   stc.get(hisisrouterresults2, "RxL1LanHelloCount"))
            print(" hisisrouterconfig1  L2LanAdjacencyState:", stc.get(hisisrouterconfig1, "L2LanAdjacencyState"))
            print(" hisisrouterconfig2  L2LanAdjacencyState:", stc.get(hisisrouterconfig2, "L2LanAdjacencyState"))
            print(" hisisrouterconfig1  RouterState:",  stc.get(hisisrouterconfig1, "RouterState"))
            print(" hisisrouterconfig2  RouterState:",  stc.get(hisisrouterconfig2, "RouterState"))
            stc.sleep(50)
            hisisrouterresults1 = stc.get(hisisrouterconfig1, "children-IsisRouterResults")
            print("hisisrouterresults1 ", stc.get(hisisrouterresults1, "adjacencylevel"), " RxL1LanHelloCount:",\
                   stc.get(hisisrouterresults1, "RxL1LanHelloCount"))
            hisisrouterresults2 = stc.get(hisisrouterconfig2, "children-IsisRouterResults")
            print("hisisrouterresults2 ", stc.get(hisisrouterresults2, "adjacencylevel"), " RxL1LanHelloCount:",\
                   stc.get(hisisrouterresults2, "RxL1LanHelloCount"))
            print(" hisisrouterconfig1  L2LanAdjacencyState:", stc.get(hisisrouterconfig1, "L2LanAdjacencyState"))
            print(" hisisrouterconfig2  L2LanAdjacencyState:", stc.get(hisisrouterconfig2, "L2LanAdjacencyState"))
            print(" hisisrouterconfig1  RouterState:",  stc.get(hisisrouterconfig1, "RouterState"))
            print(" hisisrouterconfig2  RouterState:",  stc.get(hisisrouterconfig2, "RouterState"))
            exit()
            
          [/Tech]







    """










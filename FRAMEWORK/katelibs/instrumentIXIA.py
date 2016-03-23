#!/usr/bin/env python
"""
###############################################################################
#
# MODULE:  instrumentIXIA.py
#
# AUTHOR:  L.Cutilli
#
# DATE  :  18/02/2016
#
#
# DETAILS: Python management module for IXIA test equipments
#
# MODULE: instrumentIXIA.py
#                          
#
###############################################################################
"""

import os
import sys
import time
import string
import getpass
import inspect
import telnetlib
import datetime
import socket

from katelibs.equipment import Equipment
from katelibs.kenviron import KEnvironment
from katelibs.kunit import Kunit
from katelibs.database import *
from katelibs.IxNetwork import *

class InstrumentIXIA(Equipment):

    def __init__(self, label, kenv):
        """ label   : equipment name used on Report file
            kenv    : instance of KEnvironment (initialized by K@TE FRAMEWORK)
        """
        # Enviroment
        self.__kenv                 = kenv             # Kate Environment
        self.__krepo                = kenv.krepo       # result report (Kunit class instance)
        self.__prs                  = kenv.kprs        # Presets for running environment
        # Session
        self.__ontType              = None             #  Specify 5xx for Ont50,506,512  6xx for Ont 601
        self.__sessionName          = "Session_KATE"   #  To be changed: meaningfuls only for  5xx 
        # Initizalization flag:
        self.__calledMethodList     = []               #  used to track all method called
        self.__calledMethodStatus   = dict()           #  used to track all method called and last execution result
        # Bridge Connection
        self.__bridgeIpAddress      = "151.98.40.136"  # ixnetwork server address       
        self.__bridgePort           = 8009             # ixnetwork server port
        self.__pingRetryNumber      = 1                #  Retry number for -c ping option
        self.__maxPortNumberForCard = 32               #  Retry number for -c ping option
        self.__checkPortUpRetries   = 60               #  Retry number for -c ping option
        self.__IXN        = None             # none before init
        # Chassis Connection
        self.__chassisIpAddress      = None             # ixia instrument (chassis) address       
        self.__chassisHandler        = None             # none before init
        #Data model (DM) main hooks
        self.__DM_ROOT               = None                       
        self.__DM_NULL               = None                       
        #self.__DM_EVENTSCHEDULER    = None                       
        #self.__DM_GLOBALS           = None                       
        #self.__DM_VPORT             = None                       
        #self.__DM_AVAILABLEHARDWARE = None                       
        #self.__DM_STATISTICS        = None                       
        #self.__DM_TESTCONFIGURATION = None                       
        #self.__DM_TRAFFIC           = None                       
        #Chassis-specific Data model  
        self.__DM_CHASSIS           = None                       
        self.__DM_CARDLIST          = dict()                        
        self.__DM_PORTLIST          = dict()                        
        self.__DM_VPORTLIST         = dict()                        
        self.__DM_VPORTINTERFACE    = dict()         
        
        #Port-specific Data model   
        self.__DM_PORT_IP_ADDRESS   = dict()                       
        self.__DM_PORT_IP_GETAWAY   = dict()                       
        self.__DM_PORT_MAC_ADDRESS  = dict()                       
        self.__DM_PORT_IPV4IFACE_OBJ= dict()                       


        #Traffic-specific Data model   
        self.__DM_TRAFFICLIST       = dict()                       
        self.__DM_TRAFFIC_ENDPOINT  = dict()                       

       
        # !!! Don't delete the following lines !!!
        super().__init__(label, self.__prs.get_id(label))
        self.__get_instrument_info_from_db(self.__prs.get_id(label)) # inizializza i dati di IP, tipo di Strumento ecc... dal DB
           

    #
    #   USEFUL FUNC & TOOLS
    #
    # 
    # __ret_func: to return and print the correct messaging in one single rows
    #
    def __ret_func(self, TFRetcode=True, MsgLevel="none", localMessage="Put here the string to print"  ):       ### krepo noy added ###
        methodLocalName = self.__lc_caller_method_name()      
        if MsgLevel == "error":
            self.__trc_err(localMessage) 
        elif MsgLevel == "none":
            pass  
        else:
            self.__trc_inf(localMessage) 
        if TFRetcode == True:
            self.__method_success(methodLocalName, None, localMessage)
        else:
            self.__method_failure(methodLocalName, None, "", localMessage)
        return TFRetcode, localMessage


    def __lc_current_method_name(self, embedKrepoInit=False):
        # Print current method name: verbose mode in test only
        # 
        # specify embedKrepoInit=True to enable the embedded  __krepo.start_time() call
        # 
        # methodName = inspect.stack()[0][3]  # <-- current method name: __lc_current_method_name)
        #
        methodName = inspect.stack()[1][3]   # <-- daddy method name  : who calls __lc_current_method_name
        #if __name__ == "__main__":
        #    print ("\n[[[ @@@@ [{}] Method Call ... Krepo[{}]   @@@ ]]] ".format(methodName,embedKrepoInit))
        #else:
        #   insert HERE the new logging method (still in progress...)   
        print ("\n[[[ @@@@ [{}] Method Call ... Krepo[{}]   @@@ ]]] ".format(methodName,embedKrepoInit))
        if self.__krepo and embedKrepoInit == True:
            self.__krepo.start_time()
        return methodName 


    def __lc_caller_method_name(self, embedKrepoInit=False):
        # Print current the method who calls this  
        # 
        # specify embedKrepoInit=True to enable the embedded  __krepo.start_time() call
        # 
        # methodName = inspect.stack()[0][3]  # <-- current method name: __lc_current_method_name)
        #
        methodName = inspect.stack()[2][3]   # <-- two levels of call
        #if __name__ == "__main__":
        #    print ("\n[[[ @@@@ [{}] Method Call ... Krepo[{}]   @@@ ]]] ".format(methodName,embedKrepoInit))
        #else:
        #   insert HERE the new logging method (still in progress...)   
        print ("\n[[[ ++++ [{}] Method Call ... Krepo[{}]   ++++ ]]] ".format(methodName,embedKrepoInit))
        if self.__krepo and embedKrepoInit == True:
            self.__krepo.start_time()
        return methodName 


    def __verify_presence_in_csv_format_answer(self, commandAnswer, valueToFind):
        """ process ONT command answer, and check if present """
        valueFound = False
        stringToParse = commandAnswer[1]
        #localMessage = "value: [{}] not found in passed CSV [{}]".format(valueToFind, stringToParse)
        localMessage = "value: [{}] not found in passed CSV".format(valueToFind)
        valueList  = stringToParse.replace("\n","").replace("> ","").split(",")
        for tempValue in valueList:
            if tempValue == valueToFind:
                valueFound = True
                #localMessage = "value: [{}] found in passed CSV [{}]".format(valueToFind, stringToParse)
                localMessage = "value: [{}] found in passed CSV".format(valueToFind)
                break
        self.__lc_msg(localMessage)
        return valueFound, localMessage





    # 
    # __is_reachable: to check if a machine is reacheable
    #
    def __is_reachable(self):
        self.__lc_msg("Function: __is_reachable")
        cmd = "ping -c {} {:s}".format(self.__pingRetryNumber,self.__bridgeIpAddress)
        if os.system(cmd) == 0:
            localMessage = "IP Address [{}]: answer received".format(self.__bridgeIpAddress)
            self.__lc_msg(localMessage)
            return True, localMessage
        localMessage = "IP Address [{}]: no answer received".format(self.__bridgeIpAddress)
        self.__lc_msg(localMessage)
        return False, localMessage


    #
    #   BRIDGE CONNECTION MANAGEMENT
    #
    def connect_bridge(self):       ### krepo added ###
        """ connect_bridge(self) - Hint: first call to use
            Purpose:
                create a bridge connection: it must be called one time only @ test/dut setup
            Return tuple:
                ("True|False" , "answer_string"  )
                True.............connection success
                False............connection failed
                answer_string....message for humans, to better understand 
                                 what happened in the processing flow  
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        bridgePingCheck = self.__is_reachable() 
        #print (bridgePingCheck)
        if bridgePingCheck[0] == False:
            return self.__ret_func(False,"error","Bridge not pingable [{}]!".format(self.__bridgeIpAddress))
        if self.__IXN != None:
            return self.__ret_func(False,"error", "BridgeHandler [{}] already allocated. Disconnect before!".format(self.__IXN))
        self.__IXN=IxNet()
        try:
            answerBridge = self.__IXN.connect(self.__bridgeIpAddress,'-port', self.__bridgePort) # use default port 8009
        except: 
            self.__IXN = None
            return self.__ret_func(False,"error", "Bridge connection failed: check ixNetwork server @ [{}] port [{}]".format(self.__bridgeIpAddress,self.__bridgePort))
        if answerBridge != "::ixNet::OK":
            self.__IXN = None
            return self.__ret_func(False,"error", "Bridge connect() answer not expected:[{}] instead of [::ixNet::OK]".format(answerBridge))
        #Data Model Initialization
        self.__DM_ROOT              = self.__IXN.getRoot()     
        self.__DM_NULL              = self.__IXN.getNull()    
        return self.__ret_func(True,"success", "BridgeHandler.connect [{}] - self.__DM_ROOT now [{}]".format(answerBridge,self.__DM_ROOT) )


    def disconnect_bridge(self):       ### krepo added ###
        """ disconnect_bridge(self)  - Hint: first call to use 
            Purpose:
                remove a bridge connection  it must be called one time only @ test/dut cleanup
            Return tuple:
                ("True|False" , "answer_string"  )
                True.............disconnec success
                False............connection failed
                answer_string....message for humans, to better understand 
                                 what happened in the processing flow  
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        if self.__IXN == None:
            return self.__ret_func(False,"error", "BridgeHandler [{}] already disconnected. Nothing to do!".format(self.__IXN))
        try:
            answerBridge = self.__IXN.disconnect() 
            self.__IXN = None
        except: 
            return self.__ret_func(False,"error", "Bridge disconnect failed: check ixNetwork server @ [{}] port [{}]".format(self.__bridgeIpAddress,self.__bridgePort))
        if answerBridge != "::ixNet::OK":
            self.__IXN = None
            return self.__ret_func(False,"error", "Bridge disconnect() answer not expected:[{}] instead of [::ixNet::OK]".format(answerBridge))
        return self.__ret_func(True,"success", "BridgeHandler.disconnect [{}]".format(answerBridge) )


    #
    #   CHASSIS CONNECTION MANAGEMENT
    #
    def __init_chassis_cards_handle_list(self):       ### krepo added ###
        """ __init_chassis_cards_handle_list(self) - Hint: internal use  
            Purpose:
                initializes the self.__DM_CARDLIST dictionary of the card plugged into the chassis 
        """
        methodLocalName = self.__lc_current_method_name()
        if self.__chassisHandler == None:
            return False,"error", "Port list not updated: add chassis before!" 
        tmpList = list(self.__IXN.getList( self.__chassisHandler,'card').replace("]","").replace("[","").split(","))
        for elementTmp in tmpList:
            keyTemp=elementTmp.replace("'","").split("card:")[1]
            self.__DM_CARDLIST[keyTemp]=elementTmp.replace("'","")   
        cardNumber=len(self.__DM_CARDLIST.keys())  
        return  True,"success", "SUCCESS: card list updated. Total cards found: [{}]".format(cardNumber) 


    def __init_chassis_ports_handle_list(self):       ### krepo added ###
        """ __init_chassis_ports_handle_list(self) - Hint: internal use  
            Purpose:
                initializes the self.__DM_PORTLIST dictionary of the ports physically available in the chassis 
        """
        methodLocalName = self.__lc_current_method_name()
        if self.__chassisHandler == None:
            return  False,"error", "Port list not updated: add chassis before!" 
        if len(self.__DM_CARDLIST.keys())  == 0:
            return  False,"error", "Port list not updated: call init_chassis_cards_handle_list before!"  
        for currentKey in self.__DM_CARDLIST.keys():
            currentCard = self.__DM_CARDLIST[currentKey]  
            tmpList = list(self.__IXN.getList(currentCard,'port').replace("]","").replace("[","").split(","))
            for elementTmp in tmpList:
                keyTemp=elementTmp.replace("'","").split("port:")[1]
                keyTempNew="{}/{}".format(currentKey,keyTemp)
                self.__DM_PORTLIST[keyTempNew]=elementTmp.replace("'","") 
        portNumber=len(self.__DM_PORTLIST.keys())  
        return True,"success", "SUCCESS: port list updated. Total ports found: [{}]".format(portNumber)      
    
    
    def add_chassis(self):       ### krepo added ###
        """ add_bridge(self)
            Purpose:
                create a chassis 
            Return tuple:
                ("True|False" , "answer_string"  )
                True.............chassis add success
                False............chassis add failed
                answer_string....message for humans, to better understand 
                                 what happened in the processing flow  
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        if self.__chassisHandler != None:
            return self.__ret_func(False,"error", "Chassis [{}] already added. Remove before!".format(self.__chassisHandler))
        try:
            socket.inet_aton(self.__chassisIpAddress)
        except socket.error:
            return self.__ret_func(False,"error", "Chassis address [{}] NOT valid".format(self.__chassisIpAddress))

        self.__IXN.execute('newConfig') 
        try:
            chassisTmp = self.__IXN.add(self.__IXN.getRoot()+'availableHardware', 'chassis', '-hostname', self.__chassisIpAddress)
            self.__IXN.commit()
            self.__chassisHandler = self.__IXN.remapIds(chassisTmp).replace("['","").replace("']","")
        except: 
            self.__IXN = None
            return self.__ret_func(False,"error", "Chassis connection failed: check instrument status @ [{}]".format(self.__chassisIpAddress))
        self.__init_chassis_cards_handle_list() 
        self.__init_chassis_ports_handle_list()  
        return self.__ret_func(True,"success", "SUCCESS: add_chassis [{}]".format(self.__chassisHandler) )


    def get_card_handler(self, slotNo):   ### krepo not added ###
        """ get_card_handler()  return the slot handler - Hint: internal use """
        #methodLocalName = self.__lc_current_method_name()
        slotNo=str(slotNo)
        localHandler=self.__DM_CARDLIST.get(slotNo, None)
        #self.__trc_inf("Slot[{}] CardHandler [{}] ".format(slotNo,localHandler))   
        return localHandler


    def get_port_handler(self, slotNo, portNo):   ### krepo not added ###
        """ get_port_handler()  return the port handler - Hint: internal use """
        #methodLocalName = self.__lc_current_method_name()
        keyTemp="{}/{}".format(str(slotNo),str(portNo))
        localHandler=self.__DM_PORTLIST.get(keyTemp, None)
        #self.__trc_inf("Port[{}] PortHandler [{}] ".format(keyTemp,localHandler))   
        return localHandler


    def clear_port_ownership(self, slotNo, portNo):   ### krepo not added ###
        """ clear_port_ownership()  release the ownership of a port - Hint: to use in single port management """
        methodLocalName = self.__lc_current_method_name()
        porthandler = self.get_port_handler( slotNo, portNo)
        if not porthandler:
            localMessage="WARNING: port handler [{}/{}] NOT FOUND".format(slotNo, portNo)
            self.__trc_inf(localMessage)
            return False, localMessage
        self.__trc_inf("Port handler [{}/{}] FOUND: [{}]".format(slotNo, portNo,porthandler))
        try:
            #self.__IXN.execute('clearOwnership', ixChassisObj+'/card:'+cardNumber+'/port:'+portNumber)
            self.__IXN.execute('clearOwnership', porthandler)
        except Exception as excMsg:
            return False,"ERROR: unable to remove port [{}/{}] ownership exception [{}]".format(slotNo, portNo,excMsg)  
        localMessage= "SUCCESS: ownership removed for port [{}/{}] ".format(slotNo, portNo)  
        self.__trc_inf(localMessage)
        return True,localMessage


    def clear_slot_ownership(self, slotNo):   ### krepo not added ###
        """ clear_slot_ownership()  release the ownership of all the ports of the card plugged in the specified slot - Hint: to use in initial slot setup """
        methodLocalName = self.__lc_current_method_name()
        for portNo in range(1,(self.__maxPortNumberForCard+1)):
            localResult = self.clear_port_ownership(slotNo, portNo)
        return True


    def __check_answer(self, ixNetAnswer):   ### krepo not added ###
        if ixNetAnswer == "::ixNet::OK":
            return True
        else:
            return False



    def set_vport_parameters(self, slotNo, portNo, mediaType = "fiber",autoNegotiate = "True"):   ### krepo not added ###
        """  set_vport_parameters(self, slotNo, portNo)
            Purpose:
               set the port parameters to a predefined state (fiber+autoneg)
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        keyTempNew="{}/{}".format(slotNo,portNo) 
        localVPortHandler = self.__DM_VPORTLIST.get(keyTempNew, None)
        if not localVPortHandler:
            localMessage="WARNING: port handler [{}/{}] NOT FOUND".format(slotNo, portNo)
            return  False,"error",localMessage 
        tempPortParameterPath="{}/l1Config/ethernet".format(localVPortHandler)  
        try:
            #retCode1 = self.__IXN.setMultiAttribute(tempPortParameterPath, '-autoNegotiate', 'True', '-media', 'fiber' , '-loopback', 'False' , '-enablePPM' ,'False' , '-autoInstrumentation', 'endOfFrame' , '-speed' ,'speed100fd' , '-flowControlDirectedAddress', '01 80 C2 00 00 01' ,'-ppm', '0' , '-enabledFlowControl', 'True')
            retCode1 = self.__IXN.setMultiAttribute(tempPortParameterPath, '-autoNegotiate', autoNegotiate, '-media', mediaType , '-loopback', 'False' , '-enablePPM' ,'False' , '-autoInstrumentation', 'endOfFrame' , '-speed' ,'speed100fd' , '-flowControlDirectedAddress', '01 80 C2 00 00 01' ,'-ppm', '0' , '-enabledFlowControl', 'True')
            retCode2 = self.__IXN.commit()
        except Exception as excMsg:
            return self.__ret_func(False,"error", "ERROR: exception [{}]".format(excMsg)  )
        #print ("tempPortParameterPath param====================================================")
        #print (self.__IXN.help(tempPortParameterPath))
        localMessage= "SUCCESS:  vport [{}] set_vport_parameters mediaType[{}] autoNegotiate[{}] created ".format(keyTempNew, mediaType,autoNegotiate) 
        self.__trc_inf(localMessage)
        return True,localMessage



    def create_vport(self, slotNo, portNo):   ### krepo added ###
        """  create_vport(self, slotNo, portNo)
            Purpose:
                create a vport 
            Return tuple:
                ("True|False" , "answer_string"  )
                True.............chassis add success
                False............chassis add failed
                answer_string....message for humans, to better understand 
                                 what happened in the processing flow  
            BE CARE: SPECIAL NOTES 
                After a vport creation, you MUST connect the vport to the physical port.
                The connection process is very slow (almost 40 seconds...)
                so it's better to split the port creation process into 3 phases.
                This method realizes the step 1 of the following process:
                -->1... CREATE ALL THE VPORTS you need (loop of create_vport(self, slotNo, portNo))
                   2... connect ALL the ports (loop of connect_vport_to_physical_port(self, slotNo, portNo))
                   3... verify ALL ports status before proceed
                so that the amount of time needed is reduced to 40 seconds for ALL the ports
                Please avoid to execute (create + connect) process in a loop for each port because 
                this way to proceed could fail.
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        if (not slotNo) or (not portNo):
            localMessage="ERROR: null portNo or slot"
            return self.__ret_func(False,"error",localMessage)
        keyTempNew="{}/{}".format(slotNo,portNo) 
        localPortHandler = self.__DM_PORTLIST.get(keyTempNew, None)
        if not localPortHandler:
            localMessage="WARNING: port handler [{}/{}] NOT FOUND".format(slotNo, portNo)
            return self.__ret_func(False,"error",localMessage)
        vport1   = self.__IXN.add(self.__DM_ROOT, 'vport')
        retCode1 = self.__IXN.commit()
        if not self.__check_answer(retCode1):
            localMessage="WARNING: unable to add [{}] or commit [{}] new vport".format(vport1, retCode1)
            return self.__ret_func(False,"error",localMessage)
        vport1   = self.__IXN.remapIds(vport1).replace("['","").replace("']","")
        retCode1 = self.__IXN.commit()
        if not self.__check_answer(retCode1):
            localMessage="WARNING: unable to remapIds [{}] or commit [{}] new vport".format(vport1, retCode1)
            return self.__ret_func(False,"error",localMessage)
        # Update vportlist with new vport 
        self.__DM_VPORTLIST[keyTempNew]=vport1 
        #print ("__DM_PORTLIST param====================================================")
        #print (self.__IXN.help(self.__DM_PORTLIST[keyTempNew]))
        #print ("__DM_VPORTLIST param====================================================")
        #print (self.__IXN.help(self.__DM_VPORTLIST[keyTempNew]))
        self.set_vport_parameters(slotNo, portNo)
        return self.__ret_func(True,"success", "SUCCESS: vport [{}] created ".format(keyTempNew))


    def connect_vport_to_physical_port(self, slotNo, portNo):   ### krepo added ###
        """  connect_vport_to_physical_port(self, slotNo, portNo)
            Purpose:
                connect a vport to it's specific physical port
            Return tuple:
                ("True|False" , "answer_string"  )
                True.............chassis add success
                False............chassis add failed
                answer_string....message for humans, to better understand 
                                 what happened in the processing flow  
            BE CARE: SPECIAL NOTES 
                Use this procedure to connect all the vports to theirs physical ports
                ONLY AFTER the whole vport set creation  
                This method realizes the step 2 of the following process:
                   1... create ALL the vports you need (loop of create_vport(self, slotNo, portNo))
                -->2... CONNECT ALL THE PORTS (loop of connect_vport_to_physical_port(self, slotNo, portNo))
                   3... verify ALL ports status before proceed
                so that the amount of time needed is reduced to 40 seconds for ALL the ports
                Please avoid to execute (create + connect) process in a loop for each port because 
                this way to proceed could fail.
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        if (not slotNo) or (not portNo):
            localMessage="ERROR: null portNo or slot"
            return self.__ret_func(False,"error",localMessage)
        keyTempNew="{}/{}".format(slotNo,portNo) 
        localPortHandler = self.__DM_PORTLIST.get(keyTempNew, None)
        if not localPortHandler:
            localMessage="WARNING: port handler [{}/{}] NOT FOUND".format(slotNo, portNo)
            return self.__ret_func(False,"error",localMessage)
        localVPortHandler = self.__DM_VPORTLIST.get(keyTempNew, None)
        if not localVPortHandler:
            localMessage="WARNING: vport handler [{}/{}] NOT FOUND".format(slotNo, portNo)
            return self.__ret_func(False,"error",localMessage)
        try:
            localMessage="INFO: [{}/{}]  trying to connect vport[{}] to port[{}]".format(slotNo, portNo, localPortHandler, localVPortHandler)
            retCode1 = self.__IXN.setAttribute(localVPortHandler, '-connectedTo', localPortHandler)
            retCode2 = self.__IXN.commit()
        except Exception as excMsg:
            return self.__ret_func(False,"error", "ERROR: exception [{}]".format(excMsg)  )
        if (not self.__check_answer(retCode1)) or (not self.__check_answer(retCode2)) :
            localMessage="ERROR: [{}/{}] unable to connect vport to port retCode1[{}] to retCode2[{}]".format(slotNo, portNo, retCode1, retCode2)
            return self.__ret_func(False,"error",localMessage)
        # Update vportlist with new vport 
        return self.__ret_func(True,"success", "SUCCESS: vport and port [{}/{}] connected".format(slotNo, portNo))


    def get_port_status(self, slotNo, portNo):   ### krepo added ###
        """   get_port_status(self, slotNo, portNo)    
            Purpose:
                retrieve the port status and wait until port became UP
            Return tuple:
                ("True|False" , "answer_string"  )
                True.............chassis add success
                False............chassis add failed
                answer_string....message for humans, to better understand 
                                 what happened in the processing flow  
            BE CARE: SPECIAL NOTES 
                Use this procedure to connect all the vports to theirs physical ports
                ONLY AFTER the whole vport set creation  
                This method realizes the step 2 of the following process:
                   1... create ALL the vports you need (loop of create_vport(self, slotNo, portNo))
                   2... connect all the ports (loop of connect_vport_to_physical_port(self, slotNo, portNo))
                -->3... VERIFY ALL PORTS STATUS BEFORE PROCEED
                so that the amount of time needed is reduced to 40 seconds for ALL the ports
                Please avoid to execute (create + connect) process in a loop for each port because 
                this way to proceed could fail.
            Return tuple:
                ("True|False" , "answer_string"  )
                True.............port UP and ready
                False............Port not ready after self.__checkPortUpRetries retries (1 retry every second)
                answer_string....message for humans, to better understand  what happened in the processing flow  
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        if (not slotNo) or (not portNo):
            localMessage="ERROR: null portNo or slot"
            return self.__ret_func(False,"error",localMessage)
        keyTempNew="{}/{}".format(slotNo,portNo) 

        localVPortHandler = self.__DM_VPORTLIST.get(keyTempNew, None)
        if localVPortHandler == None:
            localMessage="ERROR: port [{}] not found in VPORTLIST".format(keyTempNew)
            return self.__ret_func(False,"error",localMessage)
        print("localVPortHandler [{}]".format(localVPortHandler))
    
        for x in range(0,self.__checkPortUpRetries):
            assignedPortState = self.__IXN.getAttribute(localVPortHandler,'-state')
            print("After [{}] sec: assignedPortState [{}]".format(x,assignedPortState))
            if assignedPortState == "up": 
                break
            time.sleep(1)
        return self.__ret_func(True,"success", "SUCCESS: vport and port [{}/{}] connected".format(slotNo, portNo))


    def create_vport_interface(self, slotNo, portNo, 
                               description = None,
                               ipAddress = None,
                               ipGetaway = None,
                               macAddress = None):   ### krepo added ###
        ''' Method
                create_vport_interface(self, slotNo, portNo, description = None , ipAddress = None, ipGetaway = None, macAddress = None)   
            Purpose:
                create an ethernet interface with the specified parameters
            Return tuple:
                ("True|False" , "answer_string"  )
                True.............port UP and ready
                False............Port not ready after self.__checkPortUpRetries retries (1 retry every second)
                answer_string....message for humans, to better understand  what happened in the processing flow  
        '''
        self.__lc_current_method_name(embedKrepoInit=True)
        keyTempNew="{}/{}".format(slotNo,portNo) 
        localVPortHandler = self.__DM_VPORTLIST.get(keyTempNew, None)
        if not localVPortHandler:
            localMessage="ERROR: port handler [{}/{}] NOT FOUND".format(slotNo, portNo)
            return  self.__ret_func(False,"error", localMessage)
        try:
            localPortInterface = self.__IXN.add(localVPortHandler, 'interface')
            if description == None:
                description = "Protocol interface port [{}]".format(keyTempNew)
            addPortInterfaceResult = self.__IXN.setMultiAttribute(localPortInterface, '-enabled', 'True', '-description', description)
            retCode1               = self.__IXN.commit()
            
            if not self.__check_answer(retCode1):
                localMessage="ERROR: unable to setMultiAttribute to portInterface[{}] ->[{}]".format(addPortInterfaceResult, retCode1)
                return  self.__ret_func(False,"error", localMessage)
            localPortInterface   = self.__IXN.remapIds(localPortInterface).replace("['","").replace("']","")
            retCode1 = self.__IXN.commit()
            if not self.__check_answer(retCode1):
                localMessage="ERROR: unable to remapIds [{}] or commit [{}] new vport".format(localPortInterface, retCode1)
                return  self.__ret_func(False,"error", localMessage)
            self.__DM_VPORTINTERFACE[keyTempNew]=localPortInterface 
        except Exception as excMsg:
            return self.__ret_func(False,"error", "ERROR [Port {}] : exception [{}]".format(keyTempNew,excMsg)  )
        #Port-specific Data model   
        #self.__DM_PORT_IP_ADDRESS[keyTempNew]  = ipAddress                    
        #self.__DM_PORT_IP_GETAWAY[keyTempNew]  = ipGetaway                  
        #self.__DM_PORT_MAC_ADDRESS[keyTempNew] = macAddress
        # Mac address specific assignment 
        if macAddress != None:
            #macAddressHandler="{}/ethernet".format(localPortInterface)
            try:
                #retCode1 = self.__IXN.setAttribute(macAddressHandler, '-macAddress', macAddress )
                retCode1 = self.__IXN.setAttribute(localPortInterface + "/ethernet", '-macAddress', macAddress )
                retCode2 = self.__IXN.commit()
                if not self.__check_answer(retCode2):
                    localMessage="ERROR:  [{}] [{}]".format(retCode1, retCode2)
                    return  self.__ret_func(False,"error", localMessage)
            except Exception as excMsg:
                return self.__ret_func(False,"error", "ERROR [Port {}] : exception [{}]".format(keyTempNew,excMsg)  )
        # Ip/Mac Addresses specific assignment 
        if (ipAddress != None) or  (ipGetaway != None) :
            if self.__DM_PORT_IPV4IFACE_OBJ.get(keyTempNew, None) == None:   
                ipv4InterfaceObject = self.__IXN.add(localPortInterface, 'ipv4')
                retCode1            = self.__IXN.commit()
                ipv4InterfaceObject = self.__IXN.remapIds(ipv4InterfaceObject).replace("['","").replace("']","")
                self.__DM_PORT_IPV4IFACE_OBJ[keyTempNew]=ipv4InterfaceObject
            else:
                ipv4InterfaceObject = self.__DM_PORT_IPV4IFACE_OBJ.get(keyTempNew, None)
            try:
                if (ipAddress != None) and  (ipGetaway == None):
                    retCode1 = self.__IXN.setMultiAttribute(ipv4InterfaceObject, '-ip', ipAddress, '-maskWidth', '24'  )
                elif (ipAddress == None) and  (ipGetaway != None):   
                    retCode1 = self.__IXN.setMultiAttribute(ipv4InterfaceObject, '-gateway', ipGetaway, '-maskWidth', '24'  )
                else: # (ipAddress != None) and  (ipGetaway != None):     
                    retCode1 = self.__IXN.setMultiAttribute(ipv4InterfaceObject, '-gateway', ipGetaway, '-ip', ipAddress, '-maskWidth', '24'  )
                retCode2 = self.__IXN.commit()
                if not self.__check_answer(retCode2):
                    localMessage="ERROR:  [{}] [{}]".format(retCode1, retCode2)
                    return  self.__ret_func(False,"error", localMessage)
            except Exception as excMsg:
                return self.__ret_func(False,"error", "ERROR [Port {}] : exception [{}]".format(keyTempNew,excMsg)  )
        newIpAddress  = self.__IXN.getAttribute(ipv4InterfaceObject,'-ip')
        newIpGetaway  = self.__IXN.getAttribute(ipv4InterfaceObject,'-gateway')
        maskWidth     = self.__IXN.getAttribute(ipv4InterfaceObject,'-maskWidth')
        newMacAddress = self.__IXN.getAttribute(localPortInterface + "/ethernet", '-macAddress')
        self.__DM_PORT_IP_ADDRESS[keyTempNew]  = newIpAddress                    
        self.__DM_PORT_IP_GETAWAY[keyTempNew]  = newIpGetaway                  
        self.__DM_PORT_MAC_ADDRESS[keyTempNew] = newMacAddress
        #print ("[ipv4InterfaceObject][Port {}] ====================================================".format(keyTempNew))
        #print("ip         [{}]".format(newIpAddress))
        #print("gateway    [{}]".format(newIpGetaway))
        #print("macaddress [{}]".format(newMacAddress))
        #print("maskWidth  [{}]".format(maskWidth))
        return self.__ret_func(True,"success", "SUCCESS: create_vport_interface [{}]  Ip[{}] Gw[{}] Mac[{}]".format(keyTempNew,newIpAddress,newIpGetaway,newMacAddress)  )



    def create_traffic_item(self, itemName    = 'My Traffic Item',
                            trafficType   = 'ipv4',
                            transmitMode  = 'interleaved',
                            biDirectional = '1',
                            routeMesh     = 'oneToOne',
                            srcDestMesh   = 'oneToOne',):
        ''' Method
                create_vport_interface(self, slotNo, portNo, description = None , ipAddress = None, ipGetaway = None, macAddress = None)   
            Purpose:
                create an ethernet interface with the specified parameters
            Return tuple:
                ("True|False" , "answer_string"  )
                True.............port UP and ready
                False............Port not ready after self.__checkPortUpRetries retries (1 retry every second)
                answer_string....message for humans, to better understand  what happened in the processing flow  
        '''
        
        
        
        
        '''
        
          # Create traffic
          trafficItem = ixNet.add(ixNet.getRoot()+'traffic', 'trafficItem', '-trafficItemType', 'raw')
          endpointSet = ixNet.add(trafficItem, 'endpointSet', '-sources', vport1+'/protocols',  '-destinations', vport2+'/protocols')
          ixNet.commit()
        
        
        
        '''
        
        
        self.__lc_current_method_name(embedKrepoInit=True)
        try:
            #localTrafficItem = self.__IXN.add(self.__DM_ROOT + '/traffic', 'trafficItem', '-trafficItemType', 'raw')
            localTrafficItem = self.__IXN.add(self.__DM_ROOT + 'traffic', 'trafficItem', '-trafficItemType', 'raw')
            retCode1         = self.__IXN.setMultiAttribute(localTrafficItem,'-enabled', 'True', '-name', itemName, '-routeMesh', routeMesh, '-srcDestMesh', srcDestMesh, '-trafficType', trafficType, '-transmitMode', transmitMode,'-biDirectional', biDirectional)
            retCode2         = self.__IXN.commit()
            localTrafficItem2 = self.__IXN.add(localTrafficItem, 'endpointSet')
            retCode2         = self.__IXN.commit()
            ''' 
            trafficItem = self.__IXN.add(self.__IXN.getRoot() +'traffic', 'trafficItem', '-trafficItemType', 'raw')
            endpointSet =self.__IXN.add(trafficItem, 'endpointSet' )
            #endpointSet =self.__IXN.add(trafficItem, 'endpointSet', '-sources', vport1+'/protocols',  '-destinations', vport2+'/protocols')
            self.__IXN.commit()
            ''' 
            
            localTrafficItem = self.__IXN.remapIds(localTrafficItem).replace("['","").replace("']","")
            self.__DM_TRAFFICLIST[itemName]=localTrafficItem
            if (not self.__check_answer(retCode1)) or (not self.__check_answer(retCode2)):
                localMessage="ERROR: unable to create traffic item [{}]:  [{}] [{}]".format(itemName, retCode1, retCode2)
                return self.__ret_func(False,"error",localMessage)
        except Exception as excMsg:
            return self.__ret_func(False,"error", "ERROR: TrafficItem  [{}] : exception [{}]".format(itemName,excMsg)  )
        return self.__ret_func(True,"success", "SUCCESS: create_traffic_item [{}]:trafficType[{}] transmitMode[{}] biDirectional[{}] routeMesh[{}] srcDestMesh[{}] ".format( itemName, trafficType,transmitMode,biDirectional,routeMesh ,srcDestMesh)  )
  
  

    def create_endpoint(self, endPointName, itemName, srcSlotNo, srcPortNo, destSlotNo, destPortNo, frameSize, frameRate, frameCount):
        ''' Method
        '''
        self.__lc_current_method_name(embedKrepoInit=True)
        #localTrafficItem = self.__DM_TRAFFICLIST.get(itemName, None)
        localTrafficItem = self.__DM_TRAFFICLIST.get(itemName, None)
        if  not localTrafficItem:
            localMessage="ERROR: local Traffic Item [{}] NOT FOUND".format(itemName)
            return self.__ret_func(False,"error",localMessage)
        if (not srcSlotNo) or  (not srcPortNo) or  (not destSlotNo) or  (not destPortNo):
            localMessage="ERROR: parameter not specified in [{}] creation: srcSlotNo[{}] srcPortNo[{}] destSlotNo[{}] destPortNo[{}]".format(endPointName ,srcSlotNo, srcPortNo, destSlotNo, destPortNo)
            return self.__ret_func(False,"error",localMessage)
        sourceKeyTemp = "{}/{}".format(srcSlotNo,srcPortNo) 
        destKeyTemp   = "{}/{}".format(destSlotNo,destPortNo) 
        #srcEndpoints  = self.__DM_VPORTINTERFACE.get(sourceKeyTemp, None)
        #destEndpoints = self.__DM_VPORTINTERFACE.get(destKeyTemp,   None)
        srcEndpoints  = self.__DM_VPORTLIST.get(sourceKeyTemp, None)
        destEndpoints = self.__DM_VPORTLIST.get(destKeyTemp,   None)
        
        print(" AA  ********* srcEndpoints[{}]  destEndpoints[{}]".format(srcEndpoints,destEndpoints))
        srcEndpoints="{}/interface".format(srcEndpoints)
        destEndpoints="{}/interface".format(destEndpoints)
        print(" BB  ********* srcEndpoints[{}]  destEndpoints[{}]".format(srcEndpoints,destEndpoints))
       
        if (not srcEndpoints) or (not destEndpoints):
            localMessage="ERROR: endPoint not found in [{}] creation: srcEndpoints[{}] srcEndpoints[{}]".format(endPointName ,srcSlotNo, srcPortNo) 
            return self.__ret_func(False,"error",localMessage)
        try:
            #localEndPointObject = self.__IXN.add(localTrafficItem, 'endpointSet', '-name', endPointName, '-sources', srcEndpoints,  '-destinations', destEndpoints )
            localEndPointObject = self.__IXN.add(localTrafficItem ,'endpointSet', '-name', endPointName, '-sources', srcEndpoints,  '-destinations', destEndpoints )
            retCode1 = self.__IXN.commit()
            if (not self.__check_answer(retCode1)) :
                localMessage="ERROR: unable to create new endpoint [{}]:  [{}] [{}]".format(endPointName, retCode1, localEndPointObject)
                return self.__ret_func(False,"error",localMessage)
            localEndPointObject = self.__IXN.remapIds(localEndPointObject).replace("['","").replace("']","")
        except Exception as excMsg:
            return self.__ret_func(False,"error", "ERROR:unable to create new endpoint  [{}] : exception [{}]".format(endPointName, excMsg)  )

        self.__DM_TRAFFIC_ENDPOINT[endPointName]=localEndPointObject 



        return self.__ret_func(True,"success", "SUCCESS: Create Endpoint [{}] : localEndPointObject[{}] ".format( endPointName, localEndPointObject)  )
          
        
       



    def config_traffic_tracking(self, itemName = None, trackingList = ['flowGroup0', 'sourceDestEndpointPair0']):
        ''' Method
                config_traffic_tracking(self, itemName, trackingList= ['fllowGroup0', 'sourceDestEndpointPair0']):
            Purpose:
                config traffic tracking for the traffic item named itemName
            Return tuple:
                ("True|False" , "answer_string"  )
                True.............port UP and ready
                False............Port not ready after self.__checkPortUpRetries retries (1 retry every second)
                answer_string....message for humans, to better understand  what happened in the processing flow  
        '''
        self.__lc_current_method_name(embedKrepoInit=True)
        localTrafficItem = self.__DM_TRAFFICLIST.get(itemName, None)
        if  not localTrafficItem:
            localMessage="WARNING: local Traffic Item [{}] NOT FOUND".format(itemName)
            return self.__ret_func(False,"error",localMessage)
        try:
            retCode1  = self.__IXN.setAttribute(localTrafficItem + '/tracking', '-trackBy', trackingList)
            retCode2  = self.__IXN.commit()
            if (not self.__check_answer(retCode1)) or (not self.__check_answer(retCode2)):
                localMessage="ERROR: unable to config traffic item tracking [{}]:  [{}] [{}]".format(itemName, retCode1, retCode2)
                return self.__ret_func(False,"error",localMessage)
        except Exception as excMsg:
            return self.__ret_func(False,"error", "ERROR: Config Traffic Item Tracking [{}] : exception [{}]".format(itemName,excMsg)  )
        return self.__ret_func(True,"success", "SUCCESS: Config Traffic Item Tracking [{}] : trackingList [  {}  ] ".format( itemName, trackingList)  )
          
        




    def config_flowgroup(self):
        self.__lc_current_method_name(embedKrepoInit=True)
        #localTrafficItem = self.__IXN.getList( self.__DM_ROOT + '/traffic', 'trafficItem').replace("['","").replace("']","")
        localElement = self.__IXN.getList( self.__DM_ROOT + '/traffic','trafficItem')
        print("/traffic -> trafficItem [{}]".format(localElement))
        localElement = self.__IXN.getList( self.__DM_ROOT + '/traffic/trafficItem','rateOptions')
        print("/traffic/trafficItem -> rateOptions [{}]".format(localElement))
        localElement = self.__IXN.getList( self.__DM_ROOT + '/traffic/trafficItem','dataCenterSettings')
        print("/traffic/trafficItem -> dataCenterSettings [{}]".format(localElement))
        localElement = self.__IXN.getList( self.__DM_ROOT + '/traffic/trafficItem','packetOptions')
        print("/traffic/trafficItem -> packetOptions [{}]".format(localElement))
        localElement = self.__IXN.getList( self.__DM_ROOT + '/traffic/trafficItem','frameOptions')
        print("/traffic/trafficItem -> frameOptions [{}]".format(localElement))
        localElement = self.__IXN.getList( self.__DM_ROOT + '/traffic/trafficItem','tracking')
        print("/traffic/trafficItem -> tracking [{}]".format(localElement))
        localElement = self.__IXN.getList( self.__DM_ROOT + '/traffic/trafficItem','pair')
        print("/traffic/trafficItem -> pair [{}]".format(localElement))
        localElement = self.__IXN.getList( self.__DM_ROOT + '/traffic/trafficItem','applicationProfile')
        print("/traffic/trafficItem -> applicationProfile [{}]".format(localElement))
        localElement = self.__IXN.getList( self.__DM_ROOT + '/traffic/trafficItem','applicationProfileType')
        print("/traffic/trafficItem -> applicationProfileType [{}]".format(localElement))
        localElement = self.__IXN.getList( self.__DM_ROOT + '/traffic/trafficItem','configEncap')
        print("/traffic/trafficItem -> configEncap [{}]".format(localElement))
        print("=-=========================================================")
        print("=-=========================================================")
        print(" TRAFFIC CHILDREN  ========================================")
        print (self.__IXN.help(self.__DM_ROOT + '/traffic'))
        print("=-=========================================================")
        print("=-=========================================================")
        print("=-=========================================================")
        print(" TRAFFIC/TRAFFICITEM CHILDREN  ============================")
        print (self.__IXN.help(self.__DM_ROOT + '/traffic/trafficItem'))
        print("=-=========================================================")
        print("=-=========================================================")
        print("=-=========================================================")
        #localElement = self.__IXN.getList( self.__DM_ROOT + '/traffic/trafficItem','configElement')
        #print("/traffic/trafficItem -> endpointSet [{}]".format(localElement))
        #localElement = self.__IXN.getList( self.__DM_ROOT + '/traffic/trafficItem/','endpointSet')
        #print("/traffic/trafficItem -> endpointSet [{}]".format(localElement))
        return self.__ret_func(True,"success", "SUCCESS: config_flow_group END ")
















    def regenerate_traffic_items(self):       ### krepo added ###
        """ regenerate_traffic_items(self)
            Purpose:
            Return tuple:
                ("True|False" , "answer_string"  )
                True.............dictionary updated
                False............dictionary not updated
                answer_string....message for humans, to better understand 
                                 what happened in the processing flow  
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
 
        #tmpList = list(self.__IXN.getList(self.__IXN.getList(self.__DM_ROOT + '/traffic', 'trafficItem')).replace("]","").replace("[","").split(","))
        tmpList = list(self.__IXN.getList(self.__DM_ROOT + '/traffic', 'trafficItem').replace("]","").replace("[","").split(","))
        print("[{}]".format(tmpList))
        for elementTmp in tmpList:
            print("Item:[{}]".format(elementTmp))
            try:
                generateResult = self.__IXN.execute('generate',elementTmp) 
                print("Regenerate --->[{}] Result:[{}]".format(elementTmp,generateResult))
            except Exception as excMsg:
                localMessage="Regenerate --->ERROR: exception [{}]".format(excMsg)    
                print("[{}]".format(localMessage))
              
            #print (self.__IXN.help(self.__DM_ROOT , 'execList'))



        return self.__ret_func(True, "success", "SUCCESS: traffic items regenerated")




    def remove_vport(self, cardNumber, portNumber):       ### krepo added ###
        """ remove_vport(self, cardNumber, portNumber)
            Purpose:
                remove a vport and its handler from the self.__DM_VPORTLIST dictionary.
                eg:  self.__DM_VPORTLIST[1/2]  
            Return tuple:
                ("True|False" , "answer_string"  )
                True.............dictionary updated
                False............dictionary not updated
                answer_string....message for humans, to better understand 
                                 what happened in the processing flow  
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        # Parameters check
        if self.__chassisHandler == None:
            return self.__ret_func(False,"error", "Port list not updated.Add chassis before!")
        if len(self.__DM_CARDLIST.keys())  == 0:
            return self.__ret_func(False,"error", "Port list not updated.Call init_chassis_cards_handle_list before!" )
        if len(self.__DM_PORTLIST.keys())   == 0:
            return self.__ret_func(False,"error", "Port list not updated.Call init_chassis_ports_handle_list() before!" )


        keyTempNew="{}/{}".format(cardNumber,portNumber) 
        try:
            localvPortHandler = self.__DM_PORTLIST[keyTempNew]
        except:
            return self.__ret_func(False,"error", "ERROR: Port handler not found for port [{}]".format(keyTempNew)  )
       
        try:
            retCode1 = self.__IXN.setAttribute(localvPortHandler, '-connectedTo', self.__DM_NULL )
            retCode2 = self.__IXN.commit()
        except Exception as excMsg:
            localMessage="ERROR: exception [{}]".format(excMsg)    
            self.__trc_err(localMessage) 

       
        try:
            print("exists BEFORE REMOVE RETCODE [{}]".format(self.__IXN.exists(localvPortHandler)))
            retCode3 = self.__IXN.remove(localvPortHandler)
            retCode4 = self.__IXN.commit()
            print("REMOVE RETCODE [{}]".format(retCode3))
            print("COMMIT AFTER REMOVE RETCODE [{}]".format(retCode4))
            print("exists AFTER REMOVE RETCODE [{}]".format(self.__IXN.exists(localvPortHandler)))
        except Exception as excMsg:
            return self.__ret_func(False,"error", "ERROR: exception [{}]".format(excMsg)    )

        if ("OK" not in retCode3) or ("OK" not in retCode4):
            return self.__ret_func(False,"error",  "ERROR:  port[{}] not removed for handler [{}]".format(keyTempNew,localvPortHandler)  )
        del self.__DM_VPORTLIST[keyTempNew]
        return self.__ret_func(True, "success", "SUCCESS: WWW port[{}] removed for handler [{}]".format(keyTempNew,localvPortHandler)   )














































    def clean_up(self):
        """ INTERNAL USAGE
        """
        self.__trc_inf("clean_up called [{}]".format(self.__ontType))


    #     
    # Krepo-related     
    #   

    def __get_instrument_info_from_db(self, ID):
        tabEqpt  = TEquipment
        # get Equipment Type ID for selected ID (i.e. 50 (for ONT506))
        #instr_type_id = tabEqpt.objects.get(id_equipment=ID).t_equip_type_id_type.id_type
        # get Equipment Type Name for selected ID (i.e. ONT506)
        instr_type_name = tabEqpt.objects.get(id_equipment=ID).t_equip_type_id_type.name
        instr_ip = self.__get_net_info(ID)
        self.__chassisIpAddress  = instr_ip
        localMessage = "__get_instrument_info_from_db: instrument type specified : Instrument:[{}] IpAddr[{}]".format(instr_type_name,instr_ip)
        self.__trc_err(localMessage) 
        return  

    def __trc_dbg(self, msg):
        """ INTERNAL USAGE
        """
        self.__kenv.ktrc.k_tracer_debug(msg, level=1)


    def __trc_inf(self, msg):
        """ INTERNAL USAGE
        """
        self.__kenv.ktrc.k_tracer_info(msg, level=1)


    def __trc_err(self, msg):
        """ INTERNAL USAGE
        """
        self.__kenv.ktrc.k_tracer_error(msg, level=1)


    def __t_success(self, title, elapsed_time, out_text):
        """ INTERNAL USAGE
        """
        if self.__krepo:
            self.__krepo.add_success(self, title, elapsed_time, out_text)



    def __t_failure(self, title, e_time, out_text, err_text, log_text=None):
        """ INTERNAL USAGE
        """
        if self.__krepo:
            self.__krepo.add_failure(self, title, e_time, out_text, err_text, log_text)



    def __t_skipped(self, title, e_time, out_text, err_text, skip_text=None):
        """ INTERNAL USAGE
        """
        if self.__krepo:
            self.__krepo.add_skipped(self, title, e_time, out_text, err_text, skip_text)



    def __method_success(self, title, elapsed_time, out_text):
        """ INTERNAL USAGE
        """
        #self.__t_success(methodLocalName, None, localMessage)
        self.__lastCallSuccess = True            # Mark current execution as successfully
        self.__calledMethodStatus[title]= "success"  #
        self.__t_success(title, elapsed_time, out_text)  # CG tracking


    def __method_failure(self, title, e_time, out_text, err_text):
        """ INTERNAL USAGE
        """
        #self.__t_failure(methodLocalName, None, "", localMessage)
        self.__lastCallSuccess = False            # Mark current execution as successfully
        self.__calledMethodStatus[title]= "error"  #
        self.__t_failure(title, e_time, out_text, err_text) # CG tracking


 
    def __method_skipped(self, title, e_time, out_text, err_text):
        """ INTERNAL USAGE
        """
        #self.__t_failure(methodLocalName, None, "", localMessage)
        #self.__lastCallSuccess = False            # Don't mark current execution as successfully
        self.__calledMethodStatus[title]= "skip"  #
        self.__t_skipped(title, e_time, out_text, err_text) # CG tracking


    def __check_method_execution(self,methodToCheck):
        """ INTERNAL USAGE
            it verifies if the "methodToCheck" method has been successfully executed    
        """
        methodName = inspect.stack()[1][3]   # <-- daddy method name  : who calls this method
        if methodToCheck in self.__calledMethodStatus:
            pass
        else:
            localMessage = "[[[ #### ERROR: Method [{}] execution inside [{}] NOT FOUND in self.__calledMethodStatus: [[ {} ]]".format(methodToCheck,methodName,self.__calledMethodStatus)
            print(localMessage) 
            self.__lc_msg(localMessage)
            return False 
        methodExecLastResult =  self.__calledMethodStatus[methodToCheck]
        if methodExecLastResult == "success":
            pass
        else:
            #localMessage = "[[[ #### ERROR: Method [{}] execution inside [{}]: [{}] ".format(methodToCheck,methodName,methodExecLastResult)
            localMessage = "[[[ #### ERROR: Method [{}] execution inside [{}] in self.__calledMethodStatus: [[ {} ]]".format(methodToCheck,methodName,self.__calledMethodStatus)
            self.__lc_msg(localMessage)
            return False 
        localMessage = "[[[ #### [{}] verified [{}] ".format(methodToCheck,methodExecLastResult)
        self.__lc_msg(localMessage)
        return True
 

    #
    #  K@TE INTERFACE
    #
    def __get_net_info(self, n):
        tabNet = TNet

        for r in tabNet.objects.all():
            if r.t_equipment_id_equipment:
                if r.t_equipment_id_equipment.id_equipment == n:
                    return r.ip

        return str(None)
 

    def __remove_dust(self,stringToClean):
        #  remove the "> " prompt and "\n" from a string
        return str(stringToClean).replace("\n","").replace("\\n","").replace("> ","").replace(">","")



    def __get_result_TF(self,callResultToParse):
        #  Extract True/False result from last call result tuple
        firstElement = callResultToParse[0]
        #localMessage = "firstElement  [{}] ".format(firstElement)
        #self.__lc_msg(localMessage)
        return firstElement



    def __get_result_string(self,callResultToParse):
        #  Extract result string from last call result tuple
        secondElement = callResultToParse[1]
        #localMessage = "secondElement [{}] ".format(secondElement)
        #self.__lc_msg(localMessage)
        return secondElement



    def __lc_msg(self,messageForDebugPurposes):
        # Print debug messages: verbose mode in test only
        #if __name__ == "__main__":
        #    print ("{:s}".format(messageForDebugPurposes))
        #else:
        #   insert HERE the new logging method (still in progress...)   
        print ("{:s}".format(messageForDebugPurposes))


#######################################################################
#
#   MODULE TEST - Test sequences used for DB-Integrated testing
#
#######################################################################
if __name__ == "__main__":   #now use this part
    print(" ")
    print("========================================")
    print("ixiaDriver DB-Integrated testing debug")
    print("========================================")
    #localUser="preint" ghelfi
    #localPwd="preint"  ghelfi

    # DA AMBIENTE DI ESECUZIONE:
    currDir,fileName = os.path.split(os.path.realpath(__file__))
    xmlReport = currDir + '/test-reports/TestSuite.'+ fileName
    print("{}".format(xmlReport))
    r = Kunit(xmlReport)
    r.frame_open(xmlReport)

    # PREINIT VARS (from file or ad-hoc class):

  
    #tester_5xx = InstrumentIXIA("tester_5xx", ID=20, krepo=r)
    #tester_6xx = InstrumentIXIA("tester_6xx", ID=21, krepo=r)
    #tester_5xx.init_instrument(portId_5xx)
    #tester_6xx.init_instrument(portId_6xx)






    print("\n\n\n\n\nTESTING SECTION *************************************")
    input("press enter to continue...")
    




    #tester_5xx.deinit_instrument( portId_5xx)
    #tester_6xx.deinit_instrument( portId_6xx)

 

    print(" ")
    print("========================================")
    print("ixiaDriver DB-Integrated -- END --    ")
    print("========================================")
    print(" ")


    r.frame_close()

    
    #sys.exit()
















#!/usr/bin/env python
"""
###############################################################################
#
# MODULE:  InstrumentMAP200.py
#
# AUTHOR:  L.Cutilli
#
# DATE  :  16/10/2015
#
#
# DETAILS: Python management module for MAP-200 chassis
#          Managed "cassette" types: 
#          - VOA
#
# MODULE: InstrumentMAP200.py  created to drive the connections and common low-level operations
#                           involving JDSU MAP-200 chassis
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

from katelibs.equipment import Equipment
from katelibs.kenviron import KEnvironment
from katelibs.kunit import Kunit
from katelibs.database import *


class InstrumentMAP(Equipment):

    def __init__(self, label, kenv):
        """ label   : equipment name used on Report file
            kenv    : instance of KEnvironment (initialized by K@TE FRAMEWORK)
        """
        # Enviroment
        self.__kenv                 = kenv             # Kate Environment
        self.__krepo                = kenv.krepo       # result report (Kunit class instance)
        self.__prs                  = kenv.kprs        # Presets for running environment
        # Session
        self.__sessionName          = "SessionMAP_KATE"    #  To be changed: meaningfuls only for  5xx 
        self.__lastCallSuccess      = False            #  track if the last call was successfully executed (not to set in case of skip)
        self.__calledMethodList     = []               #  used to track all method called
        self.__calledMethodStatus   = dict()           #  used to track all method called and last execution result
        # Connection
        self.__mapUser              = None             #  Ont session authentication user
        self.__mapPassword          = "map200"         #  Ont session user's password
        self.__mapIpAddress         = ""               #  Map200 IP address
        self.__mapInstrType         = ""               #  Instrument type
        self.__mapInstrLabel        = label            #  Instrument label
        self.__chassisSlotContent   = []               #  Map slot to 
       
        #self.__mapIpAddress         = "135.221.123.146"   #  Map200 IP address
        self.__mapIpAddress         = None             #  Map200 IP address
        self.__mapTelnetPort        = 8100             #  Map200 telnet port (default 5001)
        self.__telnetConnection     = None             #  Handler of the established telnet connection
        self.__pingRetryNumber      = 1                #  Retry number for -c ping option
        self.__telnetExpectedPrompt = [b'> ']          #  it must be specified as keys LIST...
        self.__telnetTimeout        = 2
        self.__instrumentId         = self.__prs.get_id(label)
        self.__mapIpAddress         = self.__get_net_info(self.__instrumentId) 
        print("Instrument ID[{}] IP[{}]".format(self.__instrumentId,self.__mapIpAddress))
        super().__init__(label, self.__instrumentId)


    #def init_instrument(self, localUser, localPwd, localOntIpAddress, portId):
    def init_instrument(self):
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        # Ping checkresponseresponse
        localResult = self.__is_reachable()
        if not localResult[0]:
            localMessage="MAP200 [{}]:not reachable. Bye...".format(self.__mapIpAddress) 
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return  localResult
        else:
            localMessage="MAP200 [{}]:reachable".format(self.__mapIpAddress)
            self.__lc_msg(localMessage)
        try:
            self.__telnetConnection = telnetlib.Telnet(self.__mapIpAddress,self.__mapTelnetPort,self.__telnetTimeout)
            #response = self.__send_cmd(":SYSTem:LAYout?")
            response = self.__send_cmd(":SYSTem:LAYout:Port?")
            localMessage = "MAP200 [{}] ANSWER [{}] :Telnet connection established".format(self.__mapIpAddress,response)
            self.__lc_msg(localMessage)
            if self.__init_chassis_slot_content(response) == False:
                localMessage = "MAP200 [{}]:Slot map ERROR".format(self.__mapIpAddress)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage


        except Exception as e:
            self.__lc_msg(str(e))
            localMessage = "MAP200 [{}]:Telnet connection ERROR".format(self.__mapIpAddress)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage

        localMessage="[{}]: init_instrument: instrument correctly initialized".format(self.__mapInstrLabel)
        self.__method_success(methodLocalName, None, localMessage)
        self.__lc_msg(localMessage)
        return True, localMessage
       
       
    def __init_chassis_slot_content(self,paramString ):
        CheckAnswer=paramString[0]
        if CheckAnswer == False: 
            return False
        portContentList=paramString[1]
        portContentList=self.__remove_dust(portContentList)
        self.__chassisSlotContent=portContentList.split(",")
        #print(">>>   after[{}]".format(self.__chassisSlotContent))
        #print(">>> 0 after[{}]".format(self.__chassisSlotContent[0]))
        #print(">>> 1  after[{}]".format(self.__chassisSlotContent[1]))
        #print(">>> 2  after[{}]".format(self.__chassisSlotContent[2]))
        #print(">>> 3  after[{}]".format(self.__chassisSlotContent[3]))
        #print(">>> 4  after[{}]".format(self.__chassisSlotContent[4]))
        #print(">>> 5  after[{}]".format(self.__chassisSlotContent[5]))
        #print(">>> 6  after[{}]".format(self.__chassisSlotContent[6]))
        #print(">>> 7  after[{}]".format(self.__chassisSlotContent[7]))
        #print(">>> 8  after[{}]".format(self.__chassisSlotContent[8]))
        return True 
          



    def get_set_switch_state(self, slotNumber, deviceNumber, inputNumber, outputNumber="",chassisNumber=1):
        """ Method:
                get_set_switch_state(slotNumber, deviceNumber, inputNumber, outputNumber="",chassisNumber=1):

            Purposes:
                Sets and  gets the state of a switch of a LCS/MCS/SCS module
               
            Parameters:
                slotNumber......slot number  where the  LCS/MCS/SCS module is plugged in MAP200
                deviceNumber....device to control the each selector has a different device number,
                                so, in LCS thre are two devices (1, for the left one, 2 for the right one in the VLC layout)
                                in SCS the device number may be 4 or 8, depending on the module 
                                specification
                inputNumber.....must be always set to 1
                outputNumber....in LCS module may be set from 0 to 4
                                in SCS module may be seto to 1 or 2
                chassisNumber...set to 1 by default 

            Usage: 
                to get values currently set in a module, don't specify outputNumber.

            Examples:
               # LCS GET Device 2 state (slot 2)
               map200_1.get_set_switch_state(2,2,1)

               # LCS SET  Device 1/2 to positions 0-4
               map200_1.get_set_switch_state(2,1,1,0)
               map200_1.get_set_switch_state(2,1,1,1)
               map200_1.get_set_switch_state(2,1,1,2)
               map200_1.get_set_switch_state(2,1,1,3)
               map200_1.get_set_switch_state(2,1,1,4)

               # SCS GET DEVICE Device 1 state (slot 5)
               map200_1.get_set_switch_state(5,1,1)

               # SET Device 4  To positions 1 and then 2
               map200_1.get_set_switch_state(5,4,1,1)
               map200_1.get_set_switch_state(5,4,1,2)



        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        #print(">>> slotNumber [{}]".format( slotNumber))       
        #print(">>> deviceNumber [{}]".format( deviceNumber))       
        #print(">>> inputNumber[{}]".format( inputNumber))       
        #print(">>> outputNumber [{}]".format( outputNumber))       
        #print(">>> chassisNumber [{}]".format( chassisNumber))       
        if slotNumber == "":
            localMessage = "{} error: slotNumber  [{}] not valid (empty value)".format(methodLocalName,slotNumber)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if deviceNumber == "":
            localMessage = "{} error: deviceNumber  [{}] not valid (empty value)".format(methodLocalName,deviceNumber)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if inputNumber == "":
            localMessage = "{} error: inputNumber  [{}] not valid (empty value)".format(methodLocalName,deviceNumber)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage

        # check slot content
        try:
            slotContent=self.__chassisSlotContent[slotNumber]
            localMessage = "MAP200 [{}]:Slot [{}] Content:[{}]".format(self.__mapIpAddress,slotNumber, slotContent )
            self.__lc_msg(localMessage)
            #self.__method_failure(methodLocalName, None, "", localMessage)
            #return False, localMessage
        except Exception as e:
            self.__lc_msg(str(e))
            localMessage = "MAP200 [{}]: ERROR [{}]".format(self.__mapIpAddress,e)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
          
        # check if moddule supports this command  
        if  (" LCS " in slotContent) or (" SCS " in slotContent) or  (" MCS " in slotContent):
            localMessage = "MAP200 [{}]:found LCS/SCS/MCS".format(self.__mapIpAddress)
            self.__lc_msg(localMessage)
        else:
            moduleName=slotContent.split(" ")
            moduleName=moduleName[1]
            localMessage = "MAP200 [{}]:ERROR: not allowed call {}() for module {}  (not LCS/SCS/MCS)".format(self.__mapIpAddress,methodLocalName,moduleName)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
          
        
        if outputNumber == "":        
            localMessage = "MAP200 [{}]:GET {}".format(self.__mapIpAddress, inputNumber)
            self.__lc_msg(localMessage)
        commandToSend=":ROUT:CLOS? {},{},{},{}".format(chassisNumber, slotNumber, deviceNumber, inputNumber)
        responseList = self.__send_cmd(commandToSend)
        time.sleep(1)
        response = responseList[1]
        response = self.__remove_dust(response)

        #localMessage = "MAP200 [{}]:params: [chassisNumber, slotNumber, deviceNumber, inputNumber]  ".format(self.__mapIpAddress )
        #self.__lc_msg(localMessage)
        #localMessage = "MAP200 [{}]:command [{}] ".format(self.__mapIpAddress, commandToSend)
        #self.__lc_msg(localMessage)
        #localMessage = "MAP200 [{}]:answer  [{}] ".format(self.__mapIpAddress, response)
        #self.__lc_msg(localMessage)
        
        if response == "":
            localMessage = "MAP200 [{}]:ERROR: invalid inputNumber[{}]  parameter".format(self.__mapIpAddress,inputNumber )
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        
        if outputNumber != "":
            commandToSend=":ROUT:CLOS {},{},{},{},{}".format(chassisNumber, slotNumber, deviceNumber, inputNumber, outputNumber)
            responseList = self.__send_cmd(commandToSend)
            self.__lc_msg(commandToSend)
            time.sleep(1)
            commandToSend=":ROUT:CLOS? {},{},{},{}".format(chassisNumber, slotNumber, deviceNumber, inputNumber)
            responseList = self.__send_cmd(commandToSend)
            time.sleep(1)
            response = responseList[1]
            response = self.__remove_dust(response)
            if int(response) != outputNumber:
                localMessage = "MAP200 [{}]:SET {} -> {} ERROR: output still set to [{}]".format(self.__mapIpAddress, inputNumber, outputNumber, response)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage
            localMessage = "MAP200 [{}]:SET {} -> {} ANSWER:[{}]".format(self.__mapIpAddress, inputNumber, outputNumber, response)
            self.__lc_msg(localMessage)
        
        #localMessage="get_set_switch_state OK"
        #self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, localMessage


































    def __create_telnet_connection(self):
        self.__lc_msg("Function: __create_telnet_connection Socket [{}:{}]".format(self.__mapIpAddress,self.__mapTelnetPort))
        try:
            self.__telnetConnection = telnetlib.Telnet(self.__mapIpAddress,self.__mapTelnetPort,self.__telnetTimeout)
            response = self.__send_cmd(":SYSTem:LAYout?")
            localMessage = "Telnet connection established"
            self.__lc_msg(localMessage)
        except Exception as e:
            self.__lc_msg(str(e))
            localMessage = "Telnet connection ERROR"
            self.__lc_msg(localMessage)
            return False, localMessage
        return True, localMessage


























    def clean_up(self):
        """ INTERNAL USAGE
        """
        print("clean_up called [{}]".format(self.__mapType))


    #     
    # Krepo-related     
    #    
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

 








 

    def deinit_instrument(self, portId):
        """
            DEINITALIZES THE ONT INSTRUMENT TO FREE IT 
            after this deinizialization another user can use this Instrument
            the ONT (5xx/6xx) instrument
            portId user's naming convention: P1, P2,...
        """
        #portId = self.__recover_port_to_use(portId)
        localMessage="[{}]: deinit_instrument: TBD".format(self.__mapType)
        self.__lc_msg(localMessage)
        return True, localMessage




    #
    #  INTERNAL UTILITIES
    #
    def __remove_dust(self,stringToClean):
        #  remove the "> " prompt and "\n" from a string
        return str(stringToClean).replace("\n","").replace("\\n","").replace("> ","").replace(">","")



    def __lc_msg(self,messageForDebugPurposes):
        # Print debug messages: verbose mode in test only
        #if __name__ == "__main__":
        #    print ("{:s}".format(messageForDebugPurposes))
        #else:
        #   insert HERE the new logging method (still in progress...)   
        print ("{:s}".format(messageForDebugPurposes))



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




    #
    #  TELNET CONNECTIONS UTILITIES
    #
    def __del__(self):
        self.__lc_msg("Function: __del__")
        if self.__telnetConnection:
            localMessage = "Telnet connection open: close now"
            self.__lc_msg(localMessage)
            self.__telnetConnection.close()
            return True, localMessage
        else:
            localMessage = "Telnet connection not openened: skip close"
            self.__lc_msg(localMessage)
            return False, localMessage



    def __is_reachable(self):
        self.__lc_msg("Function: __is_reachable")
        cmd = "ping -c {} {:s}".format(self.__pingRetryNumber,self.__mapIpAddress)
        if os.system(cmd) == 0:
            localMessage = "IP Address [{}]: answer received".format(self.__mapIpAddress)
            self.__lc_msg(localMessage)
            return True, localMessage
        localMessage = "IP Address [{}]: no answer received".format(self.__mapIpAddress)
        self.__lc_msg(localMessage)
        return False, localMessage



    def __send_cmd(self, command):
        if command == "":
            localMessage = "__send_cmd error: command string [{}] empty".format(command)
            self.__lc_msg(localMessage)
            return False, localMessage
        if not   self.__telnetConnection:
            localMessage = "__send_cmd error: telnet connection [{}] not valid".format(self.__telnetConnection)
            self.__lc_msg(localMessage)
            return False, localMessage
        localCmd="{:s}\n".format(command).encode()
        self.__telnetConnection.write(localCmd)
        result=self.__telnetConnection.expect(self.__telnetExpectedPrompt, 2)
        if result:
            localMessage = "MAP200 command OK"
            #self.__lc_msg(localMessage)
            return True, str(result[2], 'utf-8')
        else:
            localMessage = "MAP200 command ERROR"
            self.__lc_msg(localMessage)
            return False, localMessage








    #
    #   SESSION MANAGEMENT
    #

    def create_session(self, sessionName):       ### krepo added ###
        """ create a new <sessionName> session """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        # create a new session if not exsists and check if done
        #localCommand=":SESM:SES:ASYN {}".format(sessionName)
        localCommand=":SESM:SES {}".format(sessionName)
        callResult = self.__send_cmd(localCommand)

        # check if session created
        localCommand=":SESM:SES?"
        callResult = self.__send_cmd(localCommand)
        verifyResult = self.__verify_presence_in_csv_format_answer(callResult, sessionName)
        if verifyResult[0]: # True
            localMessage="Session [{}] created".format(sessionName)
            self.__lc_msg(localMessage)
            # self.__sessionName = None    # workaround for multiple port management with the same ** default ** session
            self.__sessionName = sessionName  # workaround for multiple port management with the same ** default ** session
            self.__method_success(methodLocalName, None, localMessage)
            return True, localMessage
        localMessage="Session [{}] not created (or not present)".format(sessionName)
        self.__lc_msg(localMessage)
        self.__sessionName = sessionName
        self.__method_failure(methodLocalName, None, "", localMessage)
        return False, localMessage

    def __get_last_error(self):   ### krepo not added ###
        """ Provides info about the last error
            True,  < info string about error >  (string format" <code>,"<message>"    )
            False, < 0, "No error" >  (if no error found)  """
        methodLocalName = self.__lc_current_method_name()
        localCommand=":SYST:ERR?"
        rawCallResult = self.__send_cmd(localCommand)
        callResult = self.__remove_dust(rawCallResult[1])
        ontRawError=tuple(callResult.split(','))
        localMessage="LAST INSTRUMENT ERROR [{}] [{}] ".format(ontRawError[0],ontRawError[1])
        self.__lc_msg(localMessage)
        if int(ontRawError[0]) == 0:  # 0 as string
            return False ,  callResult
    def select_port(self, portId):  ### krepo added ###
        """ Select the portId ( /rack/slotNo/portNo ) port
            if available for the use
            Return tuple:
            True , < information string >
            False, < cause of fail (eg: port already selected... >  """
        # basic check input parameter
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if portId == "":
            localMessage = "port:[{}] not specified: empty parameter".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        # port availability check
        callResult = self.get_available_ports()
        verifyResult = self.__verify_presence_in_csv_format_answer(callResult, portId)
        if not verifyResult[0]: # False
            localMessage = "Port [{}] not selected: not found in available ports list".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        # ONT command
        localCommand = ":PRTM:SEL {}".format(portId)
        CallResult   = self.__send_cmd(localCommand)
        # verify command execution result
        portAllocated = False
        localMessage = "Port [{}] selection FAILED: still present in available ports list".format(portId)
        for n in range(1,self.__mapCmdMaxRetry):
            callResult = self.get_available_ports()
            verifyResult = self.__verify_presence_in_csv_format_answer(callResult, portId)
            if not verifyResult[0]: # False means: port correctly allocated
                commandExecTime = (n * self.__mapSleepTimeForRetry)
                localMessage="Port [{}] selection OK: no more present in available ports list (retry : [{}])".format(portId, n)
                self.__lc_msg(localMessage)
                portAllocated = True
                break
            time.sleep(self.__mapSleepTimeForRetry)
        if portAllocated == True:
            self.__method_success(methodLocalName, None, localMessage)
        else:
            self.__method_failure(methodLocalName, None, "", localMessage)
        return portAllocated, localMessage



    def deselect_port(self, portId): ### krepo added ###
        """ Deselect the portId ( /rack/slotNo/portNo ) port
            if available for the use
            Return tuple:
            True , < information string >
            False, < cause of fail (eg: port already selected... >  """
        # basic check input parameter
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if portId == "":
            localMessage = "port:[{}] not specified: empty parameter".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage

        # port status check
        callResult = self.get_available_ports()
        verifyResult = self.__verify_presence_in_csv_format_answer(callResult, portId)
        if verifyResult[0]: # True: port already deselected
            localMessage = "Port [{}] already deselected: found in available ports list".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage

        # ONT command
        localCommand = ":PRTM:DEL {}".format(portId)
        CallResult   = self.__send_cmd(localCommand)

        # verify command execution result: now the post shoul appear again in the available ports list
        portDeselected = False
        localMessage =  "Port [{}] deselection FAILED: still not present in available ports list".format(portId)
        for n in range(1,self.__mapCmdMaxRetry):
            callResult = self.get_available_ports()
            verifyResult = self.__verify_presence_in_csv_format_answer(callResult, portId)
            if  verifyResult[0]: # True means: port correctly deallocated and present in available ports list
                commandExecTime = (n * self.__mapSleepTimeForRetry)
                localMessage="Port [{}] deselection OK: now present in available ports list (retry : [{}])".format(portId, n)
                self.__lc_msg(localMessage)
                portDeselected = True
                break
            time.sleep(self.__mapSleepTimeForRetry)
        if portDeselected == True:
            self.__method_success(methodLocalName, None, localMessage)
        else:
            self.__method_failure(methodLocalName, None, "", localMessage)
        return portDeselected, localMessage


    def get_selected_ports(self, portId):  ### krepo not added ###
        """ Gets the list of TCP ports selected and ready for the use.
            Return tuple:
            True, < ports : the CSV list of the TCP used to remote control the test module >
                  /rack/slotNo/portNo, /rack/slot/portNo,...
            False, <empty list> if there is no suitable port """
        #methodLocalName = self.__lc_current_method_name()
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        print("@@@ PORT ID := [{:s}] @@@".format(portId))
        localCommand=":PRTM:SEL? {}".format(portId)
        rawCallResult = self.__send_cmd(localCommand)
        callResult = self.__remove_dust(rawCallResult[1])
        localMessage="{}".format(callResult)
        self.__lc_msg(localMessage)
        if callResult == "" :
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, ""
        if callResult == "1" :
            localMessage="ONT ERROR :PRTM:SEL? answers [{}] ".format(callResult)
            self.__lc_msg(localMessage)
            callResult = self.reboot_slot(portId)
            localMessage = self.__get_result_string(callResult)
            self.__lc_msg(localMessage)
            time.sleep(20)
            errorCode=self.__get_last_error()
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, errorCode
        self.__method_success(methodLocalName, None, localMessage)
        return True, localMessage



    def reboot_slot(self,portId):    ### krepo not added ###
        """ Reboot the ONT or a specified port
            Return tuple:
            True, < available ports : the CSV list of not
                    reserved or locked ports with the syntax:
                    /rack/slotNo/portNo
            False, <empty list> if there is no suitable port """
        methodLocalName = self.__lc_current_method_name()
        portId = self.__recover_port_to_use(portId)
        if portId == "":  # reboot rack
            rackSlotId=""
            localMessage="Reboot Instrument NOW (rackSlotId:[{}])".format(rackSlotId)
        else: # reboot slot specified in /rackNo/slotNo(/portNo)  format
            rackSlotPortArray = portId.split("/")
            rackSlotPortArray
            for index, element in enumerate(rackSlotPortArray):
                localMessage="Element:[{}] Value:[{}]".format(index, element)
                self.__lc_msg(localMessage)
            rackSlotId="/{}/{}".format(rackSlotPortArray[1],rackSlotPortArray[2])
            localMessage="Reboot Instrument Slot (rackSlotId:[{}])".format(rackSlotId)
        self.__lc_msg(localMessage)
        localCommand=":PRTM:REBOOT {}".format(rackSlotId)
        rawCallResult = self.__send_cmd(localCommand)
        callResult = self.__remove_dust(rawCallResult[1])
        localMessage="Instrument Cmd Answer:[{}]".format(callResult)
        self.__lc_msg(localMessage)
        if callResult == "":
            return False, ""
        return True, callResult



    #
    #   COMMON COMMANDS
    #
    def wait_ops_completed(self):    ### krepo not added ###
        """ waits untill all ONT operations pending are completed
            True, <  info string >
            False, < info string >   """
        #methodLocalName = self.__lc_current_method_name()
        operationCompleted = False
        for n in range(0,self.__mapCmdMaxRetry):
            localCommand="*OPC?"
            callResult = self.__send_cmd(localCommand)
            verifyResult = self.__verify_presence_in_csv_format_answer(callResult, "1")
            commandExecTime = ((n+1) * self.__mapSleepTimeForRetry)
            if verifyResult[0]: # True means: operations finished
                localMessage="All operations completed (retry: [{}])".format(n)
                self.__lc_msg(localMessage)
                operationCompleted = True
                break
            localMessage="Operation still in progress after [{}] retry)".format(n)
            time.sleep(self.__mapSleepTimeForRetry)
        return operationCompleted, localMessage


 
 






#######################################################################
#
#   MODULE TEST - Test sequences used for DB-Integrated testing
#
#######################################################################
if __name__ == "__main__":   #now use this part
    print(" ")
    print("========================================")
    print("map200Driver  debug")
    print("========================================")

    # K Environment
    kenv = KEnvironment(testfilename=__file__)

    #test with 
    #ID=1046
    map200_1 = InstrumentMAP("map200_1", kenv)
    #ID=1047
    map200_2 = InstrumentMAP("map200_2", kenv)
    
    #map200_1.init_instrument()

    print("\n\n\n\n\nTESTING SECTION *************************************")
    input("press enter to continue...")
    

    #tester_map.deinit_instrument( portId_5xx)

 

    print(" ")
    print("========================================")
    print("map200Driver  debug -- END -- ")
    print("========================================")
    print(" ")

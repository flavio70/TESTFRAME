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
# NOTES:  At the bottom of this file (main section) methods call are reported as examples
#
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
        self.__mapType              = ""               #  Instrument type
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


    def get_preset(self, name):
        """ Get current value for specified presetting
        """
        return self.__prs.get_elem(self.get_label(), name)



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
            self.__mapType = response[1].split(",")[0]
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
                deviceNumber....device to control each selector has a different device number,
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
        else:
            localMessage = "MAP200 [{}]:SET {} to {}".format(self.__mapIpAddress,inputNumber,outputNumber)
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
 


    def get_set_voa_attenuation(self, slotNumber, deviceNumber, attenuation="", chassisNumber=1):
        """ Method:
            Purposes:
                Sets and  gets the attenuation of the VOA module
            Parameters:
                slotNumber......slot number  where the  VOA module is plugged in MAP200
                deviceNumber....device to control: each VOA has two different devices identified by number 1 or 2,
                                so, in LCS thre are two devices (1, for the left one, 2 for the right one in the VLC layout)
                                in SCS the device number may be 4 or 8, depending on the module 
                                specification
                chassisNumber...set to 1 by default 
                attenuation.....Range: 70-0.001 dB to set attenuation
                                No value to read current attenuation setting
            Usage: 
                to get values currently set in a module, don't specify the value.

            Further info from user's manual:
                INPUT RANGE
                Attenuation* Float IA3, VBR: 0.00 to 60.00 dB**
                VOA: (0 + ATToffset) to (ATTmax + ATToffset) dB**
                * Decimal place resolution: IA3: 0.01 dB; SMA: 0.001dB.
                ** The attenuation unit is always dB
            
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        localCommandSet=":OUTP:ATT"
        localCommandGet="{}?".format(localCommandSet)

        # check parameters
        if slotNumber == "":
            localMessage = "{} error: slotNumber  [{}] not valid (empty value)".format(methodLocalName,slotNumber)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if (deviceNumber != 1) and  (deviceNumber != 2):
            localMessage = "{} error: deviceNumber [{}] not valid (1 or 2 allowed)".format(methodLocalName,deviceNumber)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage

        # check slot content
        try:
            slotContent=self.__chassisSlotContent[slotNumber]
            localMessage = "MAP200 [{}]:Slot [{}] Content:[{}]".format(self.__mapIpAddress,slotNumber, slotContent )
            self.__lc_msg(localMessage)
        except Exception as e:
            self.__lc_msg(str(e))
            localMessage = "MAP200 [{}]: ERROR [{}]".format(self.__mapIpAddress,e)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
          
        # check if moddule supports this command  
        if " VOA " in slotContent:
            localMessage = "MAP200 [{}]:found VOA".format(self.__mapIpAddress)
            self.__lc_msg(localMessage)
        else:
            moduleName=slotContent.split(" ")
            moduleName=moduleName[1]
            localMessage = "MAP200 [{}]:ERROR: not allowed call {}() for module {}  (not VOA module)".format(self.__mapIpAddress,methodLocalName,moduleName)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        
        if attenuation == "":        
            localMessage = "MAP200 [{}]:GET {}".format(self.__mapIpAddress,localCommandGet)
            self.__lc_msg(localMessage)
        else:
            localMessage = "MAP200 [{}]:SET {}".format(self.__mapIpAddress,localCommandSet)
            self.__lc_msg(localMessage)
            
        commandToSend="{} {},{},{}".format(localCommandGet ,chassisNumber, slotNumber, deviceNumber)
        responseList = self.__send_cmd(commandToSend)
        time.sleep(1)
        response = responseList[1]
        response = self.__remove_dust(response)
        localMessage = "MAP200 [{}]:current attenuation [{}]".format(self.__mapIpAddress, response )
        self.__lc_msg(localMessage) 
        
        if attenuation != "":
            attenuation="{0:.3f}".format(attenuation)  # need do fix 3 decimal digits for result compare
            commandToSend="{} {},{},{},{}".format(localCommandSet ,chassisNumber, slotNumber, deviceNumber, attenuation)
            responseList = self.__send_cmd(commandToSend)
            self.__lc_msg(commandToSend)
            time.sleep(1)
            commandToSend="{} {},{},{}".format(localCommandGet ,chassisNumber, slotNumber, deviceNumber)
            responseList = self.__send_cmd(commandToSend)
            time.sleep(1)
            response = responseList[1]
            response = self.__remove_dust(response)
            if response != attenuation:
                localMessage = "MAP200 [{}]:ERROR attenuation required [{}] SET instead to [{}]".format(self.__mapIpAddress, attenuation , response)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage
            localMessage = "MAP200 [{}]: ATTENUATION required [{}] SET to [{}]  ".format(self.__mapIpAddress, attenuation, response)
            self.__lc_msg(localMessage)
        localMessage = "MAP200 [{}]:VOA slot {} (Device {}) Attenuation:[{}]".format(self.__mapIpAddress,slotNumber, deviceNumber,response)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, localMessage



    def get_set_voa_attenuation_offset(self, slotNumber, deviceNumber, attOffset="", chassisNumber=1):
        """ Method:
            Purposes:
                Sets and  gets the attenuation offset of the VOA module
            Parameters:
                slotNumber......slot number  where the  VOA module is plugged in MAP200
                deviceNumber....device to control: each VOA has two different devices identified by number 1 or 2,
                                so, in LCS thre are two devices (1, for the left one, 2 for the right one in the VLC layout)
                                in SCS the device number may be 4 or 8, depending on the module 
                                specification
                chassisNumber...set to 1 by default 
                attOffset.....Range: 70-0.001 dB to set attOffset
                                No value to read current attOffset setting
                
            Usage: 
                to get values currently set in a module, don't specify the value.

            Further info from user's manual:
                DESCRIPTION
                Set the attenuation offset of the specified device.
                Note: This value is applied to all VOA attenuation queries (see Output:ATTenuation and Output:ATTenuation? commands).
                INPUT FORMAT
                :OUTPut:ATTenuation:OFFSet <D>,<ATToffset>
                INPUT RANGE
                ATToffset* Float OFFSmin to OFFSmax
                *Resolution: 0.001 dB. The unit of attenuation offset is always dB.

        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        localCommandSet=":OUTP:ATT:OFFS"
        localCommandGet="{}?".format(localCommandSet)

        # check parameters
        if slotNumber == "":
            localMessage = "{} error: slotNumber  [{}] not valid (empty value)".format(methodLocalName,slotNumber)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if (deviceNumber != 1) and  (deviceNumber != 2):
            localMessage = "{} error: deviceNumber [{}] not valid (1 or 2 allowed)".format(methodLocalName,deviceNumber)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage

        # check slot content
        try:
            slotContent=self.__chassisSlotContent[slotNumber]
            localMessage = "MAP200 [{}]:Slot [{}] Content:[{}]".format(self.__mapIpAddress,slotNumber, slotContent )
            self.__lc_msg(localMessage)
        except Exception as e:
            self.__lc_msg(str(e))
            localMessage = "MAP200 [{}]: ERROR [{}]".format(self.__mapIpAddress,e)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
          
        # check if moddule supports this command  
        if  " VOA " in slotContent:
            localMessage = "MAP200 [{}]:found VOA".format(self.__mapIpAddress)
            self.__lc_msg(localMessage)
        else:
            moduleName=slotContent.split(" ")
            moduleName=moduleName[1]
            localMessage = "MAP200 [{}]:ERROR: not allowed call {}() for module {}  (not VOA module)".format(self.__mapIpAddress,methodLocalName,moduleName)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        
        if attOffset == "":        
            localMessage = "MAP200 [{}]:GET {}".format(self.__mapIpAddress,localCommandGet)
            self.__lc_msg(localMessage)
        else:
            localMessage = "MAP200 [{}]:SET {}".format(self.__mapIpAddress,localCommandSet)
            self.__lc_msg(localMessage)
            
        commandToSend="{} {},{},{}".format(localCommandGet ,chassisNumber, slotNumber, deviceNumber)
        responseList = self.__send_cmd(commandToSend)
        time.sleep(1)
        response = responseList[1]
        response = self.__remove_dust(response)
        localMessage = "MAP200 [{}]:current attOffset [{}]".format(self.__mapIpAddress, response )
        self.__lc_msg(localMessage) 
        
        if attOffset != "":
            attOffset="{0:.3f}".format(attOffset)  # need do fix 3 decimal digits for result compare
            commandToSend="{} {},{},{},{}".format(localCommandSet ,chassisNumber, slotNumber, deviceNumber, attOffset)
            responseList = self.__send_cmd(commandToSend)
            self.__lc_msg(commandToSend)
            time.sleep(1)
            commandToSend="{} {},{},{}".format(localCommandGet ,chassisNumber, slotNumber, deviceNumber)
            responseList = self.__send_cmd(commandToSend)
            time.sleep(1)
            response = responseList[1]
            response = self.__remove_dust(response)
            if response != attOffset:
                localMessage = "MAP200 [{}]:ERROR attOffset required [{}] SET instead to [{}]".format(self.__mapIpAddress, attOffset , response)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage
            localMessage = "MAP200 [{}]: ATT OFFSET required [{}] SET to [{}]  ".format(self.__mapIpAddress, attOffset, response)
            self.__lc_msg(localMessage)
        localMessage = "MAP200 [{}]:VOA slot {} (Device {}) Attenuation Offset:[{}]".format(self.__mapIpAddress,slotNumber, deviceNumber,response)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, localMessage


    def get_set_voa_beam_block(self, slotNumber, deviceNumber, state="", chassisNumber=1):
        """ Method:
            Purposes:
                Sets and  gets the attenuation offset of the VOA module
            Parameters:
                slotNumber......slot number  where the  VOA module is plugged in MAP200
                deviceNumber....device to control: each VOA has two different devices identified by number 1 or 2,
                                so, in LCS thre are two devices (1, for the left one, 2 for the right one in the VLC layout)
                                in SCS the device number may be 4 or 8, depending on the module 
                                specification
                chassisNumber...set to 1 by default 
                state...........0=disable, Laser Beam on 
                                1=enable, Laser Beam off
                                No value to read current state setting
                
            Usage: 
                to get values currently set in a module, don't specify the value.

            Further info from user's manual:
                DESCRIPTION
                Set the beam block to one of two states:
                - Beam block activated (beam is blocked). No light is emitted from output port.
                - Beam block deactivated (beam is unblocked). Light may be emitted from the output port 
                  (depending on input signal or internal source state).
                When system is powered up or reset, the beam block is activated (default state). 
                Deactivating the beam block does not guarantee a signal output. 
                See the Laser Source Signal Output Truth Table (Table 4, pg 13 in the manual) for an illustration
                of the interaction between the laser driver, beam block, and the system interlock line.
                If VOA power tracking is enabled (see OUTPut:POWer:CONTrol command) activating the 
                beam block will disable power tracking. Power tracking will be re-enabled once the beam is unblocked.
                INPUT FORMAT
                :OUTPut:BBLock <D>,<State>
                INPUT RANGE
                State Boolean 0 - Deactivated; Beam is unblocked
                1 - Activated; Beam is blocked

        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        localCommandSet=":OUTP:BBL"
        localCommandGet="{}?".format(localCommandSet)

        # check parameters
        if slotNumber == "":
            localMessage = "{} error: slotNumber  [{}] not valid (empty value)".format(methodLocalName,slotNumber)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if (deviceNumber != 1) and  (deviceNumber != 2):
            localMessage = "{} error: deviceNumber [{}] not valid (1 or 2 allowed)".format(methodLocalName,deviceNumber)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage

        # check slot content
        try:
            slotContent=self.__chassisSlotContent[slotNumber]
            localMessage = "MAP200 [{}]:Slot [{}] Content:[{}]".format(self.__mapIpAddress,slotNumber, slotContent )
            self.__lc_msg(localMessage)
        except Exception as e:
            self.__lc_msg(str(e))
            localMessage = "MAP200 [{}]: ERROR [{}]".format(self.__mapIpAddress,e)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
          
        # check if moddule supports this command  
        if  " VOA " in slotContent:
            localMessage = "MAP200 [{}]:found VOA".format(self.__mapIpAddress)
            self.__lc_msg(localMessage)
        else:
            moduleName=slotContent.split(" ")
            moduleName=moduleName[1]
            localMessage = "MAP200 [{}]:ERROR: not allowed call {}() for module {}  (not VOA module)".format(self.__mapIpAddress,methodLocalName,moduleName)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        
        if state == "":        
            localMessage = "MAP200 [{}]:GET {}".format(self.__mapIpAddress,localCommandGet)
            self.__lc_msg(localMessage)
        else:
            localMessage = "MAP200 [{}]:SET {}".format(self.__mapIpAddress,localCommandSet)
            self.__lc_msg(localMessage)
            
        commandToSend="{} {},{},{}".format(localCommandGet ,chassisNumber, slotNumber, deviceNumber)
        responseList = self.__send_cmd(commandToSend)
        time.sleep(1)
        response = responseList[1]
        response = self.__remove_dust(response)
        localMessage = "MAP200 [{}]:current state [{}]".format(self.__mapIpAddress, response )
        self.__lc_msg(localMessage) 
        
        if state != "":
            if (state != 0) and  (state != 1):
                localMessage = "{} error: state [{}] not valid (0 or 1 allowed)".format(methodLocalName,deviceNumber)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage
           
            commandToSend="{} {},{},{},{}".format(localCommandSet ,chassisNumber, slotNumber, deviceNumber, state)
            responseList = self.__send_cmd(commandToSend)
            self.__lc_msg(commandToSend)
            time.sleep(1)
            commandToSend="{} {},{},{}".format(localCommandGet ,chassisNumber, slotNumber, deviceNumber)
            responseList = self.__send_cmd(commandToSend)
            time.sleep(1)
            response = responseList[1]
            response = self.__remove_dust(response)
            #print ("response{}".format(type(response)))
            #print ("state{}".format(type(state)))
            try:
                intresponse=int(response)
            except:
                intresponse=response
            if intresponse != state:
                localMessage = "MAP200 [{}]:ERROR state required [{}] SET instead to [{}]".format(self.__mapIpAddress, state , response)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage
            localMessage = "MAP200 [{}]: BEAM BLOCK required [{}] SET to [{}]  ".format(self.__mapIpAddress, state, response)
            self.__lc_msg(localMessage)
        localMessage = "MAP200 [{}]:VOA slot {} (Device {}) Beam Block State:[{}]".format(self.__mapIpAddress,slotNumber, deviceNumber,response)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, localMessage



    def get_set_voa_offset(self, slotNumber, deviceNumber, offset="", chassisNumber=1):
        """ Method:
            Purposes:
                Sets and  gets the offset of the VOA module
            Parameters:
                slotNumber......slot number  where the  VOA module is plugged in MAP200
                deviceNumber....device to control: each VOA has two different devices identified by number 1 or 2,
                                so, in LCS thre are two devices (1, for the left one, 2 for the right one in the VLC layout)
                                in SCS the device number may be 4 or 8, depending on the module 
                                specification
                chassisNumber...set to 1 by default 
                offset..........Range: -100+100 dB to set offset
                                No value to read current offset setting
                
            Usage: 
                to get values currently set in a module, don't specify the value.

            Further info from user's manual:
                DESCRIPTION
                Set the reference value used in calculating theoretical output power of the specified device.
                Note: This is a legacy command, valid only on the IA3. The VOA implements this command only for backward compatibility. On the VOA, use OUTPut:POWer:OFFSet command.
                INPUT FORMAT
                :OUTPut:OFFSet <C>,<S>,<D>,<REFoffset>
                MAP-200 Programming Manual (21147945 rev 002)  167
                INPUT RANGE
                REFoffset* Float -100.00 to 100.00 dB
                *Resolution: IA3: 0.01dB; VOA: 0.002 dB.
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        localCommandSet=":OUTP:OFFS"
        localCommandGet="{}?".format(localCommandSet)

        # check parameters
        if slotNumber == "":
            localMessage = "{} error: slotNumber  [{}] not valid (empty value)".format(methodLocalName,slotNumber)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if (deviceNumber != 1) and  (deviceNumber != 2):
            localMessage = "{} error: deviceNumber [{}] not valid (1 or 2 allowed)".format(methodLocalName,deviceNumber)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage

        # check slot content
        try:
            slotContent=self.__chassisSlotContent[slotNumber]
            localMessage = "MAP200 [{}]:Slot [{}] Content:[{}]".format(self.__mapIpAddress,slotNumber, slotContent )
            self.__lc_msg(localMessage)
        except Exception as e:
            self.__lc_msg(str(e))
            localMessage = "MAP200 [{}]: ERROR [{}]".format(self.__mapIpAddress,e)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
          
        # check if moddule supports this command  
        if  " VOA " in slotContent:
            localMessage = "MAP200 [{}]:found VOA".format(self.__mapIpAddress)
            self.__lc_msg(localMessage)
        else:
            moduleName=slotContent.split(" ")
            moduleName=moduleName[1]
            localMessage = "MAP200 [{}]:ERROR: not allowed call {}() for module {}  (not VOA module)".format(self.__mapIpAddress,methodLocalName,moduleName)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        
        if offset == "":        
            localMessage = "MAP200 [{}]:GET {}".format(self.__mapIpAddress,localCommandGet)
            self.__lc_msg(localMessage)
        else:
            localMessage = "MAP200 [{}]:SET {}".format(self.__mapIpAddress,localCommandSet)
            self.__lc_msg(localMessage)
            
        commandToSend="{} {},{},{}".format(localCommandGet ,chassisNumber, slotNumber, deviceNumber)
        responseList = self.__send_cmd(commandToSend)
        time.sleep(1)
        response = responseList[1]
        response = self.__remove_dust(response)
        localMessage = "MAP200 [{}]:current offset [{}]".format(self.__mapIpAddress, response )
        self.__lc_msg(localMessage) 
        
        if offset != "":
            offset="{0:.3f}".format(offset)  # need do fix 3 decimal digits for result compare
            commandToSend="{} {},{},{},{}".format(localCommandSet ,chassisNumber, slotNumber, deviceNumber, offset)
            responseList = self.__send_cmd(commandToSend)
            self.__lc_msg(commandToSend)
            time.sleep(1)
            commandToSend="{} {},{},{}".format(localCommandGet ,chassisNumber, slotNumber, deviceNumber)
            responseList = self.__send_cmd(commandToSend)
            time.sleep(1)
            response = responseList[1]
            response = self.__remove_dust(response)
            if response != offset:
                localMessage = "MAP200 [{}]:ERROR offset required [{}] SET instead to [{}]".format(self.__mapIpAddress, offset , response)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage
            localMessage = "MAP200 [{}]: OFFSET required [{}] SET to [{}]  ".format(self.__mapIpAddress, offset, response)
            self.__lc_msg(localMessage)
        localMessage = "MAP200 [{}]:VOA slot {} (Device {}) Attenuation Offset:[{}]".format(self.__mapIpAddress,slotNumber, deviceNumber,response)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, localMessage



    def get_voa_power(self, slotNumber, deviceNumber, chassisNumber=1):
        """ Method:
            Purposes:
                Query the theoretical output power of the specified device
            Parameters:
                slotNumber......slot number  where the  VOA module is plugged in MAP200
                deviceNumber....device to control: each VOA has two different devices identified by number 1 or 2,
                                so, in LCS thre are two devices (1, for the left one, 2 for the right one in the VLC layout)
                                in SCS the device number may be 4 or 8, depending on the module 
                                specification
                chassisNumber...set to 1 by default 

            Further info from user's manual:
            DESCRIPTION
                Query the theoretical optical output power of the specified device.
                - The input power is always assumed to be 0 dBm. If actual input power is different 
                  the OUTPut:OFFSet command should be used to set a reference value.
                - This query does not necessarily reflect the actual power of the output signal. 
                  For example, if the beam block is activated, no signal is output therefore the 
                  output power is actually 0.
                - For VOA with output power detector, use FETCh:POWer:OUTPut? to query the actual 
                  output power.
                INPUT FORMAT
                :OUTPut:POWer? <D>
                INPUT RANGE
                None
                OUTPUT FORMAT
                <Power>
                OUTPUT RANGE
                Power* Float (-Attenuation**) + REFoffset dB***                
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        localCommandSet=":OUTP:POW"
        localCommandGet="{}?".format(localCommandSet)

        # check parameters
        if slotNumber == "":
            localMessage = "{} error: slotNumber  [{}] not valid (empty value)".format(methodLocalName,slotNumber)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if (deviceNumber != 1) and  (deviceNumber != 2):
            localMessage = "{} error: deviceNumber [{}] not valid (1 or 2 allowed)".format(methodLocalName,deviceNumber)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage

        # check slot content
        try:
            slotContent=self.__chassisSlotContent[slotNumber]
            localMessage = "MAP200 [{}]:Slot [{}] Content:[{}]".format(self.__mapIpAddress,slotNumber, slotContent )
            self.__lc_msg(localMessage)
        except Exception as e:
            self.__lc_msg(str(e))
            localMessage = "MAP200 [{}]: ERROR [{}]".format(self.__mapIpAddress,e)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
          
        # check if moddule supports this command  
        if  " VOA " in slotContent:
            localMessage = "MAP200 [{}]:found VOA".format(self.__mapIpAddress)
            self.__lc_msg(localMessage)
        else:
            moduleName=slotContent.split(" ")
            moduleName=moduleName[1]
            localMessage = "MAP200 [{}]:ERROR: not allowed call {}() for module {}  (not VOA module)".format(self.__mapIpAddress,methodLocalName,moduleName)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
             
        commandToSend="{} {},{},{}".format(localCommandGet ,chassisNumber, slotNumber, deviceNumber)
        responseList = self.__send_cmd(commandToSend)
        time.sleep(1)
        response = responseList[1]
        response = self.__remove_dust(response)
        localMessage = "MAP200 [{}]:current state [{}]".format(self.__mapIpAddress, response )
        self.__lc_msg(localMessage) 
        
        localMessage = "MAP200 [{}]:VOA slot {} (Device {}) power:[{}]".format(self.__mapIpAddress,slotNumber, deviceNumber,response)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, localMessage


    #==========================
    # CHIARIRE CON TOSI i requisiti affinche' si possa attivare
    #==========================
    def get_set_voa_power_control(self, slotNumber, deviceNumber, state="", chassisNumber=1):
        """ Method:
            Purposes:
                Enable or disable power tracking mode whereby, if enabled, the attenuation will be adjusted 
                until the output power level matches the target values  
            Parameters:
                slotNumber......slot number  where the  VOA module is plugged in MAP200
                deviceNumber....device to control: each VOA has two different devices identified by number 1 or 2,
                                so, in LCS thre are two devices (1, for the left one, 2 for the right one in the VLC layout)
                                in SCS the device number may be 4 or 8, depending on the module 
                                specification
                chassisNumber...set to 1 by default 
                state...........0=disable power control
                                1=enable power control
                                No value to read current state setting
                
            Usage: 
                to get values currently set in a module, don't specify the value.

            Further info from user's manual:
                DESCRIPTION
                Enables or disables power tracking mode whereby, if enabled, the attenuation 
                will be adjusted until the output power level matches the target value 
                (see the OUTPut:POWer:TARGet command), within the accuracy limit specified 
                (see the OUTPut:POWer:THREshold command).
                If the output power level exceeds the hold threshold, attenuation will again 
                be adjusted until the target output power level is achieved.
                Output power sampling (thus target power updates) frequency is defined by 
                the ATIME (see SENSe:POWer:ATIMe command).
                INPUT FORMAT
                :OUTPut:POWer:CONTrol <D>,<State>
                INPUT RANGE
                State Boolean 0  Power tracking disabled
                1  Power tacking is enabled
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        localCommandSet=":OUTP:POW:CONT"
        localCommandGet="{}?".format(localCommandSet)

        # check parameters
        if slotNumber == "":
            localMessage = "{} error: slotNumber  [{}] not valid (empty value)".format(methodLocalName,slotNumber)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if (deviceNumber != 1) and  (deviceNumber != 2):
            localMessage = "{} error: deviceNumber [{}] not valid (1 or 2 allowed)".format(methodLocalName,deviceNumber)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage

        # check slot content
        try:
            slotContent=self.__chassisSlotContent[slotNumber]
            localMessage = "MAP200 [{}]:Slot [{}] Content:[{}]".format(self.__mapIpAddress,slotNumber, slotContent )
            self.__lc_msg(localMessage)
        except Exception as e:
            self.__lc_msg(str(e))
            localMessage = "MAP200 [{}]: ERROR [{}]".format(self.__mapIpAddress,e)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
          
        # check if moddule supports this command  
        if  " VOA " in slotContent:
            localMessage = "MAP200 [{}]:found VOA".format(self.__mapIpAddress)
            self.__lc_msg(localMessage)
        else:
            moduleName=slotContent.split(" ")
            moduleName=moduleName[1]
            localMessage = "MAP200 [{}]:ERROR: not allowed call {}() for module {}  (not VOA module)".format(self.__mapIpAddress,methodLocalName,moduleName)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        
        if state == "":        
            localMessage = "MAP200 [{}]:GET {}".format(self.__mapIpAddress,localCommandGet)
            self.__lc_msg(localMessage)
        else:
            localMessage = "MAP200 [{}]:SET {}".format(self.__mapIpAddress,localCommandSet)
            self.__lc_msg(localMessage)
            
        commandToSend="{} {},{},{}".format(localCommandGet ,chassisNumber, slotNumber, deviceNumber)
        responseList = self.__send_cmd(commandToSend)
        time.sleep(1)
        response = responseList[1]
        response = self.__remove_dust(response)
        localMessage = "MAP200 [{}]:current state [{}]".format(self.__mapIpAddress, response )
        self.__lc_msg(localMessage) 
        
        if state != "":
            if (state != 0) and  (state != 1):
                localMessage = "{} error: state [{}] not valid (0 or 1 allowed)".format(methodLocalName,deviceNumber)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage
           
            commandToSend="{} {},{},{},{}".format(localCommandSet ,chassisNumber, slotNumber, deviceNumber, state)
            responseList = self.__send_cmd(commandToSend)
            self.__lc_msg(commandToSend)
            time.sleep(1)
            commandToSend="{} {},{},{}".format(localCommandGet ,chassisNumber, slotNumber, deviceNumber)
            responseList = self.__send_cmd(commandToSend)
            time.sleep(1)
            response = responseList[1]
            response = self.__remove_dust(response)
            try:
                intresponse=int(response)
            except:
                intresponse=response
            if intresponse != state:
                localMessage = "MAP200 [{}]:ERROR state required [{}] SET instead to [{}]".format(self.__mapIpAddress, state , response)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage
            localMessage = "MAP200 [{}]: power control required [{}] SET to [{}]  ".format(self.__mapIpAddress, state, response)
            self.__lc_msg(localMessage)
        localMessage = "MAP200 [{}]:VOA slot {} (Device {}) power control  State:[{}]".format(self.__mapIpAddress,slotNumber, deviceNumber,response)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, localMessage




    def get_set_voa_power_offset(self, slotNumber, deviceNumber, powerOffset="", chassisNumber=1):
        """ Method:
            Purposes:
                Sets and  gets the laser power offset of the VOA module
            Parameters:
                slotNumber......slot number  where the  VOA module is plugged in MAP200
                deviceNumber....device to control: each VOA has two different devices identified by number 1 or 2,
                chassisNumber...set to 1 by default 
                powerOffset.....Range: 70-0.001 dB to set powerOffset
                                No value to read current powerOffset setting
                
            Usage: 
                to get values currently set in a module, don't specify the value.

            Further info from user's manual:
                POWoffset* Float OFFSmin to OFFSmax
                *The unit is always dB.

        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        localCommandSet=":OUTP:POW:OFFS"
        localCommandGet="{}?".format(localCommandSet)

        # check parameters
        if slotNumber == "":
            localMessage = "{} error: slotNumber  [{}] not valid (empty value)".format(methodLocalName,slotNumber)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if (deviceNumber != 1) and  (deviceNumber != 2):
            localMessage = "{} error: deviceNumber [{}] not valid (1 or 2 allowed)".format(methodLocalName,deviceNumber)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage

        # check slot content
        try:
            slotContent=self.__chassisSlotContent[slotNumber]
            localMessage = "MAP200 [{}]:Slot [{}] Content:[{}]".format(self.__mapIpAddress,slotNumber, slotContent )
            self.__lc_msg(localMessage)
        except Exception as e:
            self.__lc_msg(str(e))
            localMessage = "MAP200 [{}]: ERROR [{}]".format(self.__mapIpAddress,e)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
          
        # check if moddule supports this command  
        if  " VOA " in slotContent:
            localMessage = "MAP200 [{}]:found VOA".format(self.__mapIpAddress)
            self.__lc_msg(localMessage)
        else:
            moduleName=slotContent.split(" ")
            moduleName=moduleName[1]
            localMessage = "MAP200 [{}]:ERROR: not allowed call {}() for module {}  (not VOA module)".format(self.__mapIpAddress,methodLocalName,moduleName)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        
        if powerOffset == "":        
            localMessage = "MAP200 [{}]:GET {}".format(self.__mapIpAddress,localCommandGet)
            self.__lc_msg(localMessage)
        else:
            localMessage = "MAP200 [{}]:SET {}".format(self.__mapIpAddress,localCommandSet)
            self.__lc_msg(localMessage)
            
        commandToSend="{} {},{},{}".format(localCommandGet ,chassisNumber, slotNumber, deviceNumber)
        responseList = self.__send_cmd(commandToSend)
        time.sleep(1)
        response = responseList[1]
        response = self.__remove_dust(response)
        localMessage = "MAP200 [{}]:current powerOffset [{}]".format(self.__mapIpAddress, response )
        self.__lc_msg(localMessage) 
        
        if powerOffset != "":
            powerOffset="{0:.3f}".format(powerOffset)  # need do fix 3 decimal digits for result compare
            commandToSend="{} {},{},{},{}".format(localCommandSet ,chassisNumber, slotNumber, deviceNumber, powerOffset)
            responseList = self.__send_cmd(commandToSend)
            self.__lc_msg(commandToSend)
            time.sleep(1)
            commandToSend="{} {},{},{}".format(localCommandGet ,chassisNumber, slotNumber, deviceNumber)
            responseList = self.__send_cmd(commandToSend)
            time.sleep(1)
            response = responseList[1]
            response = self.__remove_dust(response)
            if response != powerOffset:
                localMessage = "MAP200 [{}]:ERROR powerOffset required [{}] SET instead to [{}]".format(self.__mapIpAddress, powerOffset , response)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage
            localMessage = "MAP200 [{}]: POWER OFFSET required [{}] SET to [{}]  ".format(self.__mapIpAddress, powerOffset, response)
            self.__lc_msg(localMessage)
        localMessage = "MAP200 [{}]:VOA slot {} (Device {}) Power Offset:[{}]".format(self.__mapIpAddress,slotNumber, deviceNumber,response)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, localMessage



    def get_set_voa_power_target(self, slotNumber, deviceNumber, powerTarget="", chassisNumber=1):
        """ Method:
            Purposes:
                Set the optical output power target.
            Parameters:
                slotNumber......slot number  where the  VOA module is plugged in MAP200
                deviceNumber....device to control: each VOA has two different devices identified by number 1 or 2,
                chassisNumber...set to 1 by default 
                powerTarget.....Range: 70-0.001 dB to set powerTarget
                                No value to read current powerTarget setting
                
            Usage: 
                to get values currently set in a module, don't specify the value.

            Further info from user's manual:
               Query the optical output power target. This query does not necessarily reflect the actual power of the output signal. For example, if the beam block is activated, no signal is output therefore the output power is actually 0.
               INPUT FORMAT
               :OUTPut:POWer:TARGet? <D>
               INPUT RANGE
               None
               OUTPUT FORMAT
               <Power>
               OUTPUT RANGE
               Power* Float (Pmin to Pmax) + PowOffset**
               *Resolution: 0.002dBm. The unit can be dBm or W depending on system power unit.
               ** See OUTPut:POWer:OFFSet command.
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        localCommandSet=":OUTP:POW:TARG"
        localCommandGet="{}?".format(localCommandSet)

        # check parameters
        if slotNumber == "":
            localMessage = "{} error: slotNumber  [{}] not valid (empty value)".format(methodLocalName,slotNumber)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if (deviceNumber != 1) and  (deviceNumber != 2):
            localMessage = "{} error: deviceNumber [{}] not valid (1 or 2 allowed)".format(methodLocalName,deviceNumber)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage

        # check slot content
        try:
            slotContent=self.__chassisSlotContent[slotNumber]
            localMessage = "MAP200 [{}]:Slot [{}] Content:[{}]".format(self.__mapIpAddress,slotNumber, slotContent )
            self.__lc_msg(localMessage)
        except Exception as e:
            self.__lc_msg(str(e))
            localMessage = "MAP200 [{}]: ERROR [{}]".format(self.__mapIpAddress,e)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
          
        # check if moddule supports this command  
        if  " VOA " in slotContent:
            localMessage = "MAP200 [{}]:found VOA".format(self.__mapIpAddress)
            self.__lc_msg(localMessage)
        else:
            moduleName=slotContent.split(" ")
            moduleName=moduleName[1]
            localMessage = "MAP200 [{}]:ERROR: not allowed call {}() for module {}  (not VOA module)".format(self.__mapIpAddress,methodLocalName,moduleName)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        
        if powerTarget == "":        
            localMessage = "MAP200 [{}]:GET {}".format(self.__mapIpAddress,localCommandGet)
            self.__lc_msg(localMessage)
        else:
            localMessage = "MAP200 [{}]:SET {}".format(self.__mapIpAddress,localCommandSet)
            self.__lc_msg(localMessage)
            
        commandToSend="{} {},{},{}".format(localCommandGet ,chassisNumber, slotNumber, deviceNumber)
        responseList = self.__send_cmd(commandToSend)
        time.sleep(1)
        response = responseList[1]
        response = self.__remove_dust(response)
        localMessage = "MAP200 [{}]:current powerTarget [{}]".format(self.__mapIpAddress, response )
        self.__lc_msg(localMessage) 
        
        if powerTarget != "":
            powerTarget="{0:.3f}".format(powerTarget)  # need do fix 3 decimal digits for result compare
            commandToSend="{} {},{},{},{}".format(localCommandSet ,chassisNumber, slotNumber, deviceNumber, powerTarget)
            responseList = self.__send_cmd(commandToSend)
            self.__lc_msg(commandToSend)
            time.sleep(1)
            commandToSend="{} {},{},{}".format(localCommandGet ,chassisNumber, slotNumber, deviceNumber)
            responseList = self.__send_cmd(commandToSend)
            time.sleep(1)
            response = responseList[1]
            response = self.__remove_dust(response)
            if response != powerTarget:
                localMessage = "MAP200 [{}]:ERROR powerTarget required [{}] SET instead to [{}]".format(self.__mapIpAddress, powerTarget , response)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage
            localMessage = "MAP200 [{}]: POWER TARGET required [{}] SET to [{}]  ".format(self.__mapIpAddress, powerTarget, response)
            self.__lc_msg(localMessage)
        localMessage = "MAP200 [{}]:VOA slot {} (Device {}) Power Target:[{}]".format(self.__mapIpAddress,slotNumber, deviceNumber,response)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, localMessage



    #==========================
    # CHIARIRE CON TOSI i requisiti affinche' si possa attivare
    #==========================
    def get_set_voa_power_threshold(self, slotNumber, deviceNumber, seekThreshold="", holdThreshold="", chassisNumber=1):
        """ Method:
            Purposes:
                Set the optical output power threshold and accuracy.
            Parameters:
                slotNumber......slot number  where the  VOA module is plugged in MAP200l
                deviceNumber....device to control: each VOA has two different devices identified by number 1 or 2,
                chassisNumber...set to 1 by default 
                seekThreshold.... use no value to read current seekThreshold setting
                holdThreshold.... use no value to read current holdThreshold setting
                
            Usage: 
                to get values currently set in a module, don't specify the value.

            Further info from user's manual:
                Seek accuracy Float 0.01 to 5dB*
               Hold threshold Float 0 to 5dB*
               *The unit is always dB.
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        localCommandSet=":OUTP:POW:THRE"
        localCommandGet="{}?".format(localCommandSet)

        # check parameters
        if slotNumber == "":
            localMessage = "{} error: slotNumber  [{}] not valid (empty value)".format(methodLocalName,slotNumber)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if (deviceNumber != 1) and  (deviceNumber != 2):
            localMessage = "{} error: deviceNumber [{}] not valid (1 or 2 allowed)".format(methodLocalName,deviceNumber)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage

        # check slot content
        try:
            slotContent=self.__chassisSlotContent[slotNumber]
            localMessage = "MAP200 [{}]:Slot [{}] Content:[{}]".format(self.__mapIpAddress,slotNumber, slotContent )
            self.__lc_msg(localMessage)
        except Exception as e:
            self.__lc_msg(str(e))
            localMessage = "MAP200 [{}]:ERROR [{}]".format(self.__mapIpAddress,e)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
          
        # check if moddule supports this command  
        if  " VOA " in slotContent:
            localMessage = "MAP200 [{}]:found VOA".format(self.__mapIpAddress)
            self.__lc_msg(localMessage)
        else:
            moduleName=slotContent.split(" ")
            moduleName=moduleName[1]
            localMessage = "MAP200 [{}]:ERROR: not allowed call {}() for module {}  (not VOA module)".format(self.__mapIpAddress,methodLocalName,moduleName)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        
        if seekThreshold == "" or holdThreshold == "":        
            localMessage = "MAP200 [{}]:GET {}".format(self.__mapIpAddress,localCommandGet)
            self.__lc_msg(localMessage)
        else:
            localMessage = "MAP200 [{}]:SET {}".format(self.__mapIpAddress,localCommandSet)
            self.__lc_msg(localMessage)
            
        commandToSend="{} {},{},{}".format(localCommandGet ,chassisNumber, slotNumber, deviceNumber)
        responseList = self.__send_cmd(commandToSend)
        time.sleep(1)
        response = responseList[1]
        response = self.__remove_dust(response)
        localMessage = "MAP200 [{}]:current seek/hold Thresholds: [{}]".format(self.__mapIpAddress, response )
        self.__lc_msg(localMessage) 
        
        if seekThreshold != "" and holdThreshold != "" :
            seekThreshold="{0:.3f}".format(seekThreshold)  # need do fix 3 decimal digits for result compare
            holdThreshold="{0:.3f}".format(holdThreshold)  # need do fix 3 decimal digits for result compare
            if (float(seekThreshold) < 0.01)  or (float(seekThreshold) > 5):
                localMessage = "MAP200 [{}]:ERROR: seekThreshold  [{}] out of allowed range 0.01-5".format(self.__mapIpAddress, seekThreshold)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage
            if (float(holdThreshold) < 0)  or (float(holdThreshold) > 5):
                localMessage = "MAP200 [{}]:ERROR: holdThreshold  [{}] out of allowed range 0-5".format(self.__mapIpAddress, holdThreshold)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage
            commandToSend="{} {},{},{},{},{}".format(localCommandSet ,chassisNumber, slotNumber, deviceNumber, seekThreshold, holdThreshold)
            responseList = self.__send_cmd(commandToSend)
            self.__lc_msg(commandToSend)
            time.sleep(1)
            commandToSend="{} {},{},{}".format(localCommandGet ,chassisNumber, slotNumber, deviceNumber)
            responseList = self.__send_cmd(commandToSend)
            time.sleep(1)
            response = responseList[1]
            response = self.__remove_dust(response)
            responseNewList=response.split(",")
            currentSeekThreshold=responseNewList[0]
            currentHoldThreshold=responseNewList[1]
 
            if ( float(seekThreshold) != float(currentSeekThreshold)) or ( float(holdThreshold) != float(currentHoldThreshold)): 
                localMessage = "MAP200 [{}]:ERROR threshold required [{}][{}]  SET instead to [{}][{}]  ".format(self.__mapIpAddress, seekThreshold, holdThreshold, currentSeekThreshold,  currentHoldThreshold)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage
            localMessage = "MAP200 [{}]:POWER threshold required [{}][{}]  SET to [{}][{}]  ".format(self.__mapIpAddress, seekThreshold, holdThreshold, currentSeekThreshold,  currentHoldThreshold)
            self.__lc_msg(localMessage)
        localMessage = "MAP200 [{}]:VOA slot {} (Device {}) Power Threshold:[{}][{}]".format(self.__mapIpAddress,slotNumber, deviceNumber, currentSeekThreshold, currentHoldThreshold)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, localMessage



    def get_set_voa_wave_length(self, slotNumber, deviceNumber, wavelength="", chassisNumber=1):
        """ Method:
            Purposes:
                Sets and  gets the wavelength of the VOA module
            Parameters:
                slotNumber......slot number  where the  VOA module is plugged in MAP200
                deviceNumber....device to control: each VOA has two different devices identified by number 1 or 2,
                                so, in LCS thre are two devices (1, for the left one, 2 for the right one in the VLC layout)
                                in SCS the device number may be 4 or 8, depending on the module 
                                specification
                chassisNumber...set to 1 by default 
                wavelength......Range Wmin-Wmax
                                Resolution: IA3, VBR: 1nm; VOA: 0.002nm.
                                No value to read current wavelength setting
            Usage: 
                to get values currently set in a module, don't specify the value.
            Further info from user's manual:
                Query the wavelength of the specified device.
                INPUT FORMAT
                :OUTPut:WAVelength? <D>
                INPUT RANGE
                OUTPUT FORMAT
                <Wavelength>
                OUTPUT RANGE
                Wavelength* Float Wmin to Wmax nm
                *Resolution: IA3, VBR: 1nm; VOA: 0.002nm.

        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        localCommandSet=":OUTP:WAV"
        localCommandGet="{}?".format(localCommandSet)

        # check parameters
        if slotNumber == "":
            localMessage = "{} error: slotNumber  [{}] not valid (empty value)".format(methodLocalName,slotNumber)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if (deviceNumber != 1) and  (deviceNumber != 2):
            localMessage = "{} error: deviceNumber [{}] not valid (1 or 2 allowed)".format(methodLocalName,deviceNumber)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage

        # check slot content
        try:
            slotContent=self.__chassisSlotContent[slotNumber]
            localMessage = "MAP200 [{}]:Slot [{}] Content:[{}]".format(self.__mapIpAddress,slotNumber, slotContent )
            self.__lc_msg(localMessage)
        except Exception as e:
            self.__lc_msg(str(e))
            localMessage = "MAP200 [{}]: ERROR [{}]".format(self.__mapIpAddress,e)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
          
        # check if moddule supports this command  
        if  " VOA " in slotContent:
            localMessage = "MAP200 [{}]:found VOA".format(self.__mapIpAddress)
            self.__lc_msg(localMessage)
        else:
            moduleName=slotContent.split(" ")
            moduleName=moduleName[1]
            localMessage = "MAP200 [{}]:ERROR: not allowed call {}() for module {}  (not VOA module)".format(self.__mapIpAddress,methodLocalName,moduleName)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        
        if wavelength == "":        
            localMessage = "MAP200 [{}]:GET {}".format(self.__mapIpAddress,localCommandGet)
            self.__lc_msg(localMessage)
        else:
            localMessage = "MAP200 [{}]:SET {}".format(self.__mapIpAddress,localCommandSet)
            self.__lc_msg(localMessage)
            
        commandToSend="{} {},{},{}".format(localCommandGet ,chassisNumber, slotNumber, deviceNumber)
        responseList = self.__send_cmd(commandToSend)
        time.sleep(1)
        response = responseList[1]
        response = self.__remove_dust(response)
        localMessage = "MAP200 [{}]:current wavelength [{}]".format(self.__mapIpAddress, response )
        self.__lc_msg(localMessage) 
        
        if wavelength != "":
            wavelength="{0:.3f}".format(wavelength)  # need do fix 3 decimal digits for result compare
            commandToSend="{} {},{},{},{}".format(localCommandSet ,chassisNumber, slotNumber, deviceNumber, wavelength)
            responseList = self.__send_cmd(commandToSend)
            self.__lc_msg(commandToSend)
            time.sleep(1)
            commandToSend="{} {},{},{}".format(localCommandGet ,chassisNumber, slotNumber, deviceNumber)
            responseList = self.__send_cmd(commandToSend)
            time.sleep(1)
            response = responseList[1]
            response = self.__remove_dust(response)
            if response != wavelength:
                localMessage = "MAP200 [{}]:ERROR wavelength required [{}] SET instead to [{}]".format(self.__mapIpAddress, wavelength , response)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage
            localMessage = "MAP200 [{}]: WAVELENGTH required [{}] SET to [{}]  ".format(self.__mapIpAddress, wavelength, response)
            self.__lc_msg(localMessage)
        localMessage = "MAP200 [{}]:VOA slot {} (Device {})  wavelength:[{}]".format(self.__mapIpAddress,slotNumber, deviceNumber,response)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, localMessage



    def get_set_voa_wave_power_offset(self, slotNumber, deviceNumber, wave="", offset="", chassisNumber=1):
        """ Method:
            Purposes:
                Define an output power offset at the specified wavelength. T
                his offset is applied to all subsequent 
                FETCh:POWer:OUTPut? queries when wavelength offset  is enabled (see OUTPut:WAVelength:POWer:OFFSet:ENABle command).  
            Parameters:
                slotNumber......slot number  where the  VOA module is plugged in MAP200l
                deviceNumber....device to control: each VOA has two different devices identified by number 1 or 2,
                chassisNumber...set to 1 by default 
                wave.... use no value to read current wave setting
                offset...Range: -10 to 10 dB.  use no value to read current offset setting 
                
            Usage: 
                to get values currently set in a module, don't specify the value.

            Further info from user's manual:
               Define an output power offset at the specified wavelength. 
               This offset is applied to all subsequent FETCh:POWer:OUTPut? queries when 
               wavelength offset is enabled (see OUTPut:WAVelength:POWer:OFFSet:ENABle command).
               This information is saved over reset/power-off/hot-swap events.
               Power offset for the device wavelength (see OUTPut:WAVelength command) is determined as follows:
               - Wavelength matches a point for which a power offset has been defined: the defined power offset is used.
               - Wavelength does not match any previously-defined points, but falls between two 
                 previously-defined points: power offset is calculated by linear interpolation 
                 using the closest neighboring points.
               - Wavelength does not match any previously-defined points, and is above or below all 
                 previously-defined points: the offset for the closest wavelength is used.
               - A single wavelength power offset is defined: this offset is always used.
               Important:
               Up to 100 different wavelength power offset points can be entered for each device. 
               After 100 points have been entered, offset values for previously-defined points 
               can be modified. However, if further wavelengths are specified an error is generated 
               and that offset not saved.
               If wavelength offset mode is enabled (see OUTPut:WAVelength:POWer:OFFSet:ENABle command), 
               offsets cannot be set. An error is generated.
               INPUT FORMAT
               :OUTPut:WAVelength:POWer:OFFSet <D>,<Wavelength>,<Offset>
               INPUT RANGE
               Offset* Float -10 to 10 dB
               *The offset unit is always dB.          
            """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        localCommandSet=":OUTP:WAV:POW:OFFS"
        localCommandGet="{}?".format(localCommandSet)

        # check parameters
        if slotNumber == "":
            localMessage = "{} error: slotNumber  [{}] not valid (empty value)".format(methodLocalName,slotNumber)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if (deviceNumber != 1) and  (deviceNumber != 2):
            localMessage = "{} error: deviceNumber [{}] not valid (1 or 2 allowed)".format(methodLocalName,deviceNumber)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage

        # check slot content
        try:
            slotContent=self.__chassisSlotContent[slotNumber]
            localMessage = "MAP200 [{}]:Slot [{}] Content:[{}]".format(self.__mapIpAddress,slotNumber, slotContent )
            self.__lc_msg(localMessage)
        except Exception as e:
            self.__lc_msg(str(e))
            localMessage = "MAP200 [{}]:ERROR [{}]".format(self.__mapIpAddress,e)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
          
        # check if moddule supports this command  
        if  " VOA " in slotContent:
            localMessage = "MAP200 [{}]:found VOA".format(self.__mapIpAddress)
            self.__lc_msg(localMessage)
        else:
            moduleName=slotContent.split(" ")
            moduleName=moduleName[1]
            localMessage = "MAP200 [{}]:ERROR: not allowed call {}() for module {}  (not VOA module)".format(self.__mapIpAddress,methodLocalName,moduleName)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        
        if wave == "" or offset == "":        
            localMessage = "MAP200 [{}]:GET {}".format(self.__mapIpAddress,localCommandGet)
            self.__lc_msg(localMessage)
        else:
            localMessage = "MAP200 [{}]:SET {}".format(self.__mapIpAddress,localCommandSet)
            self.__lc_msg(localMessage)
         
            
        commandToSend="{} {},{},{}".format(localCommandGet ,chassisNumber, slotNumber, deviceNumber)
        responseList = self.__send_cmd(commandToSend)
        time.sleep(1)
        response = responseList[1]
        response = self.__remove_dust(response)
        response = response.split(" ")        
        currentWave=response[0]
        currentOffset=response[1]
        localMessage = "MAP200 [{}]:current seek/hold Thresholds:[{}]".format(self.__mapIpAddress, response)
        self.__lc_msg(localMessage) 
        
        if ( wave != "" ) and ( offset != "" ) :
            wave="{0:.3f}".format(wave)  # need do fix 3 decimal digits for result compare
            offset="{0:.3f}".format(offset)  # need do fix 3 decimal digits for result compare
            #if (float(wave) < 0.01)  or (float(wave) > 5):
            #    localMessage = "MAP200 [{}]:ERROR: wave  [{}] out of allowed range 0.01-5".format(self.__mapIpAddress, wave)
            #    self.__lc_msg(localMessage)
            #    self.__method_failure(methodLocalName, None, "", localMessage)
            #    return False, localMessage
            if (float(offset) < -10)  or (float(offset) > 10):
                localMessage = "MAP200 [{}]:ERROR: offset  [{}] out of allowed range 0-5".format(self.__mapIpAddress, offset)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage
            commandToSend="{} {},{},{},{},{}".format(localCommandSet ,chassisNumber, slotNumber, deviceNumber, wave, offset)
            responseList = self.__send_cmd(commandToSend)
            self.__lc_msg(commandToSend)
            time.sleep(1)
            commandToSend="{} {},{},{}".format(localCommandGet ,chassisNumber, slotNumber, deviceNumber)
            responseList = self.__send_cmd(commandToSend)
            time.sleep(1)
            response = responseList[1]
            response = self.__remove_dust(response)
            response = response.split(" ")        
            currentWave=response[0]
            currentOffset=response[1]

            if ( float(wave) != float(currentWave)) or ( float(offset) != float(currentOffset)): 
                localMessage = "MAP200 [{}]:ERROR [wave][offset]  required [{}][{}]  SET instead to [{}][{}]  ".format(self.__mapIpAddress, wave, offset, currentWave,  currentOffset)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage
            localMessage = "MAP200 [{}]:WAVE POWER  [wave][offset] required [{}][{}]  SET to [{}][{}]  ".format(self.__mapIpAddress, wave, offset, currentWave,  currentOffset)
            self.__lc_msg(localMessage)
        localMessage = "MAP200 [{}]:VOA slot {} (Device {}) [wave][offset]:[{}][{}]".format(self.__mapIpAddress,slotNumber, deviceNumber, currentWave, currentOffset)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, localMessage



    def get_set_voa_wave_power_offset_enable(self, slotNumber, deviceNumber, enable="", chassisNumber=1):
        """ Method:
                get_set_voa_wave_power_offset_enable(self, slotNumber, deviceNumber, enable="", chassisNumber=1)
            Purposes:
                Enables or disables usage of a wavelength power offset value in power calculations. 
                - When enabled (enable=1), a wavelength-specific power offset will be applied to all power queries. 
                - When disabled (enable=0), wavelength-specific power offsets will not be applied to power queries.
                NOTE: Wavelength power offset values can only be entered or deleted when wavelength power offsets are disabled.
            Parameters:
                slotNumber......slot number  where the  VOA module is plugged in MAP200
                deviceNumber....device to control: each VOA has two different devices identified by number 1 or 2,
                                so, in LCS thre are two devices (1, for the left one, 2 for the right one in the VLC layout)
                                in SCS the device number may be 4 or 8, depending on the module 
                                specification
                chassisNumber...set to 1 by default 
                enable...........0=disable power offset 
                                1=enable power offset  
                                No value to read current enable setting
            Usage: 
                
            Further info from user's manual:
                
                to get values currently set in a module, don't specify the value.
                Enables or disables usage of a wavelength power offset value in power calculations. 
                When enabled, a wavelength-specific power offset will be applied to all power queries. 
                When disabled, wavelength-specific power offsets will not be applied to power queries.
                NOTE: Wavelength power offset values can only be entered or deleted when wavelength power offsets are disabled.
                INPUT FORMAT
                :OUTPut:WAVelength:POWer:OFFSet:ENABle <D>,<State>
                INPUT RANGE
                State Boolean 0  Disabled (wavelength power offset NOT

        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        localCommandSet=":OUTP:WAV:POW:OFFS:ENAB"
        localCommandGet="{}?".format(localCommandSet)

        # check parameters
        if slotNumber == "":
            localMessage = "{} error: slotNumber  [{}] not valid (empty value)".format(methodLocalName,slotNumber)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if (deviceNumber != 1) and  (deviceNumber != 2):
            localMessage = "{} error: deviceNumber [{}] not valid (1 or 2 allowed)".format(methodLocalName,deviceNumber)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage

        # check slot content
        try:
            slotContent=self.__chassisSlotContent[slotNumber]
            localMessage = "MAP200 [{}]:Slot [{}] Content:[{}]".format(self.__mapIpAddress,slotNumber, slotContent )
            self.__lc_msg(localMessage)
        except Exception as e:
            self.__lc_msg(str(e))
            localMessage = "MAP200 [{}]:ERROR [{}]".format(self.__mapIpAddress,e)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
          
        # check if moddule supports this command  
        if  " VOA " in slotContent:
            localMessage = "MAP200 [{}]:found VOA".format(self.__mapIpAddress)
            self.__lc_msg(localMessage)
        else:
            moduleName=slotContent.split(" ")
            moduleName=moduleName[1]
            localMessage = "MAP200 [{}]:ERROR: not allowed call {}() for module {}  (not VOA module)".format(self.__mapIpAddress,methodLocalName,moduleName)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        
        if enable == "":        
            localMessage = "MAP200 [{}]:GET {}".format(self.__mapIpAddress,localCommandGet)
            self.__lc_msg(localMessage)
        else:
            localMessage = "MAP200 [{}]:SET {}".format(self.__mapIpAddress,localCommandSet)
            self.__lc_msg(localMessage)
            
        commandToSend="{} {},{},{}".format(localCommandGet ,chassisNumber, slotNumber, deviceNumber)
        responseList = self.__send_cmd(commandToSend)
        time.sleep(1)
        response = responseList[1]
        response = self.__remove_dust(response)
        localMessage = "MAP200 [{}]:current enable [{}]".format(self.__mapIpAddress, response )
        self.__lc_msg(localMessage) 
        
        if enable != "":
            if (enable != 0) and  (enable != 1):
                localMessage = "{} ERROR:enable [{}] not valid (0 or 1 allowed)".format(methodLocalName,deviceNumber)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage
           
            commandToSend="{} {},{},{},{}".format(localCommandSet ,chassisNumber, slotNumber, deviceNumber, enable)
            responseList = self.__send_cmd(commandToSend)
            self.__lc_msg(commandToSend)
            time.sleep(1)
            commandToSend="{} {},{},{}".format(localCommandGet ,chassisNumber, slotNumber, deviceNumber)
            responseList = self.__send_cmd(commandToSend)
            time.sleep(1)
            response = responseList[1]
            response = self.__remove_dust(response)
            try:
                intresponse=int(response)
            except:
                intresponse=response
            if intresponse != enable:
                localMessage = "MAP200 [{}]:ERROR enable required [{}] SET instead to [{}]".format(self.__mapIpAddress, enable , response)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage
            localMessage = "MAP200 [{}]:power offset required [{}] SET to [{}]  ".format(self.__mapIpAddress, enable, response)
            self.__lc_msg(localMessage)
        localMessage = "MAP200 [{}]:VOA slot {} (Device {}) power offset enable:[{}]".format(self.__mapIpAddress,slotNumber, deviceNumber,response)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, localMessage
                


    def get_set_voa_wave_power_offset_delete(self, slotNumber, deviceNumber, waveLength="", chassisNumber=1):
        """ Method:
                get_set_voa_wave_power_offset_delete(self, slotNumber, deviceNumber, waveLength="", chassisNumber=1)
            Purposes:
                Define an output power offset at the specified waveLengthlength. This offset is applied to all subsequent 
                FETCh:POWer:OUTPut? queries when waveLengthlength offset  is enabled (see OUTPut:WAVelength:POWer:OFFSet:ENABle command).  
            BE CARE:
                If wavelength offset mode is enabled (see OUTPut:WAVelength:POWer:OFFSet:ENABle command), offsets cannot be deleted. 
                An error is generated.
            Parameters:
                slotNumber......slot number  where the  VOA module is plugged in MAP200l
                deviceNumber....device to control: each VOA has two different devices identified by number 1 or 2,
                chassisNumber...set to 1 by default 
                waveLength.... use no value to delete all waveLengths
            Usage: 

            Further info from user's manual:
                If no wavelength is provided, the entire table is deleted.
                Important:
                - If wavelength offset mode is enabled (see OUTPut:WAVelength:POWer:OFFSet:ENABle command), 
                offsets cannot be deleted. An error is generated.
                INPUT FORMAT
                :OUTPut:WAVelength:POWer:OFFSet:DELete <D>,[Wavelength]
                INPUT RANGE
                [Wavelength]* Float Wmin to Wmax nm
                If no wavelength is specified, all entries in the table are set to 0 dBm.

        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        localCommandSet=":OUTP:WAV:POW:OFFS:DEL"
        localCommandGet="{}?".format(localCommandSet)

        # check parameters
        if slotNumber == "":
            localMessage = "{} error: slotNumber  [{}] not valid (empty value)".format(methodLocalName,slotNumber)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if (deviceNumber != 1) and  (deviceNumber != 2):
            localMessage = "{} error: deviceNumber [{}] not valid (1 or 2 allowed)".format(methodLocalName,deviceNumber)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage

        # check slot content
        try:
            slotContent=self.__chassisSlotContent[slotNumber]
            localMessage = "MAP200 [{}]:Slot [{}] Content:[{}]".format(self.__mapIpAddress,slotNumber, slotContent )
            self.__lc_msg(localMessage)
        except Exception as e:
            self.__lc_msg(str(e))
            localMessage = "MAP200 [{}]:ERROR [{}]".format(self.__mapIpAddress,e)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
          
        # check if moddule supports this command  
        if  " VOA " in slotContent:
            localMessage = "MAP200 [{}]:found VOA".format(self.__mapIpAddress)
            self.__lc_msg(localMessage)
        else:
            moduleName=slotContent.split(" ")
            moduleName=moduleName[1]
            localMessage = "MAP200 [{}]:ERROR: not allowed call {}() for module {}  (not VOA module)".format(self.__mapIpAddress,methodLocalName,moduleName)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        
        localMessage = "MAP200 [{}]:SET {}".format(self.__mapIpAddress,localCommandSet)
        self.__lc_msg(localMessage)
        if waveLength != "":
            waveLength="{0:.3f}".format(waveLength)  # need do fix 3 decimal digits for result compare
            commandToSend="{} {},{},{},{}".format(localCommandSet ,chassisNumber, slotNumber, deviceNumber, waveLength)
        else:
            commandToSend="{} {},{},{} ".format(localCommandSet ,chassisNumber, slotNumber, deviceNumber)
        responseList = self.__send_cmd(commandToSend)
        #print("responseList[{}]".format(responseList))
        self.__lc_msg(commandToSend)
        response = responseList[1]
        #print("response[{}]".format(response))
        response = self.__remove_dust(response)
        #print("response[{}]".format(response))
        
        localMessage = "MAP200 [{}]:VOA slot {} (Device {}) WAVE OFFSET DELETE waveLength[{}] ".format(self.__mapIpAddress,slotNumber, deviceNumber, waveLength)
        self.__lc_msg(localMessage)
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
    
    #=========================================
    #
    # * * *   EXAMPLES  * * *
    #
    #=========================================
    #
    # The following calls are used in TestMAP200.py
    # and hare reported here as a reference for 
    # the developers.
    #
    # L.C, March 23th, 2016  Vimercate
    #
       
    #=========================================
    # VOA Slot 1 Get/Set examples
    #=========================================
    # ATTENUATION
    # Slot 1, Devices 1 & 2 get attenuation
    #map200_1.get_set_voa_attenuation(1,1)
    #map200_1.get_set_voa_attenuation(1,2)
    # Slot 1, Devices 1 & 2 set attenuation to 1, 1.22, 32.404, 61.5 dB
    #map200_1.get_set_voa_attenuation(1,1,1)
    #map200_1.get_set_voa_attenuation(1,2,1.22)
    #map200_1.get_set_voa_attenuation(1,2,32.404)
    #map200_1.get_set_voa_attenuation(1,2,61.5)
    
    # ATTENUATION OFFSET
    # Slot 1, Devices 1 & 2 get attenuation OFFSET
    #map200_1.get_set_voa_attenuation_offset(1,1)
    #map200_1.get_set_voa_attenuation_offset(1,2)
    # Slot 1, Devices 1 & 2 set attenuation OFFSET to 1, 2.2, 3.33, 4.444 
    #map200_1.get_set_voa_attenuation_offset(1,1,1)
    #map200_1.get_set_voa_attenuation_offset(1,2,2.2)
    #map200_1.get_set_voa_attenuation_offset(1,2,3.33)
    #map200_1.get_set_voa_attenuation_offset(1,2,4.444)
       
    
    # BEAM BLOCK - To activate laser the beam block must be removed (set to 0)
    # Slot 1, Devices 1 & 2 get BEAM BLOCK state
    #map200_1.get_set_voa_beam_block(1,1)
    #map200_1.get_set_voa_beam_block(1,2)
    # Slot 1, Devices 1 & 2 set attenuation BEAM BLOCK  1=enable block (Laser OFF) 0=disable block (Laser ON)
    #map200_1.get_set_voa_beam_block(1,1,0)
    #map200_1.get_set_voa_beam_block(1,1,1)
    #map200_1.get_set_voa_beam_block(1,2,0)
    #map200_1.get_set_voa_beam_block(1,2,1)
    
  
    # OFFSET
    # Slot 1, Devices 1 & 2 get OFFSET
    #map200_1.get_set_voa_offset(1,1)
    #map200_1.get_set_voa_offset(1,2)
    # Slot 1, Devices 1 & 2 set OFFSET to 2, 2.1, 4.444, -7.4 
    #map200_1.get_set_voa_offset(1,1,2)
    #map200_1.get_set_voa_offset(1,2,2.5)
    #map200_1.get_set_voa_offset(1,2,4.55)
    #map200_1.get_set_voa_offset(1,2,-7.555)
    
    
    # GET POWER (theoretical output power of the specified device)
    # Slot 1, Devices 1 & 2 get POWER 
    #map200_1.get_voa_power(1,1)
    #map200_1.get_voa_power(1,2)
    
    
    # POWER CONTROL
    # Slot 1, Devices 1 & 2 get power control state
    #map200_1.get_set_voa_power_control(1,1)
    #map200_1.get_set_voa_power_control(1,2)
    # Slot 1, Devices 1 & 2 set power control: enable or disable power tracking mode whereby, if enabled, the attenuation will be adjusted until the output power level matches the target value
    #map200_1.get_set_voa_power_control(1,1,0)
    #map200_1.get_set_voa_power_control(1,1,1)
    #map200_1.get_set_voa_power_control(1,2,0)
    #map200_1.get_set_voa_power_control(1,2,1)
 
 
    # POWER OFFSET
    # Slot 1, Devices 1 & 2 get OFFSET
    #map200_1.get_set_voa_power_offset(1,1)
    #map200_1.get_set_voa_power_offset(1,2)
    # Slot 1, Devices 1 & 2 set OFFSET 
    #map200_1.get_set_voa_power_offset(1,1,-22)
    #map200_1.get_set_voa_power_offset(1,1,12)
    #map200_1.get_set_voa_power_offset(1,2,-2.31)
    #map200_1.get_set_voa_power_offset(1,2,-4.25)
    #map200_1.get_set_voa_power_offset(1,2,7.533)
    
    # POWER TARGET
    # Slot 1, Devices 1 & 2 get TARGET
    #map200_1.get_set_voa_power_target(1,1)
    #map200_1.get_set_voa_power_target(1,2)
    # Slot 1, Devices 1 & 2 set TARGET  
    #map200_1.get_set_voa_power_target(1,1,21)
    #map200_1.get_set_voa_power_target(1,1,2)
    #map200_1.get_set_voa_power_target(1,2,-23)
    #map200_1.get_set_voa_power_target(1,2,5)
    #map200_1.get_set_voa_power_target(1,2,4)
    
    
    # POWER THRESHOLD  *** PROBLEMA ***
    # Slot 1, Devices 1 & 2 get TARGET
    #map200_1.get_set_voa_power_threshold(1,1)
    #map200_1.get_set_voa_power_threshold(1,2)
    # Slot 1, Devices 1 & 2 set OFFSET 
    #map200_1.get_set_voa_power_threshold(1,1,3,4)   
    #map200_1.get_set_voa_power_threshold(1,2,2,1)
    #map200_1.get_set_voa_power_threshold(1,1,0.1,1)
    #map200_1.get_set_voa_power_threshold(1,2,0.1,2)
      
    
    # WAVELENGTH 
    # Slot 1, Devices 1 & 2 get TARGET
    #map200_1.get_set_voa_wave_length(1,1)
    #map200_1.get_set_voa_wave_length(1,2)
    # Slot 1, Devices 1 & 2 set WAVELENGTH 
    #map200_1.get_set_voa_wave_length(1,1,1310)
    #map200_1.get_set_voa_wave_length(1,1,1312)
    #map200_1.get_set_voa_wave_length(1,1,1308.01)
    #map200_1.get_set_voa_wave_length(1,1,1308.002)
    
 
    # WAVE POWER OFFSET   
    # Slot 1, Devices 1 & 2 get TARGET
    #map200_1.get_set_voa_wave_power_offset(1,1)
    #map200_1.get_set_voa_wave_power_offset(1,2)
    # Slot 1, Devices 1 & 2 set OFFSET 
    #map200_1.get_set_voa_wave_power_offset(1,1,1300,1)
    #map200_1.get_set_voa_wave_power_offset(1,2,1350.002,-10)
    #map200_1.get_set_voa_wave_power_offset(1,2,1350.1,3)

    # WAVE POWER OFFSET ENABLE  
    # Slot 1, Devices 1 & 2 get power control state
    #map200_1.get_set_voa_wave_power_offset_enable(1,1)
    #map200_1.get_set_voa_wave_power_offset_enable(1,2)
    # Slot 1, Devices 1 & 2 set power control: enable or disable power offset
    #map200_1.get_set_voa_wave_power_offset_enable(1,1,0)
    #map200_1.get_set_voa_wave_power_offset_enable(1,1,1)
    #map200_1.get_set_voa_wave_power_offset_enable(1,1,0)
    #map200_1.get_set_voa_wave_power_offset_enable(1,2,1)
    #map200_1.get_set_voa_wave_power_offset_enable(1,2,1)
    #map200_1.get_set_voa_wave_power_offset_enable(1,2,0)
 
    # WAVE POWER OFFSET DELETE  
    #map200_1.get_set_voa_wave_power_offset_delete(1,1,1350.002)
    #map200_1.get_set_voa_wave_power_offset_delete(1,2,1350.002)
    #map200_1.get_set_voa_wave_power_offset_delete(1,1)
    #map200_1.get_set_voa_wave_power_offset_delete(1,2)
 
 
    
    #=========================================
    # LCS Slot 2 Get/Set examples
    #=========================================
    # Get Device 1/2
    #map200_1.get_set_switch_state(2,1,1)
    # Get Device 2/2
    #map200_1.get_set_switch_state(2,2,1)
    # SET  Device 1/2 to positions 0-4
    #map200_1.get_set_switch_state(2,1,1,0)
    #map200_1.get_set_switch_state(2,1,1,1)
    #map200_1.get_set_switch_state(2,1,1,2)
    #map200_1.get_set_switch_state(2,1,1,3)
    #map200_1.get_set_switch_state(2,1,1,4)
    # SET  Device 2/2 to positions 0-4
    #map200_1.get_set_switch_state(2,2,1,0)
    #map200_1.get_set_switch_state(2,2,1,1)
    #map200_1.get_set_switch_state(2,2,1,2)
    #map200_1.get_set_switch_state(2,2,1,3)
    #map200_1.get_set_switch_state(2,2,1,4)

    #=========================================
    # SCS/4 Slot 5 Get/Set examples
    #=========================================
    # Get Device 1/4
    #map200_1.get_set_switch_state(5,1,1)
    # Get Device 2/4
    #map200_1.get_set_switch_state(5,2,1)
    # Get Device 3/4
    #map200_1.get_set_switch_state(5,3,1)
    # Get Device 4/4
    #map200_1.get_set_switch_state(5,4,1)

    # SET Device 1/4 To positions 1/2
    #map200_1.get_set_switch_state(5,1,1,1)
    #map200_1.get_set_switch_state(5,1,1,2)
    # SET Device 2/4 To positions 1/2
    #map200_1.get_set_switch_state(5,2,1,1)
    #map200_1.get_set_switch_state(5,2,1,2)
    # SET Device 3/4 To positions 1/2
    #map200_1.get_set_switch_state(5,3,1,1)
    #map200_1.get_set_switch_state(5,3,1,2)
    # SET Device 4/4 To positions 1/2
    #map200_1.get_set_switch_state(5,4,1,1)
    #map200_1.get_set_switch_state(5,4,1,2)


    #=========================================
    # SCS/8  Slot 8 Get/Set examples
    #=========================================
    # Get Device 1/8
    #map200_1.get_set_switch_state(8,1,1)
    # Get Device 2/8
    #map200_1.get_set_switch_state(8,2,1)
    # Get Device 3/8
    #map200_1.get_set_switch_state(8,3,1)
    # Get Device 4/8
    #map200_1.get_set_switch_state(8,4,1)
    # Get Device 5/8
    #map200_1.get_set_switch_state(8,5,1)
    # Get Device 6/8
    #map200_1.get_set_switch_state(8,6,1)
    # Get Device 7/8
    #map200_1.get_set_switch_state(8,7,1)
    # Get Device 8/8
    #map200_1.get_set_switch_state(8,8,1)


    # SET Device 1/8 To positions 1/2
    #map200_1.get_set_switch_state(8,1,1,1)
    #map200_1.get_set_switch_state(8,1,1,2)
    # SET Device 2/8 To positions 1/2
    #map200_1.get_set_switch_state(8,2,1,1)
    #map200_1.get_set_switch_state(8,2,1,2)
    # SET Device 3/8 To positions 1/2
    #map200_1.get_set_switch_state(8,3,1,1)
    #map200_1.get_set_switch_state(8,3,1,2)
    # SET Device 4/8 To positions 1/2
    #map200_1.get_set_switch_state(8,4,1,1)
    #map200_1.get_set_switch_state(8,4,1,2)
    # SET Device 1/8 To positions 1/2
    #map200_1.get_set_switch_state(8,5,1,1)
    #map200_1.get_set_switch_state(8,5,1,2)
    # SET Device 2/8 To positions 1/2
    #map200_1.get_set_switch_state(8,6,1,1)
    #map200_1.get_set_switch_state(8,6,1,2)
    # SET Device 3/8 To positions 1/2
    #map200_1.get_set_switch_state(8,7,1,1)
    #map200_1.get_set_switch_state(8,7,1,2)
    # SET Device 4/8 To positions 1/2
    #map200_1.get_set_switch_state(8,8,1,1)
    #map200_1.get_set_switch_state(8,8,1,2)

















    print("\n\n\n\n\nTESTING SECTION *************************************")
    input("press enter to continue...")
    

    #tester_map.deinit_instrument( portId_5xx)

 

    print(" ")
    print("========================================")
    print("map200Driver  debug -- END -- ")
    print("========================================")
    print(" ")

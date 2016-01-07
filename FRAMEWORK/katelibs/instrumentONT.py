#!/usr/bin/env python
"""
###############################################################################
#
# MODULE:  InstrumentONT.py
#
# AUTHOR:  L.Cutilli
#
# DATE  :  16/10/2015
#
#
# DETAILS: Python management module of the following test equipments:
#          - 5xx... Ont-50, Ont-506, Ont-512
#          - 6xx... Ont-601
#
# MODULE: InstrumentONT.py  created to drive the connections and common low-level operations
#                           involving JDSU Optical Network Tester ONT-50/506/512/601
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


class InstrumentONT(Equipment):

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
        self.__sessionName          = "Session5xx_KATE"    #  To be changed: meaningfuls only for  5xx 
        # Initizalization flag:
        # Inside init_instrument() call: True if previous step ok, 
        # after: each method called inside "test_body" section must found this flag to True to be executed
        self.__lastCallSuccess      = False            #  track if the last call was successfully executed (not to set in case of skip)
        self.__calledMethodList     = []               #  used to track all method called
        self.__calledMethodStatus   = dict()           #  used to track all method called and last execution result
        # Connection
        self.__ontUser              = None             #  Ont session authentication user
        self.__ontPassword          = None             #  Ont session user's password
        self.__ontIpAddress         = None             #  OntXXX IP address
        self.__ontTelnetPort        = 5001             #  OntXXX telnet port (default 5001)
        self.__telnetConnection     = None             #  Handler of the established telnet connection
        self.__pingRetryNumber      = 1                #  Retry number for -c ping option
        self.__telnetExpectedPrompt = [b'> ']          #  it must be specified as keys LIST...
        self.__telnetTimeout        = 2
        # Ont command execution
        self.__ontSleepTimeForRetry = 0.5              # one retry every 0.5 second
        self.__ontCmdMaxRetry       = 120              # max 120 retries
        # Application Port Socket
        self.__portToSocketMap      = dict()           # OntXXX port telnet socket
        self.__portConnection       = dict()           # OntXXX port telnet socket ID (used to send messages to port)
        self.__labelToPortId        = dict()           # used to get back /x/y/z port from user portId)
        self.StmToOc={"STM0":"OC1", "STM1":"OC3","STM4":"OC12","STM16":"OC48","STM64":"OC192"}
        self.OcToStm={"OC1":"STM0", "OC3":"STM1","OC12":"STM4","OC48":"STM16","OC192":"STM64"}
        self.VcToAu={"VC11":"AU4_C11", "VC12":"AU4_C12", "VC2":"NOTSUPPORTED", "VC3":"AU3_C3", "VC4":"AU4_C4", "VC4_4C":"AU4_4C", "VC4_16C":"AU4_16C", "VC4_64C":"AU4_64C"}
        self.E_TAG = "-10"

        super().__init__(label, self.__prs.get_id(label))
        self.__get_instrument_info_from_db(self.__prs.get_id(label)) # inizializza i dati di IP, tipo di ONT..

        self.__ontUser        = self.__prs.get_elem(self.get_label(), 'USER')
        self.__ontPassword    = self.__prs.get_elem(self.get_label(), 'PWD')
        self.__ontApplication = self.__prs.get_elem(self.get_label(), 'APPL')
        # Unique 5xx sessionName generation bound to start date&time (UTC)  Comment next row if a single static name needed
        #self.__sessionName          = "Session__" + datetime.datetime.utcnow().strftime("%d%b_%H%M%S") + "__UTC"



    def clean_up(self):
        """ INTERNAL USAGE
        """
        print("clean_up called [{}]".format(self.__ontType))


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


    def __get_instrument_info_from_db(self, ID):
        tabEqpt  = TEquipment
        # get Equipment Type ID for selected ID (i.e. 50 (for ONT506))
        #instr_type_id = tabEqpt.objects.get(id_equipment=ID).t_equip_type_id_type.id_type
        # get Equipment Type Name for selected ID (i.e. ONT506)
        instr_type_name = tabEqpt.objects.get(id_equipment=ID).t_equip_type_id_type.name
        instr_ip = self.__get_net_info(ID)

        self.__ontIpAddress = instr_ip
        if   instr_type_name == "ONT50":
            self.__ontType = "5xx"
        elif instr_type_name == "ONT506":
            self.__ontType = "5xx"
        elif instr_type_name == "ONT512":
            self.__ontType = "5xx"
        elif instr_type_name == "ONT601":
            self.__ontType = "6xx"
        else:
            localMessage = "__get_instrument_info_from_db error: Unknown instrument type for the specified ID. ID [{}] Instrument[{}] IpAddr[{}]".format(ID,instr_type_name,instr_ip)
            print(localMessage) 
            self.__lc_msg(localMessage)
            return  

        localMessage = "__get_instrument_info_from_db: instrument type specified :ID [{}] Instrument:[{}] IpAddr[{}]".format(ID,instr_type_name,instr_ip)
        print(localMessage) 
        self.__lc_msg(localMessage)
        return  
 


    #def init_instrument(self, localUser, localPwd, localOntIpAddress, portId):
    def init_instrument(self, portId):
        """
            INITALIZES THE ONT INSTRUMENT TO GET READY TO ACCEPT USER (Library) COMMANDS
            after this inizialization the user can start to send commands to 
            the ONT (5xx/6xx) instrument
            portId user's naming convention: P1, P2,...
        """
        # portId = self.__recover_port_to_use(portId)

        localPortId = self.__prs.get_elem(self.get_label(), portId)
        self.__labelToPortId[portId]=localPortId
        localMethodName = inspect.stack()[0][3]   # init_instrument
        
        if self.__ontType  == "6xx":   # ONT-6xx Init
            localUser = self.__ontUser  
            localPwd = self.__ontPassword 
            localOntIpAddress = self.__ontIpAddress
            myApplication="New-Application"

            # 6xx init
            #tester = InstrumentONT(localUser,localPwd,localOntIpAddress, krepo=r)
            callResult = self.connect()
            if self.__check_method_execution("connect") == False: 
                localMessage="Error in method [{}] call \n".format(localMethodName)
                self.__lc_msg(localMessage)
                return False, "Error in method "+ localMethodName +" call "
            self.__lc_msg("Step 1 ++++++++++++++++++++++++++")

            callResult = self.open_port_channel(portId)
            if self.__check_method_execution("open_port_channel") == False: 
                localMessage="Error in method [{}] call \n".format(localMethodName)
                self.__lc_msg(localMessage)
                return False, "Error in method "+ localMethodName +" call "
            self.__lc_msg("Step 2 ++++++++++++++++++++++++++")



            # Check declared and found instrument type
            declaredOntType = self.__ontType
            callResult = self.get_instrument_id()
            if self.__check_method_execution("get_instrument_id") == False: 
                localMessage="Error in method [{}] call \n".format(localMethodName)
                self.__lc_msg(localMessage)
                return False, "Error in method "+ localMethodName +" call "
            self.__lc_msg("Step 3 ++++++++++++++++++++++++++")
            if declaredOntType == self.__ontType: 
                localMessage="Instrument declared [{}] and found [{}] consistency verified".format(declaredOntType, self.__ontType)
                self.__lc_msg(localMessage)
            else:
                localMessage="Instrument declared [{}] but not found [{}] please verify DB data for id [{}]".format(declaredOntType, self.__ontType)
                self.__lc_msg(localMessage)
                return False, localMessage

            # Unload Application to clean wrong situations...
            callResult = self.unload_app(portId, myApplication)
            time.sleep(10)
            #callResult = self.get_currently_loaded_app(portId)
            callResult = self.load_app(portId, myApplication)
            if self.__check_method_execution("load_app") == False: 
                localMessage="Error in method [{}] call \n".format(localMethodName) 
                self.__lc_msg(localMessage)
                return False, "Error in method "+ localMethodName +" call "
            time.sleep(20)
            self.__lc_msg("Step 4 ++++++++++++++++++++++++++")
            callResult = self.set_current_signal_structure(portId,"PHYS_SDH")  
            if self.__check_method_execution("set_current_signal_structure") == False: 
                localMessage="Error in method [{}] call \n".format(localMethodName) 
                self.__lc_msg(localMessage)
                return False, "Error in method "+ localMethodName +" call "

            self.__lc_msg("Step 5 ++++++++++++++++++++++++++")
        else:                         # ONT-5xx Init
            # 5xx init
            myApplication="SdhBert"
            #tester = InstrumentONT(localUser,localPwd, krepo=r)
            
            callResult = self.connect()
            if self.__check_method_execution("connect") == False: 
                localMessage="Error in method [{}] call \n".format(localMethodName)
                self.__lc_msg(localMessage)
                return False, "Error in method "+ localMethodName +" call "

            self.__lc_msg("Step 1 ++++++++++++++++++++++++++")
           
            callResult = self.create_session(self.__sessionName)
            if self.__check_method_execution("create_session") == False: 
                localMessage="Error in method [{}] call \n".format(localMethodName)
                self.__lc_msg(localMessage)
                return False, "Error in method "+ localMethodName +" call "

            self.__lc_msg("Step 2 ++++++++++++++++++++++++++")

            callResult = self.select_port(portId)
            if self.__check_method_execution("select_port") == False: 
                callResult = self.deselect_port(portId)    # uncomment to deselect the specified port
                localMessage="Error in method [{}] call \n".format(localMethodName)
                self.__lc_msg(localMessage)
                return False, "Error in method "+ localMethodName +" call "

            self.__lc_msg("Step 3 ++++++++++++++++++++++++++")
            
            callResult = self.get_selected_ports("")
            if self.__check_method_execution("get_selected_ports") == False: 
                localMessage="Error in method [{}] call \n".format(localMethodName)
                self.__lc_msg(localMessage)
                return False, "Error in method "+ localMethodName +" call "
                
            self.__lc_msg("Step 4 ++++++++++++++++++++++++++")

            # Check declared and found instrument type
            declaredOntType = self.__ontType
            
            callResult = self.get_instrument_id()
            if self.__check_method_execution("get_instrument_id") == False: 
                localMessage="Error in method [{}] call \n".format(localMethodName)
                self.__lc_msg(localMessage)
                return False, "Error in method "+ localMethodName +" call "
            
            self.__lc_msg("Step 5 ++++++++++++++++++++++++++")
            
            if declaredOntType == self.__ontType: 
                localMessage="Instrument declared [{}] and found [{}] consistency verified".format(declaredOntType, self.__ontType)
                self.__lc_msg(localMessage)
            else:
                localMessage="Instrument declared [{}] but found [{}] please verify DB data for id [{}]".format(declaredOntType, self.__ontType)
                self.__lc_msg(localMessage)
                return False, localMessage
            
            self.__lc_msg("Step 6 ++++++++++++++++++++++++++")
            
            callResult = self.init_port_to_socket_map()
            if self.__check_method_execution("init_port_to_socket_map") == False: 
                localMessage="Error in method [{}] call \n".format(localMethodName)
                self.__lc_msg(localMessage)
                return False, "Error in method "+ localMethodName +" call "
            
            self.__lc_msg("Step 7 ++++++++++++++++++++++++++")
            
            callResult = self.open_port_channel(portId)
            if self.__check_method_execution("open_port_channel") == False: 
                localMessage="Error in method [{}] call \n".format(localMethodName)
                self.__lc_msg(localMessage)
                return False, "Error in method "+ localMethodName +" call "
            
            self.__lc_msg("Step 8 ++++++++++++++++++++++++++")
            
            callResult = self.get_currently_loaded_app(portId)
            #if self.__check_method_execution("get_currently_loaded_app") == False: 
            #    print("Error in method [{}] call \n".format(localMethodName))
            #    return False, "Error in method "+ localMethodName +" call "
            
            self.__lc_msg("Step 9 ++++++++++++++++++++++++++")
            
            callResult = self.unload_app(portId, myApplication)
            time.sleep(10)
            
            self.__lc_msg("Step 10 ++++++++++++++++++++++++++")
            
            callResult = self.load_app(portId, myApplication)
            if self.__check_method_execution("load_app") == False: 
                localMessage="Error in method [{}] call \n".format(localMethodName) 
                self.__lc_msg(localMessage)
                return False, "Error in method "+ localMethodName +" call "
            
            
        localMessage=" ####  #### Current callMethodStatus content:  [ {} ] ####".format(self.__calledMethodStatus)
        self.__lc_msg(localMessage)
            
        localMessage="[{}]: init_instrument: instrument correctly initialized".format(self.__ontType)
        self.__lc_msg(localMessage)
        return True, localMessage






    def __recover_port_to_use(self, portId):
        """ Smart port translator (5xx/6xx):
            if portId=/rack/slot/portNo  --> return      /rack/slot/portNo  
            if portId=Px                 --> return its  /rack/slot/portNo format """
        #if self.__ontType  != "6xx":   # ONT-5xx, or ontType not yet initialize: do nothing
        #    return portId

        try: # port specified as P1,P2, ...
            originalPortId = self.__labelToPortId[portId]
        except Exception:
            originalPortId = portId
        localMessage = "Port fixed: [{}]-->[{}]".format(portId, originalPortId )
        self.__lc_msg(localMessage)
        return originalPortId  






 

    def deinit_instrument(self, portId):
        """
            DEINITALIZES THE ONT INSTRUMENT TO FREE IT 
            after this deinizialization another user can use this Instrument
            the ONT (5xx/6xx) instrument
            portId user's naming convention: P1, P2,...
        """
        #portId = self.__recover_port_to_use(portId)
        if self.__ontType  == "6xx":   
            # Unload Application to clean wrong situations...
            myApplication="New-Application"
            callResult = self.unload_app(portId, myApplication)
            time.sleep(5)
        else:                         # ONT-5xx Init
            # 5xx init
            myApplication="SdhBert"
            callResult = self.unload_app(portId, myApplication)
            time.sleep(5)
            callResult = self.deselect_port(portId)    # uncomment to deselect the specified port
            callResult = self.delete_session(self.__sessionName)

        localMessage="[{}]: deinit_instrument: instrument correctly initialized".format(self.__ontType)
        self.__lc_msg(localMessage)
        return True, localMessage




    #
    #  INTERNAL UTILITIES
    #
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
        cmd = "ping -c {} {:s}".format(self.__pingRetryNumber,self.__ontIpAddress)
        if os.system(cmd) == 0:
            localMessage = "IP Address [{}]: answer received".format(self.__ontIpAddress)
            self.__lc_msg(localMessage)
            return True, localMessage
        localMessage = "IP Address [{}]: no answer received".format(self.__ontIpAddress)
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
            localMessage = "Ont command OK"
            self.__lc_msg(localMessage)
            return True, str(result[2], 'utf-8')
        else:
            localMessage = "Ont command ERROR"
            self.__lc_msg(localMessage)
            return False, localMessage



    def __create_telnet_connection(self):
        self.__lc_msg("Function: __create_telnet_connection Socket [{}:{}]".format(self.__ontIpAddress,self.__ontTelnetPort))
        try:
            self.__telnetConnection = telnetlib.Telnet(self.__ontIpAddress,self.__ontTelnetPort,self.__telnetTimeout)
            response = self.__send_cmd("*PROMPT ON")
            localMessage = "Telnet connection established"
            self.__lc_msg(localMessage)
        except Exception as e:
            self.__lc_msg(str(e))
            localMessage = "Telnet connection ERROR"
            self.__lc_msg(localMessage)
            return False, localMessage
        return True, localMessage



    def __authenticate_user(self):
        """ Recognizes user as valid user and try to authenticate him """
        validUser  = None
        # Identify ONT 5xx/6xx type (different authentication cmd needed...)
        self.init_ont_type()
        if self.__ontType  == "6xx":   # ONT-6xx Authentication
            #6xx-equivalent init_port_to_socket_map now
            callResult = self.get_available_ports()
            rowsArray = callResult[1].replace("\n","").replace("> ","").split(",")
            for row in rowsArray:
                #print("Processing port [{}]".format(row))
                keyValuePair=row.split(":")
                self.__portToSocketMap[keyValuePair[0]]=keyValuePair[1]
            #print(self.__portToSocketMap)
            localMessage="[{}]: authentication SKIPPED: do it directly in the port cli".format(self.__ontType)
            self.__lc_msg(localMessage)
            return True, localMessage
        else:                         # ONT-5xx Authentication
            # check if user is in the Ont user list
            localCommand=":ACCM:LIST?"
            callResult = self.__send_cmd(localCommand)
            # generate userList "array"
            userList   = callResult[1].replace("\n","").replace("> ","").split(",")
            for tempUser in userList:
                if self.__ontUser == tempUser:
                    validUser = tempUser
                    localMessage="User: [{}] == [{}] recognized".format(tempUser, self.__ontUser)
                    self.__lc_msg(localMessage)
                    break
            if not validUser:
                localMessage="User: [{}] not recognized".format(self.__ontUser)
                self.__lc_msg(localMessage)
                return False, localMessage
            # login user
            localCommand=":ACCM:USER {} {}".format(self.__ontUser, self.__ontPassword)
            callResult = self.__send_cmd(localCommand)
            callResult=callResult[1].replace("\n","").replace("> ","")
            # current user verify
            localCommand=":ACCM:USER?".format(self.__ontUser, self.__ontPassword)
            callResult = self.__send_cmd(localCommand)
            filteredResult = callResult[1].replace("\n","").replace("> ","")
            if filteredResult == self.__ontUser:
                localMessage="User: [{}] login confirmed".format(self.__ontUser)
                self.__lc_msg(localMessage)
                return True, localMessage
            else:
                localMessage="User: [{}] differs by expected [{}]".format(filteredResult,self.__ontUser)
                self.__lc_msg(localMessage)
            return False, localMessage



    def __authenticate_user_on_6xx_port(self, portId):  # On ONT6xx the authentication is at port level
        """ Recognizes user as valid user and try to authenticate him """
        #portId = self.__recover_port_to_use(portId)
        self.init_ont_type()
        if self.__ontType  == "6xx":   # ONT-6xx Authentication
            # login user
            localCommand=":PRT:REG \"{}\",\"{}\" ".format(self.__ontUser, self.__ontPassword)

            callResult = self.__send_port_cmd(portId, localCommand)
            callResult=callResult[1].replace("\n","").replace("> ","")
            self.__lc_msg(callResult)

            """# current user verify
            localCommand=":PRT:REG?".format(self.__ontUser, self.__ontPassword)
            callResult = self.__send_cmd(localCommand)
            filteredResult = callResult[1].replace("\n","").replace("> ","")
            if filteredResult == self.__ontUser:
                localMessage="User: [{}] login confirmed".format(self.__ontUser)
                self.__lc_msg(localMessage)
            else:
                localMessage="User: [{}] differs by expected [{}]".format(filteredResult,self.__ontUser)
                self.__lc_msg(localMessage)
                return False, localMessage  """
            return True, callResult
        else:                         # ONT-5xx Authentication
            localMessage="Port authentication needed ONLY in 6xx test equipments [{}]".format(self.__ontType)
            self.__lc_msg(localMessage)
            return False, localMessage



    def __string_to_TR16(self,stringToConvert):
        spacesString="                  "
        tempStr=stringToConvert+spacesString
        tempStr1=tempStr[0:15]
        asciiCsvTempResult=[ord(c) for c in tempStr1]
        asciiCsvResult=""
        flag=0
        for element in  asciiCsvTempResult:
            if flag == 0:
                asciiCsvResult+=str(element)
                flag=1
            else:
                asciiCsvResult+=","+str(element)
        localMessage="Ascii CSV string:[{}]".format(asciiCsvResult)
        self.__lc_msg(localMessage)
        return asciiCsvResult



    def __TR16_to_string(self,tr16ToConvert):
        stringResult=""
        for element in tr16ToConvert.split(","):
            stringResult+="" + chr(int(element))
        return stringResult



    #
    #   ACCOUNT MANAGEMENT
    #
    def connect(self):    ### krepo added ###
        """ create a connection and authenticate the user """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        # Ping check
        localResult = self.__is_reachable()
        if not localResult[0]:
            localMessage="ONTXXX [{}]:not reachable. Bye...".format(self.__ontIpAddress)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return  localResult
        else:
            localMessage="ONTXXX [{}]:reachable".format(self.__ontIpAddress)
            self.__lc_msg(localMessage)

        # Ont Socket connection
        localResult = self.__create_telnet_connection()
        if not localResult[0]:
            localMessage="ONTXXX [{}]:telnet session open (port {}) failed. Bye...".format(self.__ontIpAddress, self.__ontTelnetPort)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return  localResult
        else:
            localMessage="ONTXXX [{}]:telnet session opened (port {})".format(self.__ontIpAddress, self.__ontTelnetPort)
            self.__lc_msg(localMessage)

        # User authentication
        localResult = self.__authenticate_user()
        if not localResult[0]:
            localMessage="ONTXXX [{}]:user {} authentication failed. Bye...".format(self.__ontIpAddress, self.__ontUser)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return  localResult
        else:
            localMessage="ONTXXX [{}]:user {} authenticated".format(self.__ontIpAddress, self.__ontUser)
            self.__lc_msg(localMessage)

        self.__method_success(methodLocalName, None, localMessage)
        return localResult



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



    def delete_session(self, sessionName):  ### krepo added ###
        """ delete a <sessionName> session if present """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        # check if session is present
        localCommand=":SESM:SES?"
        callResult = self.__send_cmd(localCommand)
        verifyResult = self.__verify_presence_in_csv_format_answer(callResult, sessionName)
        if not verifyResult[0]: # False
            localMessage="Session [{}] not found: unable to delete it".format(sessionName)
            self.__lc_msg(localMessage)
            # self.__sessionName = None    # workaround for multiple port management with the same ** default ** session
            self.__sessionName = sessionName  # workaround for multiple port management with the same ** default ** session
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        localMessage="Session [{}] found: delete".format(sessionName)
        self.__lc_msg(localMessage)

        # remove session
        localCommand=":SESM:DEL"
        callResult = self.__send_cmd(localCommand)

        # check if the current session has been removed as expected
        localCommand=":SESM:SES?"
        callResult = self.__send_cmd(localCommand)
        verifyResult = self.__verify_presence_in_csv_format_answer(callResult, sessionName)
        if verifyResult[0]: # True
            localMessage="Session [{}] not removed: unable to delete it".format(sessionName)
            self.__lc_msg(localMessage)
            # self.__sessionName = None    # workaround for multiple port management with the same ** default ** session
            self.__sessionName = sessionName  # workaround for multiple port management with the same ** default ** session
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        localMessage="Session [{}] deleted".format(sessionName)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, localMessage



    #
    #   PORT MANAGEMENT
    #
    def get_available_ports(self):   ### krepo not added ###
        """ Gets the ports available for the use.
            Return tuple:
            True, < available ports : the CSV list of not
                    reserved or locked ports with the syntax:
                    /rack/slotNo/portNo, /rack/slot/portNo,...
            False, <empty list> if there is no suitable port """
        methodLocalName = self.__lc_current_method_name()
        localCommand=":PRTM:LIST?"
        rawCallResult = self.__send_cmd(localCommand)
        callResult = self.__remove_dust(rawCallResult[1])
        localMessage="PORTLIST:[{}]".format(callResult)
        self.__lc_msg(localMessage)
        if callResult == "":
            return False, ""
        return True, callResult



    def init_port_to_socket_map(self):   ### krepo not added ###
        """ It Initializes the self.__portToSocketMap dictionary
            to ease the fast socket recovery for each available port
            Return tuple:
            ('True', '< self.__portToSocketMap content >') ... if at least one available port found
            ('False','<empty list>')...no available port found """
        methodLocalName = self.__lc_current_method_name()
        if self.__ontType  == "5xx":
            pass
        else:
            localMessage="Command supported by ONT-5xx only (current test equipment type:[{}]) ".format(self.__ontType)
            self.__lc_msg(localMessage)
            self.__calledMethodStatus[methodLocalName]= "failed"   
            return False, localMessage
        # port availability check
        callResult = self.get_selected_ports("")
        localMessage = "Available ports found:[{}]".format(callResult)
        self.__lc_msg(localMessage)
        portAvailableFound = self.__get_result_TF(callResult)
        if not portAvailableFound:
            localMessage = "No available port found"
            self.__lc_msg(localMessage)
            self.__calledMethodStatus[methodLocalName]= "failed"   
            return False, localMessage
        portAvailableList = self.__get_result_string(callResult)
        localMessage = "Found ports available :Port Id CSV List Received [{}]".format(portAvailableList)
        self.__lc_msg(localMessage)
        portIdList  = portAvailableList.split(",")
        i=0
        for portId in portIdList:
            i+=1
            keyValuePair =  portId.split(":")
            self.__portToSocketMap[keyValuePair[0]]=keyValuePair[1]
            localMessage = "Port {} Id: [{}]".format(i,portId)
            self.__lc_msg(localMessage)
        initializedPortsNumber=len(self.__portToSocketMap)
        localMessage = "Added {} ports to Port-Socket map :[{}]".format(initializedPortsNumber, self.__portToSocketMap)
        self.__lc_msg(localMessage)
        self.__calledMethodStatus[methodLocalName]= "success"   
        return True, localMessage



    def init_ont_type(self):  ### krepo not added ###
        """ It Initializes the self.__ontType to switch the proper commands
        depending on ONT-5xx or ONT-6xx (or ...) test instrument usage  """
        callResult = self.get_instrument_id()
        testInstrumentAnswers = self.__get_result_TF(callResult)
        if not testInstrumentAnswers:
            localMessage = "Test Instrument answer not received"
            self.__lc_msg(localMessage)
            return False, localMessage
        testInstrumentIdString = self.__get_result_string(callResult)
        localMessage = "Id string from instrument [{}]".format(testInstrumentIdString)
        if str(testInstrumentIdString).find("ONT-5") != -1:
            # test se __ontType e' corretto
            self.__ontType  = "5xx"
            localMessage = "Identified [{}]".format(self.__ontType)
            self.__lc_msg(localMessage)
        elif str(testInstrumentIdString).find("ONT-6") != -1:
            self.__ontType  = "6xx"
            localMessage = "Identified [{}]".format(self.__ontType)
            self.__lc_msg(localMessage)
        else:
            self.__ontType  = "Unknown"
            localMessage = "Test equipment [{}] Id received:[{}]".format(self.__ontType, testInstrumentIdString)
            self.__lc_msg(localMessage)
            return False, localMessage
        return True, localMessage



    def print_port_to_socket_map(self):  ### krepo not added ###
        # just a check print...in debug mode only...to check if map dictionary is initialized
        localMessage = "Current Port-Map dictionary: [{}]".format(self.__portToSocketMap)
        self.__lc_msg(localMessage)
        return True



    def print_ont_type(self):  ### krepo not added ###
        # just a check print...in debug mode only...to check if Ont Type has been correctly detected
        localMessage = "Detected Ont Type : [{}]".format(self.__ontType)
        self.__lc_msg(localMessage)
        return True



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
        for n in range(1,self.__ontCmdMaxRetry):
            callResult = self.get_available_ports()
            verifyResult = self.__verify_presence_in_csv_format_answer(callResult, portId)
            if not verifyResult[0]: # False means: port correctly allocated
                commandExecTime = (n * self.__ontSleepTimeForRetry)
                localMessage="Port [{}] selection OK: no more present in available ports list (retry : [{}])".format(portId, n)
                self.__lc_msg(localMessage)
                portAllocated = True
                break
            time.sleep(self.__ontSleepTimeForRetry)
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
        for n in range(1,self.__ontCmdMaxRetry):
            callResult = self.get_available_ports()
            verifyResult = self.__verify_presence_in_csv_format_answer(callResult, portId)
            if  verifyResult[0]: # True means: port correctly deallocated and present in available ports list
                commandExecTime = (n * self.__ontSleepTimeForRetry)
                localMessage="Port [{}] deselection OK: now present in available ports list (retry : [{}])".format(portId, n)
                self.__lc_msg(localMessage)
                portDeselected = True
                break
            time.sleep(self.__ontSleepTimeForRetry)
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
        for n in range(0,self.__ontCmdMaxRetry):
            localCommand="*OPC?"
            callResult = self.__send_cmd(localCommand)
            verifyResult = self.__verify_presence_in_csv_format_answer(callResult, "1")
            commandExecTime = ((n+1) * self.__ontSleepTimeForRetry)
            if verifyResult[0]: # True means: operations finished
                localMessage="All operations completed (retry: [{}])".format(n)
                self.__lc_msg(localMessage)
                operationCompleted = True
                break
            localMessage="Operation still in progress after [{}] retry)".format(n)
            time.sleep(self.__ontSleepTimeForRetry)
        return operationCompleted, localMessage



    def get_instrument_id(self):    ### krepo not added ###
        """ Gets the instrument identification
            Return tuple:
            True, < instrument identification string, e.g. JDSU,ONT-XXX,...
            False, <empty list> if there is no suitable port """
        # wait until no operation is in progress...
        callResult = self.wait_ops_completed()
        if not callResult[0]:  # False: operation pending: unable to proceed
            localMessage="Instrument busy: unable to proceed [{}]".format(callResult[1])
            self.__calledMethodStatus["get_instrument_id"]= "failed"  #
            self.__lc_msg(localMessage)
            return callResult, localMessage
        localCommand="*IDN?"
        rawCallResult = self.__send_cmd(localCommand)
        callResult = self.__remove_dust(rawCallResult[1])
        localMessage="INSTRUMENT ID[{}]".format(callResult)
        self.__lc_msg(localMessage)
        if callResult == "":
            self.__calledMethodStatus["get_instrument_id"]= "failed"  #
            return False, ""
        self.__calledMethodStatus["get_instrument_id"]= "success"  #
        return True, callResult



    #
    #   GENERAL
    #
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
        #self.__method_success(methodLocalName, None, localMessage)
        return True, callResult


    def get_last_error(self):  ### krepo added ###
        """ Provides info about the last error
            True,  < info string about error >  (string format" <code>,"<message>"    )
            False, < 0, "No error" >  (if no error found)  """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        localCommand=":SYST:ERR?"
        rawCallResult = self.__send_cmd(localCommand)
        callResult = self.__remove_dust(rawCallResult[1])
        ontRawError=tuple(callResult.split(','))
        localMessage="LAST INSTRUMENT ERROR [{}] [{}] ".format(ontRawError[0],ontRawError[1])
        self.__lc_msg(localMessage)
        if int(ontRawError[0]) == 0:  # 0 as string
            self.__method_success(methodLocalName, None, localMessage)
            return False ,  callResult
        self.__method_success(methodLocalName, None, localMessage)
        return True, callResult


    #
    #   APPLICATION CONTROL: APPLICATION HANDLING
    #
    def __send_port_cmd(self, portId, command):    ### krepo not added ###
        ### GHELFI ##portId = self.__recover_port_to_use(portId)
        # send a command to an instrument port specified by its portId ( /rack/slotNo/portNo ) port
        if command == "":
            localMessage = "__send_port_cmd error: command string [{}] empty".format(command)
            self.__lc_msg(localMessage)
            return False, localMessage
        if portId == "":
            localMessage = "__send_port_cmd error: portId  [{}] not valid (empty...)".format(portId)
            self.__lc_msg(localMessage)
            return False, localMessage
        localTelnetConnection=self.__portConnection[portId]
        if not localTelnetConnection:
            localMessage = "__send_port_cmd error: telnet connection [{}] not valid".format(localTelnetConnection)
            self.__lc_msg(localMessage)
            return False, localMessage
        localCmd="{:s}\n".format(command).encode()
        localTelnetConnection.write(localCmd)
        result=localTelnetConnection.expect(self.__telnetExpectedPrompt, 2)
        if result:
            localMessage = "sendPortCmd [{}] command OK".format(portId)
            #self.__lc_msg(localMessage)
            return True, str(result[2], 'utf-8')
        else:
            localMessage = "send_port_cmd [{}] command ERROR".format(portId)
            self.__lc_msg(localMessage)
            return False, localMessage



    def __create_port_connection(self,portId):    ### krepo not added ###
        # create a telnet connection with the portId custom TCP port of the ONT for Application cmd issue ( /rack/slotNo/portNo ) port
        portId = self.__recover_port_to_use(portId)
        tcpPortNumber = self.__portToSocketMap[portId]
        localMessage="Port [{}] bound to TCP Socket [{}][{}]".format(portId,self.__ontIpAddress, tcpPortNumber)
        self.__lc_msg(localMessage)
        self.__lc_msg("Function: __create_port_connection Socket [{}:{}]".format(self.__ontIpAddress, tcpPortNumber))
        try:
            self.__portConnection[portId] = telnetlib.Telnet(self.__ontIpAddress,tcpPortNumber,self.__telnetTimeout)
            response = self.__send_port_cmd(portId,"*PROMPT ON")
            localMessage = "Port [{}] connection established via [{}][{}] socket".format(portId,self.__ontIpAddress, tcpPortNumber)
            self.__lc_msg(localMessage)
        except Exception as e:
            self.__lc_msg(str(e))
            localMessage = "Port [{}] connection ERROR. Socket Info: [{}][{}]".format(portId,self.__ontIpAddress, tcpPortNumber)
            self.__lc_msg(localMessage)
            return False, localMessage

        if self.__ontType  == "6xx":
            # port-level authentication is a need ONLY for ONT-6xx
            # to allow the port to accept further commands
            localMessage = "[{}]: port authentication in progress".format(self.__ontType)
            self.__lc_msg(localMessage)
            self.__authenticate_user_on_6xx_port(portId)
            response = self.__send_port_cmd(portId,"*PROMPT ON")
            localMessage = "Port [{}] connection established via [{}][{}] socket".format(portId,self.__ontIpAddress, tcpPortNumber)
            self.__lc_msg(localMessage)
        return True, localMessage



    def open_port_channel(self, portId):    ### krepo not added ###
        # open a TCP channel to Port specified by portId( /rack/slotNo/portNo )
        portId = self.__recover_port_to_use(portId)
        if portId == "":
            localMessage = "open_port_channel error: portId  [{}] not valid (empty value)".format(portId)
            self.__lc_msg(localMessage)
            self.__calledMethodStatus["open_port_channel"]= "failed"   
            return False, localMessage
        callResult = self.__create_port_connection(portId)
        self.__calledMethodStatus["open_port_channel"]= "success"   
        return True, callResult



    def __get_currently_loaded_app(self, portId):   ### krepo not added ###
        """ Provides the name of the application currently loaded in <portId> port.
            True,  < application currently loaded (e.g. SdhBert)>
            False, < empty string >  """
        methodLocalName = self.__lc_current_method_name()
        portId = self.__recover_port_to_use(portId)
        localCommand=":INST:CAT?"
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        #callResult = self.__remove_dust(rawCallResult[1]).replace(">","")
        callResult = self.__remove_dust(rawCallResult[1]).replace(">","").replace("\"","")
        if  callResult == "":
            localMessage="No Application Currently Loaded[{}] PortId[{}]".format(callResult, portId)
            callRetCode = False
        else:
            localMessage="Currently Loaded Application [{}] PortId[{}]".format(callResult, portId)
            callRetCode = True
        self.__lc_msg(localMessage)
        return callRetCode, callResult



    def get_currently_loaded_app(self, portId): ### krepo added ###
        """ Provides the name of the application currently loaded in <portId> port.
            True,  < application currently loaded (e.g. SdhBert)>
            False, < empty string >  """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        localCommand=":INST:CAT?"
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        #callResult = self.__remove_dust(rawCallResult[1]).replace(">","")
        callResult = self.__remove_dust(rawCallResult[1]).replace(">","").replace("\"","")
        if  callResult == "":
            localMessage="No Application Currently Loaded[{}] PortId[{}]".format(callResult, portId)
            callRetCode = False
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
        else:
            localMessage="Currently Loaded Application [{}] PortId[{}] ".format(callResult, portId)
            callRetCode = True
            self.__lc_msg(localMessage)
            self.__method_success(methodLocalName, None, localMessage)
        return callRetCode, callResult



    def load_app(self, portId, applicationName):  ### krepo added ###
        """ It loads the <applicationName> application in <portId> port and waits until
            the application results in loaded status.
            True.... application loaded
            False... application load failed   """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if portId == "":
            localMessage = "load_app error: portId  [{}] not valid (empty value)".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if applicationName == "":
            localMessage = "load_app error: applicationName  [{}] not valid (empty value)".format(applicationName)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage

        if self.__ontType  == "6xx":
            if applicationName == "New-Application":
                localMessage = "[{}] load_app: [{}] application name ok".format(self.__ontType, applicationName)
                self.__lc_msg(localMessage)
            else:
                localMessage = "[{}] load_app error: applicationName [{}] not in expected list: [New-Application]".format(self.__ontType, applicationName)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage
        else:
            if applicationName == "SdhBert"      or \
               applicationName == "SonetBert"    or \
               applicationName == "OTN-G709"     or \
               applicationName == "OTN-G709-SDH" or \
               applicationName == "OTN-G709-SONET":
                localMessage = "[{}] load_app: application name [{}] ok".format(self.__ontType, applicationName)
                self.__lc_msg(localMessage)
            else:
                localMessage = "[{}] load_app error: applicationName [{}] not in expected list: [SdhBert|SonetBert|OTN-G709|OTN-G709-SDH|OTN-G709-SONET]".format(self.__ontType, applicationName)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage

        localCommand=":INST:LOAD \"{}\"".format(applicationName)
        callResult = self.__send_port_cmd(portId, localCommand)
        messageFromPort="[{}][{}]".format(callResult[0],callResult[1])
        # wait until port will be detect as in loaded state
        applicationLoaded = False
        for n in range(1,self.__ontCmdMaxRetry):
            callResult = self.__get_currently_loaded_app(portId)
            verifyResult = self.__verify_presence_in_csv_format_answer(callResult, applicationName)
            if  verifyResult[0]: # True means: application correctly loaded
                commandExecTime = (n * self.__ontSleepTimeForRetry)
                localMessage="[{}] Application [{}] loaded in [{}] retries".format(self.__ontType, applicationName, n)
                self.__lc_msg(localMessage)
                applicationLoaded = True
                break
                localMessage="[{}] Application [{}] not loaded after [{}] retries".format(self.__ontType, applicationName, n)
            time.sleep(self.__ontSleepTimeForRetry)
        self.__lc_msg(messageFromPort)
        if applicationLoaded == True:
            self.__method_success(methodLocalName, None, localMessage)
        else:
            self.__method_failure(methodLocalName, None, "", localMessage)
        return applicationLoaded, callResult



    def unload_app(self, portId, applicationName):  ### krepo added ###
        """ It deletes the <applicationName> application in <portId> port and waits until
            the application results really deleted.
            True.... application unloaded
            False... application unload failed   """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if portId == "":
            localMessage = "unload_app error: portId  [{}] not valid (empty value)".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if applicationName == "":
            localMessage = "unload_app error: applicationName  [{}] not valid (empty value)".format(applicationName)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if self.__ontType  == "6xx":
            if applicationName == "New-Application":
                localMessage = "load_app: [{}] app name ok".format(applicationName)
                self.__lc_msg(localMessage)
            else:
                localMessage = "load_app error: app name [{}] not in expected list: [New-Application]".format(applicationName)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage
        else:
            if applicationName == "SdhBert"      or \
               applicationName == "SonetBert"    or \
               applicationName == "OTN-G709"     or \
               applicationName == "OTN-G709-SDH" or \
               applicationName == "OTN-G709-SONET":
                localMessage = "unload_app:  app name [{}] ok".format(applicationName)
                self.__lc_msg(localMessage)
            else:
                localMessage = "unload_app error:  app name  [{}] not in expected list: [SdhBert|SonetBert|OTN-G709|OTN-G709-SDH|OTN-G709-SONET]".format(applicationName)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage

        localCommand=":INST:DEL \"{}\"".format(applicationName)
        callResult = self.__send_port_cmd(portId, localCommand)
        messageFromPort="[{}][{}]".format(callResult[0],callResult[1])
        # wait until port will be detect as in loaded state
        applicationUnloaded = False
        for n in range(1,self.__ontCmdMaxRetry):
            callResult = self.__get_currently_loaded_app(portId)
            verifyResult = self.__verify_presence_in_csv_format_answer(callResult, applicationName)
            if  not verifyResult[0]: # False means: application correctly unloaded
                commandExecTime = (n * self.__ontSleepTimeForRetry)
                localMessage="Application [{}] unloaded after [{}] retries".format(applicationName, n)
                self.__lc_msg(localMessage)
                applicationUnloaded = True
                break
                localMessage="Application [{}] not unloaded after [{}] retries".format(applicationName, n)
            time.sleep(self.__ontSleepTimeForRetry)
        time.sleep(10) # safety delay: unload answer finished even if still in progress...
        self.__lc_msg(messageFromPort)
        if applicationUnloaded == True:
            self.__method_success(methodLocalName, None, localMessage)
        else:
            self.__method_failure(methodLocalName, None, "", localMessage)
        return applicationUnloaded, callResult



    #
    #   APPLICATION CONTROL: APPLICATION CONFIGURATION - LAYER EDITOR
    #
    def open_edit_session(self, portId, command):   # ONT-6xx  Only  ### krepo not added ###
        """ UNDER TESTING: ONT-6XX only
            It opens edit session for new application configuration.
            The edit session is then closed by the next apply_edit_session()   command   """
        methodLocalName = self.__lc_current_method_name()
        portId = self.__recover_port_to_use(portId)
        if self.__ontType  == "6xx":
            pass
        else:
            localMessage="Command supported by ONT-6xx only "
            self.__lc_msg(localMessage)
            return False, localMessage

        if portId == "":
            localMessage = "open_edit_session error: portId  [{}] not valid (empty value)".format(portId)
            self.__lc_msg(localMessage)
            return False, localMessage
        if command != "ON" and \
           command != "on" and \
           command != "OFF"and \
           command != "off":
            localMessage = "open_edit_session error: command  [{}] not valid specify [ON|OFF]".format(command)
            self.__lc_msg(localMessage)
            return False, localMessage
        # INSERT PRE/POST PROCESSING CHECKS
        localCommand=":INST:CONF:EDIT:OPEN {}".format(command)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        currentEditSessionStatus = self.__remove_dust(rawCallResult[1])
        localMessage="Cmd:[{}] Result:[{}]".format(localCommand, currentEditSessionStatus)
        self.__lc_msg(localMessage)
        #self.__method_success(methodLocalName, None, localMessage)
        return True, callResult



    def apply_edit_session(self, portId, command):   # ONT-6xx  Only    ### krepo added ###
        """ UNDER TESTING: ONT-6XX only
            It applies settings of the edit session and closes the edit session. """
        methodLocalName = self.__lc_current_method_name()
        portId = self.__recover_port_to_use(portId)
        if self.__ontType  == "6xx":
            pass
        else:
            localMessage="Command supported by ONT-6xx only "
            self.__lc_msg(localMessage)
            return False, localMessage

        if portId == "":
            localMessage = "apply_edit_session error: portId  [{}] not valid (empty value)".format(portId)
            self.__lc_msg(localMessage)
            return False, localMessage
        if command != "ON" and \
           command != "on" and \
           command != "OFF"and \
           command != "off":
            localMessage = "apply_edit_session error: command  [{}] not valid specify [ON|OFF]".format(command)
            self.__lc_msg(localMessage)
            return False, localMessage
        # INSERT PRE/POST PROCESSING CHECKS
        localCommand=":INST:CONF:EDIT:APPL {}".format(command)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        currentEditSessionStatus = self.__remove_dust(rawCallResult[1])
        localMessage="Cmd:[{}] Result:[{}]".format(localCommand, currentEditSessionStatus)
        self.__lc_msg(localMessage)
        #self.__method_success(methodLocalName, None, localMessage)
        return True, callResult



    def set_current_signal_structure(self, portId, sigStructType):   # ONT-6xx  Only   ### krepo added ###
        """ UNDER TESTING: ONT-6XX only
            Determines the current signal structure (layer stack).
            Allowed sigStructType values and meaning:
            Values                               Meaning
            # SDH
            PHYS_SDH                             SDH BERT
            PHYS_SDH_GFP_MAC                     SDH GFP-F L2 L3 Traffic
            PHYS_SDH_GFP_MPLS                    SDH GFP-F L3 Traffic
            PHYS_SDH_HDLC_MPLS                   SDH HDLC L3 Traffic
            PHYS_SDHMC                           SDH-Multichannel BERT
            PHYS_SDHVC                           SDH-VC BERT
            PHYS_SDHVC_GFP_MAC                   SDH-VC GFP-F L2 L3 Traffic
            PHYS_SDHW                            10GigE WAN-SDH L1 BERT
            PHYS_SDHW_PCS_MAC                    10GigE WAN-SDH L2 L3 Traffic
            # PHYSICAL
            PHYS                                 Unframed BERT
            PHYS_OTN                             OTN BERT
            PHYS_OTN_GFP_MAC                     OTN GFP-F L2 L3 Traffic
            PHYS_OTN_GFP_PCS_MAC                 OTN GFP-F PCS L2 L3 Traffic
            PHYS_OTN_ODU                         OTN ODU BERT
            PHYS_OTN_ODU_GFP_MAC                 OTN ODU GFP-F L2 L3 Traffic
            PHYS_OTN_ODU_GFP_PCS1G_MAC           OTN ODU0 GFP-T L2 L3 Traffic
            PHYS_OTN_ODU_ODU                     OTN ODU1 ODU0 BERT
            PHYS_OTN_ODU_ODU_GFP_MAC             OTN ODU1 ODU0 GFP-F L2 L3 Traffic
            PHYS_OTN_ODU_ODU_GFP_PCS1G_MAC       OTN ODU1 ODU0 GFP-T L2 L3 Traffic
            PHYS_OTN_ODU_ODU_SDH                 OTN ODU1 ODU0 SDH BERT
            PHYS_OTN_ODU_ODU_SON                 OTN ODU1 ODU0 SONET BERT
            PHYS_OTN_ODU_SDH                     OTN ODU SDH BERT
            PHYS_OTN_ODU_SDHMC                   OTN ODU SDH-Multichannel BERT
            PHYS_OTN_ODU_SDHVC                   OTN ODU SDH-VC BERT
            PHYS_OTN_ODU_SDHVC_GFP_MAC           OTN ODU SDH-VC GFP-F L2 L3 Traffic
            PHYS_OTN_ODU_SON                     OTN ODU SONET BERT
            PHYS_OTN_ODU_SONMC                   OTN ODU SONET-Multichannel BERT
            PHYS_OTN_ODU_SONVC                   OTN ODU SONET-VC BERT
            PHYS_OTN_ODU_SONVC_GFP_MAC           OTN ODU SONET-VC GFP-F L2 L3 Traffic
            PHYS_OTN_ODUMC                       OTN ODU-Multichannel BERT
            PHYS_OTN_PCS                         OTN PCS [64B/66B] BERT
            PHYS_OTN_PCS_FC2                     OTN 10GigFC L2 Traffic
            PHYS_OTN_PCS_MAC                     OTN 10GigE LAN L2 L3 Traffic
            PHYS_OTN_SDH                         OTN SDH BERT
            PHYS_OTN_SDH_GFP_MAC                 OTN SDH GFP-F L2 L3 Traffic
            PHYS_OTN_SDHMC                       OTN SDH-Multichannel BERT
            PHYS_OTN_SDHVC                       OTN SDH-VC BERT
            PHYS_OTN_SDHVC_GFP_MAC               OTN SDH-VC GFP-F L2 L3 Traffic
            PHYS_OTN_SDHW                        OTN 10GigE WAN-SDH L1 BERT
            PHYS_OTN_SDHW_PCS_MAC                OTN 10GigE WAN-SDH L2 L3 Traffic
            PHYS_OTN_SON                         OTN SONET BERT
            PHYS_OTN_SON_GFP_MAC                 OTN SONET GFP-F L2 L3 Traffic
            PHYS_OTN_SONMC                       OTN SONET-Multichannel BERT
            PHYS_OTN_SONVC                       OTN SONET-VC BERT
            PHYS_OTN_SONVC_GFP_MAC               OTN SONET-VC GFP-F L2 L3 Traffic
            PHYS_OTN_SONW                        OTN 10GigE WAN-SONET L1 BERT
            PHYS_OTN_SONW_PCS_MAC                OTN 10GigE WAN-SONET L2 L3 Traffic
            PHYS_PCS                             PCS [64B/66B] BERT
            PHYS_PCS_FC2                         10GigFC L2 Traffic
            PHYS_PCS_MAC                         10GigE LAN L2 L3 Traffic
            PHYS_PCS1G_MAC                       1GigE LAN L2 L3 Traffic
            # SONET
            PHYS_SON                             SONET BERT
            PHYS_SON_GFP_MAC                     SONET GFP-F L2 L3 Traffic
            PHYS_SON_GFP_MPLS                    SONET GFP-F L3 Traffic
            PHYS_SON_HDLC_MPLS                   SONET HDLC L3 Traffic
            PHYS_SONMC                           SONET-Multichannel BERT
            PHYS_SONVC                           SONET-VC BERT
            PHYS_SONVC_GFP_MAC                   SONET-VC GFP-F L2 L3 Traffic
            PHYS_SONW                            10GigE WAN-SONET L1 BERT
            PHYS_SONW_PCS_MAC                    10GigE WAN-SONET L2 L3 Traffic
            """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if self.__ontType  == "6xx":
            pass
        else:
            localMessage="Command supported by ONT-6xx only "
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if portId == "":
            localMessage = "set_current_signal_structure error: portId  [{}] not valid (empty value)".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if sigStructType == "":
            localMessage = "set_current_signal_structure error: sigStructType [{}] not valid (empty value)".format(sigStructType)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage

        # INSERT PRE/POST PROCESSING CHECKS
        # SET SIGNAL STRUCTURE
        localCommand=":INST:CONF:EDIT:LAY:STAC {}".format(sigStructType)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        currentEditSessionStatus = self.__remove_dust(rawCallResult[1])
        localMessage="Cmd:[{}] Result:[{}]".format(localCommand, currentEditSessionStatus)
        self.__lc_msg(localMessage)
        time.sleep(1)

        # APPLY SIGNAL STRUCTURE
        localCommand=":INST:CONF:EDIT:APPL ON"
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        currentEditSessionStatus = self.__remove_dust(rawCallResult[1])
        localMessage="Cmd:[{}] Result:[{}]".format(localCommand, currentEditSessionStatus)
        # WAIT UNTIL LOAD TERMINATION
        # Trying to give a chick to the TestEq to fix :INST:CONF:EDIT:APPL? always OFF issue...
        time.sleep(30)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, localMessage



    #
    #   APPLICATION CONTROL: MEASUREMENT CONTROL
    #
    def start_measurement(self, portId):   # ONT-5xx  Only    ### krepo added ###       
        """ ONT-5XX only
            Starts a measurement.. """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if self.__ontType  == "5xx":
            pass
        else:
            localMessage="start_measurement: Command supported by ONT-5xx only "
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage

        if portId == "":
            localMessage = "start_measurement error: portId  [{}] not valid (empty value)".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        # INSERT PRE/POST PROCESSING CHECKS IF POSSIBLE
        localCommand=":INIT:IMM:ALL"
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        callResult = self.__remove_dust(rawCallResult[1])
        localMessage="Cmd:[{}] Result:[{}]".format(localCommand, callResult)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, callResult



    def halt_measurement(self, portId):   # ONT-5xx  Only    ### krepo added ###       
        """ Halts a running measurement. """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if self.__ontType  == "5xx":
            pass
        else:
            localMessage="{}:Command supported by ONT-5xx only ".format(methodLocalName)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if portId == "":
            localMessage = "{} error: portId  [{}] not valid (empty value)".format(methodLocalName,portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        # INSERT PRE/POST PROCESSING CHECKS IF POSSIBLE
        localCommand=":ABOR"
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        callResult = self.__remove_dust(rawCallResult[1])
        localMessage="Cmd:[{}] Result:[{}]".format(localCommand, callResult)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, callResult


        
    def cli_user_debug_command(self,commandString, portId):   # To give the user the possibility to check commands       
        """ To give the user the possibility to check commands """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        localCommand = commandString 
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        callResult = self.__remove_dust(rawCallResult[1])
        localMessage="Cmd:[{}] Result:[{}]".format(localCommand, callResult)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, callResult


    def get_set_measurement_time(self, portId, gatingTime=""):   # ONT-5xx  Only   ### krepo added ###    
        """ Sets and  gets the measurement gating time.
            gatingTime values :
            0 or ""    ...provides the current time
            1...8553600...gating time
            Notes: The maximal possible gating time depends on the application
                   and may be shorter than 99 days.
                   Setting the maximal possible gating time is equivalent to 'Continuous'. """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if self.__ontType  == "5xx":
            pass
        else:
            localMessage="{}:Command supported by ONT-5xx only ".format(methodLocalName)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if portId == "":
            localMessage = "{} error: portId  [{}] not valid (empty value)".format(methodLocalName,portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if gatingTime  == "" or \
           gatingTime  == 0:  # get time request
            localCommand=":SENS:SWE:TIME?"
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            callResult = self.__remove_dust(rawCallResult[1]).replace(">","")
            localMessage="Get measurement time result:[{}]".format(callResult)
            self.__lc_msg(localMessage)
            self.__method_success(methodLocalName, None, localMessage)
            return True, callResult
        localCommand=":SENS:SWE:TIME {}".format(gatingTime)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        callResult = self.__remove_dust(rawCallResult[1]).replace(">","")
        localMessage="Set measurement time result:[{}]".format(callResult)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, callResult


    #
    #   SDH EXPERT COMMANDS
    #
    def retrieve_optical_alarms(self, portId):   # ONT-5xx  ONT-6xx    ### krepo added ###       
        """ ONT-5XX  and ONT-6xx
            Retrieve optical alarms
            LOS Loss of signal
            POV Power Overload.
            FOV Frequency Out Of Range.
            Return tuple:
            ( "True|False" , "<return string/ error list>)
            True : command execution ok, return string contains the alarm list (empty if no alarm)
            False: command execution failed, error string for debug purposes
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        retList = []
        if self.__ontType  == "5xx":
            ONTCmdString=":HST:RX:OPT"
        else:
            ONTCmdString=":PHYS:LINE:CST:ALAR"
        if portId == "":
            localMessage = "ERROR retrieve_optical_alarms: portId  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        localCommand="{}?".format(ONTCmdString)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        resultItemsArray=sdhAnswer.split(",")
        if resultItemsArray[0] == "-1":  # SDH command error
            localMessage = "[{}] ERROR: retrieve_optical_alarms ({}) answers :[{}] ".format(self.__ontType,localCommand,resultItemsArray[0])
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        alarmCodes = resultItemsArray[1]
        if self.__ontType  == "5xx":
            localMessage="[5xx] Optical alarms retcode: [{}]".format(str(alarmCodes))
            alarmCodes=int(float(alarmCodes))
            if alarmCodes & 2:
                retList += ["LOS"]
            if alarmCodes & 4:
                retList += ["POV"]
            if alarmCodes & 8:
                retList += ["FOV"]
        else:
            localMessage="[6xx] Optical alarms retcode: [{}]".format(str(alarmCodes))
            self.__lc_msg(str(localMessage))
            alarmCodes=int(float(alarmCodes))
            if alarmCodes & 1:
                retList += ["LOS"]
            if alarmCodes & 16:
                retList += ["POV"]
            if alarmCodes & 32:
                retList += ["FOV"]
            if alarmCodes & 256:
                retList += ["MissingXFPSFP"]
        localMessage="Optical Found Alarms: [{}]".format(retList)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, retList



    def retrieve_sdh_alarms(self, portId):   # ONT-5xx  and ONT-6xx    ### krepo added ###       
        """ ONT-5XX  and ONT-6xx 
            Retrieve SDH Alarms in both instruments types, without no HO/LO distinction.
            Use this method to ease the alarms retrieving for all JDSU/ Ont5xx/6xx instruments
            ONT-5XX / Higher Order SDH Alarms:  
              OOF
              LOF
              MS-AIS
              MS-RDI
              AU-AIS
              AU-LOP
              HP-UNEQ
              RS-TIM
              HP-TIM
              HP-PLM
            ONT-5XX / Lower Order SDH Alarms
              TU-AIS
              LP-RDI
              TU-LOP
              LP-UNEQ
              TU-LOM
              LP-RFI
              LP-TIM
              LP-PLM
            ONT-6XX only both HO and LO alarms SDH Alarms
              LOPL
              LOF
              OOF
              RS-TIM
              MS-AIS
              MS-RDI
              AU-AIS
              AU-LOP
              AU-NDF
              HP-TIM
              HP-UNEQ
              HP-PLM
              HP-RDI
              HP-RDI-C
              HP-RDI-S
              HP-RDI-P
              LOM
              TU-AIS
              TU-LOP
              LP-TIM
              LP-UNEQ
              LP-PLM
              LP-RDI
              LP-RFI
              LSS
            Return tuple:
            ( "True|False" , "<return string / error list>)
            True : command execution ok, the return string contains the alarm list (empty if no alarm)
            False: command execution failed, error string for debug purposes
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if portId == "":
            localMessage = "[{}] ERROR retrieve_ho_alarms: portId  [{}] not specified".format(methodLocalName,portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        retList = []
        if self.__ontType  == "6xx":  # ONT 6xx management
            localCommand="SDH:SEL:CST:ALAR?"
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            resultItemsArray=sdhAnswer.split(",")
            if resultItemsArray[0] == "-1":  # SDH command error
                localMessage = "ERROR: retrieve_ho_lo_alarms ({}) answers :[{}] ".format(localCommand,resultItemsArray[0])
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage
            alarmCodes = resultItemsArray[1]
            localMessage="[6xx] Optical alarms retcode: [{}]".format(str(alarmCodes))
            self.__lc_msg(str(localMessage))
            alarmCodes=int(float(alarmCodes))
            if alarmCodes & 1 :           retList += ["LOPL"]
            if alarmCodes & 2 :           retList += ["LOF"]
            if alarmCodes & 4 :           retList += ["OOF"]
            if alarmCodes & 8 :           retList += ["RS-TIM"]
            if alarmCodes & 16 :          retList += ["MS-AIS"]
            if alarmCodes & 32 :          retList += ["MS-RDI"]
            if alarmCodes & 64 :          retList += ["AU-AIS"]
            if alarmCodes & 128 :         retList += ["AU-LOP"]
            if alarmCodes & 256 :         retList += ["AU-NDF"]
            if alarmCodes & 512 :         retList += ["HP-TIM"]
            if alarmCodes & 1024 :        retList += ["HP-UNEQ"]
            if alarmCodes & 2048 :        retList += ["HP-PLM"]
            if alarmCodes & 8192 :        retList += ["HP-RDI"]
            if alarmCodes & 16384 :       retList += ["HP-RDI-C"]
            if alarmCodes & 32768 :       retList += ["HP-RDI-S"]
            if alarmCodes & 65536 :       retList += ["HP-RDI-P"]
            if alarmCodes & 131072 :      retList += ["LOM"]
            if alarmCodes & 262144 :      retList += ["TU-AIS"]
            if alarmCodes & 524288 :      retList += ["TU-LOP"]
            if alarmCodes & 2097152 :     retList += ["LP-TIM"]
            if alarmCodes & 4194304 :     retList += ["LP-UNEQ"]
            if alarmCodes & 8388608 :     retList += ["LP-PLM"]
            if alarmCodes & 33554432 :    retList += ["LP-RDI"]
            if alarmCodes & 536870912 :   retList += ["LP-RFI"]
            if alarmCodes & 1073741824 :  retList += ["LSS"]
            localMessage="High Order and Lower Order Found Alarms: [{}]".format(retList)
            self.__lc_msg(localMessage)
            self.__method_success(methodLocalName, None, localMessage)
            return True, retList
        elif self.__ontType  == "5xx":  # ONT 5xx management :
            localCommand=":HST:RX:SDH?"
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            resultItemsArray=sdhAnswer.split(",")
            if resultItemsArray[0] == "-1":  # SDH command error
                localMessage = "ERROR: retrieve_ho_alarms ({}) answers :[{}] ".format(localCommand,resultItemsArray[0])
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage
            alarmCodes = resultItemsArray[1]
            alarmCodes=int(float(alarmCodes))
            if alarmCodes & 4:            retList += ["OOF"]
            if alarmCodes & 8:            retList += ["LOF"]
            if alarmCodes & 16:           retList += ["MS-AIS"]
            if alarmCodes & 32:           retList += ["MS-RDI"]
            if alarmCodes & 128:          retList += ["AU-AIS"]
            if alarmCodes & 256:          retList += ["HP-RDI"]
            if alarmCodes & 4096:         retList += ["AU-LOP"]
            if alarmCodes & 8192:         retList += ["HP-UNEQ"]
            if alarmCodes & 16384:        retList += ["RS-TIM"]
            if alarmCodes & 32768:        retList += ["HP-TIM"]
            if alarmCodes & 65536:        retList += ["HP-PLM"] #if alarmCodes & 65535:
             
            localCommand=":HST:RX:SDH:TRIB?"
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            resultItemsArray=sdhAnswer.split(",")
            if resultItemsArray[0] == "-1":  # SDH command errorJust print a message in case of lower order alarms
                localMessage = "INFO: retrieve_lo_alarms ({}) answers :[{}] skipping LO sdh alarm processing".format(localCommand,resultItemsArray[0])
                self.__lc_msg(localMessage)
                #self.__method_failure(methodLocalName, None, "", localMessage)
                #return False, localMessage
            else:  # with no errors in lower order alarm retrieve process alarmCodes
                alarmCodes = resultItemsArray[1]
                alarmCodes=int(float(alarmCodes))
                if alarmCodes & 1:            retList += ["TU-AIS"]
                if alarmCodes & 2:            retList += ["LP-RDI"]
                if alarmCodes & 4:            retList += ["TU-LOP"]
                if alarmCodes & 8:            retList += ["LP-UNEQ"]
                if alarmCodes & 16:           retList += ["TU-LOM"]
                if alarmCodes & 32:           retList += ["LP-RFI"]
                if alarmCodes & 128:          retList += ["LP-TIM"]
                if alarmCodes & 256:          retList += ["LP-PLM"]
            localMessage="Found Alarms: [{}]".format(retList)
            self.__lc_msg(localMessage)
            self.__method_success(methodLocalName, None, localMessage)
            return True, retList
        else :  # "Instrument not supported" case management :
            localMessage="Instrument [{}] not supported".format(retList)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, retList



    def retrieve_ho_alarms(self, portId):   # ONT-5xx  Only    ### krepo added ###       
        """ ONT-5XX only
            Retrieve the following Higher Order SDH Alarms
            OOF
            LOF
            MS-AIS
            MS-RDI
            AU-AIS
            AU-LOP
            HP-UNEQ
            RS-TIM
            HP-TIM
            HP-PLM
            Return tuple:
            ( "True|False" , "<return string/ error list>)
            True : command execution ok, return string contains the alarm list (empty if no alarm)
            False: command execution failed, error string for debug purposes
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        retList = []
        if self.__ontType  == "5xx":
            pass
        else:
            localMessage="ERROR: Command supported by ONT-5xx only "
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if portId == "":
            localMessage = "ERROR retrieve_ho_alarms: portId  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        localCommand=":HST:RX:SDH?"
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        resultItemsArray=sdhAnswer.split(",")
        if resultItemsArray[0] == "-1":  # SDH command error
            localMessage = "ERROR: retrieve_ho_alarms ({}) answers :[{}] ".format(localCommand,resultItemsArray[0])
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        alarmCodes = resultItemsArray[1]
        alarmCodes=int(float(alarmCodes))
        if alarmCodes & 4:
            retList += ["OOF"]
        if alarmCodes & 8:
            retList += ["LOF"]
        if alarmCodes & 16:
            retList += ["MS-AIS"]
        if alarmCodes & 32:
            retList += ["MS-RDI"]
        if alarmCodes & 128:
            retList += ["AU-AIS"]
        if alarmCodes & 256:
            retList += ["HP-RDI"]
        if alarmCodes & 4096:
            retList += ["AU-LOP"]
        if alarmCodes & 8192:
            retList += ["HP-UNEQ"]
        if alarmCodes & 16384:
            retList += ["RS-TIM"]
        if alarmCodes & 32768:
            retList += ["HP-TIM"]
        if alarmCodes & 65536: #if alarmCodes & 65535:
            retList += ["HP-PLM"]
        localMessage="High Order Found Alarms: [{}]".format(retList)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, retList



    def retrieve_lo_alarms(self, portId):   # ONT-5xx  Only    ### krepo added ###       
        """ ONT-5XX only
            Retrieve the following Lower Order SDH Alarms
            TU-AIS
            LP-RDI
            TU-LOP
            LP-UNEQ
            TU-LOM
            LP-RFI
            LP-TIM
            LP-PLM
            Return tuple:
            ( "True|False" , "<return string/ error list>)
            True : command execution ok, return string contains the alarm list (empty if no alarm)
            False: command execution failed, error string for debug purposes
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        retList = []
        if self.__ontType  == "5xx":
            pass
        else:
            localMessage="ERROR: Command supported by ONT-5xx only "
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if portId == "":
            localMessage = "ERROR retrieve_lo_alarms: portId  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        localCommand=":HST:RX:SDH:TRIB?"
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        resultItemsArray=sdhAnswer.split(",")
        if resultItemsArray[0] == "-1":  # SDH command error
            localMessage = "ERROR: retrieve_lo_alarms ({}) answers :[{}] ".format(localCommand,resultItemsArray[0])
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        alarmCodes = resultItemsArray[1]
        alarmCodes=int(float(alarmCodes))
        if alarmCodes & 1:
            retList += ["TU-AIS"]
        if alarmCodes & 2:
            retList += ["LP-RDI"]
        if alarmCodes & 4:
            retList += ["TU-LOP"]
        if alarmCodes & 8:
            retList += ["LP-UNEQ"]
        if alarmCodes & 16:
            retList += ["TU-LOM"]
        if alarmCodes & 32:
            retList += ["LP-RFI"]
        if alarmCodes & 128:
            retList += ["LP-TIM"]
        if alarmCodes & 256:
            retList += ["LP-PLM"]
        localMessage="Lower Order Found Alarms: [{}]".format(retList)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, retList



    def retrieve_ho_lo_alarms(self, portId):   # ONT-6xx  Only    ### krepo added ###       
        """ ONT-6XX only: both HO and LO alarms retrieved here
            Retrieve the following SDH Alarms
            LOPL
            LOF
            OOF
            RS-TIM
            MS-AIS
            MS-RDI
            AU-AIS
            AU-LOP
            AU-NDF
            HP-TIM
            HP-UNEQ
            HP-PLM
            HP-RDI
            HP-RDI-C
            HP-RDI-S
            HP-RDI-P
            LOM
            TU-AIS
            TU-LOP
            LP-TIM
            LP-UNEQ
            LP-PLM
            LP-RDI
            LP-RFI
            LSS
            Return tuple:
            ( "True|False" , "<return string/ error list>)
            True : command execution ok, return string contains the alarm list (empty if no alarm)
            False: command execution failed, error string for debug purposes
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        retList = []
        if self.__ontType  == "6xx":
            pass
        else:
            #
            # for 5xx consider to call HERE both retrieve_ho_alarms() and retrieve_lo_alarms()
            # and return the result with only one call to retrieve_ho_lo_alarms()
            #
            localMessage="ERROR: Command supported by ONT-5xx only "
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if portId == "":
            localMessage = "ERROR retrieve_ho_lo_alarms: portId  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        localCommand="SDH:SEL:CST:ALAR?"
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        resultItemsArray=sdhAnswer.split(",")
        if resultItemsArray[0] == "-1":  # SDH command error
            localMessage = "ERROR: retrieve_ho_lo_alarms ({}) answers :[{}] ".format(localCommand,resultItemsArray[0])
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        alarmCodes = resultItemsArray[1]
        localMessage="[6xx] Optical alarms retcode: [{}]".format(str(alarmCodes))
        self.__lc_msg(str(localMessage))
        alarmCodes=int(float(alarmCodes))
        if alarmCodes & 1 :           retList += ["LOPL"]
        if alarmCodes & 2 :           retList += ["LOF"]
        if alarmCodes & 4 :           retList += ["OOF"]
        if alarmCodes & 8 :           retList += ["RS-TIM"]
        if alarmCodes & 16 :          retList += ["MS-AIS"]
        if alarmCodes & 32 :          retList += ["MS-RDI"]
        if alarmCodes & 64 :          retList += ["AU-AIS"]
        if alarmCodes & 128 :         retList += ["AU-LOP"]
        if alarmCodes & 256 :         retList += ["AU-NDF"]
        if alarmCodes & 512 :         retList += ["HP-TIM"]
        if alarmCodes & 1024 :        retList += ["HP-UNEQ"]
        if alarmCodes & 2048 :        retList += ["HP-PLM"]
        if alarmCodes & 8192 :        retList += ["HP-RDI"]
        if alarmCodes & 16384 :       retList += ["HP-RDI-C"]
        if alarmCodes & 32768 :       retList += ["HP-RDI-S"]
        if alarmCodes & 65536 :       retList += ["HP-RDI-P"]
        if alarmCodes & 131072 :      retList += ["LOM"]
        if alarmCodes & 262144 :      retList += ["TU-AIS"]
        if alarmCodes & 524288 :      retList += ["TU-LOP"]
        if alarmCodes & 2097152 :     retList += ["LP-TIM"]
        if alarmCodes & 4194304 :     retList += ["LP-UNEQ"]
        if alarmCodes & 8388608 :     retList += ["LP-PLM"]
        if alarmCodes & 33554432 :    retList += ["LP-RDI"]
        if alarmCodes & 536870912 :   retList += ["LP-RFI"]
        if alarmCodes & 1073741824 :  retList += ["LSS"]
        localMessage="High Order and Lower Order Found Alarms: [{}]".format(retList)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, retList



    def get_set_laser_status(self, portId, laserStatus=""):   # ONT-5xx and ONT-6xx    ### krepo added ###       
        """ ONT-5XX and ONT-6xx
            Set or Retrieve the laser status
            laserStatus ON | OFF | "" (get status)
            Return tuple:
            ( "True|False" , "< Laser Status / error list>)
            True : command execution ok, current laser status [ON|OFF]
            False: command execution failed, error string for debug purposes
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        retList = []
        if self.__ontType  == "5xx":
            ONTCmdString=":OUTP:TEL:LINE:OPT:STAT"
        else:
            ONTCmdString=":OUTP:TEL:PHYS:LINE:OPT:STAT"
        if portId == "":
            localMessage = "ERROR get_set_laser_status: portId  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        laserStatus = laserStatus.upper()
        if laserStatus != "ON"  and \
           laserStatus != "OFF" and \
           laserStatus != "":
            localMessage = "ERROR get_set_laser_status: laserStatus  [{}] not valid [ON|OFF|''(to get status)]".format(laserStatus)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if laserStatus == "":  # Get laser status and exit
            localCommand="{}?".format(ONTCmdString)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            self.__method_success(methodLocalName, None, sdhAnswer)
            return True, sdhAnswer
        localCommand="{} {}".format(ONTCmdString, laserStatus)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        localCommand="{}?".format(ONTCmdString)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        localMessage="Current Laser Status After set:[{}] ".format(sdhAnswer)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, sdhAnswer



    def get_set_wavelenght(self, portId, waveLenght=""):   # ONT-5xx and ONT-6xx    ### krepo added ###       
        """ ONT-5XX only
            Get or Set the laser wavelenght between
                W1310 (Generator wavelength is 1310 nm)
                W1550 (Generator wavelength is 1550 nm BE CARE:not available for OC192/STM-64)
            Return tuple: ( "True|False" , "< result/error list>)
                True : command execution ok, current read wavelenght in result string
                False: error in command execution, details in error list string

        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        #retList = []
        if portId == "":
            localMessage = "ERROR get_set_wavelenght: portId  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if self.__ontType  == "5xx":
            ONTCmdString=":OUTP:TEL:LINE:OPT:WLEN"
        else:
            # In ONT-6xx the cmd string depends on involved port:SFP or XFP(Stm64)
            # Read tx tate to get Port Type
            localCommand=":SOUR:DATA:TEL:PHYS:LINE:RATE?"
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            if sdhAnswer == "STM64" or  sdhAnswer == "OC192":
                ONTCmdString=":PHYS:TX:XFP:MSA:WLEN"
                localMessage="Found XFP module: using command [{}]".format(ONTCmdString)
                self.__lc_msg(localMessage)
            else:
                ONTCmdString=":PHYS:TX:SFP1:MSA:WLEN"
                localMessage="Found SFP module: using command [{}]".format(ONTCmdString)
                self.__lc_msg(localMessage)
        waveLenght = waveLenght.upper()
        # Parameter check enabled for ONT5xx only
        if self.__ontType  == "5xx":
            if waveLenght != "W1310"  and \
               waveLenght != "W1550" and \
               waveLenght != "":
                localMessage = "ERROR get_set_wavelenght: waveLenght  [{}] not valid [W1310|W1550|1310|1550|''(to get status)]".format(waveLenght)
                self.__lc_msg(localMessage)
                self.__method_success(methodLocalName, None, localMessage)
                return False, localMessage
        if waveLenght == "":  # Get laser wavelenght and exit
            localCommand="{}?".format(ONTCmdString)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            self.__method_success(methodLocalName, None, sdhAnswer)
            return True, sdhAnswer
        localCommand="{} {}".format(ONTCmdString, waveLenght)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        localCommand="{}?".format(ONTCmdString)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        localMessage="Current Laser wlenght set to [{}]... status After set :[{}] ".format(waveLenght,sdhAnswer)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, sdhAnswer



    def __get_set_rx_bit_rate(self, portId, bitRate=""):   # ONT-5xx  ONT-6xx    ### krepo not added ###
        """ ONT-5XX only
            Get or Set the current bitRate from:
                STM0  Bit rate is 55.84 Mbit/s.
                STM1  Bit rate is 155.52 Mbit/s. (for OC-1/3/12/48 / STM-0/1/4/16 module)
                STM4  Bit rate is 622.08 Mbit/s.
                STM16 Bit rate is 2488.32 Mbit/s.
                STM64 Bit rate is 9953.28 Mbit/s (only available for OC-192/STM-64 modules).
            Return tuple: ( "True|False" , "< result/error list>)
                True : command execution ok, current read bitRate in result string
                False: error in command execution, details in error list string
        """
        methodLocalName = self.__lc_current_method_name()
        portId = self.__recover_port_to_use(portId)
        if self.__ontType  == "5xx":
            ONTCmdString=":SENS:DATA:TEL:OPT:RATE"
        else:
            ONTCmdString=":SENS:DATA:TEL:PHYS:LINE:RATE"
        if portId == "":
            localMessage = "ERROR get_set_bitRate: portId  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            return False, localMessage
        bitRate = bitRate.upper()
        if bitRate != "STM0"  and \
           bitRate != "STM1"  and \
           bitRate != "STM4"  and \
           bitRate != "STM16" and \
           bitRate != "STM64" and \
           bitRate != "":
            localMessage = "ERROR get_set_bitRate: bitRate  [{}] not valid [STM0|STM1|STM4|STM16|STM64|''(to get status)]".format(bitRate)
            self.__lc_msg(localMessage)
            return False, localMessage
        if bitRate == "":  # Get laser bitRate and exit
            localCommand="{}?".format(ONTCmdString)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            return True, sdhAnswer
        if self.__ontType  == "6xx": # for 6xx we need to use OCs instead of STMs
            localMessage="[6xx]: [{}] translated to [{}]".format(bitRate,self.StmToOc[bitRate])
            self.__lc_msg(localMessage)
            bitRate = self.StmToOc[bitRate]
        rxBitRateRequired = bitRate
        localCommand="{} {}".format(ONTCmdString, bitRate)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        localCommand="{}?".format(ONTCmdString)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        #self.__lc_msg(sdhAnswer)
        #self.__lc_msg(rxBitRateRequired)
        if sdhAnswer != rxBitRateRequired:
            localMessage="Set RX bitRate mismatch required [{}] but set [{}] ".format(rxBitRateRequired,sdhAnswer)
            self.__lc_msg(localMessage)
            return False, sdhAnswer
        localMessage="Set RX bitRate required=[{}] after set=[{}] ".format(rxBitRateRequired,sdhAnswer)
        self.__lc_msg(localMessage)
        return True, sdhAnswer



    def get_set_rx_bit_rate(self, portId, bitRate=""):   # ONT-5xx  ONT-6xx    ### krepo added ###       
        """ ONT-5XX only
            Get or Set the current bitRate from:
                STM0  Bit rate is 55.84 Mbit/s.
                STM1  Bit rate is 155.52 Mbit/s. (for OC-1/3/12/48 / STM-0/1/4/16 module)
                STM4  Bit rate is 622.08 Mbit/s.
                STM16 Bit rate is 2488.32 Mbit/s.
                STM64 Bit rate is 9953.28 Mbit/s (only available for OC-192/STM-64 modules).
            Return tuple: ( "True|False" , "< result/error list>)
                True : command execution ok, current read bitRate in result string
                False: error in command execution, details in error list string
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if self.__ontType  == "5xx":
            ONTCmdString=":SENS:DATA:TEL:OPT:RATE"
        else:
            ONTCmdString=":SENS:DATA:TEL:PHYS:LINE:RATE"
        if portId == "":
            localMessage = "ERROR get_set_bitRate: portId  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        bitRate = bitRate.upper()
        if bitRate != "STM0"  and \
           bitRate != "STM1"  and \
           bitRate != "STM4"  and \
           bitRate != "STM16" and \
           bitRate != "STM64" and \
           bitRate != "":
            localMessage = "ERROR get_set_bitRate: bitRate  [{}] not valid [STM0|STM1|STM4|STM16|STM64|''(to get status)]".format(bitRate)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if bitRate == "":  # Get laser bitRate and exit
            localCommand="{}?".format(ONTCmdString)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            self.__method_success(methodLocalName, None, sdhAnswer)
            return True, sdhAnswer
        if self.__ontType  == "6xx": # for 6xx we need to use OCs instead of STMs
            localMessage="[6xx]: [{}] translated to [{}]".format(bitRate,self.StmToOc[bitRate])
            self.__lc_msg(localMessage)
            bitRate = self.StmToOc[bitRate]
        rxBitRateRequired = bitRate
        localCommand="{} {}".format(ONTCmdString, bitRate)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        localCommand="{}?".format(ONTCmdString)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        if sdhAnswer != rxBitRateRequired:
            localMessage="Set RX bitRate mismatch required [{}] but set [{}] ".format(rxBitRateRequired,sdhAnswer)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, sdhAnswer
        localMessage="Set RX bitRate required=[{}] after set=[{}] ".format(rxBitRateRequired,sdhAnswer)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, sdhAnswer



    def get_set_clock_reference_source(self, portId, clockMode=""):   # ONT-5xx and ONT-6xx    ### krepo added ###       
        """ ONT-5XX and ONT-6XX
            Get or Set the source of the reference clock:
                CM(5xx)/LOCAL(6xx) Controlled via internal Clock Module
                RX  Derived from RX signal !!! BE CARE !!! : call get_set_rx_bit_rate() before select RX
            Return tuple: ( "True|False" , "< result/error list>)
                True : command execution ok, current reference clock mode in result string
                False: error in command execution, details in error list string
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if self.__ontType  == "5xx":
            ONTCmdString=":SENS:DATA:TEL:RCL:TX:CLOC:SEL"
            ontSpecificLocalClockParam="CM"     # Local mode string "CM"
        else:
            ONTCmdString=":SOUR:DATA:TEL:PHYS:LINE:CLOC:SEL"
            ontSpecificLocalClockParam="LOCAL"  # Local mode string "LOCAL"
        if portId == "":
            localMessage = "ERROR get_set_clockMode: portId  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        clockMode = clockMode.upper()
        if clockMode != ontSpecificLocalClockParam  and \
           clockMode != "RX" and \
           clockMode != "":
            localMessage = "ERROR get_set_clockMode: clockMode  [{}] not valid [{}|RX|''(to get status)]".format( clockMode,ontSpecificLocalClockParam )
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if clockMode == "":  # Get clockMode and exit
            localCommand="{}?".format(ONTCmdString)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            self.__method_success(methodLocalName, None, sdhAnswer)
            return True, sdhAnswer
        localCommand="{} {}".format(ONTCmdString, clockMode)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        localCommand="{}?".format(ONTCmdString)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        localMessage="Current reference clock source after set:[{}] ".format(sdhAnswer)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, sdhAnswer



    def get_set_rx_measure_channel(self, portId, rxChannel=""):   # ONT-5xx  Only    ### krepo added ###       
        """ ONT-5XX only
            Get or Set measurement channel on RX side:
                1...48  (up to STM-16)
                1...192 (up to STM-65)
            Return tuple: ( "True|False" , "< result/error list>)
                True : command execution ok, current read rxChannel in result string
                False: error in command execution, details in error list string
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if self.__ontType  == "5xx":
            pass
        else:
            localMessage="ERROR get_set_rxChannel: Command supported by ONT-5xx only "
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if portId == "":
            localMessage = "ERROR get_set_rxChannel: rxChannel  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if rxChannel == "":  # Get rxChannel and exit
            localCommand=":SENS:DATA:TEL:SDH:PATH1:CHAN?"
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            self.__method_success(methodLocalName, None, sdhAnswer)
            return True, sdhAnswer
        rxChannelRequired=rxChannel
        channelNumber=int(float(rxChannel))
        if channelNumber < 1 or\
           channelNumber > 192 :
            localMessage = "ERROR get_set_rxChannel: rxChannel  [{}] not in range (1-192)''(to get status)]".format(str(channelNumber))
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        localCommand=":SENS:DATA:TEL:SDH:PATH1:CHAN {}".format(rxChannel)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        localCommand=":SENS:DATA:TEL:SDH:PATH1:CHAN?"
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        if sdhAnswer != rxChannelRequired:
            localMessage="Set RX channel mismatch required [{}] but set [{}] ".format(rxChannelRequired,sdhAnswer)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, sdhAnswer
        localMessage="Set RX channel after set:[{}] ".format(sdhAnswer)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, sdhAnswer



    def get_set_rx_channel_mapping_size(self, portId, channelMapping=""):   # ONT-5xx and ONT-6xx     ### krepo added ###       
        """ ONT-5XX only
            Get or Set RX mapping size used for the measurement channel:
                VC11     Mapping is VC-11.
                VC12     Mapping is VC-12.
                VC2      Mapping is VC-2.
                VC3      Mapping is VC-3.
                VC4      Mapping is VC-4.
                VC4_4C   Mapping is VC-4-4c.
                VC4_16C  Mapping is VC-4-16c.
                VC4_64C  Mapping is VC-4-64c (only available for STM-64 module).
            Return tuple: ( "True|False" , "< result/error list>)
                True : command execution ok, current mapping size set in result string
                False: error in command execution, details in error list string
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)

        if portId == "":
            localMessage = "ERROR get_set_rx_channel_mapping_size: portId  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if self.__ontType  == "5xx":
            ONTCmdString=":SENS:DATA:TEL:SDH:PATH1:MAPP:SIZE"
        else:
            ONTCmdString=":SENS:DATA:TEL:SDH:MAPP:BLOC"
            if channelMapping == "VC2" or channelMapping == "VC11":
                localMessage = "[{}] ERROR get_set_rx_channel_mapping_size: channel Mapping [{}] not supported".format(self.__ontType,channelMapping)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage
        if channelMapping == "":  # Get channel mapping size and exit
            localCommand="{}?".format(ONTCmdString)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            self.__method_success(methodLocalName, None, sdhAnswer)
            return True, sdhAnswer
        channelMappingSizeRequired=channelMapping
        if self.__ontType  == "5xx":  # original ONT-5xx management
            if channelMapping != "VC12"   and \
               channelMapping != "VC3"    and \
               channelMapping != "VC4"    and \
               channelMapping != "VC4_4C" and \
               channelMapping != "VC4_16C"and \
               channelMapping != "VC4_64C" :
                localMessage = "ERROR get_set_rx_channel_mapping_size: channel Mapping size [{}] not valid [VC12|VC3|VC4|VC4_4C|VC4_16C|VC4_64C|''(to get status)]".format(channelMapping)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage
            localCommand="{} {}".format(ONTCmdString, channelMapping)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            localCommand="{}?".format(ONTCmdString)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            if sdhAnswer != channelMappingSizeRequired:
                localMessage="Set RX channel mapping size mismatch: required [{}] but set [{}] ".format(channelMappingSizeRequired,sdhAnswer)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, sdhAnswer
            localMessage="Current RX channel mapping size after set:[{}] ".format(sdhAnswer)
            self.__lc_msg(localMessage)
            self.__method_success(methodLocalName, None, sdhAnswer)
            return True, sdhAnswer
        else:  # ONT-6xx management rework
            callResult = self.__get_set_rx_bit_rate(portId,"")
            channelRate=callResult[1]
            mappingString="-10"
            fillingString=",30000"
            # STM1 management
            if channelRate == "OC3":
                localMessage="STM1 Rate result NOW[{}]".format(channelRate)
                self.__lc_msg(localMessage)
                if channelMapping == "VC12":
                    primerString=",41002,41002,41002"
                elif channelMapping == "VC3":
                    primerString=",41048,41048,41048"
                elif channelMapping == "VC4":
                    primerString=",40003,1,1"
                else:
                    localMessage="ERROR get_set_rx_channel_mapping_size: channel mapping [{}] not supported by STM1 [{}] rate".format(channelMapping,channelRate)
                    self.__lc_msg(localMessage)
                    self.__method_failure(methodLocalName, None, "", localMessage)
                    return False, localMessage
                mappingString+=primerString
                for indeXX in range(1,190):
                    mappingString += fillingString
            # STM4 management
            elif channelRate == "OC12":
                localMessage="STM4 Rate result NOW[{}]".format(channelRate)
                self.__lc_msg(localMessage)
                if channelMapping == "VC12":
                    primerString=",41002,41002,41002,41002,41002,41002,41002,41002,41002,41002,41002,41002"
                elif channelMapping == "VC3":
                    primerString=",41048,41048,41048,41048,41048,41048,41048,41048,41048,41048,41048,41048"
                elif channelMapping == "VC4":
                    primerString=",40003,1,1,40003,1,1,40003,1,1,40003,1,1"
                elif channelMapping == "VC4_4C":
                    primerString=",40012,1,1,1,1,1,1,1,1,1,1,1"
                else:
                    localMessage="ERROR get_set_rx_channel_mapping_size: channel mapping [{}] not supported by STM4 [{}] rate".format(channelMapping,channelRate)
                    self.__lc_msg(localMessage)
                    self.__method_failure(methodLocalName, None, "", localMessage)
                    return False, localMessage
                mappingString+=primerString
                for indeXX in range(1,181):
                    mappingString += fillingString
            # STM16 management
            elif channelRate == "OC48":
                localMessage="STM16 Rate result NOW[{}]".format(channelRate)
                self.__lc_msg(localMessage)
                primerString=""
                if channelMapping == "VC12":
                    for indeXX in range(1,49):
                        primerString +=",41002"
                elif channelMapping == "VC3":
                    for indeXX in range(1,49):
                        primerString +=",41048"
                elif channelMapping == "VC4":
                    for indeXX in range(1,17):
                        primerString +=",40003,1,1"
                elif channelMapping == "VC4_4C":
                    for indeXX in range(1,5):
                        primerString +=",40012,1,1,1,1,1,1,1,1,1,1,1"
                elif channelMapping == "VC4_16C":
                    primerString+=",40048"
                    for indeXX in range(1,48):
                        primerString +=",1"
                else:
                    localMessage="ERROR get_set_rx_channel_mapping_size: channel mapping [{}] not supported by STM16 [{}] rate".format(channelMapping,channelRate)
                    self.__lc_msg(localMessage)
                    self.__method_failure(methodLocalName, None, "", localMessage)
                    return False, localMessage
                mappingString+=primerString
                for indeXX in range(1,145):
                    mappingString += fillingString
            # OC192/STM64 management
            else:
                localMessage="STM64 Rate result NOW[{}]".format(channelRate)
                self.__lc_msg(localMessage)
                primerString=""
                if channelMapping == "VC12":
                    primerString =",41002" * 192
                elif channelMapping == "VC3":
                    primerString =",41048" * 192
                elif channelMapping == "VC4":
                    primerString =",40003,1,1" * 64
                elif channelMapping == "VC4_4C":
                    primerString =",40012,1,1,1,1,1,1,1,1,1,1,1" * 16
                elif channelMapping == "VC4_16C":
                    primerString = (",40048" + ",1"*47)*4
                elif channelMapping == "VC4_64C":
                    primerString =",40192"+",1"*191
                else:
                    localMessage="ERROR get_set_rx_channel_mapping_size: channel mapping [{}] not supported by STM64 [{}] rate".format(channelMapping,channelRate)
                    self.__lc_msg(localMessage)
                    self.__method_failure(methodLocalName, None, "", localMessage)
                    return False, localMessage
                mappingString+=primerString

            #localMessage="PARAM STRING NOW: [{}]  ".format(mappingString)
            #self.__lc_msg(localMessage)
            localCommand="{} {}".format(ONTCmdString, mappingString)    # ADDED -10 mapping version tag
            #self.__lc_msg(localCommand)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            localCommand="{}?".format(ONTCmdString)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])

            if sdhAnswer != mappingString:
                localMessage="[{}] Current RX channel mapping [{}] size mismatch wanted:[{}] but current setting is not correct:[{}] ".format(self.__ontType,channelMapping,mappingString,sdhAnswer)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage

            localMessage="[{}] Current RX channel mapping size after setting [{}] is:[{}] ".format(self.__ontType,channelMapping,sdhAnswer)
            self.__lc_msg(localMessage)
            self.__method_success(methodLocalName, None, localMessage)
            return True, sdhAnswer




    def get_set_alarmed_frames_number(self, portId, alarmedFramesNumber=""):   # ONT-5xx  and ONT-6xx    ### krepo added ###       
        """ ONT-5XX / ONT-6xx
            Get or Set the number of frames, in which alarm insertion is active.:
                1...65536
             Return tuple: ( "True|False" , "< result/error list>)
                True : command execution ok, current read alarmedFramesNumber in result string
                False: error in command execution, details in error list string
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if self.__ontType  == "5xx":
            ONTCmdString=":SOUR:DATA:TEL:ALAR:BURS:ACTI"
        else:
            ONTCmdString=":SOUR:DATA:TEL:SDH:ALAR:BURS:ACTI"
        if portId == "":
            localMessage = "ERROR get_set_alarmed_frames_number: portId  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if alarmedFramesNumber == "":  # Get alarmedFramesNumber and exit
            localCommand="{}?".format(ONTCmdString)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            self.__method_success(methodLocalName, None, sdhAnswer)
            return True, sdhAnswer
        alarmedFramesNumberRequired=alarmedFramesNumber
        almFrNum=int(float(alarmedFramesNumber))
        if almFrNum < 1 or  almFrNum > 65536:
            localMessage = "ERROR get_set_alarmed_frames_number: alarmedFramesNumber  [{}] not in range (1-65536) or use ''(to get status)]".format(str(almFrNum))
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        localCommand="{} {}".format(ONTCmdString, alarmedFramesNumber)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        localCommand="{}?".format(ONTCmdString)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        if sdhAnswer != alarmedFramesNumberRequired:
            localMessage="Set the number of alarmed frames: required [{}] but set [{}]".format(alarmedFramesNumberRequired,sdhAnswer)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, sdhAnswer
        localMessage="Current number of alarmed frames:[{}]".format(sdhAnswer)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, sdhAnswer



    def get_set_not_alarmed_frames_number(self, portId, notAlarmedFramesNumber=""):   # ONT-5xx  and ONT-6xx    ### krepo added ###      
        """ ONT-5XX only / ONT-6xx
            Get or Set the number of frames, in which alarm insertion is inactive.:
                0...65536
             Return tuple: ( "True|False" , "< result/error list>)
                True : command execution ok, current read notAlarmedFramesNumber in result string
                False: error in command execution, details in error list string
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if self.__ontType  == "5xx":
            ONTCmdString=":SOUR:DATA:TEL:ALAR:BURS:INAC"
        else:
            ONTCmdString=":SOUR:DATA:TEL:SDH:ALAR:BURS:INAC"
        if portId == "":
            localMessage = "ERROR get_set_not_alarmed_frames_number: portId  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if notAlarmedFramesNumber == "":  # Get notAlarmedFramesNumber and exit
            localCommand="{}?".format(ONTCmdString)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            self.__method_success(methodLocalName, None, sdhAnswer)
            return True, sdhAnswer
        notAlarmedFramesNumberRequired=notAlarmedFramesNumber
        notAlmFrNum=int(float(notAlarmedFramesNumber))
        if notAlmFrNum < 0 or  notAlmFrNum > 65536:
            localMessage = "ERROR get_set_not_alarmed_frames_number: notAlarmedFramesNumber [{}] not in range (0-65536) or use ''(to get status)]".format(str(notAlmFrNum))
            self.__lc_msg(localMessage)
            return False, localMessage
        localCommand="{} {}".format(ONTCmdString, notAlarmedFramesNumber)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        localCommand="{}?".format(ONTCmdString)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        if sdhAnswer != notAlarmedFramesNumberRequired:
            localMessage="Set the number of alarmed frames: required [{}] but set [{}]".format(notAlarmedFramesNumberRequired,sdhAnswer)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, sdhAnswer
        localMessage="Current number of alarmed frames:[{}]".format(sdhAnswer)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, sdhAnswer



    def get_set_alarm_activation(self, portId, alarmActivation=""):   # ONT-5xx  ONT-6xx    ### krepo added ###       
        """ ONT-5XX  / ONT-6xx
            Get or Set the alarm insertion status:
                ON   Enable Alarms
                OFF  Disable Alarms
            Return tuple: ( "True|False" , "< result/error list>)
                True : command execution ok, current  alarm status in result string
                False: error in command execution, details in error list string
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if self.__ontType  == "5xx":
            ONTCmdString=":SOUR:DATA:TEL:ALAR:INS"
        else:
            ONTCmdString=":SOUR:DATA:TEL:SDH:ALAR:INS"

        if portId == "":
            localMessage = "ERROR get_set_alarmActivation: portId  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        alarmActivation = alarmActivation.upper()
        if alarmActivation != "ON"  and \
           alarmActivation != "OFF" and \
           alarmActivation != "":
            localMessage = "ERROR get_set_alarmActivation: alarmActivation  [{}] not valid [ON|OFF|''(to get status)]".format(alarmActivation)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if alarmActivation == "":  # Get alarmActivation and exit
            localCommand="{}?".format(ONTCmdString)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            self.__method_success(methodLocalName, None, sdhAnswer)
            return True, sdhAnswer
        localCommand="{} {}".format(ONTCmdString, alarmActivation)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        localCommand="{}?".format(ONTCmdString)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        if sdhAnswer != alarmActivation:
            localMessage="Alarms insertion status mismatch: required [{}] but set [{}]".format(alarmActivation,sdhAnswer)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, sdhAnswer
        localMessage="Current alarms insertion status:[{}]".format(sdhAnswer)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, sdhAnswer



    def get_set_alarm_insertion_mode(self, portId, alarmInsertionMode=""):   # ONT-5xx  ONT-6xx    ### krepo added ###       
        """ ONT-5XX ONT-6xx
            Get or Set the alarm insertion mode from:
                NONE No alarm insertion.
                CONT Continous alarm insertion.
                BURST_ONCE  Once insertion of burst alarms as set by
                    :SOUR:DATA:TEL:ALAR:BURS:ACTI
                    :SOUR:DATA:TEL:ALAR:BURS:ACTI:TIME)
                BURST_CONT  Continous insertion of burst alarms as set by
                    :SOUR:DATA:TEL:ALAR:BURS:ACTI
                    :SOUR:DATA:TEL:ALAR:BURS:INAC
                    :SOUR:DATA:TEL:ALAR:BURS:ACTI:TIME
                    :SOUR:DATA:TEL:ALAR:BURS:INAC:TIME
            Return tuple: ( "True|False" , "< result/error list>)
                True : command execution ok, current  alarm insertion mode in result string
                False: error in command execution, details in error list string
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if self.__ontType  == "5xx":
            ONTCmdString=":SOUR:DATA:TEL:ALAR:MODE"
        else:
            ONTCmdString=":SOUR:DATA:TEL:SDH:ALAR:MODE"
        if portId == "":
            localMessage = "ERROR get_set_alarm_insertion_mode: portId  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            return False, localMessage
        alarmInsertionMode = alarmInsertionMode.upper()
        if alarmInsertionMode != "NONE"  and \
           alarmInsertionMode != "CONT" and \
           alarmInsertionMode != "BURST_ONCE" and \
           alarmInsertionMode != "BURST_CONT" and \
           alarmInsertionMode != "":
            localMessage = "ERROR get_set_alarm_insertion_mode: alarmInsertionMode  [{}] not valid [NONE|CONT|BURST_ONCE|BURST_CONT|''(to get status)]".format(alarmInsertionMode)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if alarmInsertionMode == "":  # Get alarmInsertionMode and exit
            localCommand="{}?".format(ONTCmdString)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            self.__method_success(methodLocalName, None, sdhAnswer)
            return True, sdhAnswer
        localCommand="{} {}".format(ONTCmdString, alarmInsertionMode)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        localCommand="{}?".format(ONTCmdString)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        if sdhAnswer != alarmInsertionMode:
            localMessage="Alarms insertion mode mismatch: required [{}] but set [{}]".format(alarmInsertionMode,sdhAnswer)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, sdhAnswer
        localMessage="Current alarms mode :[{}]".format(sdhAnswer)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, sdhAnswer



    def get_set_alarm_insertion_type(self, portId, alarmInsertionType=""):   # ONT-5xx  ONT-6xx   ### krepo added ###      
        """ ONT-5XX   ONT-6xx
            Get or Set the alarm insertion type from:
                LOS     Loss of Signal.
                LOF     Loss Of Frame.
                RSTIM   Section Trace Identifier
                MSAIS   Line Alarm Indication Signal.
                MSRDI   Line Remote Defect Indication.
                AUAIS   AU Path Alarm Indication Signal.
                HPRDI   AU Path Remote Defect Indication.
                AULOP   AU Path Loss Of Pointer.
                HPUNEQ  AU Path Unequipped.
                HPTIM   AU Path Trace Identifier Mismatch.
                HPPLM   AU Path Payload Label Mismatch.
                TULOM   Loss of Multiframe
                TUAIS   TU Path Alarm Indication Signal.
                LPRDI   TU Path Remote Defect Indication.
                LPRFI   TU Path Remote Failure Indication.
                TULOP   TU Path Loss of Pointer.
                LPTIM   TU Path Trace Identifier Mismatch.
                LPPLM   TU Path Payload Label Mismatch.
                LPUNEQ  TU Path Unequipped.
            Return tuple: ( "True|False" , "< result/error list>)
                True : command execution ok, current  alarm insertion type in result string
                False: error in command execution, details in error list string
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if portId == "":
            localMessage = "ERROR get_set_alarm_insertion_type: portId  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        alarmInsertionType = alarmInsertionType.upper()
        if self.__ontType  == "5xx":
            ONTCmdString=":SOUR:DATA:TEL:ALAR:TYPE"
            if alarmInsertionType != "LOS" and \
               alarmInsertionType != "LOF" and \
               alarmInsertionType != "RSTIM" and \
               alarmInsertionType != "MSAIS" and \
               alarmInsertionType != "MSRDI" and \
               alarmInsertionType != "AUAIS" and \
               alarmInsertionType != "HPRDI" and \
               alarmInsertionType != "AULOP" and \
               alarmInsertionType != "HPUNEQ" and \
               alarmInsertionType != "HPTIM" and \
               alarmInsertionType != "HPPLM" and \
               alarmInsertionType != "TULOM" and \
               alarmInsertionType != "TUAIS" and \
               alarmInsertionType != "LPRDI" and \
               alarmInsertionType != "LPRFI" and \
               alarmInsertionType != "TULOP" and \
               alarmInsertionType != "LPTIM" and \
               alarmInsertionType != "LPPLM" and \
               alarmInsertionType != "LPUNEQ" and \
               alarmInsertionType != "":
                localMessage = "[5xx] ERROR get_set_alarm_insertion_type: alarmInsertionType  [{}] not valid [LOS|LOF|RSTIM|MSAIS|MSRDI|AUAIS|HPRDI|AULOP|HPUNEQ|HPTIM|HPPLM|TULOM|TUAIS|LPRDI|LPRFI|TULOP|LPTIM|LPPLM|LPUNEQ|''(to get status)]".format(alarmInsertionType)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage
        else:
            ONTCmdString=":SOUR:DATA:TEL:SDH:ALAR:TYPE"
            if alarmInsertionType != "LOF" and \
               alarmInsertionType != "RSTIM" and \
               alarmInsertionType != "MSAIS" and \
               alarmInsertionType != "MSRDI" and \
               alarmInsertionType != "AUAIS" and \
               alarmInsertionType != "AULOP" and \
               alarmInsertionType != "HPUNEQ" and \
               alarmInsertionType != "HPTIM" and \
               alarmInsertionType != "HPPLM" and \
               alarmInsertionType != "HPRDI" and \
               alarmInsertionType != "HPRDIC" and \
               alarmInsertionType != "HPRDIS" and \
               alarmInsertionType != "HPRDIP" and \
                alarmInsertionType != "":
                localMessage = "[6xx] ERROR get_set_alarm_insertion_type: alarmInsertionType  [{}] not valid [LOF|RSTIM|MSAIS|MSRDI|AUAIS|AULOP|HPUNEQ|HPTIM|HPPLM|HPRDI|HPRDIC|HPRDIS|HPRDIP|''(to get status)]".format(alarmInsertionType)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage

        if alarmInsertionType == "":  # Get alarmInsertionType and exit
            localCommand="{}?".format(ONTCmdString)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            self.__method_success(methodLocalName, None, sdhAnswer)
            return True, sdhAnswer
        localCommand="{} {}".format(ONTCmdString, alarmInsertionType)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        localCommand="{}?".format(ONTCmdString)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        if sdhAnswer != alarmInsertionType:
            localMessage="Alarms insertion type mismatch: required [{}] but set [{}]".format(alarmInsertionType,sdhAnswer)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, sdhAnswer
        localMessage="Current alarms type :[{}]".format(sdhAnswer)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, sdhAnswer


    def get_set_num_errored_burst_frames(self, portId, burstErroredFramesNumber=""):   # ONT-5xx  ONT-6xx   ### krepo added ###      
        """ ONT-5xx  ONT-6xx
            Get or Set number of frames, in which error insertion is active:
            is the duration of error insertion is burstErroredFramesNumber frames.
                1...65536
             Return tuple: ( "True|False" , "< result/error list>)
                True : command execution ok, current read burstErroredFramesNumber in result string
                False: error in command execution, details in error list string
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if self.__ontType  == "5xx":
            ONTCmdString=":SOUR:DATA:TEL:ERR:BURS:ACTI"
        else:
            ONTCmdString=":SOUR:DATA:TEL:SDH:ERR:BURS:ACTI"
        if portId == "":
            localMessage = "ERROR get_set_num_errored_burst_frames: portId  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if burstErroredFramesNumber == "":  # Get burstErroredFramesNumber and exit
            localCommand="{}?".format(ONTCmdString)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            self.__method_success(methodLocalName, None, sdhAnswer)
            return True, sdhAnswer
        burstErroredFramesNumberRequired=burstErroredFramesNumber
        notAlmFrNum=int(float(burstErroredFramesNumber))
        if notAlmFrNum < 1 or  notAlmFrNum > 65536:
            localMessage = "ERROR get_set_num_errored_burst_frames: burstErroredFramesNumber [{}] not in range (1-65536) or use ''(to get status)]".format(str(notAlmFrNum))
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        localCommand="{} {}".format(ONTCmdString, burstErroredFramesNumber)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        localCommand="{}?".format(ONTCmdString)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        if sdhAnswer != burstErroredFramesNumberRequired:
            localMessage="Set the number of errored burst frames: required [{}] but set [{}]".format(burstErroredFramesNumberRequired,sdhAnswer)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, sdhAnswer
        localMessage="Current number of errored burst frames:[{}]".format(sdhAnswer)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, sdhAnswer


    def get_set_num_not_errored_burst_frames(self, portId, burstNotErroredFramesNumber=""):   # ONT-5xx  ONT-6xx   ### krepo added ###       
        """ ONT-5xx  ONT-6xx
            Get or Set number of frames, in which error insertion is inactive:
            is the duration of inactive error insertion is burstNotErroredFramesNumber frames.
                0...65536
             Return tuple: ( "True|False" , "< result/error list>)
                True : command execution ok, current read burstNotErroredFramesNumber in result string
                False: error in command execution, details in error list string
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if self.__ontType  == "5xx":
            ONTCmdString=":SOUR:DATA:TEL:ERR:BURS:INAC"
        else:
            ONTCmdString=":SOUR:DATA:TEL:SDH:ERR:BURS:INAC"
        if portId == "":
            localMessage = "ERROR get_set_num_not_errored_burst_frames: portId  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if burstNotErroredFramesNumber == "":  # Get burstNotErroredFramesNumber and exit
            localCommand="{}?".format(ONTCmdString)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            self.__method_success(methodLocalName, None, sdhAnswer)
            return True, sdhAnswer
        burstNotErroredFramesNumberRequired=burstNotErroredFramesNumber
        notAlmFrNum=int(float(burstNotErroredFramesNumber))
        if notAlmFrNum < 0 or  notAlmFrNum > 65536:
            localMessage = "ERROR get_set_num_not_errored_burst_frames: burstNotErroredFramesNumber [{}] not in range (0-65536) or use ''(to get status)]".format(str(notAlmFrNum))
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        localCommand="{} {}".format(ONTCmdString, burstNotErroredFramesNumber)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        localCommand="{}?".format(ONTCmdString)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        if sdhAnswer != burstNotErroredFramesNumberRequired:
            localMessage="Set the number of not errored burst frames: required [{}] but set [{}]".format(burstNotErroredFramesNumberRequired,sdhAnswer)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, sdhAnswer
        localMessage="Current number of not errored burst frames:[{}]".format(sdhAnswer)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, sdhAnswer



    def get_set_error_activation(self, portId, errorActivation=""):   # ONT-5xx  ONT-6xx   ### krepo added ###       
        """ ONT-5xx  ONT-6xx
            Get or Set the error insertion status:
                ON   Activate Error Insertion
                OFF  Deactivate Error Insertion
            Return tuple: ( "True|False" , "< result/error list>)
                True : command execution ok, current  alarm status in result string
                False: error in command execution, details in error list string
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if self.__ontType  == "5xx":
            ONTCmdString=":SOUR:DATA:TEL:ERR:INS"  # ONT original command string put here
        else:
            ONTCmdString=":SOUR:DATA:TEL:SDH:ERR:INS"  # ONT original command string put here
        if portId == "":
            localMessage = "ERROR get_set_error_activation: portId  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        errorActivation = errorActivation.upper()
        if errorActivation != "ON"  and \
           errorActivation != "OFF" and \
           errorActivation != "":
            localMessage = "ERROR get_set_error_activation: errorActivation  [{}] not valid [ON|OFF|''(to get status)]".format(errorActivation)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if errorActivation == "":  # Get errorActivation and exit
            localCommand="{}?".format(ONTCmdString)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            self.__method_success(methodLocalName, None, sdhAnswer)
            return True, sdhAnswer
        localCommand="{} {}".format(ONTCmdString, errorActivation)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        localCommand="{}?".format(ONTCmdString)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        if sdhAnswer != errorActivation:
            localMessage="Error insertion status mismatch: required [{}] but set [{}]".format(errorActivation,sdhAnswer)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, sdhAnswer
        localMessage="Current error insertion status:[{}]".format(sdhAnswer)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, sdhAnswer



    def get_set_error_insertion_mode(self, portId, errorInsertionMode=""):   # ONT-5xx  ONT-6xx    ### krepo added ###       
        """ ONT-5XX ONT-6xx
            Get or Set the error insertion mode from:
                NONE            No error insertion..
                ONCE            Insertion of a single error.
                RATE            Error rate as set by
                                :SOUR:DATA:TEL:ERR:RATE
                BURST_ONCE      Once insertion of burst errors as set by
                                :SOUR:DATA:TEL:ERR:BURS:ACTI or
                                :SOUR:DATA:TEL:ERR:BURS:ACTI:TIME
                BURST_CONT      Continous insertion of burst errors as set by
                                :SOUR:DATA:TEL:ERR:BURS:ACTI
                                :SOUR:DATA:TEL:ERR:BURS:INAC
                                :SOUR:DATA:TEL:ERR:BURS:ACTI:TIME
                                :SOUR:DATA:TEL:ERR:BURS:INAC:TIME
                RATE_BURST_ONCE Once insertion of errored rate as set by
                                :SOUR:DATA:TEL:ERR:BURS:ACTI
                                :SOUR:DATA:TEL:ERR:BURS:ACTI:TIME
                RATE_BURST_CONT Continous insertion of errored rate as set by
                                :SOUR:DATA:TEL:ERR:BURS:ACTI
                                :SOUR:DATA:TEL:ERR:BURS:INAC
                                :SOUR:DATA:TEL:ERR:BURS:ACTI:TIME
                                :SOUR:DATA:TEL:ERR:BURS:INAC:TIME
            Return tuple: ( "True|False" , "< result/error list>)
                True : command execution ok, current  error insertion mode in result string
                False: error in command execution, details in error list string
       """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if self.__ontType  == "5xx":
            ONTCmdString=":SOUR:DATA:TEL:ERR:MODE"
        else:
            ONTCmdString=":SOUR:DATA:TEL:SDH:ERR:MODE"
        if portId == "":
            localMessage = "ERROR get_set_error_insertion_mode: portId  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        errorInsertionMode = errorInsertionMode.upper()
        if errorInsertionMode != "NONE" and \
           errorInsertionMode != "ONCE" and \
           errorInsertionMode != "RATE" and \
           errorInsertionMode != "BURST_ONCE" and \
           errorInsertionMode != "BURST_CONT" and \
           errorInsertionMode != "RATE_BURST_ONCE" and \
           errorInsertionMode != "RATE_BURST_CONT" and \
           errorInsertionMode != "":
            localMessage = "ERROR get_set_error_insertion_mode: errorInsertionMode  [{}] not valid [NONE|ONCE|RATE|BURST_ONCE|BURST_CONT|RATE_BURST_ONCE|RATE_BURST_CONT|''(to get status)]".format(errorInsertionMode)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if errorInsertionMode == "":  # Get errorInsertionMode and exit
            localCommand="{}?".format(ONTCmdString)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            self.__method_success(methodLocalName, None, sdhAnswer)
            return True, sdhAnswer
        localCommand="{} {}".format(ONTCmdString, errorInsertionMode)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        localCommand="{}?".format(ONTCmdString)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        if sdhAnswer != errorInsertionMode:
            localMessage="Alarms insertion mode mismatch: required [{}] but set[{}]".format(errorInsertionMode,sdhAnswer)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, sdhAnswer
        localMessage="Current alarms mode :[{}]".format(sdhAnswer)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, sdhAnswer



    def get_set_error_rate(self, portId, errorRate=""):   # ONT-5xx  ONT-6xx    ### krepo added ###       
        """ ONT-5XX ONT-6xx
            Get or Set number of frames, in which error insertion is active:
            is the duration of error insertion is errorRate frames.
                1E-10...0.01
             Return tuple: ( "True|False" , "< result/error list>)
                True : command execution ok, current read errorRate in result string
                False: error in command execution, details in error list string
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if self.__ontType  == "5xx":
            ONTCmdString=":SOUR:DATA:TEL:ERR:RATE"
        else:
            ONTCmdString=":SOUR:DATA:TEL:SDH:ERR:RATE"
        if portId == "":
            localMessage = "ERROR get_set_error_rate: portId  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if errorRate == "":  # Get errorRate and exit
            localCommand="{}?".format(ONTCmdString)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            self.__method_success(methodLocalName, None, sdhAnswer)
            return True, sdhAnswer
        errorRateRequired=errorRate
        #myErrorRate=float(errorRate)
        #self.__lc_msg(errorRate)
        #self.__lc_msg(str(myErrorRate))
        # INSERT (IF POSSIBLE) CONTROLS ON ERROR RATE (!!! the instrument rounds with internal rulse, so it's difficult...)
        #if myErrorRate < 1 or  myErrorRate > 65536:
        #    localMessage = "ERROR get_set_error_rate: errorRate [{}] not in range (1-65536) or use ''(to get status)]".format(str(myErrorRate))
        #    self.__lc_msg(localMessage)
        #    return False, localMessage
        localCommand="{} {}".format(ONTCmdString, errorRate)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        localCommand="{}?".format(ONTCmdString)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        #sdhAnswer = float(self.__remove_dust(rawCallResult[1]))
        #if sdhAnswer != errorRateRequired:
        #    localMessage="Set the number of alarmed burst frames: required [{}] but set [{}]".format(errorRateRequired,sdhAnswer)
        #    self.__lc_msg(localMessage)
        #    return False, sdhAnswer
        localMessage="Current number of alarmed burst frames:[{}]".format(sdhAnswer)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, sdhAnswer



    def get_set_error_insertion_type(self, portId, errorInsertionType=""):   # ONT-5xx ONT-6xx    ### krepo added ###      
        """ ONT-5XX  ONT-6xx
            Get or Set the error insertion type from:
                LOGIC  Pattern Bit Error.
                RAND   Random Error.
                FAS    FAS Error.
                RSBIP  RS-BIP error.
                MSBIP  MS-BIP error.
                MSREI  MS-REI error.
                HPBIP  HP-BIP error.
                HPREI  HP-REI error.
                LPBIP  LP-BIP error.
                LPREI  LP-REI error.
            Return tuple: ( "True|False" , "< result/error list>)
                True : command execution ok, current  alarm insertion type in result string
                False: error in command execution, details in error list string
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if portId == "":
            localMessage = "ERROR get_set_error_insertion_type: portId  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        errorInsertionType = errorInsertionType.upper()
        if self.__ontType  == "5xx":
            ONTCmdString=":SOUR:DATA:TEL:ERR:TYPE"
            if errorInsertionType != "LOGIC" and \
               errorInsertionType != "RAND" and \
               errorInsertionType != "FAS" and \
               errorInsertionType != "RSBIP" and \
               errorInsertionType != "MSBIP" and \
               errorInsertionType != "MSREI" and \
               errorInsertionType != "HPBIP" and \
               errorInsertionType != "HPREI" and \
               errorInsertionType != "LPBIP" and \
               errorInsertionType != "LPREI" and \
               errorInsertionType != "":
                localMessage = "[5xx] ERROR get_set_error_insertion_type: errorInsertionType  [{}] not valid [LOGIC|RAND|FAS|RSBIP|MSBIP|MSREI|HPBIP|HPREI|LPBIP|LPREI|''(to get status)]".format(errorInsertionType)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage
        else:
            ONTCmdString=":SOUR:DATA:TEL:SDH:ERR:TYPE"
            if errorInsertionType != "RAND" and \
               errorInsertionType != "FAS" and \
               errorInsertionType != "RSBIP" and \
               errorInsertionType != "MSBIP" and \
               errorInsertionType != "MSREI" and \
               errorInsertionType != "HPBIP" and \
               errorInsertionType != "HPREI" and \
               errorInsertionType != "":
                localMessage = "[6xx] ERROR get_set_error_insertion_type: errorInsertionType  [{}] not valid [RAND|FAS|RSBIP|MSBIP|MSREI|HPBIP|HPREI|''(to get status)]".format(errorInsertionType)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage

        if errorInsertionType == "":  # Get errorInsertionType and exit
            localCommand="{}?".format(ONTCmdString)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            self.__method_success(methodLocalName, None, localMessage)
            return True, sdhAnswer
        localCommand="{} {}".format(ONTCmdString, errorInsertionType)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        localCommand="{}?".format(ONTCmdString)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        if sdhAnswer != errorInsertionType:
            localMessage="Errors insertion type mismatch: required [{}] but set [{}]".format(errorInsertionType,sdhAnswer)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, sdhAnswer
        localMessage="Current alarms type :[{}]".format(sdhAnswer)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, sdhAnswer



    def get_set_tx_bit_rate(self, portId, bitRate=""):   # ONT-5XX and ONT-6XX    ### krepo added ###    
        """ ONT-5XX and ONT-6XX
            Get or Set the current TX bitRate from:
                STM0  Bit rate is 55.84 Mbit/s.
                STM1  Bit rate is 155.52 Mbit/s. (for OC-1/3/12/48 / STM-0/1/4/16 module)
                STM4  Bit rate is 622.08 Mbit/s.
                STM16 Bit rate is 2488.32 Mbit/s.
                STM64 Bit rate is 9953.28 Mbit/s (only available for OC-192/STM-64 modules).
            Return tuple: ( "True|False" , "< result/error list>)
                True : command execution ok, current read bitRate in result string
                False: error in command execution, details in error list string
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if self.__ontType  == "5xx":
            ONTCmdString=":SOUR:DATA:TEL:OPT:RATE"
        else:
            ONTCmdString=":SOUR:DATA:TEL:PHYS:LINE:RATE"
        if portId == "":
            localMessage = "ERROR get_set_tx_bit_rate: portId  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        bitRate = bitRate.upper()
        if bitRate != "STM0"  and \
           bitRate != "STM1"  and \
           bitRate != "STM4"  and \
           bitRate != "STM16" and \
           bitRate != "STM64" and \
           bitRate != "":
            localMessage = "ERROR get_set_tx_bit_rate: bitRate  [{}] not valid [STM0|STM1|STM4|STM16|STM64|''(to get status)]".format(bitRate)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if bitRate == "":  # Get laser bitRate and exit
            localCommand="{}?".format(ONTCmdString)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            self.__method_success(methodLocalName, None, sdhAnswer)
            return True, sdhAnswer
        if self.__ontType  != "5xx": # for 6xx we need to use OCs instead of STMs
            localMessage="[6xx]: [{}] translated to [{}]".format(bitRate,self.StmToOc[bitRate])
            self.__lc_msg(localMessage)
            bitRate = self.StmToOc[bitRate]
        txBitRateRequired = bitRate
        localCommand="{} {}".format(ONTCmdString, bitRate)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        localCommand="{}?".format(ONTCmdString)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        if sdhAnswer != txBitRateRequired:
            localMessage="Set TX bitRate mismatch required [{}] but set [{}] ".format(txBitRateRequired,sdhAnswer)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, sdhAnswer
        localMessage="Set TX bitRate required=[{}] after set=[{}] ".format(txBitRateRequired,sdhAnswer)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, sdhAnswer



    def get_set_tx_measure_channel(self, portId, txChannel=""):   # ONT-5xx  Only    ### krepo added ###       
        """ ONT-5XX only
            Get or Set measurement channel on TX side:
                1...48  (up to STM-16)
                1...192 (up to STM-65)
            Return tuple: ( "True|False" , "< result/error list>)
                True : command execution ok, current read txChannel in result string
                False: error in command execution, details in error list string
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        ONTCmdString=":SOUR:DATA:TEL:SDH:PATH1:CHAN"  # ONT original command string put here
        if self.__ontType  == "5xx":
            pass
        else:
            localMessage="ERROR get_set_tx_measure_channel: Command supported by ONT-5xx only "
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if portId == "":
            localMessage = "ERROR get_set_tx_measure_channel: txChannel  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if txChannel == "":  # Get txChannel and exit
            localCommand="{}?".format(ONTCmdString)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            self.__method_success(methodLocalName, None, sdhAnswer)
            return True, sdhAnswer
        txChannelRequired=txChannel
        channelNumber=int(float(txChannel))
        if channelNumber < 1 or channelNumber > 192 :
            localMessage = "ERROR get_set_tx_measure_channel: txChannel  [{}] not in range (1-192)''(to get status)]".format(str(channelNumber))
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        localCommand="{} {}".format(ONTCmdString, txChannel)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        localCommand="{}?".format(ONTCmdString)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        if sdhAnswer != txChannelRequired:
            localMessage="Set TX measure channel mismatch required [{}] but set [{}] ".format(txChannelRequired,sdhAnswer)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, sdhAnswer
        localMessage="Set TX measure channel after set:[{}] ".format(sdhAnswer)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, sdhAnswer



    def get_set_tx_channel_mapping_size(self, portId, channelMapping=""):     # ONT-5XX and ONT-6XX    ### krepo added ###    
        """ ONT-5XX only
            Get or Set TX mapping size used for the measurement channel:
                VC11     Mapping is VC-11.
                VC12     Mapping is VC-12.
                VC2      Mapping is VC-2.
                VC3      Mapping is VC-3.
                VC4      Mapping is VC-4.
                VC4_4C   Mapping is VC-4-4c.
                VC4_16C  Mapping is VC-4-16c.
                VC4_64C  Mapping is VC-4-64c (only available for STM-64 module).
            Return tuple: ( "True|False" , "< result/error list>)
                True : command execution ok, current mapping size set in result string
                False: error in command execution, details in error list string
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if portId == "":
            localMessage = "ERROR get_set_tx_channel_mapping_size: portId  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            return False, localMessage
        if self.__ontType  == "5xx":
            ONTCmdString=":SOUR:DATA:TEL:SDH:PATH1:MAPP:SIZE"
        else:
            ONTCmdString=":SOUR:DATA:TEL:SDH:SEL:MAPP:SIZE"
            if channelMapping == "VC2":
                localMessage = "[{}] ERROR get_set_tx_channel_mapping_size: channel Mapping [{}] not supported".format(self.__ontType,channelMapping)
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage

        if channelMapping == "":  # Get channel mapping size and exit
            localCommand="{}?".format(ONTCmdString)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            self.__method_success(methodLocalName, None, sdhAnswer)
            return True, sdhAnswer
        if channelMapping != "VC11"   and \
           channelMapping != "VC12"   and \
           channelMapping != "VC2"    and \
           channelMapping != "VC3"    and \
           channelMapping != "VC4"    and \
           channelMapping != "VC4_4C" and \
           channelMapping != "VC4_16C"and \
           channelMapping != "VC4_64C" :
            localMessage = "ERROR get_set_tx_channel_mapping_size: channel Mapping size [{}] not valid [VC11|VC12|VC2|VC3|VC4|VC4_4C|VC4_16C|VC4_64C|''(to get status)]".format(channelMapping)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage

        if self.__ontType  == "6xx": # for 6xx we need to use AUs instead of VCs
            localMessage="[6xx]: get_set_tx_channel_mapping_size [{}] translated to [{}]".format(channelMapping,self.VcToAu[channelMapping])
            self.__lc_msg(localMessage)
            channelMapping = self.VcToAu[channelMapping]

        channelMappingSizeRequired=channelMapping
        localCommand="{} {}".format(ONTCmdString, channelMapping)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        localCommand="{}?".format(ONTCmdString)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        if sdhAnswer != channelMappingSizeRequired:
            localMessage="Set TX channel mapping size mismatch: required [{}] but set [{}] ".format(channelMappingSizeRequired,sdhAnswer)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, sdhAnswer
        localMessage="Current TX channel mapping size after [{}]set:[{}] ".format(channelMapping,sdhAnswer)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, sdhAnswer



    def get_set_tx_lo_measure_channel(self, portId, txLoChannel=""):   # ONT-5xx  ONT-6xx    ### krepo added ###      
        """ ONT-5XX  ONT-6xx

            !!! BE CARE: parameter format mismatch 5xx vs 6xx  !!!

            Get or Set Lower Order measurement channel on TX side:
                1...84  (5xx) / "a.b.c.d" for 6xx
             Return tuple: ( "True|False" , "< result/error list>)
                True : command execution ok, current read txLoChannel in result string
                False: error in command execution, details in error list string
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if self.__ontType  == "5xx":
            ONTCmdString=":SOUR:DATA:TEL:SDH:TRIB:PATH1:CHAN"
        else:
            ONTCmdString=":SOUR:DATA:TEL:SDH:SEL:CHAN"
        if portId == "":
            localMessage = "ERROR get_set_tx_lo_measure_channel: txLoChannel  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if txLoChannel == "":  # Get txLoChannel and exit
            localCommand="{}?".format(ONTCmdString)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            self.__method_success(methodLocalName, None, sdhAnswer)
            return True, sdhAnswer
        txLoChannelRequired=txLoChannel
        #self.__lc_msg(txLoChannel)
        #self.__lc_msg(str(loChannelNumber))
        if self.__ontType  == "5xx":
            loChannelNumber=int(float(txLoChannel))
            if loChannelNumber < 1 or\
               loChannelNumber > 84 :
                localMessage = "ERROR get_set_tx_lo_measure_channel: txLoChannel  [{}] not in range (1-84) or use ''(to get status)]".format(str(loChannelNumber))
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage
        else:  # wrap string inside "" as the cmd required it...
            txLoChannel="\"{}\"".format(txLoChannel)
            txLoChannelRequired=txLoChannel

        localCommand="{} {}".format(ONTCmdString, txLoChannel)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        localCommand="{}?".format(ONTCmdString)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        if sdhAnswer != txLoChannelRequired:
            localMessage="Set Lower Order TX channel mismatch: required [{}] but set [{}] ".format(txLoChannelRequired,sdhAnswer)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, sdhAnswer
        localMessage="Current Lower Order TX channel after set:[{}] ".format(sdhAnswer)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, sdhAnswer



    def get_set_rx_lo_measure_channel(self, portId, rxLoChannel=""):   # ONT-5xx  ONT-6xx    ### krepo added ###    
        """ ONT-5XX ONT-6xx

            !!! BE CARE: parameter format mismatch 5xx vs 6xx  !!!

            Get or Set Lower Order measurement channel on RX side:
                1...84  (5xx) / "a.b.c.d" for 6xx

             Return tuple: ( "True|False" , "< result/error list>)
                True : command execution ok, current read rxLoChannel in result string
                False: error in command execution, details in error list string
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if self.__ontType  == "5xx":
            ONTCmdString=":SENS:DATA:TEL:SDH:TRIB:PATH1:CHAN"
        else:
            ONTCmdString=":SENS:DATA:TEL:SDH:SEL:CHAN"
        if portId == "":
            localMessage = "ERROR get_set_rxLoChannel: rxLoChannel  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if rxLoChannel == "":  # Get rxLoChannel and exit
            localCommand="{}?".format(ONTCmdString)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            self.__method_success(methodLocalName, None, sdhAnswer)
            return True, sdhAnswer
        rxLoChannelRequired=rxLoChannel
        if self.__ontType  == "5xx":
            loChannelNumber=int(float(rxLoChannel))
            if loChannelNumber < 1 or\
               loChannelNumber > 84 :
                localMessage = "ERROR get_set_rxLoChannel: rxLoChannel  [{}] not in range (1-84) or use ''(to get status)]".format(str(loChannelNumber))
                self.__lc_msg(localMessage)
                self.__method_failure(methodLocalName, None, "", localMessage)
                return False, localMessage
        else:  # wrap string inside "" as the cmd required it...
            rxLoChannel="\"{}\"".format(rxLoChannel)
            rxLoChannelRequired=rxLoChannel

        localCommand="{} {}".format(ONTCmdString, rxLoChannel)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        localCommand="{}?".format(ONTCmdString)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        if sdhAnswer != rxLoChannelRequired:
            localMessage="Set Lower Order RX channel mismatch: required [{}] but set [{}] ".format(rxLoChannelRequired ,sdhAnswer)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, sdhAnswer
        localMessage="Current Lower Order RX channel after set:[{}] ".format(sdhAnswer)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, sdhAnswer



    def get_set_background_channels_fill_mode(self, portId, backgroundMode=""):   # ONT-6xx only    ### krepo added ###      
        """ ONT-6xx only
            Get or Set the alarm insertion status:
                COPY   Mapping size of background is equivalent to foreground chhannel
                FIX    User defined backgroud
            Return tuple: ( "True|False" , "< result/error list>)
                True : command execution ok, current  alarm status in result string
                False: error in command execution, details in error list string
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if self.__ontType  == "6xx":
            ONTCmdString=":SOUR:DATA:TEL:SDH:BCH:MODE"
        else:
            localMessage="Command supported by ONT-6xx only (current test equipment type:[{}]) ".format(self.__ontType)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage

        if portId == "":
            localMessage = "ERROR get_set_background_channels_fill_mode: portId  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        backgroundMode = backgroundMode.upper()
        if backgroundMode != "COPY"  and \
           backgroundMode != "FIX" and \
           backgroundMode != "":
            localMessage = "ERROR get_set_background_channels_fill_mode: backgroundMode  [{}] not valid [COPY|FIX|''(to get status)]".format(backgroundMode)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if backgroundMode == "":  # Get backgroundMode and exit
            localCommand="{}?".format(ONTCmdString)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            self.__method_success(methodLocalName, None, sdhAnswer)
            return True, sdhAnswer
        localCommand="{} {}".format(ONTCmdString, backgroundMode)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        localCommand="{}?".format(ONTCmdString)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        if sdhAnswer != backgroundMode:
            localMessage="Background mode selection mismatch: required [{}] but set [{}]".format(backgroundMode,sdhAnswer)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, sdhAnswer
        localMessage="Current background mode selection:[{}]".format(sdhAnswer)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, sdhAnswer



    def get_set_tx_au_path_J1_trace_mode(self, portId, sequenceInJ1Byte=""):   # ONT-6xx only    ### krepo added ###       
        """ ONT-6xx only
            Get or Set the Tx Au Path Trace Mode of the background channel il J1 byte:
                OFF    No sequence sent in J1
                TRC16  A 16 byte long sequence is sent in J1 byte
                TRC64  A 64 byte long sequence is sent in J1 byte
            Return tuple: ( "True|False" , "< result/error list>)
                True : command execution ok, current  alarm status in result string
                False: error in command execution, details in error list string
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if self.__ontType  == "6xx":
            ONTCmdString=":SOUR:DATA:TEL:SDH:BCH:PATH:J1TR:MODE"
        else:
            localMessage="Command supported by ONT-6xx only (current test equipment type:[{}]) ".format(self.__ontType)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if portId == "":
            localMessage = "ERROR get_set_tx_au_path_J1_trace_mode: portId  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        sequenceInJ1Byte = sequenceInJ1Byte.upper()
        if sequenceInJ1Byte != "OFF"  and \
           sequenceInJ1Byte != "TRC16" and \
           sequenceInJ1Byte != "TRC64" and \
           sequenceInJ1Byte != "":
            localMessage = "ERROR get_set_tx_au_path_J1_trace_mode: sequenceInJ1Byte  [{}] not valid [OFF|TRC16|TRC64|''(to get status)]".format(sequenceInJ1Byte)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if sequenceInJ1Byte == "":  # Get sequenceInJ1Byte and exit
            localCommand="{}?".format(ONTCmdString)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            self.__method_success(methodLocalName, None, sdhAnswer)
            return True, sdhAnswer
        localCommand="{} {}".format(ONTCmdString, sequenceInJ1Byte)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        localCommand="{}?".format(ONTCmdString)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        if sdhAnswer != sequenceInJ1Byte:
            localMessage="Tx AU Path J1 Trace Mode mismatch: required [{}] but set [{}]".format(sequenceInJ1Byte,sdhAnswer)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, sdhAnswer
        localMessage="Tx AU Path J1 Trace Mode selection:[{}]".format(sdhAnswer)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, sdhAnswer



    def get_set_au_path_trace_rx_channel(self, portId, auPathTraceMode=""):   # ONT-6xx only    ### krepo added ###       
        """ ONT-6xx only
            Get or Set the Au Path Trace Mode of the selected RX channel in J1 byte:
                OFF     No sequence expected in J1
                AUTO16  An auto generated 16 byte long sequence
                AUTO64  An auto generated 64 byte long sequence
                TRC16   A 16 byte long sequence is expected in J1 byte
                TRC64   A 64 byte long sequence is expected in J1 byte
            Return tuple: ( "True|False" , "< result/error list>)
                True : command execution ok, current  alarm status in result string
                False: error in command execution, details in error list string
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if self.__ontType  == "6xx":
            ONTCmdString=":SENS:DATA:TEL:SDH:PATH:SEL:J1TR:MODE"
        else:
            localMessage="Command supported by ONT-6xx only (current test equipment type:[{}]) ".format(self.__ontType)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage

        if portId == "":
            localMessage = "ERROR get_set_au_path_trace_rx_channel: portId  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        auPathTraceMode = auPathTraceMode.upper()
        if auPathTraceMode != "OFF"  and \
           auPathTraceMode != "AUTO16" and \
           auPathTraceMode != "AUTO64" and \
           auPathTraceMode != "TRC16" and \
           auPathTraceMode != "TRC64" and \
           auPathTraceMode != "":
            localMessage = "ERROR get_set_au_path_trace_rx_channel: auPathTraceMode  [{}] not valid [OFF|AUTO16|AUTO64|TRC16|TRC64|''(to get status)]".format(auPathTraceMode)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if auPathTraceMode == "":  # Get auPathTraceMode and exit
            localCommand="{}?".format(ONTCmdString)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            self.__method_success(methodLocalName, None, sdhAnswer)
            return True, sdhAnswer
        localCommand="{} {}".format(ONTCmdString, auPathTraceMode)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        localCommand="{}?".format(ONTCmdString)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        if sdhAnswer != auPathTraceMode:
            localMessage="Rx AU Path Trace Mode mismatch: required [{}] but set [{}]".format(auPathTraceMode,sdhAnswer)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, sdhAnswer
        localMessage="Rx AU Path Trace Mode selection:[{}]".format(sdhAnswer)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, sdhAnswer



    def get_set_au_path_trace_tx_channel(self, portId, auPathTraceMode=""):   # ONT-6xx only    ### krepo added ###      
        """ ONT-6xx only
            Get or Set the Au Path Trace Mode of the selected TX channel in J1 byte:
                OFF     No sequence sent in J1
                AUTO16  An auto generated 16 byte long sequence
                AUTO64  An auto generated 64 byte long sequence
                TRC16   A 16 byte long sequence is sent in J1 byte
                TRC64   A 64 byte long sequence is sent in J1 byte
            Return tuple: ( "True|False" , "< result/error list>)
                True : command execution ok, current  alarm status in result string
                False: error in command execution, details in error list string
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if self.__ontType  == "6xx":
            ONTCmdString=":SOUR:DATA:TEL:SDH:PATH:SEL:J1TR:MODE"
        else:
            localMessage="Command supported by ONT-6xx only (current test equipment type:[{}]) ".format(self.__ontType)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage

        if portId == "":
            localMessage = "ERROR get_set_au_path_trace_tx_channel: portId  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        auPathTraceMode = auPathTraceMode.upper()
        if auPathTraceMode != "OFF"  and \
           auPathTraceMode != "AUTO16" and \
           auPathTraceMode != "AUTO64" and \
           auPathTraceMode != "TRC16" and \
           auPathTraceMode != "TRC64" and \
           auPathTraceMode != "":
            localMessage = "ERROR get_set_au_path_trace_tx_channel: auPathTraceMode  [{}] not valid [OFF|AUTO16|AUTO64|TRC16|TRC64|''(to get status)]".format(auPathTraceMode)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if auPathTraceMode == "":  # Get auPathTraceMode and exit
            localCommand="{}?".format(ONTCmdString)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            self.__method_success(methodLocalName, None, sdhAnswer)
            return True, sdhAnswer
        localCommand="{} {}".format(ONTCmdString, auPathTraceMode)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        localCommand="{}?".format(ONTCmdString)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        if sdhAnswer != auPathTraceMode:
            localMessage="Tx AU Path Trace Mode mismatch: required [{}] but set [{}]".format(auPathTraceMode,sdhAnswer)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, sdhAnswer
        localMessage="Tx AU Path Trace Mode selection:[{}]".format(sdhAnswer)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, sdhAnswer



    def get_set_au_path_trace_rx_TR16_string(self, portId, expectedString=""):   # ONT-6xx only    ### krepo added ###      
        """ ONT-6xx only
            Get or Set the 15-char string in J1 byte for RX channel:
                expectedString: "string"|empty string to read current value
            Return tuple: ( "True|False" , "< result/error list>)
                True : command execution ok, current  alarm status in result string
                False: error in command execution, details in error list string
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if portId == "":
            localMessage = "ERROR get_set_au_path_trace_rx_TR16_string: portId  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if self.__ontType  == "6xx":
            ONTCmdString=":SENS:DATA:TEL:SDH:PATH:SEL:J1TR:REF:TR16:BLOC"
        else:
            localMessage="Command supported by ONT-6xx only (current test equipment type:[{}]) ".format(self.__ontType)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if expectedString == "":  # Get auPathTraceMode and exit
            localCommand="{}?".format(ONTCmdString)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            plainTextAnswer = self.__TR16_to_string(sdhAnswer)
            self.__method_success(methodLocalName, None, plainTextAnswer)
            return True, plainTextAnswer
        asciiCsvString=self.__string_to_TR16(expectedString) # this is the format used in set and get
        localCommand="{} {}".format(ONTCmdString, asciiCsvString)
        #self.__lc_msg(localCommand)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        localCommand="{}?".format(ONTCmdString)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        plainTextAnswer = self.__TR16_to_string(sdhAnswer)
        if sdhAnswer != asciiCsvString:
            localMessage="Rx expected TR16J1 String: required [{}] but set [{}]".format(expectedString,plainTextAnswer)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, plainTextAnswer
        localMessage="Rx expected TR16J1 String specified:[{}]".format(plainTextAnswer)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, plainTextAnswer



    def get_set_au_path_trace_tx_TR16_string(self, portId, tr16String=""):   # ONT-6xx only  ### krepo added ###  
        """ ONT-6xx only
            Get or Set the 15-char string in J1 byte for TX channel:
                tr16String: "string"|empty string to read current value
            Return tuple: ( "True|False" , "< result/error list>)
                True : command execution ok, current  alarm status in result string
                False: error in command execution, details in error list string
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        portId = self.__recover_port_to_use(portId)
        if portId == "":
            localMessage = "ERROR get_set_au_path_trace_tx_TR16_string: portId  [{}] not specified".format(portId)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if self.__ontType  == "6xx":
            ONTCmdString=":SOUR:DATA:TEL:SDH:PATH:SEL:J1TR:TR16:BLOC"
        else:
            localMessage="Command supported by ONT-6xx only (current test equipment type:[{}]) ".format(self.__ontType)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return False, localMessage
        if tr16String == "":  # Get auPathTraceMode and exit
            localCommand="{}?".format(ONTCmdString)
            rawCallResult = self.__send_port_cmd(portId, localCommand)
            sdhAnswer = self.__remove_dust(rawCallResult[1])
            plainTextAnswer = self.__TR16_to_string(sdhAnswer)
            self.__method_success(methodLocalName, None, plainTextAnswer)
            return True, plainTextAnswer
        asciiCsvString=self.__string_to_TR16(tr16String) # this is the format used in set and get
        localCommand="{} {}".format(ONTCmdString, asciiCsvString)
        #self.__lc_msg(localCommand)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        localCommand="{}?".format(ONTCmdString)
        rawCallResult = self.__send_port_cmd(portId, localCommand)
        sdhAnswer = self.__remove_dust(rawCallResult[1])
        plainTextAnswer = self.__TR16_to_string(sdhAnswer)
        if sdhAnswer != asciiCsvString:
            localMessage="Tx TR16 J1 Send String required [{}] but set [{}]".format(tr16String,plainTextAnswer)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, plainTextAnswer, localMessage)
            return False, localMessage
        localMessage="Tx TR16 J1 Send String specified:[{}]".format(plainTextAnswer)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, plainTextAnswer)
        return True, plainTextAnswer























































#######################################################################
#
#   MODULE TEST - Test sequences used for DB-Integrated testing
#
#######################################################################
if __name__ == "__main__":   #now use this part
    print(" ")
    print("========================================")
    print("ontXXXDriver DB-Integrated testing debug")
    print("========================================")
    #localUser="preint" ghelfi
    #localPwd="preint"  ghelfi

    # DA AMBIENTE DI ESECUZIONE:
    currDir,fileName = os.path.split(os.path.realpath(__file__))
    xmlReport = currDir + '/test-reports/TestSuite.'+ fileName
    r = Kunit(xmlReport)
    r.frame_open(xmlReport)

    # PREINIT VARS (from file or ad-hoc class):
    # 5xx
    localUser_5xx="Automation"
    localPwd_5xx="Automation"
    portId_5xx="/0/1/1"
    myApplication1_5xx="SdhBert"
    myApplication2_5xx="SonetBert"

    # 6xx
    localUser_6xx="Automation"
    localPwd_6xx="Automation"
    portId_6xx="/0/1/1"
    myApplication1_6xx="New-Application"


  
    tester_5xx = InstrumentONT("tester_5xx", ID=20, krepo=r)
    tester_6xx = InstrumentONT("tester_6xx", ID=21, krepo=r)
    tester_5xx.init_instrument(portId_5xx)
    tester_6xx.init_instrument(portId_6xx)






    print("\n\n\n\n\nTESTING SECTION *************************************")
    input("press enter to continue...")
    




    tester_5xx.deinit_instrument( portId_5xx)
    tester_6xx.deinit_instrument( portId_6xx)

 

    print(" ")
    print("========================================")
    print("ontXXXDriver DB-Integrated -- END --    ")
    print("========================================")
    print(" ")


    r.frame_close()




#######################################################################
#
#   MODULE TEST - Test sequences used fot ONT5xx testing
#
#######################################################################
if __name__ == "__main__xxx":   #now skip this part
    print(" ")
    print("=============================")
    print("ontXXXDriver 5xx module debug")
    print("=============================")
    #localUser="preint" ghelfi
    #localPwd="preint"  ghelfi

    xmlReport = currDir + '/test-reports/TestSuite.'+ fileName
    r = Kunit(xmlReport)
    r.frame_open(xmlReport)

    localUser="Automation"
    localPwd="Automation"
    portId1="/0/1/1"
    portId2="/0/2/1"
    portId3="/0/3/1"
    myApplication1="SdhBert"
    myApplication2="SonetBert"

    tester = InstrumentONT(localUser,localPwd, krepo=r)
    callResult = tester.connect()
    print("tester.connect result: [{}]".format(callResult))

    callResult = tester.create_session(self.__sessionName)
    print("tester.create_session result: [{}]".format(callResult))

    #    callResult = tester.wait_ops_completed()
    #    print("tester.wait_ops_completed result: [{}]".format(callResult))

    callResult = tester.select_port(portId1)
    print("tester.select_port result: [{}]".format(callResult))
    callResult = tester.select_port(portId2)
    print("tester.select_port result: [{}]".format(callResult))
    callResult = tester.select_port(portId3)
    print("tester.select_port result: [{}]".format(callResult))
    callResult = tester.get_selected_ports("")
    print("tester.get_selected_ports result: [{}]".format(callResult))
    callResult = tester.get_instrument_id()
    print("tester.get_instrument_id result: [{}]".format(callResult))

    #    callResult = tester.get_last_error()
    #    print("tester.get_last_error result: [{}]".format(callResult))
    #    callResult = tester.get_available_ports()
    #    print("tester.get_available_ports result: [{}]".format(callResult))

    #    callResult = tester.reboot_slot(portId1)
    #    print("*********** callResult: [{}]".format(callResult))
    #    time.sleep(20)

    #callResult = tester.init_ont_type()
    #print("tester.init_ont_type result: [{}]".format(callResult))
    #callResult = tester.print_ont_type()  # uncomment to check the detected Ont Type

    callResult = tester.init_port_to_socket_map()
    print("tester.init_port_to_socket_map result: [{}]".format(callResult))
    #tester.print_port_to_socket_map() # uncomment to check if map is initialized

    callResult = tester.open_port_channel(portId1)
    print("tester.open_port_channel result: [{}]".format(callResult))

    callResult = tester.get_currently_loaded_app(portId1)
    print("tester.get_currently_loaded_app result: [{}]".format(callResult))

    callResult = tester.load_app(portId1, myApplication1)
    print("tester.load_app result: [{}]".format(callResult))

    #callResult = tester.get_set_measurement_time(portId1, 0)
    #print("tester.get_set_measurement_time result: [{}]".format(callResult))
    #callResult = tester.get_set_measurement_time(portId1, 123456)
    #print("tester.get_set_measurement_time result: [{}]".format(callResult))
    #callResult = tester.get_set_measurement_time(portId1, 0)
    #print("tester.get_set_measurement_time result: [{}]".format(callResult))
    #callResult = tester.retrieve_optical_alarms(portId1)
    #print("tester.retrieve_optical_alarms result: [{}]".format(callResult))
    #callResult = tester.retrieve_ho_alarms(portId1)
    #print("tester.retrieve_ho_alarms result: [{}]".format(callResult))
    #callResult = tester.retrieve_lo_alarms(portId1)
    #print("tester.retrieve_lo_alarms result: [{}]".format(callResult))
    #callResult = tester.get_set_wavelenght(portId1,"W1310")
    #print("tester.get_set_wavelenght result: [{}]".format(callResult))
    #callResult = tester.get_set_wavelenght(portId1,"")
    #print("tester.get_set_wavelenght result: [{}]".format(callResult))
    #callResult = tester.get_set_laser_status(portId1,"ON")
    #print("tester.get_set_laser_status result: [{}]".format(callResult))
    #callResult = tester.get_set_laser_status(portId1,"")
    #print("tester.get_set_laser_status result: [{}]".format(callResult))
    #callResult = tester.get_set_rx_bit_rate(portId1,"")
    #print("tester.get_set_rx_bit_rate result: [{}]".format(callResult))
    #callResult = tester.get_set_rx_bit_rate(portId1,"STM1")
    #print("tester.get_set_rx_bit_rate result: [{}]".format(callResult))
    #callResult = tester.get_set_clock_reference_source(portId1,"")
    #print("tester.get_set_clock_reference_source result: [{}]".format(callResult))
    #callResult = tester.get_set_clock_reference_source(portId1,"RX")
    #print("tester.get_set_clock_reference_source result: [{}]".format(callResult))
    #callResult = tester.get_set_rx_bit_rate(portId1,"STM16")
    #print("tester.get_set_rx_bit_rate result: [{}]".format(callResult))
    #callResult = tester.get_set_tx_bit_rate(portId1,"STM16")
    #print("tester.get_set_tx_bit_rate result: [{}]".format(callResult))
    #callResult = tester.get_set_rx_measure_channel(portId1,"1")
    #print("tester.get_set_rx_measure_channel result: [{}]".format(callResult))
    #callResult = tester.get_set_rx_channel_mapping_size(portId1,"VC12")
    #print("tester.get_set_rx_channel_mapping_size result: [{}]".format(callResult))
    #callResult = tester.get_set_rx_lo_measure_channel(portId1,"4")
    #print("tester.get_set_rx_lo_measure_channel result: [{}]".format(callResult))
    #callResult = tester.get_set_alarm_insertion_type(portId1,"LOF")
    #print("tester.get_set_alarm_insertion_type result: [{}]".format(callResult))
    #callResult = tester.get_set_alarmed_frames_number(portId1,"222")
    #print("tester.get_set_alarmed_frames_number result: [{}]".format(callResult))
    #callResult = tester.get_set_not_alarmed_frames_number(portId1,"444")
    #print("tester.get_set_not_alarmed_frames_number result: [{}]".format(callResult))
    #callResult = tester.get_set_alarm_activation(portId1,"")
    #print("tester.get_set_alarm_activation result: [{}]".format(callResult))
    #callResult = tester.get_set_alarm_activation(portId1,"OFF")
    #print("tester.get_set_alarm_activation result: [{}]".format(callResult))
    #callResult = tester.get_set_alarm_insertion_mode(portId1,"BURST_CONT")
    #print("tester.get_set_alarm_insertion_mode result: [{}]".format(callResult))
    #callResult = tester.get_set_alarm_insertion_type(portId1,"")
    #print("tester.get_set_alarm_insertion_type result: [{}]".format(callResult))
    #callResult = tester.get_set_num_errored_burst_frames(portId1,"7")
    #print("tester.get_set_num_errored_burst_frames result: [{}]".format(callResult))
    #callResult = tester.get_set_num_not_errored_burst_frames(portId1,"")
    #print("tester.get_set_num_not_errored_burst_frames result: [{}]".format(callResult))
    #callResult = tester.get_set_num_not_errored_burst_frames(portId1,"300")
    #print("tester.get_set_num_not_errored_burst_frames result: [{}]".format(callResult))
    #callResult = tester.get_set_error_activation(portId1,"ON")
    #print("tester.get_set_error_activation result: [{}]".format(callResult))
    #callResult = tester.get_set_error_insertion_mode(portId1,"ONCE")
    #print("tester.get_set_error_insertion_mode result: [{}]".format(callResult))
    #callResult = tester.get_set_error_insertion_type(portId1,"FAS")
    #print("tester.get_set_error_insertion_type result: [{}]".format(callResult))
    #callResult = tester.get_set_error_insertion_type(portId1,"RSBIP")
    #print("tester.get_set_error_insertion_type result: [{}]".format(callResult))
    #callResult = tester.get_set_tx_bit_rate(portId1,"STM16")
    #print("tester.get_set_tx_bit_rate result: [{}]".format(callResult))
    #callResult = tester.get_set_tx_measure_channel(portId1,"")
    #print("tester.get_set_tx_measure_channel result: [{}]".format(callResult))
    #callResult = tester.get_set_tx_measure_channel(portId1,"7")
    #print("tester.get_set_tx_measure_channel result: [{}]".format(callResult))
    #callResult = tester.get_set_rx_channel_mapping_size(portId1,"VC12")
    #print("tester.get_set_rx_channel_mapping_size result: [{}]".format(callResult))
    #callResult = tester.get_set_tx_channel_mapping_size(portId1,"VC12")
    #print("tester.get_set_tx_channel_mapping_size result: [{}]".format(callResult))


    #print("\n\n\n\n\nTESTING SECTION START *************************************")
    #input("press enter to continue...\n")

    #callResult = tester.get_set_rx_lo_measure_channel(portId1,"4")
    #print("tester.get_set_rx_lo_measure_channel result: [{}]".format(callResult))
    #input("press enter to continue...\n")
    #callResult = tester.get_set_tx_lo_measure_channel(portId1,"5")
    #print("tester.get_set_tx_lo_measure_channel result: [{}]".format(callResult))
    #input("press enter to continue...\n")



    print("\n\n\n\n\nTESTING SECTION STOP *************************************")
    #input("press enter to continue...")

    callResult = tester.retrieve_ho_alarms(portId1)
    print("tester.retrieve_ho_alarms result: [{}]".format(callResult))
    callResult = tester.retrieve_lo_alarms(portId1)
    print("tester.retrieve_lo_alarms result: [{}]".format(callResult))

    callResult = tester.retrieve_ho_lo_alarms(portId1)
    print("tester.retrieve_ho_lo_alarms result: [{}]".format(callResult))



    callResult = tester.unload_app(portId1, myApplication1)
    print("tester.unload_app result: [{}]".format(callResult))
    callResult = tester.deselect_port(portId1)    # uncomment to deselect the specified port
    print("tester.deselect_port result: [{}]".format(callResult))
    callResult = tester.deselect_port(portId2)   # uncomment to deselect the specified port
    print("tester.deselect_port result: [{}]".format(callResult))
    callResult = tester.deselect_port(portId3)   # uncomment to deselect the specified port
    print("tester.deselect_port result: [{}]".format(callResult))

    callResult = tester.delete_session(self.__sessionName)
    print("tester.delete_session result: [{}]".format(callResult))

    print(" ")
    print("=============================")
    print("ontXXXDriver 5xx -- END--")
    print("=============================")
    print(" ")

    r.frame_close()

    #sys.exit()







#######################################################################
#
#   MODULE TEST - Test sequences used for ONT6xx testing
#
#######################################################################
if __name__ == "__main__xxx":
    print(" ")
    print("=============================")
    print("ontXXXDriver 6xx module debug")
    print("=============================")

    currDir,fileName = os.path.split(os.path.realpath(__file__))
    xmlReport = currDir + '/test-reports/TestSuite.'+ fileName
    r = Kunit(xmlReport)
    r.frame_open(xmlReport)


    localUser="Automation"
    localPwd="Automation"
    localOntIpAddress="135.221.123.147"
    portId1="/0/1/1"
    portId2=""
    portId3="/0/3/1"
    myApplication1="New-Application"
    mySigStructType1="PHYS_SDH"

    tester = InstrumentONT(localUser,localPwd,localOntIpAddress, krepo=r)
    callResult = tester.connect()
    print("tester.connect result: [{}]".format(callResult))

    callResult = tester.open_port_channel(portId1)
    print("tester.open_port_channel result: [{}]".format(callResult))
    callResult = tester.unload_app(portId1, myApplication1)
    print("tester.unload_app result: [{}]".format(callResult))
    callResult = tester.get_currently_loaded_app(portId1)
    print("tester.get_currently_loaded_app result: [{}]".format(callResult))
    callResult = tester.load_app(portId1, myApplication1)
    print("tester.load_app result: [{}]".format(callResult))
    callResult = tester.set_current_signal_structure(portId1, mySigStructType1)
    print("tester.set_current_signal_structure result: [{}]".format(callResult))
    #callResult = tester.get_set_tx_bit_rate(portId1,"STM16")
    #print("tester.get_set_tx_bit_rate result: [{}]".format(callResult))
    #callResult = tester.get_set_rx_bit_rate(portId1,"STM16")
    #print("tester.get_set_rx_bit_rate result: [{}]".format(callResult))
    #callResult = tester.get_set_clock_reference_source(portId1,"LOCAL")
    #print("tester.get_set_clock_reference_source result: [{}]".format(callResult))
    #callResult = tester.get_set_clock_reference_source(portId1,"RX")
    #print("tester.get_set_clock_reference_source result: [{}]".format(callResult))
    # ### get_set_wavelenght under testing ###
    #callResult = tester.get_set_wavelenght(portId1,"1310")
    #print("tester.get_set_wavelenght result: [{}]".format(callResult))
    #input("press enter to continue...")
    #callResult = tester.get_set_wavelenght(portId1,"1550")
    #print("tester.get_set_wavelenght result: [{}]".format(callResult))
    #input("press enter to continue...")

    # Laser ON/OFF
    #callResult = tester.get_set_laser_status(portId1,"ON")
    #print("tester.get_set_laser_status result: [{}]".format(callResult))
    #callResult = tester.retrieve_optical_alarms(portId1)
    #print("tester.retrieve_optical_alarms result: [{}]".format(callResult))
    #input("press enter to continue...")
    #callResult = tester.get_set_laser_status(portId1,"OFF")
    #print("tester.get_set_laser_status result: [{}]".format(callResult))


    callResult = tester.get_set_tx_bit_rate(portId1,"STM64")
    print("tester.get_set_tx_bit_rate result: [{}]".format(callResult))
    callResult = tester.get_set_rx_bit_rate(portId1,"STM64")
    print("tester.get_set_rx_bit_rate result: [{}]".format(callResult))
    callResult = tester.get_set_clock_reference_source(portId1,"LOCAL")
    print("tester.get_set_clock_reference_source result: [{}]".format(callResult))
    callResult = tester.retrieve_optical_alarms(portId1)
    print("tester.retrieve_optical_alarms result: [{}]".format(callResult))
    callResult = tester.retrieve_ho_lo_alarms(portId1)
    print("tester.retrieve_ho_lo_alarms result: [{}]".format(callResult))

    #callResult = tester.get_set_rx_channel_mapping_size(portId1,"VC4")
    #print("tester.get_set_rx_channel_mapping_size result: [{}]".format(callResult))
    #callResult = tester.get_set_tx_channel_mapping_size(portId1,"VC4")
    #print("tester.get_set_tx_channel_mapping_size result: [{}]".format(callResult))

    #callResult = tester.get_set_alarmed_frames_number(portId1,"222")
    #print("tester.get_set_alarmed_frames_number result: [{}]".format(callResult))
    #callResult = tester.get_set_not_alarmed_frames_number(portId1,"444")
    #print("tester.get_set_not_alarmed_frames_number result: [{}]".format(callResult))

    #callResult = tester.get_set_alarm_insertion_mode(portId1,"BURST_CONT")
    #print("tester.get_set_alarm_insertion_mode result: [{}]".format(callResult))

    #callResult = tester.get_set_alarm_insertion_type(portId1,"LOF")
    #print("tester.get_set_alarm_insertion_type result: [{}]".format(callResult))

    #callResult = tester.get_set_alarm_activation(portId1,"OFF")
    #print("tester.get_set_alarm_activation result: [{}]".format(callResult))
    #callResult = tester.get_set_alarm_activation(portId1,"ON")
    #print("tester.get_set_alarm_activation result: [{}]".format(callResult))
    #callResult = tester.get_set_num_errored_burst_frames(portId1,"7")
    #print("tester.get_set_num_errored_burst_frames result: [{}]".format(callResult))
    #callResult = tester.get_set_num_errored_burst_frames(portId1,"")
    #print("tester.get_set_num_errored_burst_frames result: [{}]".format(callResult))
    #callResult = tester.get_set_num_not_errored_burst_frames(portId1,"")
    #print("tester.get_set_num_not_errored_burst_frames result: [{}]".format(callResult))
    #callResult = tester.get_set_num_not_errored_burst_frames(portId1,"300")
    #print("tester.get_set_num_not_errored_burst_frames result: [{}]".format(callResult))
    # not working
    #callResult = tester.get_set_rx_channel_mapping_size(portId1,"VC11")
    #print("tester.get_set_rx_channel_mapping_size result: [{}]".format(callResult))
    # not working
    #callResult = tester.get_set_rx_channel_mapping_size(portId1,"VC12")
    #print("tester.get_set_rx_channel_mapping_size result: [{}]".format(callResult))
    #callResult = tester.get_set_error_insertion_mode(portId1,"")
    #print("tester.get_set_error_insertion_mode result: [{}]".format(callResult))
    #callResult = tester.get_set_error_insertion_mode(portId1,"NONE")
    #print("tester.get_set_error_insertion_mode result: [{}]".format(callResult))
    #callResult = tester.get_set_error_insertion_mode(portId1,"ONCE")
    #print("tester.get_set_error_insertion_mode result: [{}]".format(callResult))
    #callResult = tester.get_set_error_insertion_mode(portId1,"RATE")
    #print("tester.get_set_error_insertion_mode result: [{}]".format(callResult))
    #callResult = tester.get_set_error_insertion_mode(portId1,"BURST_ONCE")
    #print("tester.get_set_error_insertion_mode result: [{}]".format(callResult))
    #callResult = tester.get_set_error_insertion_mode(portId1,"BURST_CONT")
    #print("tester.get_set_error_insertion_mode result: [{}]".format(callResult))
    #callResult = tester.get_set_error_insertion_mode(portId1,"RATE_BURST_ONCE")
    #print("tester.get_set_error_insertion_mode result: [{}]".format(callResult))
    #callResult = tester.get_set_error_insertion_mode(portId1,"RATE_BURST_CONT")
    #print("tester.get_set_error_insertion_mode result: [{}]".format(callResult))
    #callResult = tester.get_set_error_insertion_type(portId1,"FAS")
    #print("tester.get_set_error_insertion_type result: [{}]".format(callResult))
    #callResult = tester.get_set_error_insertion_type(portId1,"RSBIP")
    #print("tester.get_set_error_insertion_type result: [{}]".format(callResult))
    #callResult = tester.get_set_error_insertion_type(portId1,"")
    #print("tester.get_set_error_insertion_type result: [{}]".format(callResult))
    #callResult = tester.get_set_error_rate(portId1,"0.00001")
    #print("tester.get_set_error_rate result: [{}]".format(callResult))
    #callResult = tester.get_set_error_rate(portId1,"0.00005")
    #print("tester.get_set_error_rate result: [{}]".format(callResult))
    #callResult = tester.get_set_error_rate(portId1,"0.000006")
    #print("tester.get_set_error_rate result: [{}]".format(callResult))
    #callResult = tester.get_set_error_rate(portId1,"0.000007")
    #print("tester.get_set_error_rate result: [{}]".format(callResult))
    #callResult = tester.get_set_error_activation(portId1,"")
    #print("tester.get_set_error_activation result: [{}]".format(callResult))
    #input("press enter to continue...")
    #callResult = tester.get_set_error_activation(portId1,"ON")
    #print("tester.get_set_error_activation result: [{}]".format(callResult))
    #input("press enter to continue...")
    #callResult = tester.get_set_error_activation(portId1,"OFF")
    #print("tester.get_set_error_activation result: [{}]".format(callResult))
    #input("press enter to continue...")
    #callResult = tester.get_set_error_activation(portId1,"")
    #print("tester.get_set_error_activation result: [{}]".format(callResult))
    #input("press enter to continue...")
    #callResult = tester.get_set_tx_lo_measure_channel(portId1,"")
    #print("tester.get_set_tx_lo_measure_channel result: [{}]".format(callResult))
    #callResult = tester.get_set_tx_lo_measure_channel(portId1,"1.1.1.1")
    #print("tester.get_set_tx_lo_measure_channel result: [{}]".format(callResult))
    #callResult = tester.get_set_tx_lo_measure_channel(portId1,"2.1.1.1")
    #print("tester.get_set_tx_lo_measure_channel result: [{}]".format(callResult))
    #callResult = tester.get_set_tx_lo_measure_channel(portId1,"3.1.1.1")
    #print("tester.get_set_tx_lo_measure_channel result: [{}]".format(callResult))
    #callResult = tester.get_set_tx_lo_measure_channel(portId1,"7.1.1.1")
    #print("tester.get_set_tx_lo_measure_channel result: [{}]".format(callResult))
    #callResult = tester.get_set_rx_lo_measure_channel(portId1,"")
    #print("tester.get_set_rx_lo_measure_channel result: [{}]".format(callResult))
    #callResult = tester.get_set_rx_lo_measure_channel(portId1,"1.1.1.1")
    #print("tester.get_set_rx_lo_measure_channel result: [{}]".format(callResult))
    #callResult = tester.get_set_rx_lo_measure_channel(portId1,"2.1.1.1")
    #print("tester.get_set_rx_lo_measure_channel result: [{}]".format(callResult))
    #callResult = tester.get_set_rx_lo_measure_channel(portId1,"3.1.1.1")
    #print("tester.get_set_rx_lo_measure_channel result: [{}]".format(callResult))
    #callResult = tester.get_set_rx_lo_measure_channel(portId1,"4.1.1.1")
    #print("tester.get_set_rx_lo_measure_channel result: [{}]".format(callResult))

    #callResult = tester.get_set_background_channels_fill_mode(portId1,"")
    #print("tester.get_set_background_channels_fill_mode result: [{}]".format(callResult))
    #callResult = tester.get_set_background_channels_fill_mode(portId1,"FIX")
    #print("tester.get_set_background_channels_fill_mode result: [{}]".format(callResult))
    #callResult = tester.get_set_background_channels_fill_mode(portId1,"COPY")
    #print("tester.get_set_background_channels_fill_mode result: [{}]".format(callResult))
    #callResult = tester.get_set_tx_au_path_J1_trace_mode(portId1,"")
    #print("tester.get_set_tx_au_path_J1_trace_mode result: [{}]".format(callResult))
    #callResult = tester.get_set_tx_au_path_J1_trace_mode(portId1,"OFF")
    #print("tester.get_set_tx_au_path_J1_trace_mode result: [{}]".format(callResult))
    #callResult = tester.get_set_tx_au_path_J1_trace_mode(portId1,"TRC16")
    #print("tester.get_set_tx_au_path_J1_trace_mode result: [{}]".format(callResult))
    #callResult = tester.get_set_tx_au_path_J1_trace_mode(portId1,"TRC64")
    #print("tester.get_set_tx_au_path_J1_trace_mode result: [{}]".format(callResult))

    #callResult = tester.get_set_au_path_trace_rx_channel(portId1,"")
    #print("tester.get_set_au_path_trace_rx_channel result: [{}]".format(callResult))
    #callResult = tester.get_set_au_path_trace_rx_channel(portId1,"OFF")
    #print("tester.get_set_tx_au_path_J1_trace_mode result: [{}]".format(callResult))
    #callResult = tester.get_set_au_path_trace_rx_channel(portId1,"TRC16")
    #print("tester.get_set_tx_au_path_J1_trace_mode result: [{}]".format(callResult))
    #callResult = tester.get_set_au_path_trace_tx_channel(portId1,"")
    #print("tester.get_set_au_path_trace_tx_channel result: [{}]".format(callResult))
    #callResult = tester.get_set_au_path_trace_tx_channel(portId1,"OFF")
    #print("tester.get_set_au_path_trace_tx_channel result: [{}]".format(callResult))
    #callResult = tester.get_set_au_path_trace_tx_channel(portId1,"TRC64")
    #print("tester.get_set_au_path_trace_tx_channel result: [{}]".format(callResult))

    #callResult = tester.get_set_au_path_trace_rx_TR16_string(portId1,"")
    #print("tester.get_set_au_path_trace_rx_TR16_string result: [{}]".format(callResult))
    #input("press enter to continue...")
    #callResult = tester.get_set_au_path_trace_rx_TR16_string(portId1,"MILANO")
    #print("tester.get_set_au_path_trace_rx_TR16_string result: [{}]".format(callResult))
    #input("press enter to continue...")
    #callResult = tester.get_set_au_path_trace_rx_TR16_string(portId1,"CINISELLO BALSAMO")
    #print("tester.get_set_au_path_trace_rx_TR16_string result: [{}]".format(callResult))
    #input("press enter to continue...")
    #callResult = tester.get_set_au_path_trace_rx_TR16_string(portId1,"MONZA")
    #print("tester.get_set_au_path_trace_rx_TR16_string result: [{}]".format(callResult))
    #input("press enter to continue...")
    #callResult = tester.get_set_au_path_trace_rx_TR16_string(portId1,"LONGONE AL SEGRINO")
    #print("tester.get_set_au_path_trace_rx_TR16_string result: [{}]".format(callResult))
    #input("press enter to continue...")
    #callResult = tester.get_set_au_path_trace_tx_TR16_string(portId1,"")
    #print("tester.get_set_au_path_trace_tx_TR16_string result: [{}]".format(callResult))
    #input("press enter to continue...")
    #callResult = tester.get_set_au_path_trace_tx_TR16_string(portId1,"MILANO")
    #print("tester.get_set_au_path_trace_tx_TR16_string result: [{}]".format(callResult))
    #input("press enter to continue...")
    #callResult = tester.get_set_au_path_trace_tx_TR16_string(portId1,"CINISELLO BALSAMO")
    #print("tester.get_set_au_path_trace_tx_TR16_string result: [{}]".format(callResult))
    #input("press enter to continue...")
    #callResult = tester.get_set_au_path_trace_tx_TR16_string(portId1,"MONZA")
    #print("tester.get_set_au_path_trace_tx_TR16_string result: [{}]".format(callResult))
    #input("press enter to continue...")
    #callResult = tester.get_set_au_path_trace_tx_TR16_string(portId1,"LONGONE AL SEGRINO")
    #print("tester.get_set_au_path_trace_tx_TR16_string result: [{}]".format(callResult))
    #input("press enter to continue...")

    callResult = tester.get_set_au_path_trace_tx_channel(portId1,"TRC16")
    print("tester.get_set_au_path_trace_tx_channel result: [{}]".format(callResult))

    callResult = tester.get_set_tx_bit_rate(portId1,"STM64")
    print("tester.get_set_tx_bit_rate result: [{}]".format(callResult))
    callResult = tester.get_set_rx_bit_rate(portId1,"STM64")
    print("tester.get_set_rx_bit_rate result: [{}]".format(callResult))


    print("\n\n\n\n\nTESTING SECTION START *************************************")
    #input("press enter to continue...")




    callResult = tester.get_set_rx_channel_mapping_size(portId1,"VC12")
    print("tester.get_set_rx_channel_mapping_size result: [{}]".format(callResult))
    #input("press enter to continue...")

    #callResult = tester.get_set_rx_channel_mapping_size(portId1,"VC3")
    #print("tester.get_set_rx_channel_mapping_size result: [{}]".format(callResult))
    #input("press enter to continue...")

    #callResult = tester.get_set_rx_channel_mapping_size(portId1,"VC4")
    #print("tester.get_set_rx_channel_mapping_size result: [{}]".format(callResult))
    #input("press enter to continue...")

    #callResult = tester.get_set_rx_channel_mapping_size(portId1,"VC4_4C")
    #print("tester.get_set_rx_channel_mapping_size result: [{}]".format(callResult))
    #input("press enter to continue...")

    #callResult = tester.get_set_rx_channel_mapping_size(portId1,"VC4_16C")
    #print("tester.get_set_rx_channel_mapping_size result: [{}]".format(callResult))
    #input("press enter to continue...")

    callResult = tester.get_set_rx_channel_mapping_size(portId1,"VC4_64C")
    print("tester.get_set_rx_channel_mapping_size result: [{}]".format(callResult))
    #input("press enter to continue...")

    #callResult = tester.get_set_rx_channel_mapping_size(portId1,"")
    #print("tester.get_set_rx_channel_mapping_size result: [{}]".format(callResult))
    #input("press enter to continue...")


    #print("\n\n\n\n\nTESTING SECTION STOP *************************************")
    #input("press enter to continue...")


    callResult = tester.unload_app(portId1, myApplication1)
    print("tester.unload_app result: [{}]".format(callResult))
    print(" ")
    print("=============================")
    print("ontXXXDriver 6xx -- END--")
    print("=============================")
    print(" ")

    r.frame_close()
    
    #sys.exit()
















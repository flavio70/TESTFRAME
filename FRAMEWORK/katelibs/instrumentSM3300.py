#!/usr/bin/env python
"""
###############################################################################
#
# MODULE:  InstrumentSM3300.py
#
# AUTHOR:  L.Cutilli
#
# DATE  :  22/04/2016
#
#
# DETAILS: Python management module of the following smart power supply:
#          - SM3300 (DELTA ELEKTRONIKA BV,SM66-AR-110)
#
# MODULE: InstrumentSM3300.py  created to drive the ON/OFF and other
#         features of the equipment
#
###############################################################################
"""

# import os
import time
import inspect
import telnetlib

from katelibs.equipment import Equipment
#from katelibs.kenviron import KEnvironment
from katelibs.kunit import Kunit
#from katelibs.database import *
from katelibs.database import TNet, TEquipment


class InstrumentSM3300(Equipment):

    def __init__(self, label, kenv):
        """ label   : equipment name used on Report file
            kenv    : instance of KEnvironment (initialized by K@TE FRAMEWORK)
        """

        # Enviroment
        self.__kenv                 = kenv             # Kate Environment
        self.__krepo                = kenv.krepo       # result report (Kunit class instance)
        self.__prs                  = kenv.kprs        # Presets for running environment
        # Session
        # Initizalization flag:
        # Inside init_instrument() call: True if previous step ok,
        # after: each method called inside "test_body" section must found this flag to True to be executed
        self.__lastCallSuccess      = False            #  track if the last call was successfully executed (not to set in case of skip)
        self.__calledMethodList     = []               #  used to track all method called
        self.__calledMethodStatus   = dict()           #  used to track all method called and last execution result
        # Connection
        self.__sm3300IpAddress      = None             #  Sm3300XXX IP address
        self.__sm3300TelnetPort     = 8462             #  Sm3300XXX telnet port (default 5001)
        self.__sm3300Id             = None             #  Sm3300XXX Id
        self.__telnetConnection     = None             #  Handler of the established telnet connection
        self.__pingRetryNumber      = 1                #  Retry number for -c ping option
        self.__telnetExpectedPrompt = [b'> ']          #  it must be specified as keys LIST...
        self.__telnetTimeout        = 5

        super().__init__(label, self.__prs.get_id(label))
        self.__get_instrument_info_from_db(self.__prs.get_id(label)) # inizializza i dati di IP,  ..dal DB

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
        self.__lastCallSuccess = True            # Mark current execution as successfully
        self.__calledMethodStatus[title]= "success"  #
        self.__t_success(title, elapsed_time, out_text)  # CG tracking


    def __method_failure(self, title, e_time, out_text, err_text):
        """ INTERNAL USAGE
        """
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
        self.__sm3300Id = tabEqpt.objects.get(id_equipment=ID).t_equip_type_id_type.name
        #self.__sm3300IpAddress = self.__get_net_info(ID)
        self.__sm3300IpAddress = "151.98.176.253"
        localMessage = "__get_instrument_info_from_db: instrument type specified : Instrument:[{}] IpAddr[{}]".format(self.__sm3300Id,self.__sm3300IpAddress)
        print(localMessage)
        self.__lc_msg(localMessage)
        return



    def init_instrument(self):
        """ SM3300 smart power supply
            Method:
              init_instrument(self)
            Purpose:
              Executes the following steps in a single call and prepare the
              intrument to provide the power supply required by the NE
              - open a communication channel with the SM3300
              - reset the instrument
              - configure the remote programming as needed
              - configure output Voltage to 50 volt
              - configure the Current to 60 ampere

            Parameters:
              none
            Return tuple:
              ( "True|False" , Retvalue)
              True : command execution ok
              False: command execution failed
              Retvalue: returned value or error string for debug purposes
        """

        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        localMessage="[{}] instrument [{}] correctly initialized".format(methodLocalName,self.__sm3300Id)


        # Sm3300 Socket connection
        localResult = self.__create_telnet_connection()
        if not localResult[0]:
            localMessage="SM3300 [{}]:telnet session open (port {}) failed. Bye...".format(self.__sm3300IpAddress, self.__sm3300TelnetPort)
            self.__lc_msg(localMessage)
            self.__method_failure(methodLocalName, None, "", localMessage)
            return  False, localResult
        else:
            localMessage="SM3300 [{}]:telnet session opened (port {})".format(self.__sm3300IpAddress, self.__sm3300TelnetPort)
            self.__lc_msg(localMessage)

        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        self.reset_instrument()
        self.instrument_access_enable()
        self.get_set_voltage(50.00)   # set the output voltage to 50 Volt (GV's former .tcl file as reference)
        self.get_set_current(60.00)   # set the output current to 60 Amp (GV's former .tcl file as reference)
        return True, localMessage



    def deinit_instrument(self):
        """ SM3300 smart power supply

            Method:
              deinit_instrument(self) ***  Not needed ***
            Purpose:
              Deinitalizes the instrument to free it

            Parameters:
              none
            Return tuple:
              (True, <not meaningful string>)
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        localMessage="[{}] instrument [{}] correctly deinitialized".format(methodLocalName,self.__sm3300Id)
        self.__lc_msg(localMessage)
        self.__method_success(methodLocalName, None, localMessage)
        return True, localMessage





    #
    #  INTERNAL UTILITIES
    #
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
        #print ("\n[[[ @@@@ [{}] Method Call ... Krepo[{}]   @@@ ]]] ".format(methodName,embedKrepoInit))

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




    def __send_cmd(self, command):
        if command == "":
            localMessage = "__send_cmd error: command string [{}] empty".format(command)
            self.__lc_msg(localMessage)
            return False, localMessage
        if not   self.__telnetConnection:
            localMessage = "__send_cmd error: telnet connection [{}] not valid".format(self.__telnetConnection)
            self.__lc_msg(localMessage)
            return False, localMessage
        localCmd="{:s} \n".format(command).encode()
        self.__telnetConnection.write(localCmd)
        result=self.__telnetConnection.expect(self.__telnetExpectedPrompt, 2)
        if result:
            localMessage = "__send_cmd command [{}] OK Result [{}]".format(command,result)
            #self.__lc_msg(localMessage)
            return True, str(result[2], 'utf-8')
        else:
            localMessage = "__send_cmd command [{}] ERROR Result [{}]".format(command,result)
            self.__lc_msg(localMessage)
            return False, localMessage



    def __create_telnet_connection(self):
        self.__lc_msg("Function: __create_telnet_connection Socket [{}:{}]".format(self.__sm3300IpAddress,self.__sm3300TelnetPort))
        try:
            self.__telnetConnection = telnetlib.Telnet(self.__sm3300IpAddress,self.__sm3300TelnetPort,self.__telnetTimeout)
            self.__send_cmd("*IDN? \n")
            localMessage = "Telnet connection established"
            self.__lc_msg(localMessage)
        except Exception as e:
            self.__lc_msg(str(e))
            localMessage = "Telnet connection ERROR"
            self.__lc_msg(localMessage)
            return False, localMessage
        return True, localMessage



    #
    #  Reset SM3300  & utilities
    #
    def reset_instrument(self,safetyTimeInterval=15):
        """ SM3300 smart power supply
            reset_instrument (already called in init_instrument()
            Parameters:
              safetyTimeInterval ... time to wait until reset (default 15 sec)
                                     it may be set to a different value if specified
            Return tuple:
              ( "True|False" , Retvalue)
              True : command execution ok
              False: command execution failed
              Retvalue: returned value or error string for debug purposes
        """
        methodLocalName = self.__lc_current_method_name()
        localCmd  = "*RST"
        telnetCmd = "{} \n".format(localCmd)
        time.sleep(safetyTimeInterval)
        try:
            #self.__lc_msg(localCmd)
            response = self.__send_cmd(telnetCmd)
            localMessage="[{}]".format(response)
            #self.__lc_msg(localMessage)
        except Exception as e:
            self.__lc_msg(str(e))
            localMessage = "[{}] Telnet connection ERROR".format(methodLocalName)
            self.__lc_msg(localMessage)
            return False, localMessage
        return True, localMessage


    def instrument_access_enable(self,safetyTimeInterval=0):
        """ SM3300 smart power supply
            Method:
              instrument_access_enable(self,safetyTimeInterval=0) (already called in init_instrument() call)
            Purpose:
              Enable remote or local programming
            Parameters:
              safetyTimeInterval ... time to wait until reset (default 0 sec)
                                     it may be set to a different value if specified
            Return tuple:
              ( "True|False" , Retvalue)
              True : command execution ok
              False: command execution failed (communication problem)
              Retvalue: returned value or error string for debug purposes
        """
        methodLocalName = self.__lc_current_method_name()
        telnetCmd1 = "SYSTem:REMote:CV:STAtus Ethernet \n"
        telnetCmd2 = "SYSTem:REMote:CC:STAtus Ethernet \n"
        time.sleep(safetyTimeInterval)
        try:
            response = self.__send_cmd(telnetCmd1)
            localMessage="[{}]".format(response)
            #self.__lc_msg(localMessage)
            response = self.__send_cmd(telnetCmd2)
            localMessage="[{}]".format(response)
            #self.__lc_msg(localMessage)
        except Exception as e:
            self.__lc_msg(str(e))
            localMessage = "[{}] Telnet connection ERROR".format(methodLocalName)
            self.__lc_msg(localMessage)
            return False, localMessage
        return True, localMessage



    #==================================
    #  Voltage related SM3300 methods
    #==================================

    #
    #  Max Output Voltage Set/Retrieve
    #
    def get_set_max_voltage(self, voltageToSet=None, safetyTimeInterval=0):
        """ SM3300 smart power supply
              get_set_max_voltage(self, voltageToSet=None, safetyTimeInterval=0)
            Purpose:
              set or read the maximum voltage to supply *** !!! SM3300 COMMAND NOT WORKING - under investigation !!! ***
            Parameters:
              safetyTimeInterval ... time to wait until reset (default 0 sec) it may be set to a different value if specified
	      voltageToSet.......... None/Max voltage to set, if not specified it will be returned a read of the currently set value
            Return tuple:
              ( "True|False" , Retvalue)
              True : command execution ok
              False: command execution failed
              Retvalue: returned value or error string for debug purposes
        """
        methodLocalName = self.__lc_current_method_name()
        localCmd = "SOURce:VOLtage:MAXimum"
        localCmdCheck = localCmd + "?"
        if voltageToSet == None:
            telnetCmd = "{} \n".format(localCmdCheck)
        else:
            telnetCmd = "{} {} \n".format(localCmd, voltageToSet)
        time.sleep(safetyTimeInterval)
        try:
            #self.__lc_msg(telnetCmd)
            response = self.__send_cmd(telnetCmd)
            retVal=response[1]
            retVal=retVal.replace('\n','')
        except Exception as e:
            self.__lc_msg(str(e))
            localMessage = "[{}] Telnet connection ERROR".format(methodLocalName)
            self.__lc_msg(localMessage)
            return False, localMessage
        if voltageToSet != None:
            telnetCmd = "{} \n".format(localCmdCheck)
            response = self.__send_cmd(telnetCmd)
            retVal=response[1]
            retVal=retVal.replace('\n','')
            if float(voltageToSet) != float(retVal):
                localMessage = "[{}] failed to set to [{}]".format(methodLocalName,voltageToSet)
                self.__lc_msg(localMessage)
                return False, retVal
        return True, retVal


    #
    #  Output Voltage Set/Retrieve
    #
    def get_set_voltage(self, voltageToSet=None, safetyTimeInterval=0):
        """ SM3300 smart power supply
              get_set_voltage(self, voltageToSet=None, safetyTimeInterval=0)
            Purpose:
              set or read the supplied output voltage
            Parameters:
              safetyTimeInterval ... time to wait until reset (default 0 sec) it may be set to a different value if specified
	      voltageToSet.......... Voltage to set, if not specified it will be returned a read of the currently set value
            Return tuple:
              ( "True|False" , Retvalue)
              True : command execution ok
              False: command execution failed
              Retvalue: returned value or error string for debug purposes
        """
        methodLocalName = self.__lc_current_method_name()
        localCmd = "SOURce:VOLtage"
        localCmdCheck = localCmd + "?"
        if voltageToSet == None:
            telnetCmd = "{} \n".format(localCmdCheck)
        else:
            telnetCmd = "{} {} \n".format(localCmd, voltageToSet)
        time.sleep(safetyTimeInterval)
        try:
            #self.__lc_msg(telnetCmd)
            response = self.__send_cmd(telnetCmd)
            retVal=response[1]
            retVal=retVal.replace('\n','')
        except Exception as e:
            self.__lc_msg(str(e))
            localMessage = "[{}] Telnet connection ERROR".format(methodLocalName)
            self.__lc_msg(localMessage)
            return False, localMessage
        if voltageToSet != None:
            telnetCmd = "{} \n".format(localCmdCheck)
            response = self.__send_cmd(telnetCmd)
            retVal=response[1]
            retVal=retVal.replace('\n','')
            if float(voltageToSet) != float(retVal):
                localMessage = "[{}] failed to set to [{}]".format(methodLocalName,voltageToSet)
                self.__lc_msg(localMessage)
                return False, retVal
        return True, retVal



    #
    #  Output Voltage Realtime Measure
    #
    def get_measured_voltage(self, safetyTimeInterval=0):
        """ SM3300 smart power supply
              get_measured_voltage(self, safetyTimeInterval=0)
            Purpose:
              read the supplied output voltage
            Parameters:
              safetyTimeInterval ... time to wait until reset (default 0 sec) it may be set to a different value if specified
            Return tuple:
              ( "True|False" , Retvalue)
              True : command execution ok
              False: command execution failed
              Retvalue: returned value or error string for debug purposes
        """
        methodLocalName = self.__lc_current_method_name()
        telnetCmd = "MEASure:VOLtage?"
        time.sleep(safetyTimeInterval)
        try:
            response = self.__send_cmd(telnetCmd)
            retVal=response[1]
            retVal=retVal.replace('\n','')
        except Exception as e:
            self.__lc_msg(str(e))
            localMessage = "[{}] Telnet connection ERROR".format(methodLocalName)
            self.__lc_msg(localMessage)
            return False, localMessage
        return True, retVal



    #==================================
    #  Current related SM3300 methods
    #==================================


    #
    #  Max Output Current Set/Retrieve
    #
    def get_set_max_current(self, currentToSet=None, safetyTimeInterval=0):
        """ SM3300 smart power supply
              get_set_max_current(self, currentToSet=None, safetyTimeInterval=0)
            Purpose:
              set or read the maximum current to supply *** !!! SM3300 COMMAND NOT WORKING - under investigation !!! ***
            Parameters:
              safetyTimeInterval ... time to wait until reset (default 0 sec) it may be set to a different value if specified
	      currentToSet.......... None/Max current to set, if not specified it will be returned a read of the currently set value
            Return tuple:
              ( "True|False" , Retvalue)
              True : command execution ok
              False: command execution failed
              Retvalue: returned value or error string for debug purposes
        """
        methodLocalName = self.__lc_current_method_name()
        localCmd = "SOURce:CURrent:MAXimum"
        localCmdCheck = localCmd + "?"
        if currentToSet == None:
            telnetCmd = "{} \n".format(localCmdCheck)
        else:
            telnetCmd = "{} {} \n".format(localCmd, currentToSet)
        time.sleep(safetyTimeInterval)
        try:
            #self.__lc_msg(telnetCmd)
            response = self.__send_cmd(telnetCmd)
            retVal=response[1]
            retVal=retVal.replace('\n','')
        except Exception as e:
            self.__lc_msg(str(e))
            localMessage = "[{}] Telnet connection ERROR".format(methodLocalName)
            self.__lc_msg(localMessage)
            return False, localMessage
        if currentToSet != None:
            telnetCmd = "{} \n".format(localCmdCheck)
            response = self.__send_cmd(telnetCmd)
            retVal=response[1]
            retVal=retVal.replace('\n','')
            if float(currentToSet) != float(retVal):
                localMessage = "[{}] failed to set to [{}]".format(methodLocalName,currentToSet)
                self.__lc_msg(localMessage)
                return False, retVal
        return True, retVal


    #
    #  Output Current Set/Retrieve
    #
    def get_set_current(self, currentToSet=None, safetyTimeInterval=0):
        """ SM3300 smart power supply
              get_set_current(self, currentToSet=None, safetyTimeInterval=0)
            Purpose:
              set or read the current to supply *** !!! SM3300 COMMAND NOT WORKING - under investigation !!! ***
            Parameters:
              safetyTimeInterval ... time to wait until reset (default 0 sec) it may be set to a different value if specified
	      currentToSet.......... Current to set, if not specified it will be returned a read of the currently set value
            Return tuple:
              ( "True|False" , Retvalue)
              True : command execution ok
              False: command execution failed
              Retvalue: returned value or error string for debug purposes
        """
        methodLocalName = self.__lc_current_method_name()
        localCmd = "SOURce:CURrent"
        localCmdCheck = localCmd + "?"
        if currentToSet == None:
            telnetCmd = "{} \n".format(localCmdCheck)
        else:
            telnetCmd = "{} {} \n".format(localCmd, currentToSet)
        time.sleep(safetyTimeInterval)
        try:
            #self.__lc_msg(telnetCmd)
            response = self.__send_cmd(telnetCmd)
            retVal=response[1]
            retVal=retVal.replace('\n','')
        except Exception as e:
            self.__lc_msg(str(e))
            localMessage = "[{}] Telnet connection ERROR".format(methodLocalName)
            self.__lc_msg(localMessage)
            return False, localMessage
        if currentToSet != None:
            telnetCmd = "{} \n".format(localCmdCheck)
            response = self.__send_cmd(telnetCmd)
            retVal=response[1]
            retVal=retVal.replace('\n','')
            if float(currentToSet) != float(retVal):
                localMessage = "[{}] failed to set to [{}]".format(methodLocalName,currentToSet)
                self.__lc_msg(localMessage)
                return False, retVal
        return True, retVal


    #
    #  Output Current Realtime Measure
    #
    def get_measured_current(self, safetyTimeInterval=0):
        """ SM3300 smart power supply
              get_measured_current(self, safetyTimeInterval=0)
            Purpose:
              read the supplied output current
            Parameters:
              safetyTimeInterval ... time to wait until reset (default 0 sec) it may be set to a different value if specified
            Return tuple:
              ( "True|False" , Retvalue)
              True : command execution ok
              False: command execution failed
              Retvalue: returned value or error string for debug purposes
        """
        methodLocalName = self.__lc_current_method_name()
        telnetCmd = "MEASure:CURrent?"
        time.sleep(safetyTimeInterval)
        try:
            response = self.__send_cmd(telnetCmd)
            retVal=response[1]
            retVal=retVal.replace('\n','')
        except Exception as e:
            self.__lc_msg(str(e))
            localMessage = "[{}] Telnet connection ERROR".format(methodLocalName)
            self.__lc_msg(localMessage)
            return False, localMessage
        return True, retVal



    #==================================
    #  Power related SM3300 methods
    #==================================

    #
    #  Output Current Realtime Measure
    #
    def get_measured_power(self, safetyTimeInterval=0):
        """ SM3300 smart power supply
            Method:
              get_measured_power(self, safetyTimeInterval=0)
            Purpose:
              Provide the real time measure of the power supplied
            Parameters:
              safetyTimeInterval... time to wait before measure (default 0)
                                    (please don't modify this period of time, to avoid delays)
            Return tuple:
              ( "True|False" , Retvalue)
              True : command execution ok
              False: command execution failed
              Retvalue: returned value or error string for debug purposes
        """
        methodLocalName = self.__lc_current_method_name()
        telnetCmd = "MEASure:POWer?"
        time.sleep(safetyTimeInterval)
        try:
            response = self.__send_cmd(telnetCmd)
            retVal=response[1]
            retVal=retVal.replace('\n','')
        except Exception as e:
            self.__lc_msg(str(e))
            localMessage = "[{}] Telnet connection ERROR".format(methodLocalName)
            self.__lc_msg(localMessage)
            return False, localMessage
        return True, retVal



    #==================================
    #  Instrument Switch ON/OFF control
    #==================================

    #
    #  Output Current Set/Retrieve
    #
    def get_set_output_enable(self, powerSupplyState=None, safetyTimeInterval=15):
        """ SM3300 smart power supply
            Method:
              get_set_output_enable(self, powerSupplyState=None, safetyTimeInterval=15)
            Purpose:
              Switch ON/OFF the power to the load or provide the ON/OFF currert state
            Parameters:
              powerSupplyState..... None (default) to read the current stater of the power
                                    "ON"  to switch on the power
                                    "OFF" to switch off the power

              safetyTimeInterval... time to wait before switch on/off the power supply
                                    (please don't reduce this period of time, to avoid NE damages)
            Return tuple:
              ( "True|False" , Retvalue)
              True : command execution ok
              False: command execution failed
              Retvalue: returned value or error string for debug purposes
        """
        methodLocalName = self.__lc_current_method_name()
        localCmd = "OUTPut"
        localCmdCheck = localCmd + "?"
        if powerSupplyState == None:
            telnetCmd = "{} \n".format(localCmdCheck)
        else:
            if powerSupplyState != "ON" and powerSupplyState != "OFF":
                localMessage = "[{}] invalid parameter: specify ON or OFF to turn on or off the power supply".format(methodLocalName)
                #self.__lc_msg(localMessage)
                return False, localMessage
            else:
                telnetCmd = "{} {} \n".format(localCmd, powerSupplyState)
                self.__lc_msg("[{}] Power {} in {} sec.".format(methodLocalName, powerSupplyState,safetyTimeInterval))
                time.sleep(safetyTimeInterval)
        try:
            #self.__lc_msg(telnetCmd)
            response = self.__send_cmd(telnetCmd)
            retVal=response[1]
            retVal=retVal.replace('\n','')
        except Exception as e:
            self.__lc_msg(str(e))
            localMessage = "[{}] Telnet connection ERROR".format(methodLocalName)
            #self.__lc_msg(localMessage)
            return False, localMessage

        if powerSupplyState != None:
            telnetCmd = "{} \n".format(localCmdCheck)
            response = self.__send_cmd(telnetCmd)
            retVal=response[1]
            retVal=retVal.replace('\n','')

            if ((powerSupplyState == "ON") and  (retVal == "0")) or ((powerSupplyState == "OFF") and  (retVal == "1")):
                localMessage = "[{}] failed to set power supply to [{}]".format(methodLocalName,powerSupplyState)
                self.__lc_msg(localMessage)
                if retVal== "0":
                    retVal = "OFF"
                elif retVal== "1":
                    retVal = "ON"
                else:
                    retVal = "ERROR"
                return False, retVal
        #print("RETVAL[{}] type[{}]".format(retVal,type(retVal)))
        if retVal== "0": retVal = "OFF"
        if retVal== "1": retVal = "ON"
        return True, retVal












#######################################################################
#
#   MODULE TEST - Test sequences used for SM3300 testing
#
#######################################################################
if __name__ == "__main__":
    pass

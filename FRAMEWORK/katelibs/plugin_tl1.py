#!/usr/bin/env python
"""
###############################################################################
# MODULE: plugin_tl1.py
#
# AUTHOR: C.Ghelfi
# DATE  : 29/07/2015
#
###############################################################################
"""

import telnetlib
import re
import threading
import time
import os
import sys


class TL1Facility():
    """ Collection of TL1 facilities
    """

    @staticmethod
    def decode(tl1_msg):
        """ Decompose an ASCII TL1 Message response to structured format
            tl1_msg : plain TL1 message (both Response or autonomous type)
            Return Value: a dictionary filled with following elements:
                - for all message type
                    'SID'        : the equipment's SID
                    'DATE'       : timestamp (date)
                    'TIME'       : timestamp (time)
                    'MSG_CODE'   : 'M' / '*C' / '**' / '*' / 'A'
                    'TAG'        : the message TAG
                - for Commands
                    'CMD_CMPL'   : COMPLD / DELAY / DENY / PRTL / RTRV
                    'CMD_BODY_OK': Body Section(Only for successfull command response)
                                   list of 1 or more items - Dictionary:
                                     aid : AID of element (key for dictionary)
                                         'VALUES' : sequence ATTR=Value
                                         'STATE'  : Primary and Secondary state
                    'CMD_BODY_KO': Body Section (Only for failure command response)
                                   list of two string response specification
                - for Spontaneous Message
                    'EVE_VMM'    : Verb and modifiers
                    'EVE_BODY'   : dictionary
        """
        f_header = True
        f_ident  = True
        f_block  = True

        is_event = False

        msg = {}    # Dictionary of decomposed TL1 message

        for line in tl1_msg.split('\n'):
            if f_header:
                if line.strip() == "":
                    continue

                msg['SID']  = " ".join(line.split()[:-2]).replace('"', '')
                msg['DATE'] = line.split()[-2]
                msg['TIME'] = line.split()[-1]
                f_header = False
                continue

            if f_ident:
                words = line.split()
                is_event = TL1Facility.__is_event(words[0])

                msg['MSG_CODE'] = words[0]
                msg['TAG']      = words[1]

                if is_event:
                    msg['EVE_VMM']     = words[2:]
                else:
                    msg['CMD_CMPL']    = words[2]
                    msg['CMD_BODY_OK'] = {}
                    msg['CMD_BODY_KO'] = []

                f_ident = False
                continue

            if f_block:
                if is_event:
                    # Event Response
                    words = line.strip().replace('"', '').split(':')
                    msg['EVE_AID']    = words[0]
                    msg['EVE_TEXT']   = words[1]
                    f_block = False
                    continue

                # Command Response
                stripped_line = line.strip()
                if ( stripped_line.find('/*') != -1                      and
                     stripped_line.find("[{:s}]".format(msg['TAG'])) != -1 and
                     stripped_line.find('*/') != -1                      ):
                    # REMARK found - closing capture
                    break
                if msg['CMD_CMPL'] == "COMPLD":
                    words = stripped_line.replace('"', '').split(':')
                    row = {}
                    row[ words[0] ] = {'VALUES' : words[2], 'STATE' : words[3]}
                    msg['CMD_BODY_OK'].update(row)
                elif msg['CMD_CMPL'] == "DENY":
                    if len(stripped_line) == 4:
                        msg['CMD_ERR'] = stripped_line
                    else:
                        msg['CMD_BODY_KO'].append(stripped_line)
                else:
                    print("[{:s}] NON ANCORA GESTITO".format(msg['CMD_CMPL']))
                continue

            if line == ';':
                # TERMINATOR found - closing capture
                break

        return msg


    @staticmethod
    def encode(msg, codec="ASCII"):
        """ Format the structured TL1 message to supplied coded
            msg   : structured TL1 Message
            codec : "ASCII" / "JSON"
        """
        new_msg = ""
        if   codec == "ASCII":
            pass
        elif codec == "JSON":
            pass
        else:
            pass

        return new_msg


    @staticmethod
    def get_sid(msg):
        """ Analize structured TL1 Response
            msg : structured TL1 Message
            Return value:
                sid
        """
        return msg['SID']


    @staticmethod
    def get_time_stamp(msg):
        """ Analize structured TL1 Response
            msg : structured TL1 Message
            Return value:
                (date, time)
        """
        return msg['DATE'], msg['TIME']


    @staticmethod
    def get_message_code(msg):
        """ Analize structured TL1 Response
            msg : structured TL1 Message
            Return value:
                code    := "M" / "**" / "*C" / "*" / "A"
        """
        return msg['MSG_CODE']


    @staticmethod
    def get_tag(msg):
        """ Analize structured TL1 Response
            msg : structured TL1 Message
            Return value:
                tag
        """
        return msg['TAG']


    @staticmethod
    def get_cmd_status(msg):
        """ Analize structured TL1 Response
            msg : structured TL1 Message
            Return value:
                (True, code)    with code := "COMPLD" / "DENY"
                (False, None)   if supplied mes isn't a command response
        """
        if TL1Facility.__is_event(msg['MSG_CODE']):
            return False, None

        return True, msg['CMD_CMPL']


    @staticmethod
    def get_cmd_aid_list(msg):
        """ Analize structured TL1 Response
            msg : structured TL1 Message
            Return value:
                list of AIDs found
                None if msg isnt a COMPLETED TL1 command response
        """
        if TL1Facility.__is_event(msg['MSG_CODE']):
            print("EVENTO")
            return None

        if TL1Facility.get_cmd_status(msg) != (True, "COMPLD"):
            print("COMANDO FALLITO")
            return None

        return list(msg['CMD_BODY_OK'].keys())


    @staticmethod
    def get_cmd_status_value(msg, aid):
        """ Analize structured TL1 Response
            msg  : structured TL1 Message
            aid  : an AID
            Return value:
                (pst,sst)   primary and secondary state
                (None,None) if msg isnt a COMPLETED TL1 command response
        """
        if TL1Facility.__is_event(msg['MSG_CODE']):
            return None

        if TL1Facility.get_cmd_status(msg) != (True, "COMPLD"):
            return None

        the_elem = msg['CMD_BODY_OK'].get(aid)
        if the_elem is not None:
            return the_elem['STATE'].split(',')
        else:
            return None, None


    @staticmethod
    def get_cmd_attr_value(msg, aid, attr):
        """ Analize structured TL1 Response
            msg  : structured TL1 Message
            aid  : an AID
            attr : a specific Attribute Name
            Return value:
                attribute value (None if supplied aid or attr isn't found)
                None if msg isnt a COMPLETED TL1 command response
        """
        if TL1Facility.__is_event(msg['MSG_CODE']):
            return None

        if TL1Facility.get_cmd_status(msg) != (True, "COMPLD"):
            return None

        for  i  in  msg['CMD_BODY_OK'].get(aid)['VALUES'].split(','):
            the_attr, the_value = i.split('=')
            if the_attr == attr:
                return the_value

        return None


    @staticmethod
    def get_cmd_error_frame(msg):
        """ Analize structured TL1 Response
            msg : structured TL1 Message
            Return value:
                (True, str1, str2)    str1 and str contains the DENY response values
                (False, None, None)   if supplied msg isn't a command response
        """
        if TL1Facility.__is_event(msg['MSG_CODE']):
            return False, None, None

        if msg['CMD_CMPL'] != "DENY":
            return False, None, None

        return True, msg['CMD_ERR'], msg['CMD_BODY_KO']


    @staticmethod
    def __is_event(msg_code):
        """ INTERNAL USAGE
        """
        return ( msg_code == '*C' or
                 msg_code == '**' or
                 msg_code == '*'  or
                 msg_code == 'A'  )



class Plugin1850TL1():
    """
    TL1 plugin for 1850TSS Equipment
    """
    TL1_TIMEOUT = 1200   # defalt timeout for commands result


    def __init__(self, IP, PORT=3083, krepo=None, eRef=None):
        """
        Costructor for generic TL1 interface
        IP   : equipment's IP Address
        PORT : TL1 interface Port
        """

        self.__the_ip      = IP
        self.__the_port    = PORT
        self.__krepo       = krepo # result report (Kunit class instance)
        self.__eqpt_ref    = eRef  # equipment reference
        self.__if_cmd      = None  # main TL1 interface (used for sending usr command)
        self.__if_eve      = None  # secondary TL1 interface (used for capturing events)
        self.__last_output = ""    # store the output of latest TL1 command

        # Activating both command and Event interfaces
        #self.__connect("CMD")
        #self.__connect("EVE")
        print("tl1 connect skipped")

        # File for Event collector
        self.__fn   = "collector.log"   # temporaneo
        self.__f = open(self.__fn, "w")
        os.chmod(self.__fn, 0o644)

        # Semaphore for TL1 Event Collector info area
        self.__thread_lock    = threading.Lock()

        # Flags for TL1 Event Collector
        self.__do_event_loop  = True  # Thread termination flag
        self.__enable_collect = False # Status of Event Collector

        # TL1 Event Collector Thread Initialization and Starting
        self.__thread = threading.Thread(   target=self.__thr_manager,
                                            name="TL1_Event_Collector"  )
        self.__thread.daemon = False
        self.__thread.start()


    def __del__(self):
        """ INTERNAL USAGE
        """
        # self.__disconnect()


    def get_last_outcome(self):
        """ Return the latest TL1 command output (multi-line string)
        """
        return self.__last_output


    def do(self, cmd, policy="COMPLD", timeout=None, condPST=None, condSST=None):
        """ Send the specified TL1 command to equipment.
            It is possible specify an error behaviour and/or a matching string
            cmd     : the TL1 command string
            policy  : "COMPLD" -> specify if a positive result has been expected (default behaviour)
                      "DENY"   -> specify if a negative result has been expected
                      "COND"   -> specify a conditional command execution (see condXXX parameters)
                      It is ignored when policy="DENY"
            timeout : (secons) timeout to close a conditional command
            condPST : (used only on polity="COND") a COMPLD will be detected if the Primary State
                      for involved AID goes to specified value. The timeout parameters will be
                      evaluated in order to close procedure
            condSST : (used only on polity="COND") a COMPLD will be detected if the Secondary State
                      for involved AID goes to specified value. The timeout parameters will be
                      evaluated in order to close procedure
        """

        if self.__krepo:
            self.__krepo.start_time()

        result = self.__do("CMD", cmd, policy, timeout, condPST, condSST)

        if result:
            self.__t_success(cmd, None, self.get_last_outcome())
        else:
            self.__t_failure(cmd, None, self.get_last_outcome(), "")

        return result


    def __do(self, channel, cmd, policy, timeout, condPST, condSST):
        """ INTERNAL USAGE
        """
        if channel == "CMD":
            print("sending [{:s}]".format(cmd))
            theIF = self.__if_cmd
        else:
            print("sending [{:s}] (EVENT INTERFACE)".format(cmd))
            theIF = self.__if_eve

        verb_lower = cmd.replace(";", "").split(":")[0].lower().replace("\r", "").replace("\n", "")

        # Trash all trailing characters from stream
        if self.__read_all(channel):
            print("error in sending tl1 command")

        to_repeat = True
        while to_repeat:
            try:
                while str(theIF.read_very_eager().strip(), 'utf-8') != "":
                    pass
                to_repeat = False
            except Exception as eee:
                print("Error in tl1.do({:s})\nException: {:s}".format(cmd, str(eee)))
                # renewing interface
                theIF = self.__connect(channel)

        # Sending command to interface
        if self.__write(channel, cmd) == False:
            print("error in sending tl1 command")


        if cmd.lower() == "canc-user;":
            msg_str = " COMPLD "
        else:
            msg_str  = ""
            keepalive_count_max = 100
            keepalive_count = 0

            while True:
                res_list  = self.__expect(channel, [b"\n\>", b"\n\;"])
                if res_list == ([], [], []):
                    print("error in sending tl1 command")

                match_idx = res_list[0]
                msg_tmp   = str(res_list[2], 'utf-8')

                if msg_tmp.find("\r\n\n") == -1:
                    continue

                resp_part_list = msg_tmp.split("\r\n\n")
                msg_tmp        = "\r\n\n".join(resp_part_list[1:])

                if match_idx ==  1:
                    if     msg_tmp.find(" REPT ") != -1:
                        continue

                    elif   msg_tmp.find("KEEP ALIVE MESSAGE") != -1 :
                        keepalive_count = keepalive_count + 1
                        if keepalive_count == keepalive_count_max:
                            return 1
                        continue

                    else:
                        msg_str = msg_str + re.sub('(\r\n)+', "\r\n", msg_tmp, 0)
                        if verb_lower != "ed-pid"  and  verb_lower != "act-user":
                            if msg_str.count(";") > 1:
                                return 1
                        if msg_str.strip() == ";":
                            continue
                        break

                elif match_idx ==  0:
                    msg_str = msg_str + msg_tmp + "\n"
                    continue

            msg_str = re.sub('(\r\n)+', "\r\n", msg_str, 0)

        self.__last_output = msg_str

        if  (msg_str.find(" COMPLD") != -1  or
             msg_str.find(" DELAY")  != -1  ):
            # Positive TL1 response
            result = (policy == "COMPLD")
        else:
            # Negative TL1 response
            result = (policy == "DENY")

        # valutare l'espressione regolare prima di restituire result
        # ###

        print("DEBUG: result := " + str(result))

        return result


    def __read_all(self, channel):
        """ INTERNAL USAGE
        """
        if channel == "CMD":
            theIF = self.__if_cmd
        else:
            theIF = self.__if_eve

        for retry in (1,2):
            try:
                while str(theIF.read_very_eager().strip(), 'utf-8') != "":
                    pass
                return True
            except Exception as eee:
                print("TL1 interface not available - retry...")
                # renewing interface
                theIF = self.__connect(channel)

        return False


    def __write(self, channel, cmd):
        """ INTERNAL USAGE
        """
        if channel == "CMD":
            theIF = self.__if_cmd
        else:
            theIF = self.__if_eve

        for retry in (1,2):
            try:
                theIF.write(cmd.encode())
                return True
            except Exception as eee:
                print("TL1 interface not available - retry...")
                # renewing interface
                theIF = self.__connect(channel)

        return False


    def __expect(self, channel, key_list):
        """ INTERNAL USAGE
        """
        if channel == "CMD":
            theIF = self.__if_cmd
        else:
            theIF = self.__if_eve

        for retry in (1,2):
            try:
                res_list = theIF.expect(key_list)
                return res_list
            except Exception as eee:
                print("TL1 interface not available - retry...")
                # renewing interface
                theIF = self.__connect(channel)

        return [],[],[]


    def __connect(self, channel):
        """ INTERNAL USAGE
        """
        if channel == "CMD":
            try:
                print("(re)connecting TL1...")
                self.__if_cmd = telnetlib.Telnet(self.__the_ip, self.__the_port, 5)
                print("... TL1 interface for commands ready.")
            except Exception as eee:
                print("TL1: error connecting CMD channel - {:s}".format(str(eee)))
                print(self.__if_cmd)
            return self.__if_cmd
        else:
            try:
                self.__if_eve = telnetlib.Telnet(self.__the_ip, self.__the_port, 5)
                print("... TL1 interface for events ready.")
            except Exception as eee:
                print("TL1: error connecting EVE channel - {:s}".format(str(eee)))
                print(self.__if_cmd)
            return self.__if_eve


    def __disconnect(self):
        """ INTERNAL USAGE
        """
        try:
            self.__do("EVE", "CANC-USER;", "COMPLD", None, None, None)
        except Exception as eee:
            msg = "Error in disconnection - {:s}".format(str(eee))
            print(msg)

        self.__if_eve = None

        try:
            self.__do("CMD", "CANC-USER;", "COMPLD", None, None, None)
        except Exception as eee:
            msg = "Error in disconnection - {:s}".format(str(eee))
            print(msg)

        self.__if_cmd = None


    def event_collection_start(self):
        """ Start TL1 event collection
        """
        self.__enable_collect = True


    def event_collection_stop(self):
        """ Stop TL1 event collection
        """
        self.__enable_collect = False


    def thr_event_terminate(self):
        """ TODO
        """
        with self.__thread_lock:
            self.__do_event_loop = False


    def __thr_manager(self):
        """ INTERNAL USAGE
        """
        # thread main
        print("Entro in __thr_manager")
        while True:
            with self.__thread_lock:
                do_repeat = self.__do_event_loop

            if do_repeat:
                self.__thr_init()
                self.__thr_event_loop()
            else:
                break


    def __thr_init(self):
        """ INTERNAL USAGE
        """
        connected = False

        while not connected:
            with self.__thread_lock:
                do_repeat = self.__do_event_loop

            if not do_repeat:
                break

            if self.__enable_collect:
                connected = self.__do(  "EVE",
                                        "ACT-USER::admin:MYTAG::Alcatel1;",
                                        policy="COMPLD",
                                        timeout=None,
                                        condPST=None,
                                        condSST=None  )
            time.sleep(1)


    def __thr_event_loop(self):
        """ INTERNAL USAGE
        """
        while True:
            with self.__thread_lock:
                do_repeat = self.__do_event_loop

            if not do_repeat:
                break

            msg_str  = ""

            while True:
                res_list  = self.__if_eve.expect([b"\n\>", b"\n\;"], timeout=10)
                match_idx = res_list[0]
                msg_tmp   = str(res_list[2], 'utf-8')

                if match_idx == -1:
                    # Timeout Detected
                    timeout_detected = True
                    break
                else:
                    timeout_detected = False

                if msg_tmp.find("\r\n\n") == -1:
                    continue

                resp_part_list = msg_tmp.split("\r\n\n")
                msg_tmp        = "\r\n\n".join(resp_part_list[1:])

                if   match_idx ==  1:
                    # Ending block detected (';' at begin of line)
                    msg_str = msg_str + re.sub('(\r\n)+', "\r\n", msg_tmp, 0)
                    if msg_str.strip() == ";":
                        continue
                    break

                elif match_idx ==  0:
                    # Continuoing mark detected ('>' at begin of line)
                    msg_str = msg_str + msg_tmp + "\n"
                    continue

            msg_str = re.sub('(\r\n)+', "\r\n", msg_str, 0)

            if not timeout_detected:
                if self.__enable_collect:
                    coded_msg = TL1Facility.decode(msg_str)
                    # self.__f.writelines(TL1Facility.encode(coded_msg, "JSON"))
                    self.__f.writelines("{:s}\n{:s}\n".format("-" * 80, msg_str))


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



if __name__ == "__main__":
    print("DEBUG")

    msg1 = "\n\
   PLEASE-SET-SID-C8A00 15-10-04 17:01:56\n\
*  243 REPT ALM EQPT\n\
   \"MDL-1-1-18:MN,ABNORMAL,NSA,10-04,17-01-56,NEND\"\n\
;\n\
"

    msg2 = "\n\
\n\
\n\
   PLEASE-SET-SID-C8A00 15-10-04 18:35:10\n\
M  379 COMPLD\n\
   \"EC320-1-1-1::PROVISIONEDTYPE=EC320,ACTUALTYPE=EC320,AINSMODE=NOWAIT,ALMPROF=LBL-ASAPEQPT-SYSDFLT,REGION=ETSI,PROVMODE=MANEQ-AUTOFC:OOS-AU,WRK&FLT\"\n\
   /* RTRV-EQPT::MDL-1-1-1 [379] (536871116) */\n\
;\n\
"

    msg3 = "\n\
\n\
\n\
   PLEASE-SET-SID-C8A00 15-10-04 20:31:15\n\
M  165 COMPLD\n\
   \"EC320-1-1-1::PROVISIONEDTYPE=EC320,ACTUALTYPE=EC320,AINSMODE=NOWAIT,ALMPROF=LBL-ASAPEQPT-SYSDFLT,REGION=ETSI,PROVMODE=MANEQ-AUTOFC:OOS-AU,WRK&FLT\"\n\
   \"MDL-1-1-18::ACTUALTYPE=PP1GE,AUTOPROV=OFF:OOS-MA,UAS\"\n\
   /* RTRV-EQPT::MDL-1-1-1&-18 [165] (536871116) */\n\
;\n\
"

    msg4 = "\n\
\n\
\n\
   PLEASE-SET-SID-C8A00 15-10-05 17:25:40\n\
M  792 DENY\n\
   IEAE\n\
   /* Input, Entity Already Exists */\n\
   /* Equipment is already Provisioned */\n\
   /* ENT-EQPT::PP1GE-1-1-18::::PROVISIONEDTYPE=PP1GE:IS [792] (536871116) */\n\
;\n\
"

    msg5 = "\n\
   \"nodeA - .TDM.EM_TEST.RtrvEqptALL\" 15-10-15 21:47:33\n\
M  963 COMPLD\n\
   \"SHELF-1-1::PROVISIONEDTYPE=UNVRSL320,ACTUALTYPE=UNVRSL320,AINSMODE=NOWAIT,SHELFNUM=1,SHELFROLE=MAIN,ALMPROF=LBL-ASAPEQPT-SYSDFLT,REGION=ETSI,PROVMODE=MANEQ-AUTOFC:IS\"\n\
   \"EC320-1-1-1::PROVISIONEDTYPE=EC320,ACTUALTYPE=UNKNOWN,AINSMODE=NOWAIT,ALMPROF=LBL-ASAPEQPT-SYSDFLT,REGION=ETSI,PROVMODE=MANEQ-AUTOFC:OOS-AU,WRK&FLT\"\n\
   \"MDL-1-1-2::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-3::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-4::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-5::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-6::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-7::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-8::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-9::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MT320-1-1-10::PROVISIONEDTYPE=MT320,ACTUALTYPE=UNKNOWN,AINSMODE=NOWAIT,ALMPROF=LBL-ASAPEQPT-SYSDFLT,REGION=ETSI,PROVMODE=MANEQ-AUTOFC:OOS-AU,WRK&UEQ\"\n\
   \"MT320-1-1-11::PROVISIONEDTYPE=MT320,ACTUALTYPE=UNKNOWN,AINSMODE=NOWAIT,ALMPROF=LBL-ASAPEQPT-SYSDFLT,REGION=ETSI,PROVMODE=MANEQ-AUTOFC:OOS-AU,STBYH&UEQ\"\n\
   \"MDL-1-1-12::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-13::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-14::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-15::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-16::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-17::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"PP1GE-1-1-18::PROVISIONEDTYPE=PP1GE,ACTUALTYPE=UNKNOWN,AINSMODE=NOWAIT,ALMPROF=LBL-ASAPEQPT-SYSDFLT,REGION=ETSI,PROVMODE=MANEQ-AUTOFC:OOS-AU,FLT\"\n\
   \"MDL-1-1-18-1::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-18-2::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-18-3::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-18-4::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-18-5::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-18-6::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-18-7::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-18-8::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-18-9::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-18-10::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-19::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-20::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-21::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-22::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-23::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-24::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-25::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-26::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-27::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-28::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-29::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-30::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-31::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-32::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-33::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-34::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-35::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-36::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"POW320-1-1-37::PROVISIONEDTYPE=PSF320,ACTUALTYPE=UNKNOWN,AINSMODE=NOWAIT,ALMPROF=LBL-ASAPEQPT-SYSDFLT,REGION=ETSI,PROVMODE=MANEQ-AUTOFC:OOS-AU,MEA\"\n\
   \"MDL-1-1-38::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"POW320-1-1-39::PROVISIONEDTYPE=PSF320,ACTUALTYPE=UNKNOWN,AINSMODE=NOWAIT,ALMPROF=LBL-ASAPEQPT-SYSDFLT,REGION=ETSI,PROVMODE=MANEQ-AUTOFC:OOS-AU,MEA\"\n\
   \"FAN320-1-1-40::PROVISIONEDTYPE=FAN320,ACTUALTYPE=UNKNOWN,AINSMODE=NOWAIT,ALMPROF=LBL-ASAPEQPT-SYSDFLT,REGION=ETSI,PROVMODE=MANEQ-AUTOFC:OOS-AU,FLT\"\n\
   \"FAN320-1-1-41::PROVISIONEDTYPE=FAN320,ACTUALTYPE=UNKNOWN,AINSMODE=NOWAIT,ALMPROF=LBL-ASAPEQPT-SYSDFLT,REGION=ETSI,PROVMODE=MANEQ-AUTOFC:OOS-AU,FLT\"\n\
   \"TBUS-1-1-42::PROVISIONEDTYPE=TBUS320,ACTUALTYPE=UNKNOWN,AINSMODE=NOWAIT,ALMPROF=LBL-ASAPEQPT-SYSDFLT,REGION=ETSI,PROVMODE=MANEQ-AUTOFC:IS\"\n\
   \"TBUS-1-1-43::PROVISIONEDTYPE=TBUS320,ACTUALTYPE=UNKNOWN,AINSMODE=NOWAIT,ALMPROF=LBL-ASAPEQPT-SYSDFLT,REGION=ETSI,PROVMODE=MANEQ-AUTOFC:IS\"\n\
   /* RTRV-EQPT::ALL [963] (536871273) */\n\
;\n\
"

    if False:
        print("[{:s}]\n{:s}".format(msg5, "-" * 80))
        print(TL1Facility.decode(msg5))
        sys.exit(0)

        print("#" * 80)

        print("[{:s}]\n{:s}".format(msg3, "-" * 80))
        mm = TL1Facility.decode(msg3)
        print(mm)
        print("@@@")
        lista = TL1Facility.get_cmd_aid_list(mm)
        #print(lista[0] + " " + TL1Facility.get_cmd_status_value(mm, lista[0])[0])
        #print(lista[0] + " " + TL1Facility.get_cmd_status_value(mm, lista[0])[1])
        #print(lista[1] + " " + TL1Facility.get_cmd_status_value(mm, lista[1])[0])
        #print(lista[1] + " " + TL1Facility.get_cmd_status_value(mm, lista[1])[1])
        print(TL1Facility.get_cmd_attr_value(mm, "EC320-1-1-1", "REGION"))
        print(TL1Facility.get_cmd_attr_value(mm, "EC320-1-1-1", "PIPPO"))
        print(TL1Facility.get_cmd_attr_value(mm, "MDL-1-1-18", "AUTOPROV"))
        print("@@@")

        print("#" * 80)

        print("[{:s}]\n{:s}".format(msg4, "-" * 80))
        mm = TL1Facility.decode(msg4)
        print(mm)
        if False:
            v1,v2,v3 = TL1Facility.get_cmd_error_frame(mm)
            if v1:
                print("ERRORE: " + v2)
                print(v3[0])
                print(v3[1])

            print("-" * 80)
        #TL1Facility.encode(m, "ASCII")

        sys.exit(0)

    tl1 = Plugin1850TL1("135.221.125.79")

    if False:
        # DB PULITO
        tl1.do("ACT-USER::admin:MYTAG::Root1850;")
        tl1.do("ED-PID::admin:::Root1850,Alcatel1,Alcatel1;")
        #
        tl1.do("SET-PRMTR-NE::::::REGION=ETSI,PROVMODE=MANEQ-AUTOFC;")
        tl1.do("RTRV-PRMTR-NE;")
        tl1.do("SET-ATTR-SECUDFLT::::::MAXSESSION=6;")
        tl1.do("ENT-EQPT::SHELF-1-1::::PROVISIONEDTYPE=UNVRSL320,SHELFNUM=1,SHELFROLE=MAIN;")
    else:
        # DB Inizializzato
        tl1.do("ACT-USER::admin:MYTAG::Alcatel1;")
        tl1.event_collection_start()
        time.sleep(2)
        tl1.do("ENT-EQPT::PP1GE-1-1-18::::PROVISIONEDTYPE=PP1GE:IS;", policy="COND", condPST="IS")
        time.sleep(30)
        tl1.do("RTRV-EQPT::MDL-1-1-18;")
        res = tl1.get_last_outcome()
        print(res)
        #print(TL1Facility.decode(res))
        tl1.do("RMV-EQPT::PP1GE-1-1-18;")
        tl1.do("DLT-EQPT::PP1GE-1-1-18;")

    time.sleep(1)

    tl1.thr_event_terminate()

    print("FINE")
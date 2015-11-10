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
import json


class TL1message():
    """ Collection of TL1 facilities
    """

    def __init__(self, tl1_msg):
        """
            Structured representation of generic TL1 Message
            A dictionary with following elements will be generated for a TL1 response message:
            - common for all message types:
                'C_SID'     : the equipment's SID
                'C_DATE'    : timestamp (date)
                'C_TIME'    : timestamp (time)
                'C_CODE'    : 'M' / '*C' / '**' / '*' / 'A'
                'C_TAG'     : the message TAG
            - only for Commands Response:
                'R_STATUS'  : COMPLD / DELAY / DENY / PRTL / RTRV
                'R_BODY_OK' : Body Section(Only for successfull command response)
                              list of 1 or more items - Dictionary:
                                 aid : AID of element (key for dictionary)
                                     'VALUES' : sequence ATTR=Value
                                     'STATE'  : Primary and Secondary state
                'R_BODY_KO' : Body Section (Only for failure command response)
                               list of two string response specification
            - only for Spontaneous Messages:
                'S_VMM'     : Verb and modifiers
                'S_BODY'    : dictionary
        """

        self.__m_plain = tl1_msg    # Plain ascii TL1 Message Response
        self.__m_coded = {}         # Coded Tl1 Message Response (dictionary)
        self.__m_event = None       # True is the message is a Spontaneous Message

        if tl1_msg is not None  and  tl1_msg != "":
            self.encode()


    def encode(self):
        """ Decompose an ASCII TL1 Message response to structured format
        """
        self.__m_event = False
        self.__m_coded = {}

        f_header = True
        f_ident  = True
        f_block  = True

        for line in self.__m_plain.split('\n'):
            if f_header:
                if line.strip() == "":
                    continue

                self.__m_coded['C_SID']  = " ".join(line.split()[:-2]).replace('"', '')
                self.__m_coded['C_DATE'] = line.split()[-2]
                self.__m_coded['C_TIME'] = line.split()[-1]
                f_header = False
                continue

            if f_ident:
                words = line.split()
                self.__m_event = ( words[0] == '*C' or
                                   words[0] == '**' or
                                   words[0] == '*'  or
                                   words[0] == 'A'  )

                self.__m_coded['C_CODE'] = words[0]
                self.__m_coded['C_TAG']  = words[1]

                if self.__m_event:
                    self.__m_coded['S_VMM'] = words[2:]
                else:
                    self.__m_coded['R_STATUS']  = words[2]
                    self.__m_coded['R_BODY_OK'] = {}
                    self.__m_coded['R_BODY_KO'] = []
                    self.__m_coded['R_ERROR']   = ""

                f_ident = False
                continue

            if f_block:
                if self.__m_event:
                    # Event Response
                    words = line.strip().replace('"', '').split(':')
                    self.__m_coded['EVE_AID']  = words[0]
                    self.__m_coded['EVE_TEXT'] = words[1]
                    f_block = False
                    continue

                # Command Response
                stripped_line = line.strip()
                if ( stripped_line.find('/*') != -1                                     and
                     stripped_line.find("[{:s}]".format(self.__m_coded['C_TAG'])) != -1 and
                     stripped_line.find('*/') != -1                                     ):
                    # REMARK found - closing capture
                    break
                if self.__m_coded['R_STATUS'] == "COMPLD":
                    words = stripped_line.replace('"', '').split(':')
                    row = {}
                    row[ words[0] ] = {'VALUES' : words[2], 'STATE' : words[3]}
                    self.__m_coded['R_BODY_OK'].update(row)
                elif self.__m_coded['R_STATUS'] == "DENY":
                    if len(stripped_line) == 4:
                        self.__m_coded['R_ERROR'] = stripped_line
                    else:
                        self.__m_coded['R_BODY_KO'].append(stripped_line)
                else:
                    print("[{:s}] NON ANCORA GESTITO".format(self.__m_coded['R_STATUS']))
                continue

            if line == ';':
                # TERMINATOR found - closing capture
                break


    def decode(self, codec="ASCII"):
        """ Format the structured TL1 message to supplied coded
            codec : "ASCII" / "JSON"
        """
        new_msg = ""
        if   codec == "ASCII":
            pass
        elif codec == "JSON":
            new_msg = json.dumps(self.__m_coded, indent=4, sort_keys=True)
        else:
            print("Codec not managed")

        return new_msg


    def get_sid(self):
        """ Return the SID
        """
        return self.__m_coded['C_SID']


    def get_time_stamp(self):
        """ Return a couple of string (date, time) for Message Time Stamp
        """
        return self.__m_coded['C_DATE'], self.__m_coded['C_TIME']


    def get_message_code(self):
        """ Return the TL1 Message code as follow: "M" / "**" / "*C" / "*" / "A"
        """
        return self.__m_coded['C_CODE']


    def get_tag(self):
        """ Return the TL1 Tag
        """
        return self.__m_coded['C_TAG']


    def get_cmd_status(self):
        """ Return a couple (result, code) as follow:
            result := True/False (True for TL1 respone message, False for spontaneous messages)
            code   := "COMPLD" / "DENY" / None     (None for spontaneous messages)
        """
        print(self.__m_coded)
        print(self.__m_event)
        if self.__m_event:
            return False, None

        return True, self.__m_coded['R_STATUS']


    def get_cmd_aid_list(self):
        """ Return the AID list found on message
            If TL1 Message is a spontaneous message, or the command is failed, a None is returned
        """
        if self.__m_event:
            return None

        if self.get_cmd_status() != (True, "COMPLD"):
            return None

        return list(self.__m_coded['R_BODY_OK'].keys())


    def get_cmd_status_value(self, aid):
        """ Return a couple (pst,sst) for command response
            (None, None) for not completed TL1 Messages
        """
        if self.__m_event:
            return None

        if self.get_cmd_status() != (True, "COMPLD"):
            return None

        the_elem = self.__m_coded['R_BODY_OK'].get(aid)
        if the_elem is None:
            return None, None

        return the_elem['STATE'].split(',')


    def get_cmd_attr_value(self, aid, attr):
        """ Return the value for specified attribute and AID
            None if wrong parameters are supplied
        """
        if self.__m_event:
            return None

        if self.get_cmd_status() != (True, "COMPLD"):
            return None

        for  i  in  self.__m_coded['R_BODY_OK'].get(aid)['VALUES'].split(','):
            the_attr, the_value = i.split('=')
            if the_attr == attr:
                return the_value

        return None


    def get_cmd_error_frame(self):
        """ Return a tuple (result, str1, str2) for a DENY response message
            'result' is False if the message isn't a command response
            'str1' and 'str2' contanis the DENY reponse values
        """
        if self.__m_event:
            return False, None, None

        if self.__m_coded['R_STATUS'] != "DENY":
            return False, None, None

        return True, self.__m_coded['R_ERROR'], self.__m_coded['R_BODY_KO']




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


    def do_until(self, cmd, timeout=None, condPST=None, condSST=None):
        """ Send the specified TL1 command to equipment until almost one of conditions will be
            reached.
            cmd     : the TL1 command string
            timeout : (secons) timeout to terminate loop
            condPST : a COMPLD will be detected if the Primary State
                      for involved AID goes to specified value. The timeout parameters will be
                      evaluated in order to close procedure
            condSST : a COMPLD will be detected if the Secondary State
                      for involved AID goes to specified value. The timeout parameters will be
                      evaluated in order to close procedure
        """
        if timeout is None:
            timeout = self.TL1_TIMEOUT

        error_msg = ""

        if self.__krepo:
            self.__krepo.start_time()

        ending_time = int(time.time()) + timeout

        while True:
            result = self.__do("CMD", cmd, "COMPLD", timeout)

            if int(time.time()) <= ending_time:
                msg_coded = TL1message(self.__last_output)
                aid_list = msg_coded.get_cmd_aid_list()
                pst,sst = msg_coded.get_cmd_status_value(aid_list[0])
                if pst is not None:
                    if pst == condPST:
                        result = True
                        break
                else:
                    error_msg = "No AID found on TL1 response"
                    result = False
                    break
                time.sleep(1)
            else:
                print("TIMEOUT ON TL1::do()")
                error_msg = "TIMEOUT ({:d}s) DETECTED ON SENDING '{:s}'".format(timeout, cmd)
                result = False
                break

        print("DEBUG: result := {:s} - errmsg := [{:s}]\n".format(str(result), error_msg))

        if result:
            self.__t_success(cmd, None, self.get_last_outcome())
        else:
            self.__t_failure(cmd, None, self.get_last_outcome(), error_msg)

        return result


    def do(self, cmd, policy="COMPLD", timeout=None, condPST=None, condSST=None):
        """ Send the specified TL1 command to equipment.
            It is possible specify an error behaviour and/or a matching string
            cmd     : the TL1 command string
            policy  : "COMPLD" -> specify if a positive result has been expected (default behaviour)
                      "DENY"   -> specify if a negative result has been expected
                      "COND"   -> specify a conditional command execution (see condXXX parameters)
                      It is ignored when policy="DENY"
            timeout : (secons) timeout to close a conditional command
            condPST : (used only on policy="COND") a COMPLD will be detected if the Primary State
                      for involved AID goes to specified value. The timeout parameters will be
                      evaluated in order to close procedure
            condSST : (used only on policy="COND") a COMPLD will be detected if the Secondary State
                      for involved AID goes to specified value. The timeout parameters will be
                      evaluated in order to close procedure
        """

        if policy == "COND":
            if condPST is None  and  condSST is None:
                print("ATTENZIONE: ALMENO UNO TRA condPST e condSST deve essere valorizzato")
                return False

        if timeout is None:
            timeout = self.TL1_TIMEOUT

        error_msg = ""

        if self.__krepo:
            self.__krepo.start_time()

        result = self.__do("CMD", cmd, policy, timeout)

        if result  and  policy == "COND":
            # Evaluation of result conditions
            msg_coded = TL1message(self.__last_output)
            aid_list = msg_coded.get_cmd_aid_list()
            pst,sst = msg_coded.get_cmd_status_value(aid_list[0])

            if pst is not None:
                result = (pst == condPST)
            else:
                error_msg = "No AID found on TL1 response"
                result = False

        print("DEBUG: result := {:s} - errmsg := [{:s}]\n".format(str(result), error_msg))

        if result:
            self.__t_success(cmd, None, self.get_last_outcome())
        else:
            self.__t_failure(cmd, None, self.get_last_outcome(), error_msg)

        return result


    def __do(self, channel, cmd, policy, timeout):
        """ INTERNAL USAGE
        """
        if channel == "CMD":
            print("sending [{:s}]".format(cmd))
        else:
            print("sending [{:s}] (EVENT INTERFACE)".format(cmd))

        verb_lower = cmd.replace(";", "").split(":")[0].lower().replace("\r", "").replace("\n", "")

        # Trash all trailing characters from stream
        if self.__read_all(channel) == False:
            print("error [1] sending TL1 command [{:s}]".format(cmd))

        # Sending command to interface
        if self.__write(channel, cmd) == False:
            print("error [2] sending TL1 command [{:s}]".format(cmd))


        if cmd.lower() == "canc-user;":
            msg_str = " COMPLD "
        else:
            msg_str  = ""
            keepalive_count_max = 100
            keepalive_count = 0

            while True:
                res_list  = self.__expect(channel, [b"\n\>", b"\n\;"])
                if res_list == ([], [], []):
                    print("error [3] sending TL1 command [{:s}]".format(cmd))

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

        if  (msg_str.find(" COMPLD") != -1  or
             msg_str.find(" DELAY")  != -1  ):
            # Positive TL1 response
            result = (policy == "COMPLD")
        else:
            # Negative TL1 response
            result = (policy == "DENY")

        self.__last_output = msg_str

        return result


    def __read_all(self, channel):
        """ INTERNAL USAGE
        """
        if channel == "CMD":
            tl1_interface = self.__if_cmd
        else:
            tl1_interface = self.__if_eve

        for retry in (1,2):
            try:
                while str(tl1_interface.read_very_eager().strip(), 'utf-8') != "":
                    pass
                return True
            except Exception as eee:
                tl1_interface = self.__connect(channel)     # renewing interface

        return False


    def __write(self, channel, cmd):
        """ INTERNAL USAGE
        """
        if channel == "CMD":
            tl1_interface = self.__if_cmd
        else:
            tl1_interface = self.__if_eve

        for retry in (1,2):
            try:
                tl1_interface.write(cmd.encode())
                return True
            except Exception as eee:
                tl1_interface = self.__connect(channel)     # renewing interface

        return False


    def __expect(self, channel, key_list):
        """ INTERNAL USAGE
        """
        if channel == "CMD":
            tl1_interface = self.__if_cmd
        else:
            tl1_interface = self.__if_eve

        for retry in (1,2):
            try:
                res_list = tl1_interface.expect(key_list)
                return res_list
            except Exception as eee:
                tl1_interface = self.__connect(channel)     # renewing interface

        return [],[],[]


    def __connect(self, channel):
        """ INTERNAL USAGE
        """
        if channel == "CMD":
            print("(re)CONNECTING TL1...")
            try:
                self.__if_cmd = telnetlib.Telnet(self.__the_ip, self.__the_port, 5)
            except Exception as eee:
                print("TL1: error connecting CMD channel - {:s}".format(str(eee)))
            print("... TL1 INTERFACE for commands ready.")
            return self.__if_cmd

        else:
            print("(re)CONNECTING TL1 (Event channel)...")
            try:
                self.__if_eve = telnetlib.Telnet(self.__the_ip, self.__the_port, 5)
            except Exception as eee:
                print("TL1: error connecting EVE channel - {:s}".format(str(eee)))
            print("... TL1 INTERFACE for events ready.")
            return self.__if_eve


    def __disconnect(self):
        """ INTERNAL USAGE
        """
        try:
            self.__do("EVE", "CANC-USER;", "COMPLD", None)
        except Exception as eee:
            msg = "Error in disconnection - {:s}".format(str(eee))
            print(msg)

        self.__if_eve = None

        try:
            self.__do("CMD", "CANC-USER;", "COMPLD", None)
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
                                        timeout=None    )
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
                    msg_coded = TL1message(msg_str)
                    # self.__f.writelines(msg_coded.decode("JSON"))
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

    if True:
        #print("[{:s}]\n{:s}".format(msg1, "-" * 80))
        mm = TL1message(msg3)
        print(mm.decode("JSON"))
        sys.exit(0)

        print("#" * 80)

        print("[{:s}]\n{:s}".format(msg3, "-" * 80))
        mm = TL1message(msg3)
        print(mm)
        print("@@@")
        lista = mm.get_cmd_aid_list()
        #print(lista[0] + " " + mm.get_cmd_status_value(lista[0])[0])
        #print(lista[0] + " " + mm.get_cmd_status_value(lista[0])[1])
        #print(lista[1] + " " + mm.get_cmd_status_value(lista[1])[0])
        #print(lista[1] + " " + mm.get_cmd_status_value(lista[1])[1])
        print(mm.get_cmd_attr_value("EC320-1-1-1", "REGION"))
        print(mm.get_cmd_attr_value("EC320-1-1-1", "PIPPO"))
        print(mm.get_cmd_attr_value("MDL-1-1-18", "AUTOPROV"))
        print("@@@")

        print("#" * 80)

        print("[{:s}]\n{:s}".format(msg4, "-" * 80))
        mm = TL1message(msg4)
        print(mm)
        if False:
            v1,v2,v3 = mm.get_cmd_error_frame()
            if v1:
                print("ERRORE: " + v2)
                print(v3[0])
                print(v3[1])

            print("-" * 80)
        #mm.encode("ASCII")

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
        tl1.do("RMV-EQPT::PP1GE-1-1-18;")
        tl1.do("DLT-EQPT::PP1GE-1-1-18;")

    time.sleep(1)

    tl1.thr_event_terminate()

    print("FINE")

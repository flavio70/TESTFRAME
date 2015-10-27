#!/usr/bin/env python

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

                msg['SID'], msg['DATE'], msg['TIME'] = line.split()
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
        return ( msg_code == '*C' or
                 msg_code == '**' or
                 msg_code == '*'  or
                 msg_code == 'A'  )



class Plugin1850TL1():
    """
    TL1 plugin for 1850TSS Equipment
    """

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
        self.__last_status = ""    # store the status of latest TL1 command ("CMPLD"/"DENY")

        # Activating both command and Event interfaces
        self.__connect()

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
        self.__disconnect()


    def get_last_outcome(self):
        """ Return the latest TL1 command output (multi-line string)
        """
        return self.__last_output


    def get_last_cmd_status(self):
        """ Return the latest TL1 command status ("CMPLD"/"DENY")
        """
        return self.__last_status


    def do(self, cmd, policy="COMPLD", match=None):
        """ Send the specified TL1 command to equipment.
            It is possible specify an error behaviour and/or a matching string
            cmd     : the TL1 command string
            policy  : "CMPLD" -> specify if a positive result has been expected (default behaviour)
                      "DENY"  -> specify if a negative result has been expected
            match   : an optional matching string to seek on command's output.
                      It is ignored when policy="DENY"
        """

        return self.__do(self.__if_cmd, cmd, policy, match)


    def __do(self, channel, cmd, policy, match):
        if self.__krepo:
            self.__krepo.startTime()

        # Trash all trailing characters from stream
        while str(channel.read_very_eager().strip(), 'utf-8') != "":
            pass

        cmd_lower  = cmd.lower()
        verb_lower = cmd.replace(";", "").split(":")[0].lower().replace("\r", "").replace("\n", "")

        try:
            if channel == self.__if_cmd:
                print("sending [" + cmd + "]")
            else:
                print("sending [" + cmd + "] (EVENT INTERFACE)")
            channel.write(cmd.encode())
        #except (socket.error, EOFError) as eee:
        except Exception as eee:
            msg = "Error in tl1.do({:s})\nException: {:s}".format(cmd, str(eee))
            print(msg)
            self.__disconnect()
            self.__connect()

        keepalive_count_max = 100
        keepalive_count    = 0
        msg_str  = ""
        echo    = ""

        while True:
            res_list  = channel.expect([b"\n\>", b"\n\;"])
            match_idx = res_list[0]
            msg_tmp   = str(res_list[2], 'utf-8')

            if msg_tmp.find("\r\n\n") == -1:
                echo = echo + msg_tmp
                continue

            resp_part_list = msg_tmp.split("\r\n\n")
            echo           = echo + resp_part_list[0]
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

        if      msg_str.find(" DENY") != -1:
            self.__last_status = "DENY"
            if policy:
                result = (policy == "DENY")
            else:
                result = False

        elif    cmd_lower == "canc-user;":
            self.__last_status = "CMPLD"
            result = (policy == "CMPLD")
        elif    msg_str.find(" COMPLD") != -1:
            self.__last_status = "CMPLD"
            result = (policy == "CMPLD")
        else:
            self.__last_status = "not assigned"
            result = False

        # valutare l'espressione regolare prima di restituire result
        # ###

        if self.__krepo:
            title = cmd
            if result:
                self.__krepo.addSuccess(self.__eqpt_ref, title, None, self.get_last_outcome())
            else:
                self.__krepo.addFailure(self.__eqpt_ref, title, None, self.get_last_outcome(), "")

        return result


    def __connect(self):
        try:
            self.__if_cmd = telnetlib.Telnet()
            self.__if_cmd.open(self.__the_ip, self.__the_port)
        except Exception as eee:
            msg = "Error in connecting __if_cmd - {:s}".format(str(eee))
            print(msg)

        try:
            self.__if_eve = telnetlib.Telnet()
            self.__if_eve.open(self.__the_ip, self.__the_port)
        except Exception as eee:
            msg = "Error in connecting __if_eve - {:s}".format(str(eee))
            print(msg)


    def __disconnect(self):
        try:
            self.__do(self.__if_eve, "CANC-USER;", "COMPLD", None)
            self.__do(self.__if_cmd, "CANC-USER;", "COMPLD", None)
        except Exception as eee:
            msg = "Error in disconnection - {:s}".format(str(eee))
            print(msg)

        try:
            self.__if_eve.close()
            self.__if_eve = None

            self.__if_cmd.close()
            self.__if_cmd = None
        except Exception as eee:
            msg = "Error in disconnection - {:s}".format(str(eee))
            print(msg)


    def event_collection_start(self):
        """ Start TL1 event collection
        """
        self.__enable_collect = True


    def event_collection_stop(self):
        """ Stop TL1 event collection
        """
        self.__enable_collect = False


    def thr_event_terminate(self):
        with self.__thread_lock:
            self.__do_event_loop = False


    def __thr_manager(self):
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
        connected = False

        while not connected:
            with self.__thread_lock:
                do_repeat = self.__do_event_loop

            if not do_repeat:
                break

            if self.__enable_collect:
                connected = self.__do(  self.__if_eve,
                                        "ACT-USER::admin:MYTAG::Alcatel1;",
                                        policy="CMPLD",
                                        match=None  )
            time.sleep(1)


    def __thr_event_loop(self):
        while True:
            with self.__thread_lock:
                do_repeat = self.__do_event_loop

            if not do_repeat:
                break

            msg_str  = ""
            echo    = ""

            while True:
                res_list  = self.__if_eve.expect([b"\n\>", b"\n\;"], timeout=10)
                match_idx = res_list[0]
                msg_tmp   = str(res_list[2], 'utf-8')

                if match_idx == -1:
                    # Timeout Detected
                    timeoutDetected = True
                    break
                else:
                    timeoutDetected = False

                if msg_tmp.find("\r\n\n") == -1:
                    echo = echo + msg_tmp
                    continue

                resp_part_list = msg_tmp.split("\r\n\n")
                echo           = echo + resp_part_list[0]
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

            if not timeoutDetected:
                if self.__enable_collect:
                    codedMsg = TL1Facility.decode(msg_str)
                    # self.__f.writelines(TL1Facility.encode(codedMsg, "JSON"))
                    self.__f.writelines("{:s}\n{:s}\n".format("-" * 80, msg_str))




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

    if True:
        print("[{:s}]\n{:s}".format(msg1, "-" * 80))
        print(TL1Facility.decode(msg1))

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

    tl1 = Plugin1850TL1("135.221.125.80")

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
        time.sleep(10)
        tl1.do("ENT-EQPT::PP1GE-1-1-18::::PROVISIONEDTYPE=PP1GE:IS;")
        time.sleep(15)
        tl1.do("RTRV-EQPT::ALL;")
        res = tl1.get_last_outcome()
        print(TL1Facility.decode(res))
        tl1.do("RMV-EQPT::PP1GE-1-1-18;")
        tl1.do("DLT-EQPT::PP1GE-1-1-18;")

    time.sleep(1)

    tl1.thr_event_terminate()

    print("FINE")

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

from katelibs.tl1_facility import TL1message



class Plugin1850TL1():
    """
    TL1 plugin for 1850TSS Equipment
    """
    TL1_TIMEOUT = 1200   # default timeout for TL1 command interaction


    def __init__(self, IP, PORT=3083, krepo=None, eRef=None, collector=None, ktrc=None):
        """
        Costructor for generic TL1 interface
        IP        : equipment's IP Address
        PORT      : TL1 interface Port
        krepo     : reference to KUnit reporting instance
        eRef      : reference to equipment (for label)
        collector : file name for event collector
        """

        self.__the_ip      = IP
        self.__the_port    = PORT
        self.__krepo       = krepo  # result report (Kunit class instance)
        self.__eqpt_ref    = eRef   # equipment reference
        self.__ktrc        = ktrc   # Tracer object
        self.__if_cmd      = None   # main TL1 interface (used for sending usr command)
        self.__if_eve      = None   # secondary TL1 interface (used for capturing events)
        self.__last_output = ""     # store the output of latest TL1 command
        self.__time_mark   = None   # Time mark to aborting a TL1 interaction

        # File for Event collector
        if collector is None:
            collector_fn = "collector.log"
        else:
            collector_fn = collector
        self.__f = open(collector_fn, "w")
        os.chmod(collector_fn, 0o644)

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


    def do_until(self, cmd, timeout=TL1_TIMEOUT, condPST=None, condSST=None):
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
        self.__time_mark = time.time() + timeout

        if self.__krepo:
            self.__krepo.start_time()

        error_msg = ""

        while True:
            result = self.__do("CMD", cmd, "COMPLD")

            if int(time.time()) <= self.__time_mark:
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
                error_msg = "TIMEOUT ({:d}s) DETECTED ON SENDING '{:s}'".format(timeout, cmd)
                self.__trc(error_msg)
                result = False
                break

        self.__trc("DEBUG: result := {:s} - errmsg := [{:s}]\n".format(str(result), error_msg))

        if result:
            self.__t_success(cmd, None, self.get_last_outcome())
        else:
            self.__t_failure(cmd, None, self.get_last_outcome(), error_msg)

        return result


    def do(self, cmd, policy="COMPLD", timeout=TL1_TIMEOUT, condPST=None, condSST=None):
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
                self.__trc("ATTENZIONE: ALMENO UNO TRA condPST e condSST deve essere valorizzato")
                return False

        self.__time_mark = time.time() + timeout

        if self.__krepo:
            self.__krepo.start_time()

        error_msg = ""

        result = self.__do("CMD", cmd, policy)

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

        self.__trc("DEBUG: result := {:s} - errmsg := [{:s}]\n".format(str(result), error_msg))

        if result:
            self.__t_success(cmd, None, self.get_last_outcome())
        else:
            self.__t_failure(cmd, None, self.get_last_outcome(), error_msg)

        return result


    def __do(self, channel, cmd, policy):
        """ INTERNAL USAGE
        """
        if channel == "CMD":
            self.__trc("sending [{:s}]".format(cmd))
        else:
            self.__trc("sending [{:s}] (EVENT INTERFACE)".format(cmd))

        verb_lower = cmd.replace(";", "").split(":")[0].lower().replace("\r", "").replace("\n", "")

        # Trash all trailing characters from stream
        if self.__read_all(channel) == False:
            self.__trc("error [1] sending TL1 command [{:s}]".format(cmd))
            self.__last_output = "TIMEOUT DETECTED ON TL1 INTERFACE"
            return False

        # Sending command to interface
        if self.__write(channel, cmd) == False:
            self.__trc("error [2] sending TL1 command [{:s}]".format(cmd))
            self.__last_output = "TIMEOUT DETECTED ON TL1 INTERFACE"
            return False


        if cmd.lower() == "canc-user;":
            msg_str = " COMPLD "
        else:
            msg_str  = ""
            keepalive_count_max = 100
            keepalive_count = 0

            while True:
                res_list  = self.__expect(channel, [b"\n\>", b"\n\;"])
                if res_list == ([], [], []):
                    self.__trc("error [3] sending TL1 command [{:s}]".format(cmd))
                    self.__last_output = "TIMEOUT DETECTED ON TL1 INTERFACE"
                    return False

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

        for _ in (1,2):
            try:
                while str(tl1_interface.read_very_eager().strip(), 'utf-8') != "":
                    pass
                return True
            except Exception:
                tl1_interface = self.__connect(channel)     # renewing interface

        return False


    def __write(self, channel, cmd):
        """ INTERNAL USAGE
        """
        if channel == "CMD":
            tl1_interface = self.__if_cmd
        else:
            tl1_interface = self.__if_eve

        for _ in (1,2):
            try:
                tl1_interface.write(cmd.encode())
                return True
            except Exception:
                tl1_interface = self.__connect(channel)     # renewing interface

        return False


    def __expect(self, channel, key_list):
        """ INTERNAL USAGE
        """
        if channel == "CMD":
            tl1_interface = self.__if_cmd
        else:
            tl1_interface = self.__if_eve

        for _ in (1,2):
            try:
                res_list = tl1_interface.expect(key_list)
                return res_list
            except Exception:
                tl1_interface = self.__connect(channel)     # renewing interface

        return [],[],[]


    def __connect(self, channel):
        """ INTERNAL USAGE
        """
        is_connected = False

        if channel == "CMD":
            self.__trc("(re)CONNECTING TL1...")

            while int(time.time()) <= self.__time_mark:
                try:
                    self.__if_cmd = telnetlib.Telnet(self.__the_ip, self.__the_port, 5)
                    self.__trc("... TL1 INTERFACE for commands ready.")
                    is_connected = True
                    break
                except Exception as eee:
                    self.__trc("TL1: error connecting CMD channel - {:s}".format(str(eee)))
                    self.__trc("... retrying in 1s ...")
                    time.sleep(1)

            if not is_connected:
                self.__trc("TL1: Timeout on connection")

            return self.__if_cmd

        else:
            self.__trc("(re)CONNECTING TL1 (Event channel)...")

            while int(time.time()) <= self.__time_mark:
                try:
                    self.__if_eve = telnetlib.Telnet(self.__the_ip, self.__the_port, 5)
                    self.__trc("... TL1 INTERFACE for events ready.")
                    is_connected = True
                    break
                except Exception as eee:
                    self.__trc("TL1: error connecting EVE channel - {:s}".format(str(eee)))
                    self.__trc("... retrying in 1s ...")
                    time.sleep(1)

            if not is_connected:
                self.__trc("TL1: Timeout on connection")

            return self.__if_eve


    def __disconnect(self):
        """ INTERNAL USAGE
        """
        try:
            self.__do("EVE", "CANC-USER;", "COMPLD")
        except Exception as eee:
            msg = "Error in disconnection - {:s}".format(str(eee))
            self.__trc(msg)

        self.__if_eve = None

        try:
            self.__do("CMD", "CANC-USER;", "COMPLD")
        except Exception as eee:
            msg = "Error in disconnection - {:s}".format(str(eee))
            self.__trc(msg)

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
                connected = self.__do("EVE", "ACT-USER::admin:MYTAG::Alcatel1;", policy="COMPLD")
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
                    self.__f.writelines("{:s}\n".format(msg_coded.decode("JSON")))


    def __t_success(self, title, elapsed_time, out_text):
        """ INTERNAL USAGE
        """
        if self.__krepo:
            self.__krepo.add_success(self.__eqpt_ref, title, elapsed_time, out_text)


    def __t_failure(self, title, e_time, out_text, err_text, log_text=None):
        """ INTERNAL USAGE
        """
        if self.__krepo:
            self.__krepo.add_failure(self.__eqpt_ref, title, e_time, out_text, err_text, log_text)


    def __t_skipped(self, title, e_time, out_text, err_text, skip_text=None):
        """ INTERNAL USAGE
        """
        if self.__krepo:
            self.__krepo.add_skipped(self.__eqpt_ref, title, e_time, out_text, err_text, skip_text)


    def __trc(self, msg):
        """ INTERNAL USAGE
        """
        if self.__ktrc is not None:
            self.__ktrc.k_tracer_function(msg)



if __name__ == "__main__":
    print("DEBUG")

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

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

from katelibs.kexception    import KFrameException
from katelibs.facility_tl1  import TL1check
from katelibs.facility_tl1  import TL1message



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
        ktrc      : reference to Kate Tracer
        """

        self.__the_ip      = IP
        self.__the_port    = PORT
        self.__krepo       = krepo  # result report (Kunit class instance)
        self.__eqpt_ref    = eRef   # equipment reference
        self.__ktrc        = ktrc   # Tracer object
        self.__if_cmd      = None   # main TL1 interface (used for sending usr command)
        self.__if_eve      = None   # secondary TL1 interface (used for capturing events)
        self.__last_cmd    = ""     # store the latest tl1 command sent
        self.__last_output = ""     # store the output of latest TL1 command sent
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
        self.__thread = threading.Thread(target=self.__thr_manager,
                                         name="TL1_Event_Collector")
        self.__thread.daemon = False
        self.__thread.start()

        self.__trc_inf("Plugin BM available")


    def get_last_outcome(self):
        """ Return the latest TL1 command output (multi-line string)
        """
        return self.__last_output


    def do_until(self, cmd, cond, timeout=TL1_TIMEOUT):
        """ Send the specified TL1 command to equipment until almost one of conditions will be
            reached.
            cmd     : the TL1 command string
            timeout : (secons) timeout to terminate loop
            cond    : instance of TL1check class (see for details).
        """
        self.__last_cmd = cmd
        self.__time_mark = time.time() + timeout

        if self.__krepo:
            self.__krepo.start_time()

        error_msg = ""

        while True:
            result = self.__do("CMD", cmd, "COMPLD")

            if int(time.time()) <= self.__time_mark:
                msg_coded = TL1message(self.__last_output)
                # Evaluation of result conditions
                match_cond = cond.evaluate_msg(msg_coded)
                self.__trc_dbg("TL1 Condition Evaluated := {}".format(match_cond))

                if match_cond[0]:
                    result = True
                    break

                time.sleep(1)
            else:
                error_msg = "TIMEOUT ({:d}s) DETECTED ON SENDING '{:s}'".format(timeout, cmd)
                self.__trc_error(error_msg)
                result = False
                raise KFrameException(error_msg)
                break

        self.__trc_dbg("DEBUG: result := {:s} - errmsg := [{:s}]\n".format(str(result), error_msg))

        if result:
            self.__t_success(cmd, None, self.get_last_outcome())
        else:
            self.__t_failure(cmd, None, self.get_last_outcome(), error_msg)

        return result


    def do(self, cmd, policy="COMPLD", timeout=TL1_TIMEOUT, cond=None):
        """ Send the specified TL1 command to equipment.
            It is possible specify an error behaviour and/or a matching string
            cmd     : the TL1 command string
            policy  : "COMPLD" -> specify if a positive result has been expected (default behaviour)
                      "DENY"   -> specify if a negative result has been expected
                      "COND"   -> specify a conditional command execution (see condXXX parameters)
                      It is ignored when policy="DENY"
            timeout : (secons) timeout to close a conditional command
            cond    : instance of TL1check class (see for details). Ignored if policy != "COND"
        """

        if policy == "COND" and cond is None:
            self.__trc_error("An instance of TL1check is mandatory for policy=='COND'")
            return False

        self.__last_cmd = cmd
        self.__time_mark = time.time() + timeout

        if self.__krepo:
            self.__krepo.start_time()

        error_msg = ""

        if policy == "COND":
            result = self.__do("CMD", cmd, "COMPLD")
        else:
            result = self.__do("CMD", cmd, policy)

        if result  and  policy == "COND":
            msg_coded = TL1message(self.__last_output)

            # Evaluation of result conditions
            print("APPLING FILTER")
            match_cond = cond.evaluate_msg(msg_coded)
            self.__trc_dbg("TL1 Condition Evaluated := {}".format(match_cond))
            print("DONE FILTER")
            print(match_cond)

            result = match_cond[0]

        self.__trc_dbg("DEBUG: result := {:s} - errmsg := [{:s}]\n".format(str(result), error_msg))

        if result:
            self.__t_success(cmd, None, self.get_last_outcome())
        else:
            self.__t_failure(cmd, None, self.get_last_outcome(), error_msg)

        return result


    def __do(self, channel, cmd, policy):
        """ INTERNAL USAGE
        """
        self.__last_cmd = cmd   # added for internal running invocation

        if channel == "CMD":
            self.__trc_dbg("sending [{:s}]".format(cmd))
        else:
            self.__trc_dbg("sending [{:s}] (EVENT INTERFACE)".format(cmd))

        tl1_verb = cmd.replace(";", "").split(":")[0].lower().replace("\r", "").replace("\n", "")

        # Trash all trailing characters from stream
        if self.__read_all(channel) == False:
            self.__trc_error("error [1] sending TL1 command [{:s}]".format(cmd))
            self.__last_output = "TIMEOUT DETECTED ON TL1 INTERFACE"
            raise KFrameException(self.__last_output)
            return False

        # Sending command to interface
        if self.__write(channel, cmd) == False:
            self.__trc_error("error [2] sending TL1 command [{:s}]".format(cmd))
            self.__last_output = "TIMEOUT DETECTED ON TL1 INTERFACE"
            raise KFrameException(self.__last_output)
            return False


        if cmd.lower() == "canc-user;":
            tl1_response = " COMPLD "
        else:
            tl1_response  = ""

            keepalive_count_max = 100
            keepalive_count = 0

            while True:
                result_list = self.__expect(channel, [b"\n\>", b"\n\;"])

                if result_list == ([],[],[]):
                    self.__trc_error("error [3] sending TL1 command [{:s}]".format(cmd))
                    self.__last_output = "TIMEOUT DETECTED ON TL1 INTERFACE"
                    raise KFrameException(self.__last_output)
                    return False

                msg_tmp = str(result_list[2], 'utf-8')

                if msg_tmp.find("\r\n\n") == -1:
                    continue

                response_partial_list = msg_tmp.split("\r\n\n")
                msg_tmp = "\r\n\n".join(response_partial_list[1:])

                if result_list[0] ==  1:
                    if msg_tmp.find(" REPT ") != -1:
                        continue

                    elif msg_tmp.find("KEEP ALIVE MESSAGE") != -1:
                        keepalive_count = keepalive_count + 1
                        if keepalive_count == keepalive_count_max:
                            self.__trc_error("error [4] sending TL1 command [{:s}]".format(cmd))
                            self.__last_output = "MAXIMUM KEEPALIVE ON TL1 RESPONSE REACHED"
                            raise KFrameException(self.__last_output)
                            return False
                        continue

                    else:
                        tl1_response = tl1_response + re.sub('(\r\n)+', "\r\n", msg_tmp, 0)
                        if tl1_verb != "ed-pid"  and  tl1_verb != "act-user":
                            if tl1_response.count(";") > 1:
                                self.__trc_error("error [5] sending TL1 command [{:s}]".format(cmd))
                                self.__last_output = "INVALID TL1 TERMINATION"
                                raise KFrameException(self.__last_output)
                                return False
                        if tl1_response.strip() == ";":
                            continue
                        break

                elif result_list[0] ==  0:
                    tl1_response = tl1_response + msg_tmp + "\n"
                    continue

            tl1_response = re.sub('(\r\n)+', "\r\n", tl1_response, 0)


        if  (tl1_response.find(" COMPLD") != -1  or
             tl1_response.find(" DELAY")  != -1  ):
            # Positive TL1 response
            result = (policy == "COMPLD")
        else:
            # Negative TL1 response
            result = (policy == "DENY")

        self.__last_output = tl1_response

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
                result_list = tl1_interface.expect(key_list)
                return result_list
            except Exception:
                tl1_interface = self.__connect(channel)     # renewing interface

        return [],[],[]


    def __connect(self, channel):
        """ INTERNAL USAGE
        """
        is_connected = False

        if channel == "CMD":
            self.__trc_dbg("(re)CONNECTING TL1...")

            while int(time.time()) <= self.__time_mark:
                try:
                    self.__if_cmd = telnetlib.Telnet(self.__the_ip, self.__the_port, 5)
                    self.__trc_dbg("... TL1 INTERFACE for commands ready.")
                    is_connected = True
                    break
                except Exception as eee:
                    self.__trc_dbg("TL1: error connecting CMD channel - {:s}".format(str(eee)))
                    self.__trc_dbg("... retrying in 1s ...")
                    time.sleep(1)

            if not is_connected:
                self.__trc_error("TL1: Timeout on connection")
                raise KFrameException("TL1: Timeout on connection")

            return self.__if_cmd

        else:
            self.__trc_dbg("(re)CONNECTING TL1 (Event channel)...")

            end_timeout = time.time() + self.TL1_TIMEOUT

            while int(time.time()) <= end_timeout:
                try:
                    self.__if_eve = telnetlib.Telnet(self.__the_ip, self.__the_port, 5)
                    self.__trc_dbg("... TL1 INTERFACE for events ready.")
                    is_connected = True
                    break
                except Exception as eee:
                    self.__trc_dbg("TL1: error connecting EVE channel - {:s}".format(str(eee)))
                    self.__trc_dbg("... retrying in 1s ...")
                    time.sleep(1)

            if not is_connected:
                self.__trc_error("TL1: Timeout on connection")
                raise KFrameException("TL1: Timeout on connection")

            return self.__if_eve


    def __disconnect(self):
        """ INTERNAL USAGE
        """
        try:
            self.__do("EVE", "CANC-USER;", "COMPLD")
        except Exception as eee:
            msg = "Error in disconnection - {:s}".format(str(eee))
            self.__trc_error(msg)
            raise KFrameException(msg)

        self.__if_eve = None

        try:
            self.__do("CMD", "CANC-USER;", "COMPLD")
        except Exception as eee:
            msg = "Error in disconnection - {:s}".format(str(eee))
            self.__trc_error(msg)
            raise KFrameException(msg)

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
        collected_items = 0

        while True:
            with self.__thread_lock:
                do_repeat = self.__do_event_loop

            if not do_repeat:
                break

            tl1_response  = ""

            while True:
                result_list = self.__if_eve.expect([b"\n\>", b"\n\;"], timeout=100)

                if result_list[0] == -1:
                    # Timeout Detected
                    print("timeout durante evento")
                    continue

                msg_tmp = str(result_list[2], 'utf-8')
                print("[{}]".format(msg_tmp))

                if msg_tmp.find("\r\n\n") == -1:
                    continue

                response_partial_list = msg_tmp.split("\r\n\n")
                msg_tmp = "\r\n\n".join(response_partial_list[1:])

                if   result_list[0] ==  1:
                    # Ending block detected (';' at begin of line)
                    tl1_response = tl1_response + re.sub('(\r\n)+', "\r\n", msg_tmp, 0)
                    if tl1_response.strip() == ";":
                        continue
                    break

                elif result_list[0] ==  0:
                    # Continuoing mark detected ('>' at begin of line)
                    tl1_response = tl1_response + msg_tmp + "\n"
                    continue

            tl1_response = re.sub('(\r\n)+', "\r\n", tl1_response, 0)

            if self.__enable_collect:
                collected_items = collected_items + 1
                print("EVENTO COLLEZIONATO #{}".format(collected_items))
                print(tl1_response)
                msg_coded = TL1message(tl1_response)
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


    def __trc_dbg(self, msg, level=None):
        """ INTERNAL USAGE
        """
        if self.__ktrc is not None:
            self.__ktrc.k_tracer_debug(msg, level)


    def __trc_inf(self, msg, level=None):
        """ INTERNAL USAGE
        """
        if self.__ktrc is not None:
            self.__ktrc.k_tracer_info(msg, level)


    def __trc_error(self, msg, level=None):
        """ INTERNAL USAGE
        """
        if self.__ktrc is not None:
            self.__ktrc.k_tracer_error(msg, level)



if __name__ == "__main__":
    from katelibs.ktracer   import KTracer

    print("DEBUG")

    trace = KTracer(level="DEBUG")
    tl1 = Plugin1850TL1("135.221.125.79", ktrc=trace)
    trace.k_tracer_error("PROVA", level=0)

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
        filt = TL1check()
        filt.add_pst("IS")
        tl1.do("ENT-EQPT::PP1GE-1-1-18::::PROVISIONEDTYPE=PP1GE:IS;", policy="COND", cond=filt)
        time.sleep(15)
        tl1.do("RTRV-EQPT::MDL-1-1-18;")
        res = tl1.get_last_outcome()
        print(res)
        tl1.do("RMV-EQPT::PP1GE-1-1-18;")
        tl1.do("DLT-EQPT::PP1GE-1-1-18;")

    time.sleep(1)

    tl1.thr_event_terminate()

    print("FINE")

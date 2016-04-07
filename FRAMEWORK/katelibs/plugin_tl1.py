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
import datetime
import os

from katelibs.kexception    import KFrameException
from katelibs.facility_tl1  import TL1check
from katelibs.facility_tl1  import TL1message


class TL1EventCollector():
    """ TL1 Event collection scan
    """
    TL1_TIMEOUT = 1200   # default timeout for TL1 command interaction

    def __init__(self, IP, PORT, collector, ktrc=None):
        """ Constructor for Event Scanner
        """
        self.__alm_cri = []
        self.__alm_maj = []
        self.__alm_min = []
        self.__not_alm = []
        self.__informs = []

        self.__the_ip = IP
        self.__the_port = PORT
        self.__if_eve = None    # TL1 interface (used for capturing events)
        self.__ktrc = ktrc

        # File for Event collector
        if collector is None:
            collector_fn = "collector.log"
        else:
            collector_fn = collector

        if os.path.isfile(collector_fn):
            os.remove(collector_fn)

        self.__f = open(collector_fn, "w")
        os.chmod(collector_fn, 0o666)

        # Semaphore for TL1 Event Collector info area
        self.__thread_semaphore = threading.Lock()

        # Flags for TL1 Event Collector
        self.__do_event_loop    = True  # Thread termination flag
        self.__do_event_connect = False # Enable/Disable connecting on event channel
        self.__enable_collect   = False # Enable/Disable collection

        # TL1 Event Collector Thread Initialization and Starting
        self.__thread = threading.Thread(target=self.__thr_manager,
                                         name="TL1_Event_Collector")
        self.__thread.daemon = False
        self.__thread.start()

        self.__trc_inf("Plugin TL1 Event Collector available")


    def __reset(self):
        """ INTERNAL USAGE
            Reset event collection
        """
        self.__alm_cri = []
        self.__alm_maj = []
        self.__alm_min = []
        self.__not_alm = []
        self.__informs = []


    def __append(self, new_elem):
        """ INTERNAL USAGE
            Add an autonomous message to appropriate list
        """
        marker = new_elem.get_message_code()
        if   marker == '*C':
            self.__alm_cri.append(new_elem)
        elif marker == '**':
            self.__alm_maj.append(new_elem)
        elif marker == '*':
            self.__alm_min.append(new_elem)
        elif marker == 'A':
            self.__not_alm.append(new_elem)
        elif marker == 'I':
            self.__informs.append(new_elem)
        else:
            self.__trc_err("UNKNOWN AUTONOMOUS MESSAGE CODE [{}]".format(marker))


    def __get_events(self, marker):
        """ INTERNAL USAGE
            Get all collected event with specified event type
            marker : '*C' / '**' / '*' / 'A' / 'I'
        """
        if   marker == '*C':
            return self.__alm_cri
        elif marker == '**':
            return self.__alm_maj
        elif marker == '*':
            return self.__alm_min
        elif marker == 'A':
            return self.__not_alm
        elif marker == 'I':
            return self.__informs
        else:
            return []


    def event_size(self, marker, aid=None, cmd=None):
        """ Return then number of collected events for specified type.
            The AID and CMD are evaluated in 'and' clause
            marker : '*C' / '**' / '*' / 'A' / 'I'
        """
        collection = self.__get_events(marker)
        if len(collection) == 0:
            return 0

        if aid is None  and  cmd is None:
            return len(collection)

        count = 0
        for elem in collection:
            if aid is not None:
                if elem.get_eve_aid() != aid:
                    continue

            if cmd is not None:
                the_body = elem.get_eve_body()
                if the_body.find(cmd) != -1:
                    count = count + 1
            else:
                count = count + 1

        return count


    def event_get(self, marker, aid=None, cmd=None):
        """ Return a list of collected events for specified type.
            The AID and CMD are evaluated in 'and' clause
            marker : '*C' / '**' / '*' / 'A' / 'I'
        """
        collection = self.__get_events(marker)
        if len(collection) == 0:
            return []

        if aid is None  and  cmd is None:
            return len(collection)

        sublist = []
        for elem in collection:
            if aid is not None:
                if elem.get_eve_aid() != aid:
                    continue

            if cmd is not None:
                the_body = elem.get_eve_body()
                if the_body.find(cmd) != -1:
                    sublist.append(elem)
            else:
                sublist.append(elem)

        return sublist


    def event_start(self, reset):
        """ Start TL1 event collection
        """
        self.__trc_inf("TL1 Event collection required")
        self.__enable_collect = True
        if reset:
            self.__reset()


    def event_stop(self):
        """ Stop TL1 event collection
        """
        self.__trc_inf("TL1 Event collection terminated")
        self.__enable_collect = False


    def thr_event_init(self):
        """ TODO
        """
        with self.__thread_semaphore:
            self.__do_event_connect = True


    def thr_event_terminate(self):
        """ TODO
        """
        with self.__thread_semaphore:
            self.__do_event_loop = False


    def __thr_manager(self):
        """ INTERNAL USAGE
        """
        with self.__thread_semaphore:
            do_repeat = self.__do_event_loop

        # thread main
        while do_repeat:
            with self.__thread_semaphore:
                do_connect = self.__do_event_connect

            if do_connect:
                self.__thr_init()
                self.__thr_event_loop()

            with self.__thread_semaphore:
                do_repeat = self.__do_event_loop


    def __thr_init(self):
        """ INTERNAL USAGE
        """
        with self.__thread_semaphore:
            do_repeat = self.__do_event_loop

        while do_repeat:
            if self.__eve_do("ACT-USER::admin:MYTAG::Alcatel1;"):
                self.__trc_dbg("CONNECTED ON TL1 EVENT CHANNEL")
                return
            else:
                self.__trc_dbg("CONNECTING ON TL1 EVENT CHANNEL...")

            time.sleep(1)

            with self.__thread_semaphore:
                do_repeat = self.__do_event_loop


    def __thr_event_loop(self):
        """ INTERNAL USAGE
        """
        num_of_events = 0

        with self.__thread_semaphore:
            do_repeat = self.__do_event_loop

        while do_repeat:
            tl1_response  = ""

            while do_repeat:
                result_list = self.__if_eve.expect([b"\n\>", b"\n\;"], timeout=3)

                if result_list[0] == -1:
                    # Timeout Detected
                    with self.__thread_semaphore:
                        do_repeat = self.__do_event_loop
                    if not do_repeat:
                        self.__trc_inf("TL1 Event collection shutdown...")
                    continue

                msg_tmp = str(result_list[2], 'utf-8')

                if msg_tmp.find("\r\n\n") == -1:
                    with self.__thread_semaphore:
                        do_repeat = self.__do_event_loop
                    continue

                response_partial_list = msg_tmp.split("\r\n\n")
                msg_tmp = "\r\n\n".join(response_partial_list[1:])

                if   result_list[0] ==  1:
                    # Ending block detected (';' at begin of line)
                    tl1_response = tl1_response + re.sub('(\r\n)+', "\r\n", msg_tmp, 0)
                    if tl1_response.strip() == ";":
                        with self.__thread_semaphore:
                            do_repeat = self.__do_event_loop
                        continue
                    break

                elif result_list[0] ==  0:
                    # Continuoing mark detected ('>' at begin of line)
                    tl1_response = tl1_response + msg_tmp + "\n"
                    with self.__thread_semaphore:
                        do_repeat = self.__do_event_loop
                    continue

                with self.__thread_semaphore:
                    do_repeat = self.__do_event_loop

            tl1_response = re.sub('(\r\n)+', "\r\n", tl1_response, 0)

            if self.__enable_collect:
                num_of_events = num_of_events + 1
                c_msg = TL1message(tl1_response)
                self.__trc_inf("Event #{} [{}] [{}]".format(num_of_events,
                                                            c_msg.get_message_code(),
                                                            c_msg.get_eve_body()))
                self.__append(c_msg)
                self.__f.writelines("{:s}\n".format(c_msg.decode("JSON")))

            with self.__thread_semaphore:
                do_repeat = self.__do_event_loop


    def __eve_do(self, cmd):
        """ INTERNAL USAGE
        """
        self.__trc_dbg("sending [{:s}] (EVENT INTERFACE)".format(cmd))

        tl1_verb = cmd.replace(";", "").split(":")[0].lower().replace("\r", "").replace("\n", "")

        # Trash all trailing characters from stream
        if self.__eve_read_all() == False:
            self.__trc_err("error [1] sending TL1 command [{:s}]".format(cmd))
            return False

        # Sending command to interface
        if self.__eve_write(cmd) == False:
            self.__trc_err("error [2] sending TL1 command [{:s}]".format(cmd))
            return False

        tl1_response  = ""

        keepalive_count_max = 100
        keepalive_count = 0

        while True:
            result_list = self.__eve_expect([b"\n\>", b"\n\;"])

            if result_list == ([],[],[]):
                self.__trc_err("error [3] sending TL1 command [{:s}]".format(cmd))
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
                        self.__trc_err("error [4] sending TL1 command [{:s}]".format(cmd))
                        return False
                    continue

                else:
                    tl1_response = tl1_response + re.sub('(\r\n)+', "\r\n", msg_tmp, 0)
                    if tl1_verb != "ed-pid"  and  tl1_verb != "act-user":
                        if tl1_response.count(";") > 1:
                            self.__trc_err("error [5] sending TL1 command [{:s}]".format(cmd))
                            raise KFrameException("INVALID TL1 TERMINATION")
                            #return False
                    if tl1_response.strip() == ";":
                        continue
                    break

            elif result_list[0] ==  0:
                tl1_response = tl1_response + msg_tmp + "\n"
                continue

        tl1_response = re.sub('(\r\n)+', "\r\n", tl1_response, 0)

        result = (tl1_response.find(" COMPLD") != -1)

        return result


    def __eve_read_all(self):
        """ INTERNAL USAGE
        """
        for _ in (1,2):
            try:
                while str(self.__if_eve.read_very_eager().strip(), 'utf-8') != "":
                    pass
                return True
            except Exception:
                self.__if_eve = self.__eve_connect()    # renewing interface

        return False


    def __eve_write(self, cmd):
        """ INTERNAL USAGE
        """
        for _ in (1,2):
            try:
                self.__if_eve.write(cmd.encode())
                return True
            except Exception:
                self.__if_eve = self.__eve_connect()    # renewing interface

        return False


    def __eve_expect(self, key_list):
        """ INTERNAL USAGE
        """
        for _ in (1,2):
            try:
                result_list = self.__if_eve.expect(key_list)
                return result_list
            except Exception:
                self.__if_eve = self.__eve_connect()    # renewing interface

        return [],[],[]


    def __eve_connect(self):
        """ INTERNAL USAGE
        """
        is_connected = False

        self.__trc_dbg("(re)CONNECTING TL1 (Event)...")

        end_timeout = time.time() + self.TL1_TIMEOUT

        while int(time.time()) <= end_timeout:
            try:
                self.__if_eve = telnetlib.Telnet(self.__the_ip, self.__the_port, 5)
                self.__trc_dbg("... TL1 INTERFACE for events ready.")
                is_connected = True
                break
            except Exception as eee:
                self.__trc_dbg("TL1: error connecting EVENT channel - {:s}".format(str(eee)))
                self.__trc_dbg("... retrying in 1s ...")
                time.sleep(1)

        if not is_connected:
            self.__trc_err("TL1: Timeout on connection")
            raise KFrameException("TL1: Timeout on connection")

        return self.__if_eve


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


    def __trc_err(self, msg, level=None):
        """ INTERNAL USAGE
        """
        if self.__ktrc is not None:
            self.__ktrc.k_tracer_error(msg, level)




class Plugin1850TL1():
    """
    TL1 plugin for 1850TSS Equipment
    """
    TL1_TIMEOUT = 1200   # default timeout for TL1 command interaction


    def __init__(self, IP, PORT=3083, krepo=None, eRef=None, collector=None, log=None, ktrc=None):
        """
        Costructor for generic TL1 interface
        IP        : equipment's IP Address
        PORT      : TL1 interface Port
        krepo     : reference to KUnit reporting instance
        eRef      : reference to equipment (for label)
        log       : file name for log collection
        collector : file name for event collector
        ktrc      : reference to Kate Tracer
        """

        self.__the_ip      = IP
        self.__the_port    = PORT
        self.__krepo       = krepo  # result report (Kunit class instance)
        self.__eqpt_ref    = eRef   # equipment reference
        self.__ktrc        = ktrc   # Tracer object
        self.__if_cmd      = None   # TL1 interface (used for sending usr command)
        self.__last_cmd    = ""     # store the latest tl1 command sent
        self.__last_output = ""     # store the output of latest TL1 command sent
        self.__time_mark   = None   # Time mark to aborting a TL1 interaction (only for CMD)
        self.__collector   = None   # TL1 Event Collector
        self.__logfile     = None   # File handler for logging purpose

        # Opening log file
        if log is not None:
            self.__logfile = open(log, "w")

        # TL1 Event Scanner initialization
        self.__collector = TL1EventCollector(self.__the_ip, self.__the_port, collector, self.__ktrc)

        self.__trc_inf("Plugin TL1 available")


    def cleanup(self):
        """ Closing all TL1 activities
        """
        self.__collector.thr_event_terminate()
        if self.__logfile is not None:
            self.__logfile.close()


    def get_last_outcome(self):
        """ Return the latest TL1 command output (multi-line string)
        """
        return self.__last_output


    def event_collection_start(self, reset=True, delay=5):
        """ Start TL1 event collection
            reset : if True, all previously collected events will be cleaned
            delay : delay time (don't change)
        """
        self.__collector.event_start(reset)
        time.sleep(delay)


    def event_collection_stop(self):
        """ Stop TL1 event collection
        """
        self.__collector.event_stop()


    def event_collection_size(self, marker, aid=None, cmd=None):
        """ Return then number of collected events for specified type
            It is possible specify an AID or a CMD involved on event
            If specified both AID and CMD, the conditions is combined
            marker : '*C' / '**' / '*' / 'A' / 'I'
        """
        return self.__collector.event_size(marker, aid, cmd)


    def event_collection_get(self, marker, aid=None, cmd=None):
        """ Return a list of collected events for specified type
            It is possible specify an AID or a CMD involved on event
            If specified both AID and CMD, the conditions is combined
            marker : '*C' / '**' / '*' / 'A' / 'I'
        """
        return self.__collector.event_get(marker, aid, cmd)


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
            result = self.__do(cmd, "COMPLD", is_until=True)

            if int(time.time()) <= self.__time_mark:
                if result:
                    c_msg = TL1message(self.__last_output)
                    # Evaluation of result conditions
                    match_cond = cond.evaluate_msg(c_msg)
                    self.__trc_dbg("TL1 Condition Evaluated := {}".format(match_cond))

                    if match_cond[0]:
                        result = True
                        break

                time.sleep(2)
            else:
                error_msg = "TIMEOUT ({:d}s) DETECTED in do_until '{:s}'".format(timeout, cmd)
                self.__trc_err(error_msg)
                result = False
                #raise KFrameException(error_msg)
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
            self.__trc_err("An instance of TL1check is mandatory for policy=='COND'")
            return False

        if cmd.find(';') == -1:
            cmd = "{:s};".format(cmd)

        self.__last_cmd = cmd
        self.__time_mark = time.time() + timeout

        if self.__krepo:
            self.__krepo.start_time()

        error_msg = ""

        if policy == "COND":
            result = self.__do(cmd, "COMPLD")
        else:
            result = self.__do(cmd, policy)

        if result  and  policy == "COND":
            c_msg = TL1message(self.__last_output)

            # Evaluation of result conditions
            print("APPLING FILTER")
            match_cond = cond.evaluate_msg(c_msg)
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


    def __do(self, cmd, policy, is_until=False):
        """ INTERNAL USAGE
        """
        self.__last_cmd = cmd   # added for internal running invocation

        self.__trc_dbg("sending [{:s}]".format(cmd))

        tl1_verb = cmd.replace(";", "").split(":")[0].lower().replace("\r", "").replace("\n", "")

        # Trash all trailing characters from stream
        if self.__cmd_read_all() == False:
            self.__trc_err("error [1] sending TL1 command [{:s}]".format(cmd))
            self.__last_output = "TIMEOUT DETECTED ON TL1 INTERFACE"
            raise KFrameException(self.__last_output)
            #return False

        # Sending command to interface
        if self.__cmd_write(cmd) == False:
            self.__trc_err("error [2] sending TL1 command [{:s}]".format(cmd))
            self.__last_output = "TIMEOUT DETECTED ON TL1 INTERFACE"
            raise KFrameException(self.__last_output)
            #return False


        if cmd.lower() == "canc-user;":
            tl1_response = " COMPLD "
        else:
            tl1_response  = ""

            keepalive_count_max = 100
            keepalive_count = 0

            while True:
                result_list = self.__cmd_expect([b"\n\>", b"\n\;"])

                if result_list == ([],[],[]):
                    if is_until:
                        self.__trc_err("error [3] UNTIL sending TL1 command [{:s}]".format(cmd))
                        self.__last_output = ""
                        return False
                    else:
                        self.__trc_err("error [3] sending TL1 command [{:s}]".format(cmd))
                        self.__last_output = "TIMEOUT DETECTED ON TL1 INTERFACE"
                        raise KFrameException(self.__last_output)
                        #return False

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
                            self.__trc_err("error [4] sending TL1 command [{:s}]".format(cmd))
                            self.__last_output = "MAXIMUM KEEPALIVE ON TL1 RESPONSE REACHED"
                            raise KFrameException(self.__last_output)
                            #return False
                        continue

                    else:
                        tl1_response = tl1_response + re.sub('(\r\n)+', "\r\n", msg_tmp, 0)
                        if tl1_verb != "ed-pid"  and  tl1_verb != "act-user":
                            if tl1_response.count(";") > 1:
                                self.__trc_err("error [5] sending TL1 command [{:s}]".format(cmd))
                                self.__last_output = "INVALID TL1 TERMINATION"
                                raise KFrameException(self.__last_output)
                                #return False
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

        if tl1_verb == "act-user" and tl1_response.find(" COMPLD") != -1 and policy == "COMPLD":
            # Start the Event collector login
            self.__collector.thr_event_init()

        return result


    def __cmd_read_all(self):
        """ INTERNAL USAGE
        """
        for _ in (1,2):
            try:
                while True:
                    block = str(self.__if_cmd.read_very_eager().strip(), 'utf-8')
                    if block == "":
                        return True
                    else:
                        self.__logger(block)
            except Exception as eee:
                self.__trc_dbg("exception in __cmd_read_all() - {}".format(eee))
                self.__if_cmd = self.__cmd_connect()    # renewing interface

        return False


    def __cmd_write(self, cmd):
        """ INTERNAL USAGE
        """
        for _ in (1,2):
            try:
                self.__if_cmd.write(cmd.encode())
                self.__trc_dbg("__cmd_write({})".format(cmd))
                return True
            except Exception as eee:
                self.__trc_dbg("exception in __cmd_write() - {}".format(eee))
                self.__if_cmd = self.__cmd_connect()    # renewing interface

        return False


    def __cmd_expect(self, key_list):
        """ INTERNAL USAGE
        """
        try:
            result_list = self.__if_cmd.expect(key_list, timeout=30)
        except Exception as eee:
            result_list = [],[],[]
            self.__trc_dbg("Exception in __cmd_expect() - {} - ignoring".format(eee))

        self.__logger(str(result_list[2], 'utf-8'))

        return result_list


    def __cmd_connect(self):
        """ INTERNAL USAGE
        """
        is_connected = False

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
            self.__trc_err("TL1: Timeout on connection")
            raise KFrameException("TL1: Timeout on connection")

        return self.__if_cmd


    def __cmd_disconnect(self):
        """ INTERNAL USAGE
        """
        #try:
            #self.__do("CANC-USER;", "COMPLD")
        #except Exception as eee:
            #msg = "Error in disconnection - {:s}".format(str(eee))
            #self.__trc_err(msg)
            #raise KFrameException(msg)
        try:
            self.__trc_err("CLOSING TELNET SESSION")
            self.__if_cmd.close()
        except Exception as eee:
            self.__trc_err("ERROR ON CLOSING TELNET SESSION")

        self.__if_cmd = None


    def __logger(self, msg):
        if self.__logfile:
            ts = datetime.datetime.now().isoformat(' ')
            for row in msg.replace("\r","").split("\n"):
                self.__logfile.write("[{}] {}\n".format(ts, row))


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


    def __trc_err(self, msg, level=None):
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

    #tl1.thr_event_terminate()

    print("FINE")

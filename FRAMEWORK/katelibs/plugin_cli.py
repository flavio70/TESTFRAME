#!/usr/bin/env python
"""
###############################################################################
# MODULE: plugin_cli.py
#         This moduled contains the definition of Class and Methods available
#         to invoke CLI commands on 1850TSS equipments.
#
# AUTHOR: G.Bonalume
# DATE  : 28/10/2015
#
###############################################################################
"""

import telnetlib
import threading
import time
import socket


########################################## CLASS Plugin1850CLI ####################

class Plugin1850CLI():
    """
        CLI plugin for 1850TSS Equipment
    """
    def __init__(self, IP, PORT=1123, krepo=None, ktrc=None, eRef=None):
        """
            Costructor for generic CLI interface
            IP   : equipment's IP Address
            PORT : CLI interface Port
        """

        # Private members:
        self.__the_ip = IP
        self.__the_port = PORT
        self.__krepo = krepo              # result report (Kunit class instance)
        self.__ktrc = ktrc                # Tracer object
        self.__eqpt_ref = eRef            # equipment reference
        self.__if_cmd = None              # CLI command interface
        self.__connected = False          # flag indicating connection performed
        self.__curr_timeout = 10          # current timeout
        self.__timeout = 0                # init timeout
        self.__ending_time = 0            # ending time for timeout evaluation
        self.__timer = None
        self.__user = ""
        self.__password = ""
        self.__prompt = ""
        self.__last_cmd = "UNSET"         # last CLI command
        self.__last_output = ""           # last CLI command output
        self.__last_status = "NONE"       # last CLI command status)
        # Semaphore for CLI Keep Alive Threading area
        #self.__thread_lock = threading.Lock()

    def get_last_cmd(self):
        """
            Return the last CLI command
        """
        return self.__last_cmd


    def get_last_outcome(self):
        """
            Return the last CLI command output (multi-line string)
        """
        return self.__last_output


    def get_last_cmd_status(self):
        """
            Return the last CLI command status ("CMPLD"/"DENY")
        """
        return self.__last_status


    def connect(self, timeout=None, user="admin", password="Alcatel1"):
        """
            Connection to CLI port of selected equipment.
            Returns False in case of failure otherwise returns True.
        """

        if self.__connected:                # already connected
            msg = "Not connected"
            self.__trc_err(msg)
            self.__last_status = "FAILURE"
            return

        self.__trc_inf("CONNECTING CLI...")

        # Setting current timeout value
        if timeout is not None:
            self.__curr_timeout = timeout

        # Setting Username, Password and Prompt
        self.__user = user
        self.__password = password
        self.__prompt = "Cli:{:s} > ".format(self.__user)

        # Initializing kunit interface
        if self.__krepo:
            self.__krepo.start_time()

        # Initializes variables for detecting timeout
        self.__to_start()

        # Performs connection
        if not self.__connect():
            self.__t_failure("CONNECT", None, "CLI CONNECTION", self.get_last_cmd_status())
            return False

        # Start cli session living timer
        if not self.__keep_alive():
            self.disconnect()
            return False

        # Disable "press any key to continue" request
        if not self.__do("administrator config confirm disable"):
            self.disconnect()
            return False

        self.__trc_inf("... CLI INTERFACE for commands ready.")
        return True




    def __connect(self):
        """
            Connection to CLI port of selected equipment.
            Returns False if detected exceptions otherwise returns True.
        """
        #with self.__thread_lock:
        self.__KeepaliveEnb = False

        try:
            # Creates telnet instance and opens connection
            self.__if_cmd = telnetlib.Telnet()
            self.__if_cmd.open(self.__the_ip, port=self.__the_port, timeout=self.__timeout)
            # Exchange username and password
            self.__if_cmd.read_until(b"Login: ", timeout=self.__timeout)
            self.__if_cmd.write(self.__user.encode() + b"\r\n")
            self.__if_cmd.read_until(b"Password: ", timeout=self.__timeout)
            self.__if_cmd.write(self.__password.encode() + b"\r\n")
            # Wait for cli prompt
            self.__if_cmd.read_until(self.__prompt.encode(), timeout=self.__timeout)
        except socket.timeout as eee:
            msg = "Timeout connecting {:s}/{:s} - Timeout: {:s} sec.".format(str(self.__the_ip), str(self.__the_port), str(self.__timeout))
            self.__trc_err(msg)
            self.__last_status = "TIMEOUT"
            return False
        except Exception as eee:
            msg = "Error connecting {:s}/{:s} - {:s}".format(str(self.__the_ip), str(self.__the_port), str(eee))
            self.__trc_err(msg)
            self.__last_status = "FAILURE"
            return False

        # Marks connection completed
        self.__connected = True

        #with self.__thread_lock:
        self.__KeepaliveEnb = True

        return True


    def disconnect(self):
        """
        Disconnection from CLI port of selected equipment.
        """
        if not self.__connected:       # already disconnected
            return

        self.__trc_inf("DISCONNECTING CLI...")
        if self.__timer is not None:
            self.__timer.cancel()
        self.__do("logout")
        self.__connected = False
        self.__trc_inf("... CLI DISCONNECTED")
        return


    def __keep_alive(self):
        """ INTERNAL USAGE
            Set and start a Timer in order to keep the cli dialog alive
        """
        #with self.__thread_lock:
        while not self.__KeepaliveEnb:
            #time.sleep(3)
            #self.__trc_inf(self.__KeepaliveEnb)
            pass

        # Exit if not connected
        if not self.__connected:
            return True

        #self.__trc_inf("++++++++++++++++++++++++")
        #self.__trc_inf("RESTART TIMER")
        #self.__trc_inf("++++++++++++++++++++++++")
        self.__timer = threading.Timer(5, self.__keep_alive)
        try:
            self.__timer.start()
        except Exception as eee:
            msg = "Error in timer start - {:s}".format(str(eee))
            self.__trc_err(msg)
            return False
        if not self.__do("\n", keepalive=True):
            return False
        return True


    def do_until(self, cmd, condition=None, timeout=None):
        """
            Send the specified CLI command to equipment until the specified condition is verified.
            or the specified timeout expires.
            cmd       = CLI command string
            condition = condition string that could mactch in command result
            timeout   = timeout to close a conditional command (seconds)
            Returns False if detected exceptions otherwise returns True.
        """

        if condition is None:
            msg = "Condition must be supplied in do_until."
            self.__trc_err(msg)
            self.__last_status = "FAILURE"
            return

        if not self.__connected:       # not connected
            msg = "Not connected"
            self.__trc_err(msg)
            self.__last_status = "FAILURE"
            return

       # Setting retries number and current timeout value
        retries = 10
        instance = 0
        if timeout is None:
            timeout = self.__curr_timeout
        self.__curr_timeout = timeout / retries

        # Initializing kunit interface interface
        if self.__krepo:
            self.__krepo.start_time()

        # Initializes variables for detecting timeout
        self.__to_start()

        while instance < retries:
            # Send command and retrieve result
            result = self.__do(cmd)
            if not result:
                self.__t_failure(cmd, None, self.get_last_outcome(), self.get_last_cmd_status())
                break
            result = self.__verify_condition(condition)
            if result:
                break
            self.__to_wait()
            instance = instance+1
            # Initializes variables for detecting timeout
            self.__to_start()

        if not result:
            errmsg = "After: {:s} sec. -- Condition ({:s}): NOT-SATISFIED".format(str(timeout), condition)
            self.__t_failure(cmd, None, self.get_last_outcome(), errmsg)
            self.__last_status = "FAILURE"
        else:
             self.__t_success(cmd, None, self.get_last_outcome())

    def do(self, cmd, timeout=None, policy=None, condition=None):
        """
            Send the specified CLI command to equipment.
            It is possible specify a positive or negative behaviour and a
            matching condition string
            cmd       = CLI command string
            timeout   = timeout to close a conditional command (seconds)
            policy    = "COMPLD" -> positive result expected
                        "DENY"   -> negative result expected
                        none     -> returns any supplied result (default)
            condition = condition string that could mactch in command result
            Returns False if detected exceptions otherwise returns True.
        """

        if policy is not None and policy != "COMPLD" and policy != "DENY":
            msg = "Policy parameter must be <none> or COMPLD or DENY"
            self.__trc_err(msg)
            self.__last_status = "FAILURE"
            return

        if not self.__connected:       # not connected
            msg = "Not connected"
            self.__trc_err(msg)
            self.__last_status = "FAILURE"
            return

        # Setting current timeout value
        if timeout is not None:
            self.__curr_timeout = timeout

        # Initializing kunit interface interface
        if self.__krepo:
            self.__krepo.start_time()

        # Initializes variables for detecting timeout
        self.__to_start()

        # Send command and retrieve result
        cmd_success = self.__do(cmd)
        if not cmd_success:
            self.__t_failure(cmd, None, self.get_last_outcome(), self.get_last_cmd_status())
            return

        # Verify result
        if policy is not None:
            cnd_success = self.__verify_result()
        else:
            cnd_success = True

        # Verify condition
        if condition:
            cnd_success = self.__verify_condition(condition)

        # Verify command result according with supplied policy
        if policy == "COMPLD":
            if cnd_success:
                self.__t_success(cmd, None, self.get_last_outcome())
                self.__last_status = "SUCCESS"
            else:
                if condition:
                    errmsg = "Policy: COMPLD -- Condition ({:s}): NOT-SATISFIED".format(condition)
                else:
                    errmsg = "Policy: COMPLD -- Result: DENY"
                self.__t_failure(cmd, None, self.get_last_outcome(), errmsg)
                self.__last_status = "FAILURE"
        elif policy == "DENY":
            if not cnd_success:
                self.__t_success(cmd, None, self.get_last_outcome())
                self.__last_status = "SUCCESS"
            else:
                if condition:
                    errmsg = "Policy: DENY -- Condition ({:s}): SATISFIED".format(condition)
                else:
                    errmsg = "Policy: DENY -- Result: COMPLD"
                self.__t_failure(cmd, None, self.get_last_outcome(), errmsg)
                self.__last_status = "FAILURE"
        else:
            if condition:
                if not cnd_success:
                    errmsg = "Policy: NONE -- Condition ({:s}): NOT-SATISFIED".format(condition)
                    self.__t_failure(cmd, None, self.get_last_outcome(), errmsg)
                    self.__last_status = "FAILURE"
                else:
                    self.__t_success(cmd, None, self.get_last_outcome())
                    self.__last_status = "SUCCESS"
            else:
                self.__t_success(cmd, None, self.get_last_outcome())


        self.__trc_inf("\n[=====>\nCommand: {:s}\nResult:  {:s}\nOutput:\n{:s}\n=====]".format(self.get_last_cmd(), self.get_last_cmd_status(), self.get_last_outcome()), level=0)

        return


    def __do(self, cmd, keepalive=False):
        """
            INTERNAL USAGE
            Send the specified CLI command to equipment.
            cmd = CLI command string
            Returns False if detected exceptions otherwise returns True.
            self.__last_output contains the result of the coomand.
        """

        #self.__trc_inf("++++++++++++++++++++++++")
        #self.__trc_inf(keepalive)
        #self.__trc_inf("++++++++++++++++++++++++")

        if cmd != "logout" and not keepalive:
            # Trash all trailing characters from stream
            while str(self.__if_cmd.read_very_eager().strip(), 'utf-8') != "":
                pass
            #self.__trc_inf("++++++++++++++++++++++++")
            #self.__trc_inf("SET KEEPALIVE FLAG FALSE")
            #self.__trc_inf("++++++++++++++++++++++++")
            #with self.__thread_lock:
            self.__KeepaliveEnb = False
            # Setting last command, last_output and last_status.
            self.__last_cmd = cmd
            self.__last_output = ""
            self.__last_status = "NONE"

            # Set current timeout value
            if not self.__to_set():
                msg = "Timeout detected before invoking commad {:s} execution".format(cmd)
                self.__trc_err(msg)
                self.__last_status = "TIMEOUT"
                return False

        # Invoking cli command execution
        try:
            self.__if_cmd.write(cmd.encode() + b"\r\n")
        except EOFError as eee:
            msg = "Error invoking cli command({:s})\nException: {:s}".format(cmd, str(eee))
            self.__trc_err(msg)
            self.__last_status = "FAILURE"
            return False

        if cmd != "logout":
            try:
                buf = self.__if_cmd.read_until(self.__prompt.encode(), timeout=self.__timeout)
            except socket.timeout as eee:
                msg = "Timeout in waiting for commad execution"
                self.__trc_err(msg)
                self.__last_status = "TIMEOUT"
                return False
            except EOFError as eee:
                msg = "Error in waiting for commad execution - {:s}".format(str(eee))
                self.__trc_err(msg)
                self.__last_status = "FAILURE"
                return False
            skip = ".. message: waiting - other CLI command in progress\r"
            self.__last_output = buf.decode().replace(skip,"")
        if not keepalive:
            #with self.__thread_lock:
            self.__KeepaliveEnb = True
            #self.__trc_inf("++++++++++++++++++++++++")
            #self.__trc_inf("SET KEEPALIVE FLAG TRUE")
            #self.__trc_inf("++++++++++++++++++++++++")
        return True


    def __verify_result(self):
        """ INTERNAL USAGE
        """
        cond_list_ok = ("DUMMY"," .. message: successful completed command\n")

        for cond in cond_list_ok:
            if self.__verify_condition(cond):
                return True
        return False

    def __verify_condition(self, condition):
        """ INTERNAL USAGE
        """
        return condition in self.get_last_outcome()

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

    def __to_start(self):
        """
            Initialize variables for starting timeout verification
            INTERNAL USAGE
        """
        self.__timeout = self.__curr_timeout
        self.__ending_time = int(time.time()) + int(self.__timeout)


    def __to_set(self):
        """
            Set the current timeout value
            Returns False if timeout is expired
            INTERNAL USAGE
        """
        self.__timeout = int(self.__ending_time) - int(time.time())
        if self.__timeout < 0:
            return False
        else:
            return True


    def __to_wait(self):
        """
            Returns the remaining time before expiration
            INTERNAL USAGE
        """
        time.sleep(int(self.__ending_time) - int(time.time()))




########################################## MAIN ####################


if __name__ == "__main__":

    from katelibs.kunit         import Kunit
    from katelibs.ktracer       import KTracer

    print("DEBUG")

    repo = Kunit('/users/bonalg/WRK', 'prova.py')
    trace = KTracer('/users/bonalg/WRK', level="ERROR", trunk=True)
    cli = Plugin1850CLI("135.221.125.80", krepo=repo, ktrc=trace)

    if not cli.connect():
        cli.disconnect()
        repo.frame_close()
        exit()

    # cli._Plugin1850CLI__trc_inf(" 1. Condizione iniziale")

    cli._Plugin1850CLI__trc_inf(" 1. Condizione iniziale")
    cli.do("linkagg show")
    
    #
    # lag      AdminKey    LAG User Label                     LAG Size Admin State
    # ======== =========== ================================== ======== ===============
    #
    # .. message: not found Entry

    cli._Plugin1850CLI__trc_inf(" 2. Creazione di una LAG (EXPECTED SUCCESS)")
    cli.do("linkagg activate lag1 size 2 adminkey  1 ets lagname LAG_1", policy="COMPLD", timeout=20)
    #
    # .. message: successful completed command
    #

    cli._Plugin1850CLI__trc_inf(" 3. SHOW delle LAG create")
    cli.do("linkagg show")
    #
    # lag      AdminKey    LAG User Label                     LAG Size Admin State
    # ======== =========== ================================== ======== ===============
    # 1        1           'LAG_1'                            2        enable

    cli._Plugin1850CLI__trc_inf(" 4. Show della LAG1 ")
    cli.do("linkagg show lag1")
    # 
    # Link Aggregation Info of lag1
    # -----------------------------
    # LAG Number: lag1
    # LAG User Label: 'LAG_1'
    # LAG Size: 2
    # ...

    cli._Plugin1850CLI__trc_inf(" 5. EDIT LAG con valore del campo size fuori range (expected Deny da parte della CLI)")
    cli._Plugin1850CLI__trc_inf("    NB: i deny dati direttamente dalla CLI non hanno sempre output univoco,")
    cli._Plugin1850CLI__trc_inf("    cmq solitamente contengono 'Error' oppure 'unsuccessful'")
    cli.do("linkagg config lag1 size 20", policy="COMPLD", timeout=20)
    #                                ^
    # Error: Out of range. Valid range is: 1 - 16

    cli._Plugin1850CLI__trc_inf(" 6. EDIT LAG con valore ammissibile  del campo size (expected SUCCESS)")
    cli.do("linkagg config lag1 size 10", policy="COMPLD", timeout=20)
    #                                ^
    # .. message: successful completed command

    cli._Plugin1850CLI__trc_inf(" 7. EDIT parametro LACP della LAG (expected Deny da parte della CLI)")
    cli.do("linkagg config lag1 lacp disable", policy="COMPLD", timeout=20)
    # 
    # .. message: enabled Lag; refused change of param lacp
    # 
    # .. message: unsuccessful completed command

    cli._Plugin1850CLI__trc_inf(" 8. EDIT Dello stato amministrativo: Disable, del parametro LACP e ancora dello")
    cli._Plugin1850CLI__trc_inf("    stato amministrativo Enable (EXPECTED SUCCESS)")
    cli.do("linkagg config lag1 adminstate disable", policy="COMPLD", timeout=10)
    # 
    # .. message: successful completed command
    # 
    cli.do("linkagg config lag1 lacp disable", policy="COMPLD", timeout=10)
    # 
    # .. message: successful completed command
    # 
    cli.do("linkagg config lag1 adminstate enable", policy="COMPLD", timeout=10)
    # 
    # .. message: successful completed command
    # 

    cli._Plugin1850CLI__trc_inf(" 11. Show delle VPLS  (expected nessuna)")
    cli.do("vpls show")
    # 
    # LabelKey     vpls VpnId                       Status
    # ============ ================================ ===============
    # 
    # .. message: not found Entry

    cli._Plugin1850CLI__trc_inf(" 12. Creazione VPLS e bind della LAG (expected SUCCESS)")
    cli.do("vpls activate  VPLAG portset lag1", policy="COMPLD", timeout=20)
    # 
    # .. message: successful completed command

    cli._Plugin1850CLI__trc_inf(" 13. Show delle VPLS")
    cli.do("vpls show")
    # 
    # LabelKey     vpls VpnId                       Status
    # ============ ================================ ===============
    # @1           'VPLAG'                          active

    cli._Plugin1850CLI__trc_inf(" 14. Show della VPLS VPLAG")
    cli.do("vpls show VPLAG")
    # 
    # VPLS Info
    # ---------
    # vpls VpnId: 'VPLAG'
    # vpls Name: ''
    # vpls Descr: ''
    # ...

    cli._Plugin1850CLI__trc_inf(" 15. Creazione di una xconnessione NNI-UNI tra la Vpls e la LAG")
    cli.do("pbflowoutunidir activate test_VPLS_LAG  port lag1 vpls VPLAG outtraffictype be", policy="COMPLD", timeout=30)
    # 
    # .. message: successful completed command

    cli._Plugin1850CLI__trc_inf(" 16. Show dei Traffic Descriptor ")
    cli.do("trafficdescriptor show")
    # 
    # LabelKey UserLabel              Status Type  cir      pir      cbs      pbs
    # ======== ====================== ====== ===== ======== ======== ======== ========
    # @1       'nullBeTD'             active be    0        0        0        0

    cli._Plugin1850CLI__trc_inf(" 17. Cancellazione del TrafficDescriptor  (expected DENY da parte dell'AGENT perche' in uso)")
    cli._Plugin1850CLI__trc_inf("     N.B.: i Deny dell'agent provocano sempre il messaggio 'error: db writing error'")
    cli.do("trafficdescriptor delete  nullBeTD", policy="COMPLD", timeout=20)
    # 
    # >> error: db writing error for Status=destroy of 1
    # 
    # .. message: unsuccessful completed command

    cli._Plugin1850CLI__trc_inf(" 18. Cancellazione della VPLS (expected DENY da parte dell'AGENT per la presenza")
    cli._Plugin1850CLI__trc_inf("     della xconnessione)")
    cli.do("vpls delete VPLAG", policy="COMPLD", timeout=10)
    # 
    # >> error: db writing error for vplsConfigStaticEgressPorts=
    #    [00] repeats 512 times of 1
    # 
    # .. message: unsuccessful completed command

    cli._Plugin1850CLI__trc_inf(" 19. Cancellazione della xconnessione (expected Success)")
    cli.do("pbflowoutunidir delete test_VPLS_LAG", policy="COMPLD", timeout=20)
    # 
    # .. message: successful completed command

    cli._Plugin1850CLI__trc_inf(" 20. Cancellazione del TrafficDescriptor (expected Success)")
    cli.do("trafficdescriptor delete  nullBeTD", policy="COMPLD", timeout=10)
    # 
    # .. message: successful completed command

    cli._Plugin1850CLI__trc_inf(" 21. Cancellazione dela VPLS (expected Success)")
    cli.do("vpls delete VPLAG", policy="COMPLD", timeout=10)
    # 
    # .. message: successful completed command

    cli._Plugin1850CLI__trc_inf(" 22. Cancellazione della Lag (Expected Success)")
    cli.do("linkagg delete lag1", policy="COMPLD", timeout=10)
    # 
    # .. message: successful completed command

    cli._Plugin1850CLI__trc_inf(" 23. Show delle LAG, delle VPLS, dei TrafficDescriptor e delle")
    cli._Plugin1850CLI__trc_inf("     Xconnessioni NNI-UNI (expected: vuoto)")
    cli.do("linkagg show")
    # 
    # lag      AdminKey    LAG User Label                     LAG Size Admin State
    # ======== =========== ================================== ======== ===============
    # 
    # .. message: not found Entry

    cli.do("vpls show")
    # 
    # LabelKey     vpls VpnId                       Status
    # ============ ================================ ===============
    # 
    # .. message: not found Entry

    cli.do("trafficdescriptor show")
    # 
    # LabelKey UserLabel              Status Type  cir      pir      cbs      pbs
    # ======== ====================== ====== ===== ======== ======== ======== ========
    # 
    # .. message: not found Entry

    cli.do("pbflowoutunidir show")
    # 
    # 
    # .. message: not found Cross Connection


    #cli.do_until("interface show", condition=".. message: not found interface\n", timeout=10)
    #cli.do("interface show", timeout=5, policy="COMPLD", condition=".. message: not found interface\n")

    cli.disconnect()
    repo.frame_close()

    print("FINE")

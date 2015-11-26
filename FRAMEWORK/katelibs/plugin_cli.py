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
        self.__user = "admin"
        self.__password = "Alcatel1"
        self.__prompt = "Cli:{:s} > ".format(self.__user)
        self.__last_cmd = ""              # last CLI command
        self.__last_output = ""           # last CLI command output
        self.__last_status = "SUCCESS"    # last CLI command status)

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


    def connect(self):
        """
            Connection to CLI port of selected equipment.
            Returns False if detected exceptions otherwise returns True.
        """

        # Initializes variables for detecting timeout
        self.__to_start()

        if self.__connected:       # already connected
            return True

        self.__trc_inf("CONNECTING CLI...")
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


    def disconnect(self):
        """
        Disconnection from CLI port of selected equipment.
        """
        if not self.__connected:       # already disconnected
            return

        if self.__timer is not None:
            self.__timer.cancel()
        self.__do("logout")
        self.__connected = False
        return


    def __keep_alive(self):
        """ INTERNAL USAGE
            Set and start a Timer in order to keep the cli dialog alive
        """
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

        # Setting current timeout value
        if timeout is not None:
            self.__curr_timeout = timeout

        # Initializing kunit interface interface
        if self.__krepo:
            self.__krepo.start_time()

        # Activating cli command interface
        if not self.connect():
            self.__t_failure(cmd, None, "CLI CONNECTION", self.get_last_cmd_status())
            return

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
            else:
                self.__t_success(cmd, None, self.get_last_outcome())
        return


    def __do(self, cmd, keepalive=False):
        """
            INTERNAL USAGE
            Send the specified CLI command to equipment.
            cmd = CLI command string
            Returns False if detected exceptions otherwise returns True.
            self.__last_output contains the result of the coomand.
        """

        # Trash all trailing characters from stream
        self.__last_cmd = cmd

        # Trash all trailing characters from stream
        while str(self.__if_cmd.read_very_eager().strip(), 'utf-8') != "":
            pass

        if cmd != "logout" and not keepalive:
            # Set current timeout value
            if not self.__to_set():
                msg = "Timeout detected before invoking commad {:s} execution".format(cmd)
                self.__trc_err(msg)
                self.__last_status = "TIMEOUT"
                return False

        try:
            # Invoking cli command execution
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
            self.__last_output = buf.decode()

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
        self.__ending_time = int(time.time()) + self.__timeout


    def __to_set(self):
        """
            Set the current timeout value
            Returns False if timeout is expired
            INTERNAL USAGE
        """
        self.__timeout = self.__ending_time - int(time.time())
        if self.__timeout <= 0:
            return False
        else:
            return True




########################################## MAIN ####################


if __name__ == "__main__":

    from katelibs.kunit         import Kunit
    from katelibs.ktracer       import KTracer

    print("DEBUG")

    repo = Kunit('/users/bonalg/WRK', 'prova.py')
    trace = KTracer('/users/bonalg/WRK', level="ERROR", trunk=True)
    cli = Plugin1850CLI("135.221.125.80", krepo=repo, ktrc=trace)

    cli.do("interface show", timeout=5, policy="COMPLD", condition=".. message: not found interface\n")

    if cli.get_last_cmd_status() == "SUCCESS":
        trace.k_tracer_info("[\n{:s}\n]".format(cli.get_last_outcome()), level=0)
    else:
        trace.k_tracer_info("[\nCommand: {:s}\nResult:  {:s}\n]".format(cli.get_last_cmd(), cli.get_last_cmd_status()), level=0)

    cli.disconnect()
    repo.frame_close()

    print("FINE")

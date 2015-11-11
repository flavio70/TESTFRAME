#!/usr/bin/env python
"""
###############################################################################
# MODULE: plugin_cli.py
#
# AUTHOR: G.Bonalume
# DATE  : 28/10/2015
#
###############################################################################
"""

import telnetlib
import re
import threading
import time
import os
import sys
import socket


########################################## CLASS Plugin1850CLI ####################

class Plugin1850CLI():
    """
        CLI plugin for 1850TSS Equipment
    """

    def __init__(self, IP, PORT=1123, krepo=None, eRef=None):
        """
            Costructor for generic CLI interface
            IP   : equipment's IP Address
            PORT : CLI interface Port
        """

        self.__the_ip      = IP
        self.__the_port    = PORT
        self.__krepo       = krepo # result report (Kunit class instance)
        self.__eqpt_ref    = eRef  # equipment reference
        self.__if_cmd      = None  # CLI command interface
        self.__connected   = False # flag indicating connection performed
        self.__timeout     = 5     # timeout
        self.__last_output = ""    # store the output of latest CLI command
        self.__last_status = ""    # store the status of latest CLI command ("CMPLD"/"DENY")
        self.__timer       = None

    def get_last_outcome(self):
        """
            Return the latest CLI command output (multi-line string)
        """
        return self.__last_output


    def get_last_cmd_status(self):
        """
            Return the latest CLI command status ("CMPLD"/"DENY")
        """
        return self.__last_status


    def connect(self):
        """
            Connection to CLI port of selected equipment.
            Returns False if detected exceptions otherwise returns True.
        """

        if self.__connected:       # already connected
            return True

        try:
            self.__if_cmd = telnetlib.Telnet()
            self.__if_cmd.open(self.__the_ip, port=self.__the_port, timeout=self.__timeout)
        except socket.timeout as eee:
            msg = "Timeout connecting cli port"
            print(msg)
            return False
        except Exception as eee:
            msg = "Error connecting cli port - {:s}".format(str(eee))
            print(msg)
            return False

        # Exchange of username and password
        user = "admin"
        password = "Alcatel1"
        cmd = "interface show"
        try:
            res = self.__if_cmd.read_until(b"Login: ", timeout=self.__timeout)
        except EOFError as eee:
            msg = "Error in waiting for login request - {:s}".format(str(eee))
            print(msg)
            return False
        self.__if_cmd.write(user.encode() + b"\r\n")
        try:
            self.__if_cmd.read_until(b"Password: ", timeout=self.__timeout)
        except EOFError as eee:
            msg = "Error in waiting for password request - {:s}".format(str(eee))
            print(msg)
            return False
        self.__if_cmd.write(password.encode() + b"\r\n")
        try:
            buf = self.__if_cmd.read_until(b"Cli:admin > ", timeout=self.__timeout)
        except EOFError as eee:
            msg = "Error in waiting for prompting - {:s}".format(str(eee))
            print(msg)
            return False

        # Marks connection completed
        self.__connected = True

        # Start cli session living timer
        self.__keep_alive()      

        return True


    def disconnect(self):
        """
        Disconnection from CLI port of selected equipment.
        """
        if not self.__connected:       # already disconnected
            return

        self.__timer.cancel()
        self.do("logout")
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
            print(msg)
        self.do("\n")


    def do(self, cmd):
        """
            Send the specified CLI command to equipment.
            cmd  = CLI command string
        """

        # Activating cli command interface
        if not self.connect():
            return 

        if self.__krepo:
            self.__krepo.start_time()

        # Trash all trailing characters from stream
        while str(self.__if_cmd.read_very_eager().strip(), 'utf-8') != "":
            pass

        try:
            self.__if_cmd.write(cmd.encode() + b"\r\n")
        except EOFError as eee:
            msg = "Error in cli.do({:s})\nException: {:s}".format(cmd, str(eee))
            print(msg)
            self.__disconnect()
            self.__connect()

        if cmd != "logout":
            buf = self.__if_cmd.read_until(b"Cli:admin > ", timeout=self.__timeout)        
            print("[" + buf.decode() + "]")


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



########################################## MAIN ####################


if __name__ == "__main__":
    print("DEBUG")

    cli = Plugin1850CLI("135.221.125.80")

    cli.do("interface show")

    cli.disconnect()


    print("FINE")

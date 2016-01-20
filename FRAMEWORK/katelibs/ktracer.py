#!/usr/bin/env python
"""
###############################################################################
# MODULE: ktracer.py
#         Collect and log trace messages for K@TE framework
#         A message log will be collect on .../logs/SUITE_trace.log file and
#         print on STDOUT if required
#         Only on file, a Time Stamp and an environment information will be
#         add on message text
#
# AUTHOR: C.Ghelfi
# DATE  : 20/11/2015
#
###############################################################################
"""

import os
import datetime
import time
import inspect



class KTracer():
    """
    Manage tracing
    """

    def __init__(self, basedir=None, level="INFO", trunk=True):
        """
        Costructor for KEnvironment.
        basedir : (opt) home of test running enviromnent
        level   : (opt) "ERROR"/"INFO"/"DEBUG" - Standard level :- "INFO"
        NOTE: the level trace will be changed in any time creating an empty file named
              'TRACE_VERBOSE' in log directory
              Presence of TRACE_VERBOSE will raise the trace verbosity on stdout
        """
        if basedir is None:
            self.__base_path = "."
        else:
            self.__base_path = basedir

        self.__enable_info_level = "{:s}/TRACE_VERBOSE".format(self.__base_path)
        if os.path.exists(self.__enable_info_level):
            self.__level = "DEBUG"
        else:
            self.__level = level

        self.__main_file = "{:s}/SUITE_trace.log".format(self.__base_path)

        if trunk:
            if os.path.isfile(self.__main_file):os.remove(self.__main_file)
            self.__main_fh = open(self.__main_file, "w")
            os.chmod(self.__main_file, 0o666)
        else:
            self.__main_fh = open(self.__main_file, "a")


    def clean_up(self):
        self.__main_fh.close()


    def k_tracer_error(self, msg, level=None):
        """ Perform an error message trace. The supplied message will be logged with a time stamp
            and module, row and function/method
        """
        ts = datetime.datetime.now().isoformat(' ')

        if level is None:
            level = 1   # The caller context to trace is the next one on call stack

        try:
            insp = inspect.stack()
            for i in range(len(insp)):
                # Searching on current stack frame for this function calling
                if insp[i][4][0].find("k_tracer_error(") != -1:
                    stack_elem = insp[i + level]
                    context_mod = os.path.basename(stack_elem[1])
                    context_row = stack_elem[2]
                    context_fun = stack_elem[3]
                    break

            label = "{}:{}({})".format(context_mod, context_row, context_fun)
        except:
            label = "FRAMEWORK"

        for row in str(msg).splitlines():
            self.__main_fh.write("[{:s} {:50s}] {:s}\n".format(ts, label, row))
        self.__main_fh.write("[{:s} {:50s}]\n".format(ts, label))

        print(msg)


    def k_tracer_info(self, msg, level=None):
        """ Perform an info message trace. The supplied message will be logged with a time stamp
            and module, row and function/method
        """
        ts = datetime.datetime.now().isoformat(' ')

        if level is None:
            level = 1   # The caller context to trace is the next one on call stack

        try:
            insp = inspect.stack()
            for i in range(len(insp)):
                # Searching on current stack frame for this function calling
                if insp[i][4][0].find("k_tracer_error(") != -1:
                    stack_elem = insp[i + level]
                    context_mod = os.path.basename(stack_elem[1])
                    context_row = stack_elem[2]
                    context_fun = stack_elem[3]
                    break

            label = "{}:{}({})".format(context_mod, context_row, context_fun)
        except:
            label = "FRAMEWORK"

        for row in str(msg).splitlines():
            self.__main_fh.write("[{:s} {:50s}] {:s}\n".format(ts, label, row))
        self.__main_fh.write("[{:s} {:50s}]\n".format(ts, label))

        print(msg)


    def k_tracer_debug(self, msg, level=None):
        """ Perform an information message trace. The supplied message will be logged with
            a time stamp and module, row and function/method
        """
        ts = datetime.datetime.now().isoformat(' ')

        if level is None:
            level = 1   # The caller context to trace is the next one on call stack

        try:
            insp = inspect.stack()
            for i in range(len(insp)):
                # Searching on current stack frame for this function calling
                if insp[i][4][0].find("k_tracer_info(") != -1:
                    stack_elem = insp[i + level]
                    context_mod = os.path.basename(stack_elem[1])
                    context_row = stack_elem[2]
                    context_fun = stack_elem[3]
                    break

            label = "{}:{}({})".format(context_mod, context_row, context_fun)
        except:
            label = "FRAMEWORK"

        for row in str(msg).splitlines():
            self.__main_fh.write("[{:s} {:50s}] {:s}\n".format(ts, label, row))

        if self.__level == "DEBUG":
            print(msg)
        elif os.path.exists(self.__enable_info_level):
            print(msg)


if __name__ == '__main__':
    print("DEBUG KEnvironment")

    tracer = KTracer()

    tracer.trc("ciao")
    time.sleep(1)
    tracer.trc("mondo")

    tracer.clean_up()

    print("FINE")

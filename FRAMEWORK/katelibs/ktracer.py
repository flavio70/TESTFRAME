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

    def __init__(self, basedir=None, send_stdout=False):
        """
        Costructor for KEnvironment.
        basedir     : (opt) home of test running enviromnent
        send_stdout : (opt) True for tracing to stdout
        """
        self.__stdout = send_stdout

        if basedir is None:
            self.__base_path = "."
        else:
            self.__base_path = basedir

        self.__main_file = "{:s}/SUITE_trace.log".format(self.__base_path)
        self.__main_fh = open(self.__main_file, "w")


    def clean_up(self):
        self.__main_fh.close()


    def k_tracer_function(self, msg):
        """ Perform a message trace. The supplied message will be logged with a time stamp
            and module, row and function/method
        """
        ts = datetime.datetime.now().isoformat(' ')

        try:
            insp = inspect.stack()
            for i in range(len(insp)):
                # Searching on current stack frame for this function calling
                if insp[i][4][0].find("k_tracer_function(") != -1:
                    # The caller contect to trace is the next one on call stack
                    stack_elem = insp[i+1]
                    context_mod = os.path.basename(stack_elem[1])
                    context_row = stack_elem[2]
                    context_fun = stack_elem[3]
                    break

            label = "{}:{}({})".format(context_mod, context_row, context_fun)
        except:
            label = "FRAMEWORK"

        for row in msg.splitlines():
            self.__main_fh.write("[{:s} {:50s}] {:s}\n".format(ts, label, row))

        if self.__stdout:
            print(msg)


if __name__ == '__main__':
    print("DEBUG KEnvironment")

    tracer = KTracer()

    tracer.trc("ciao")
    time.sleep(1)
    tracer.trc("mondo")

    tracer.clean_up()

    print("FINE")

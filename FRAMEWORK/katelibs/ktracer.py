#!/usr/bin/env python
"""
###############################################################################
# MODULE: ktracer.py
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


    def trc(self, msg, item_ref=None):
        ts = datetime.datetime.now().isoformat(' ')

        try:
            insp = inspect.stack()[2]
            context_mod = os.path.basename(insp[1])
            context_row = insp[2]
            context_fun = insp[3]
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

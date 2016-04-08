#!/usr/bin/env python
"""
###############################################################################
# MODULE: klogger.py
#
# AUTHOR: C.Ghelfi
# DATE  : 07/04/2016
#
###############################################################################
"""

import datetime
import telnetlib
import threading

from katelibs.facility1850  import SerIF


class Klogger1850():
    """ Serial Logger for 1850TSS320
        For each configured serial interface, a log file will be generated
        The capture starts with Klogger1850 creation and will be terminated invoking
        the cleanup() method
    """

    def __init__(self, serials, basedir, testname, label):
        """ Constructor for Klogger1850
            serials : instance of SerIF class (list of couple <slot, serial info>)
            basedir : home dir for logging
            testname: current test file name
            label   : equipment label
        """
        self.__ser = serials        # Instance of SerIF (for list of < slot, <IP,port> >)
        self.__basedir = basedir    # Base dir for log files
        self.__testname = testname  # Current Test File Name
        self.__label = label        # Equipment's label
        self.__if = None            # Serial interface handler

        # Semaphore for klogger info area
        self.__thread_semaphore = threading.Lock()

        # Flag for klogger capture loop
        with self.__thread_semaphore:
            self.__do_loop = True

        # Serial log threads initialization and starting
        self.__threads = {}
        for slot in self.__ser.get_slots():
            self.__threads[slot] = threading.Thread(target=self.__log_manager,
                                                    args=[slot],
                                                    name="log_serial_{:02d}".format(slot))
            self.__threads[slot].daemon = False
            self.__threads[slot].start()


    def __connect(self, slot):
        """ INTERNAL USAGE
        """
        the_ip = self.__ser.get_val(slot)[0]
        the_port = self.__ser.get_val(slot)[1]

        try:
            self.__if = telnetlib.Telnet(the_ip, the_port, 5)
        except Exception as eee:
            print("Error opening serial interface - [{}]".format(eee))
            return False

        return True


    def __log_manager(self, slot):
        """ Capture stream from serial and store on file
        """
        file_name = "{}/{}_{}_ser#{:02d}.log".format(self.__basedir, self.__testname, self.__label, slot)

        file_handler = open(file_name, "w")

        if file_handler is None:
            print("Error in opening {}".format(file_name))
            return

        if self.__connect(slot):
            while True:
                with self.__thread_semaphore:
                    if not self.__do_loop:
                        break
                block = str(self.__if.read_until(b'\n', timeout=5).strip(), 'utf-8')
                if block != "":
                    timestamp = datetime.datetime.now().isoformat(' ')
                    for row in block.replace("\r","").split("\n"):
                        file_handler.write("[{}] {}\n".format(timestamp, row))

        file_handler.close()


    def clean_up(self):
        """ Closing capture
        """
        with self.__thread_semaphore:
            self.__do_loop = False



if __name__ == "__main__":
    import time
    from katelibs.facility1850  import IP

    print("DEBUG")

    SER = SerIF()
    SER.set_serial_to_slot( 1, IP("151.98.176.8"),   1007)
    SER.set_serial_to_slot(10, IP("151.98.176.254"), 1004)
    SER.set_serial_to_slot( 2, IP("151.98.176.254"), 1012)
    SER.set_serial_to_slot( 9, IP("151.98.176.254"), 1019)
    SER.set_serial_to_slot(12, IP("151.98.176.254"), 1022)
    SER.set_serial_to_slot(15, IP("151.98.176.254"), 1025)

    LOG = Klogger1850(SER, "~/GITLABREPO/TESTFRAME/FRAMEWORK/examples/logs", "TestName", "NE1")

    time.sleep(20)

    LOG.cleanup()

    print("FINE")

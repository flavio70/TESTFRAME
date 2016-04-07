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

from katelibs.facility1850  import IP, SerIF


class Klogger1850():
    """ Serial Logger for 1850TSS320
        For each configured serial interface, a log file will be generated
        The capture starts with Klogger1850 creation and will be terminated invoking
        the cleanup() method
    """

    def __init__(self, serials, basedir, label):
        """ Constructor for Klogger1850
            serials : instance of SerIF class (list of couple <slot, serial info>)
            basedir : home dir for logging
            label   : equipment label
        """
        self.__if = None            # Serial interface
        self.__ser = serials        # Instance of SerIF (for list of < slot, <IP,port> >)
        self.__basedir = basedir    # Base dir for log files
        self.__label = label        # Equipment's label

        # Semaphore for klogger info area
        self.__thread_semaphore = threading.Lock()

        # Flag for klogger capture loop
        with self.__thread_semaphore:
            self.__do_loop = True

        # Serial log threads initialization and starting
        for slot_num in self.__ser.get_slots():
            self.__thread = threading.Thread(target=self.__log_manager,
                                             args=[slot_num],
                                             name="log_serial_{:02d}".format(slot_num))
            self.__thread.daemon = False
            self.__thread.start()


    def __connect(self, slot_num):
        """ INTERNAL USAGE
        """
        the_ip = self.__ser.get_val(slot_num)[0]
        the_port = self.__ser.get_val(slot_num)[1]

        try:
            self.__if = telnetlib.Telnet(the_ip, the_port, 5)
        except Exception as eee:
            print("Error opening serial interface - [{}]".format(eee))
            return False

        return True


    def __log_manager(self, slot_num):
        """ Capture stream from serial and store on file
        """
        file_name = "{}#{:02d}.log".format(self.__label, slot_num)
        handler = open(file_name, "w")

        self.__connect(slot_num)

        while True:
            with self.__thread_semaphore:
                if not self.__do_loop:
                    break
            block = str(self.__if.read_until(b'\n', timeout=5).strip(), 'utf-8')
            if block != "":
                timestamp = datetime.datetime.now().isoformat(' ')
                for row in block.replace("\r","").split("\n"):
                    handler.write("[{}] {}\n".format(timestamp, row))

        handler.close()


    def cleanup(self):
        """ Closing capture
        """
        with self.__thread_semaphore:
            self.__do_loop = False



if __name__ == "__main__":
    import time

    print("DEBUG")

    SER = SerIF()
    SER.set_serial_to_slot(1, IP("135.221.125.125"), 2011)

    LOG = Klogger1850(SER, "~/GITLABREPO/TESTFRAME/FRAMEWORK/examples/logs", "NE1")

    time.sleep(20)

    LOG.cleanup()

    print("FINE")

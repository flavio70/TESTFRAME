#!/usr/bin/env python
"""
###############################################################################
# MODULE: kunit.py
#
# AUTHOR: C.Ghelfi
# DATE  : 29/07/2015
#
###############################################################################
"""

import os
import datetime
import time


class Kunit:
    """
    Unit Test Result - JUnit compliant
    """

    def __init__(self, fileName):
        """
        fileName : test's file name
        """
        self.__cnt  = 0     # counter of atomic test
        self.__st   = None  # test execution starting time
        self.__dir  = None  # test dir

        # Lista dei file di report
        self.__reports = { }


        # per ogni report file
        # dizionario con chiave filename e contenuto file descriptor
        self.__fn   = None  # xml file name
        self.__clnm = None  # basic name of test, i.e. without path and suffix
        self.__f    = None  # file descriptor

        self.children = None # object's children list
        self.frame_status = None # object's frameStatus
        self.name = None # object name

        self.__fn   = '{:s}.XML'.format(os.path.splitext(fileName)[0])
        self.__clnm = os.path.splitext(os.path.basename(self.__fn))[0]

        self.__dir = os.path.split(os.path.abspath(fileName))[0]
        self.children = []
        self.frame_status = False
        self.name = fileName

    def __str__(self):
        return self.__fn

    def frame_open(self):
        """ Start xml composition
        """
        self.__f = open(self.__fn, "w")
        try:
            os.chmod(self.__fn, 0o666)
        except:
            pass
        self.__f.writelines('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.__f.writelines('<testsuite>\n')
        self.frame_status = True


    def frame_close(self):
        """ Close xml composition
        """
        self.__f.writelines('</testsuite>\n')
        self.__f.close()
        self.frame_status = False


    def add_success(self, ref_obj, title, elapsed_time, out_text):
        """ Inject a POSITIVE record on xml result file
            ref_obj      : reference to an Equipment variable (could be None)
            title        : describe the performed action. For example, a CLI/TL1/... command
            out_text     : verbose description of test outcome.
            elapsed_time : explicit declaration of test's time execution. See start_time()
        """
        if elapsed_time is None:
            delta_t = str((datetime.datetime.now() - self.__st).total_seconds())
        else:
            delta_t = elapsed_time
        self.__st = None
        self.__f.writelines(self.__make_test_case(ref_obj, title, delta_t))
        self.__make_system_out(out_text)
        self.__f.writelines('\t</testcase>\n')
        #
        # The following code is used in case we have to fill up also the xml part related to any open kunit child
        # For example for any TPSBlock opened inside testcase istance
        for child in self.children:
            if child.frame_status:
                child.__st = None
                child.__f.writelines(child.__make_test_case(ref_obj, title, delta_t))
                child.__make_system_out(out_text)
                child.__f.writelines('\t</testcase>\n')


    #pylint: disable=too-many-arguments
    def add_failure(self, ref_obj, title, elapsed_time, out_text, err_text, log_text=None):
        """ Inject a FAILURE record on xml result file
            ref_obj      : reference to an Equipment variable (could be None)
            title        : describe the performed action. For example, a CLI/TL1/... command
            out_text     : verbose description of test outcome.
            err_text     : verbose description of errored scenario.
            log_text     : additional reference to log repository (optional)
            elapsed_time : explicit declaration of test's time execution. See start_time()
        """
        if elapsed_time is None:
            delta_t = str((datetime.datetime.now() - self.__st).total_seconds())
        else:
            delta_t = elapsed_time
        self.__st = None
        row = self.__make_test_case(ref_obj, title, delta_t)
        self.__f.writelines(row)
        self.__make_log_error(log_text)
        self.__make_system_out(out_text)
        self.__make_system_err(err_text)
        self.__f.writelines('\t</testcase>\n')
        #
        # The following code is used in case we have to fill up also the xml part related to any open kunit child
        # For example for any TPSBlock opened inside testcase istance
        #
        for child in self.children:
            if child.frame_status:
                child.__st = None
                row1 = child.__make_test_case(ref_obj, title, delta_t)
                child.__f.writelines(row1)
                child.__make_log_error(log_text)
                child.__make_system_out(out_text)
                child.__make_system_err(err_text)
                child.__f.writelines('\t</testcase>\n')
    #pylint: enable=too-many-arguments


    #pylint: disable=too-many-arguments
    def add_skipped(self, ref_obj, title, elapsed_time, out_text, err_text, skip_text=None):
        """ Inject a SKIPPED record on xml result file
            ref_obj      : reference to an Equipment variable (could be None)
            title        : describe the performed action. For example, a CLI/TL1/... command
            out_text     : verbose description of test outcome.
            err_text     : verbose description of skip reasons
            log_text     : additional reference to log repository (optional)
            elapsed_time : explicit declaration of test's time execution. See start_time()
        """
        if elapsed_time is None:
            delta_t = str((datetime.datetime.now() - self.__st).total_seconds())
        else:
            delta_t = elapsed_time
        self.__st = None
        row = self.__make_test_case(ref_obj, title, delta_t)
        self.__f.writelines(row)
        self.__make_skipped(skip_text)
        self.__make_system_out(out_text)
        self.__make_system_err(err_text)
        self.__f.writelines('\t</testcase>\n')
        #
        # The following code is used in case we have to fill up also the xml part related to any open kunit child
        # For example for any TPSBlock opened inside testcase istance
        #
        for child in self.children:
            if child.frame_status:
                child.__st = None
                row1 = child.__make_test_case(ref_obj, title, delta_t)
                child.__f.writelines(row1)
                child.__make_skipped(skip_text)
                child.__make_system_out(out_text)
                child.__make_system_err(err_text)
                child.__f.writelines('\t</testcase>\n')
    #pylint: enable=too-many-arguments


    def start_time(self):
        """ Save the starting time for a single test.
            The information will be used by add_success(), add_failure() and add_skipped()
            in order to evaluate elapsed time of test execution.
            In this case, a None value must be supplied for elapsed_time
            on above add_success(),... methods
        """
        self.__st = datetime.datetime.now()


    def start_tps_block(self, tps_area, tps_name):
        '''
        Start an official block containg all code related to aspecific TPS (Test Procedure)
        calling this function into testcase object will generate a specific XML report file for each TPSName provided
        '''

        file_name = "{:s}/{:s}.{:s}_{:s}.XML".format(self.__dir,
                                                     os.path.splitext(os.path.splitext(self.__clnm)[0])[0],
                                                     tps_area,
                                                     tps_name)
        tpsreport = None

        for mychild in self.children:
            if mychild.name == file_name:
                tpsreport = mychild
                break
        else:
            tpsreport = Kunit(file_name)
            self.children.append(tpsreport)

        if not tpsreport.frame_status:
            tpsreport.frame_open()

        print(tpsreport.__fn)


    def stop_tps_block(self, tps_area, tps_name):
        '''
        Stop the block containing the code related to the specific TPS (test Procedure)
        This function will terminate the specific XML report file related to TPSName test id
        '''
        file_name = "{:s}/{:s}.{:s}_{:s}.XML".format(self.__dir,
                                                     os.path.splitext(os.path.splitext(self.__clnm)[0])[0],
                                                     tps_area,
                                                     tps_name)
        for mychild in self.children:
            if mychild.__fn == file_name:
                mychild.frame_close()


    def __make_test_case(self, ref_obj, title, elapsed_time):
        """ INTERNAL USAGE
        """
        if ref_obj is None:
            obj_name = ""
        else:
            obj_name = ref_obj.getLabel()

        self.__cnt = self.__cnt + 1

        t_title = '{:05n} [{:s}] {:.100}'.format(self.__cnt, obj_name, title.replace("&", "&amp;"))
        t_now = str(datetime.datetime.now())

        msg = '\t<testcase classname="{:s}" name="{:s}" timestamp="{:s}" time="{:s}">\n'.format(\
                        self.__clnm,
                        t_title,
                        t_now,
                        elapsed_time)
        return msg


    def __make_system_out(self, out_text):
        """ INTERNAL USAGE
        """
        self.__f.writelines('\t\t<system-out>\n')
        self.__f.writelines('\t\t\t<![CDATA[\n')
        self.__f.writelines(out_text + '\n')
        self.__f.writelines('\t\t\t]]>\n')
        self.__f.writelines('\t\t</system-out>\n')


    def __make_system_err(self, out_text):
        """ INTERNAL USAGE
        """
        self.__f.writelines('\t\t<system-err>\n')
        self.__f.writelines('\t\t\t<![CDATA[\n')
        self.__f.writelines(out_text + '\n')
        self.__f.writelines('\t\t\t]]>\n')
        self.__f.writelines('\t\t</system-err>\n')


    def __make_log_error(self, out_text):
        """ INTERNAL USAGE
        """
        self.__f.writelines('\t\t<failure>\n')
        self.__f.writelines('\t\t\t<![CDATA[\n')
        if out_text is not None:
            self.__f.writelines(out_text)
        self.__f.writelines('\n')
        self.__f.writelines('\t\t\t]]>\n')
        self.__f.writelines('\t\t</failure>\n')


    def __make_skipped(self, out_text):
        """ INTERNAL USAGE
        """
        self.__f.writelines('\t\t<skipped>\n')
        self.__f.writelines('\t\t\t<![CDATA[\n')
        if out_text != None:
            self.__f.writelines(out_text)
        self.__f.writelines('\n')
        self.__f.writelines('\t\t\t]]>\n')
        self.__f.writelines('\t\t</skipped>\n')



###############################################################################

if __name__ == "__main__":
    print("DEBUG")
    kun = Kunit("/users/ghelfc/domain.prova.py")

    kun.frame_open()

    kun.start_time()
    # simulo un tempo di esecuzione
    time.sleep(3)

    kun.start_tps_block("DATA", "1.2.3")
    kun.start_tps_block("TDM",  "5.3.6")

    print(kun.children)

    kun.add_success(None, "TL1 AAA", None, "TESTO")
    kun.add_failure(None, "TL1 BBB", "120.0", "DENY detected", "internal timeout", "traccia")

    kun.stop_tps_block("TDM",  "5.3.6")

    kun.add_skipped(None, "CLI AAA", "0.0", "TESTO", "not applicable")
    kun.add_success(None, "TL1 DDD", "2.3", "TESTO")

    kun.start_tps_block("TDM",  "5.3.6")
    kun.add_success(None, "TL1 EEE", "2.8", "TESTO")

    kun.frame_close()

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
        self.__fn   = None  # xml file name
        self.__cnt  = None  # counter of atomic test
        self.__clnm = None  # basic name of test, i.e. without path and suffix
        self.__st   = None  # test execution starting time
        self.__f    = None  # file descriptor
        self.__fn   = '{:s}.XML'.format(os.path.splitext(fileName)[0])
        self.__clnm = os.path.splitext(os.path.basename(self.__fn))[0]
        self.__cnt  = 0


    def frame_open(self):
        """ Start xml composition
        """
        self.__f = open(self.__fn, "w")
        os.chmod(self.__fn, 0o644)
        self.__f.writelines('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.__f.writelines('<testsuite>\n')


    def frame_close(self):
        """ Close xml composition
        """
        self.__f.writelines('</testsuite>\n')
        self.__f.close()


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
    #pylint: enable=too-many-arguments


    def start_time(self):
        """ Save the starting time for a single test.
            The information will be used by add_success(), add_failure() and add_skipped()
            in order to evaluate elapsed time of test execution.
            In this case, a None value must be supplied for elapsed_time
            on above add_success(),... methods
        """
        self.__st = datetime.datetime.now()


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
    kun.add_success(None,
                    "TL1 command1",
                    None,
                    "aaaaaaaaaaaaabbbbbbbbbbbbbbbbbbbbbbccccccccccccccc")

    kun.add_failure(None,
                    "TL1 command with many arguments",
                    "120.0",
                    "DENY detected",
                    "internal timeout",
                    "http://ip:port/path/xxx.html")

    kun.add_skipped(None,
                    "CLI command1",
                    "0.0",
                    "asdasdkjakjsdjioafdioufsdosduiafsd",
                    "not applicable")

    kun.frame_close()

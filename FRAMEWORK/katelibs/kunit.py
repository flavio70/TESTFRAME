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

    def __init__(self, path_repo, test_file_name):
        """
        path_repo      : Base path for XML reporting
        test_file_name : Test file name
        """
        self.__cnt  = 0     # counter of atomic test
        self.__st   = None  # test execution starting time

        # Base path of xml result area
        self.__dir  = path_repo

        # xml file name (path complete)
        self.master_file_name = '{:s}/{:s}._main.XML'.format(path_repo,
                                                             os.path.splitext(test_file_name)[0])

        # basic name of test, i.e. without path and suffix
        self.__clnm = { }

        # Lista dei file di report
        self.__reports = { }

        self.frame_open(self.master_file_name)


    def frame_open(self, file_name):
        """ Start xml composition
        """
        self.__reports[file_name] = open(file_name, "w")
        self.__clnm[file_name] = os.path.splitext(os.path.basename(file_name))[0]
        try:
            os.chmod(file_name, 0o666)
        except:
            pass

        self.__reports[file_name].writelines('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.__reports[file_name].writelines('<testsuite>\n')


    def frame_close(self, file_name=None):
        """ Close xml composition
        """
        if file_name is None:
            for elem in self.__reports:
                print("\nREPORT IN [{:s}]\n".format(elem))
                self.__reports[elem].writelines('</testsuite>\n')
                self.__reports[elem].close()
        else:
            print("**" + file_name)
            self.__reports[file_name].writelines('</testsuite>\n')
            self.__reports[file_name].close()


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
        self.__cnt = self.__cnt + 1

        for elem in self.__reports:
            file_desc = self.__reports[elem]
            file_clnm = self.__clnm[elem]

            block = "{:s}{:s}\t</testcase>\n".format(self.__make_test_case(ref_obj, file_clnm, title, delta_t, self.__cnt),
                                                     self.__make_system_out(out_text))
            file_desc.writelines(block)


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
        self.__cnt = self.__cnt + 1

        for elem in self.__reports:
            file_desc = self.__reports[elem]
            file_clnm = self.__clnm[elem]

            block = "{:s}{:s}{:s}{:s}\t</testcase>\n".format(self.__make_test_case(ref_obj, file_clnm, title, delta_t, self.__cnt),
                                                             self.__make_log_error(log_text),
                                                             self.__make_system_out(out_text),
                                                             self.__make_system_err(err_text))
            file_desc.writelines(block)
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
        self.__cnt = self.__cnt + 1

        for elem in self.__reports:
            file_desc = self.__reports[elem]
            file_clnm = self.__clnm[elem]

            block = "{:s}{:s}{:s}{:s}\t</testcase>\n".format(self.__make_test_case(ref_obj, file_clnm, title, delta_t, self.__cnt),
                                                             self.__make_skipped(skip_text),
                                                             self.__make_system_out(out_text),
                                                             self.__make_system_err(err_text))
            file_desc.writelines(block)
    #pylint: enable=too-many-arguments


    def start_time(self):
        """ Save the starting time for a single test.
            The information will be used by add_success(), add_failure() and add_skipped()
            in order to evaluate elapsed time of test execution.
            In this case, a None value must be supplied for elapsed_time
            on above add_success(),... methods
        """
        self.__st = datetime.datetime.now()


    def start_tps_block(self, dut_id, tps_area, tps_name):
        '''
        Start an official block containg all code related to aspecific TPS (Test Procedure)
        calling this function into testcase object will generate a specific XML report file for each TPSName provided
        '''

        file_name = "{:s}/{:s}.[{:s}]_{:s}_{:s}.XML".format(self.__dir,
                                                     os.path.splitext(os.path.splitext(self.__clnm[self.master_file_name])[0])[0],
                                                     dut_id,
                                                     tps_area,
                                                     tps_name)

        self.__reports[file_name] = None
        self.__clnm[file_name] = None

        self.frame_open(file_name)


    def stop_tps_block(self, dut_id, tps_area, tps_name):
        '''
        Stop the block containing the code related to the specific TPS (test Procedure)
        This function will terminate the specific XML report file related to TPSName test id
        '''
        file_name = "{:s}/{:s}.[{:s}]_{:s}_{:s}.XML".format(self.__dir,
                                                     os.path.splitext(os.path.splitext(self.__clnm[self.master_file_name])[0])[0],
                                                     dut_id,
                                                     tps_area,
                                                     tps_name)
        self.frame_close(file_name)

        self.__reports.pop(file_name)
        self.__clnm.pop(file_name)


    def __make_test_case(self, ref_obj, clnm, title, elapsed_time, counter):
        """ INTERNAL USAGE
        """
        try:
            obj_name = ref_obj.get_label()
        except Exception as eee:
            obj_name = ""

        t_title = '{:05n} [{:s}] {:.100}'.format(counter, obj_name, title.replace("&", "&amp;"))
        t_now = str(datetime.datetime.now())

        msg = '\t<testcase classname="{:s}" name="{:s}" timestamp="{:s}" time="{:s}">\n'.format(\
                        clnm,
                        t_title,
                        t_now,
                        elapsed_time)
        return msg


    def __make_system_out(self, out_text):
        """ INTERNAL USAGE
        """
        return  '\t\t<system-out>\n'    +\
                '\t\t\t<![CDATA[\n'     +\
                out_text                +\
                '\n\t\t\t]]>\n'         +\
                '\t\t</system-out>\n'


    def __make_system_err(self, out_text):
        """ INTERNAL USAGE
        """
        return  '\t\t<system-err>\n'    +\
                '\t\t\t<![CDATA[\n'     +\
                out_text                +\
                '\n\t\t\t]]>\n'         +\
                '\t\t</system-err>\n'


    def __make_log_error(self, out_text):
        """ INTERNAL USAGE
        """
        if out_text is None:
            out_text = ""

        return  '\t\t<failure>\n'       +\
                '\t\t\t<![CDATA[\n'     +\
                out_text                +\
                '\n\t\t\t]]>\n'         +\
                '\t\t</failure>\n'


    def __make_skipped(self, out_text):
        """ INTERNAL USAGE
        """
        if out_text is None:
            out_text = ""

        return  '\t\t<skipped>\n'       +\
                '\t\t\t<![CDATA[\n'     +\
                out_text                +\
                '\n\t\t\t]]>\n'         +\
                '\t\t</skipped>\n'



###############################################################################

if __name__ == "__main__":
    print("DEBUG")
    kun = Kunit("/users/ghelfc/domain.prova.py")

    kun.start_time()
    # simulo un tempo di esecuzione
    time.sleep(3)

    kun.start_tps_block("DATA", "1.2.3")
    kun.start_tps_block("TDM",  "5.3.6")

    kun.add_success(None, "TL1 AAA", None, "TESTO")
    kun.add_failure(None, "TL1 BBB", "120.0", "DENY detected", "internal timeout", "traccia")

    kun.stop_tps_block("TDM",  "5.3.6")

    kun.add_skipped(None, "CLI AAA", "0.0", "TESTO", "not applicable")
    kun.add_success(None, "TL1 DDD", "2.3", "TESTO")

    kun.stop_tps_block("DATA", "1.2.3")

    kun.add_success(None, "TL1 EEE", "2.8", "TESTO")

    kun.frame_close()

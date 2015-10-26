#!/usr/bin/env python
###############################################################################
# MODULE: kunit.py
# 
# AUTHOR: C.Ghelfi
# DATE  : 29/07/2015
#
###############################################################################

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
        self.__fn    = None  # xml file name
        self.__cnt   = None  # counter of atomic test
        self.__clnm  = None  # basic name of test, i.e. without path and suffix
        self.__st    = None  # test execution starting time

        self.__fn   = '{:s}.XML'.format(os.path.splitext(fileName)[0])
        self.__clnm = os.path.splitext(os.path.basename(self.__fn))[0]
        self.__cnt  = 0

    def frameOpen(self):
        """ Start xml composition
        """
        self.__f = open(self.__fn, "w")
        os.chmod(self.__fn, 0o644)
        self.__f.writelines('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.__f.writelines('<testsuite>\n')

    def frameClose(self):
        """ Close xml composition
        """
        self.__f.writelines('</testsuite>\n')
        self.__f.close()

    def addSuccess(self, refObj, title, elapsedTime, outText):
        """ Inject a POSITIVE record on xml result file
            refObj      : reference to an Equipment variable (could be None)
            title       : describe the performed action. For example, a CLI/TL1/... command
            outText     : verbose description of test outcome.
            elapsedTime : explicit declaration of test's time execution. See startTime()
        """
        if elapsedTime is None:
            deltaTime = str((datetime.datetime.now() - self.__st).total_seconds())
        else:
            deltaTime = elapsedTime
        self.__st = None
        self.__f.writelines(self.__makeTestCase(refObj, title, deltaTime))
        self.__makeSystemOut(outText)
        self.__f.writelines('\t</testcase>\n')


    def addFailure(self, refObj, title, elapsedTime, outText, errText, logText=None):
        """ Inject a FAILURE record on xml result file
            refObj      : reference to an Equipment variable (could be None)
            title       : describe the performed action. For example, a CLI/TL1/... command
            outText     : verbose description of test outcome.
            errText     : verbose description of errored scenario.
            logText     : additional reference to log repository (optional)
            elapsedTime : explicit declaration of test's time execution. See startTime()
        """
        if elapsedTime is None:
            deltaTime = str((datetime.datetime.now() - self.__st).total_seconds())
        else:
            deltaTime = elapsedTime
        self.__st = None
        row = self.__makeTestCase(refObj, title, deltaTime)
        self.__f.writelines(row)
        self.__makeLogError(logText)
        self.__makeSystemOut(outText)
        self.__makeSystemErr(errText)
        self.__f.writelines('\t</testcase>\n')

    def addSkipped(self, refObj, title, elapsedTime, outText, errText, skipText=None):
        """ Inject a SKIPPED record on xml result file
            refObj      : reference to an Equipment variable (could be None)
            title       : describe the performed action. For example, a CLI/TL1/... command
            outText     : verbose description of test outcome.
            errText     : verbose description of skip reasons
            logText     : additional reference to log repository (optional)
            elapsedTime : explicit declaration of test's time execution. See startTime()
        """
        if elapsedTime is None:
            deltaTime = str((datetime.datetime.now() - self.__st).total_seconds())
        else:
            deltaTime = elapsedTime
        self.__st = None
        row = self.__makeTestCase(refObj, title, deltaTime)
        self.__f.writelines(row)
        self.__makeSkipped(skipText)
        self.__makeSystemOut(outText)
        self.__makeSystemErr(errText)
        self.__f.writelines('\t</testcase>\n')

    def startTime(self):
        """ Save the starting time for a single test.
            The information will be used by addSuccess(), addFailure() and addSkipped()
            in order to evaluate elapsed time of test execution.
            In this case, a None value must be supplied for elapsedTime
            on above addSuccess(),... methods
        """
        self.__st = datetime.datetime.now()

    def __makeTestCase(self, refObj, title, elapsedTime):
        try:
            objName = refObj.getLabel()
        except:
            objName = ""
        self.__cnt = self.__cnt + 1
        t = '{:05n} [{:s}] {:.100}'.format(self.__cnt, objName, title.replace("&", "&amp;"))
        c = str(datetime.datetime.now())
        return '\t<testcase classname="{:s}" name="{:s}" timestamp="{:s}" time="{:s}">\n'.format(self.__clnm, t, c, elapsedTime)

    def __makeSystemOut(self, outText):
        self.__f.writelines('\t\t<system-out>\n')
        self.__f.writelines('\t\t\t<![CDATA[\n')
        self.__f.writelines(outText + '\n')
        self.__f.writelines('\t\t\t]]>\n')
        self.__f.writelines('\t\t</system-out>\n')

    def __makeSystemErr(self, outText):
        self.__f.writelines('\t\t<system-err>\n')
        self.__f.writelines('\t\t\t<![CDATA[\n')
        self.__f.writelines(outText + '\n')
        self.__f.writelines('\t\t\t]]>\n')
        self.__f.writelines('\t\t</system-err>\n')

    def __makeLogError(self, outText):
        self.__f.writelines('\t\t<failure>\n')
        self.__f.writelines('\t\t\t<![CDATA[\n')
        if outText is not None:
            self.__f.writelines(outText)
        self.__f.writelines('\n')
        self.__f.writelines('\t\t\t]]>\n')
        self.__f.writelines('\t\t</failure>\n')

    def __makeSkipped(self, outText):
        self.__f.writelines('\t\t<skipped>\n')
        self.__f.writelines('\t\t\t<![CDATA[\n')
        if outText != None:
            self.__f.writelines(outText)
        self.__f.writelines('\n')
        self.__f.writelines('\t\t\t]]>\n')
        self.__f.writelines('\t\t</skipped>\n')



###############################################################################

if __name__ == "__main__":
    print("DEBUG")
    kun = Kunit("/users/ghelfc/domain.prova.py")

    kun.frameOpen()

    kun.startTime()
    # simulo un tempo di esecuzione
    time.sleep(3)
    kun.addSuccess( None,
                    "TL1 command1",
                    None,
                    "aaaaaaaaaaaaabbbbbbbbbbbbbbbbbbbbbbccccccccccccccc")

    kun.addFailure( None,
                    "TL1 command with many arguments",
                    "120.0",
                    "DENY detected",
                    "internal timeout",
                    "http://ip:port/path/xxx.html")

    kun.addSkipped( None,
                    "CLI command1",
                    "0.0",
                    "asdasdkjakjsdjioafdioufsdosduiafsd",
                    "not applicable")

    kun.frameClose()

#!/usr/bin/env python
"""
###############################################################################
# MODULE: kenviron.py
#
# AUTHOR: C.Ghelfi
# DATE  : 13/11/2015
#
###############################################################################
"""

import os

from katelibs.kunit     import Kunit
from katelibs.kpreset   import KPreset
from katelibs.ktracer   import KTracer



class KEnvironment():
    """
    Describe a Test Context Execution
    """

    def __init__(self, basedir=None, testfilename=__file__):
        """
        Costructor for KEnvironment.
        basedir      : (opt) home of test running enviromnent
                       If called passing None, the working area could be:
                       - a Jenkins project's workspace (checking 'WORKSPACE' environment variable)
                       - a local area on user home directory (i.e. '~/K_WORKSPACE')
        testfilename : (only for debug) A test file name
        """
        # Public members:
        self.kprs   = None  # Presettings for test execution
        self.krepo  = None  # XML Reporting
        self.ktrc   = None  # Tracer

        # Private members:
        self.__test_fn = None   # Test File Name
        self.__paths   = { }    # Environment Paths (see below)

        # Pre-init of Paths dictionary
        self.__paths['WSPC'] = None     # Test Execution Working area
        self.__paths['TEST'] = None     # Test Suite area
        self.__paths['REPO'] = None     # XML reporting area
        self.__paths['TL1E'] = None     # TL1 Event message area
        self.__paths['LOGS'] = None     # Logs working area

        # Setup Working Area
        self.__setup_workspace(basedir, testfilename)

        # Test File Name
        self.__test_fn = os.path.basename(testfilename)

        # Trace Management
        self.ktrc = KTracer(self.__paths['LOGS'], filename=testfilename, level="ERROR", trunk=True)

        # Presets Management
        self.kprs = KPreset(self.__paths['TEST'], self.__test_fn)

        # Reporting Management
        self.krepo = Kunit(self.__paths['REPO'], self.__test_fn)

        # Log Management
        # ...

        # All done
        self.__closed = False


    def __setup_workspace(self, basedir, testfilename):
        """
        Set or change current working area
        If called passing None, the working area could be:
        - a Jenkins project's workspace (checking WORKSPACE environment variable)
        - a local area on user home directory (i.e. '~/K_WORKSPACE')
        """
        if basedir is None:
            # Get path from ${WORKSPACE}
            try:
                basedir = os.environ['WORKSPACE']
            except:
                basedir = None

        if basedir is None:
            # Get Path from test file name
            #home_dir = os.path.expanduser("~")
            #basedir = "{:s}/K_WORKSPACE".format(home_dir)
            basedir = os.path.dirname(os.path.abspath(testfilename))

        print("WORKSPACE FOR TEST: [{:s}]\n".format(basedir))

        if not os.path.exists(basedir):
            os.system("mkdir {:s}".format(basedir))
        else:
            if not os.path.isdir(basedir):
                print("ERROR CONFIGURING WORKING AREA")
                print("'{:s}' isn't a directory".format(basedir))
                self.__paths['WSPC'] = None
                return

        self.__paths['WSPC'] = basedir
        self.__paths['TEST'] = basedir
        self.__paths['REPO'] = "{:s}/test-reports".format(basedir)
        self.__paths['LOGS'] = "{:s}/logs".format(basedir)
        self.__paths['TL1E'] = "{:s}/events".format(basedir)

        # Configure file system on working area
        os.system("mkdir -p {:s} {:s} {:s} {:s}".format(self.__paths['TEST'],
                                                        self.__paths['REPO'],
                                                        self.__paths['LOGS'],
                                                        self.__paths['TL1E']))


    def get_test_name(self):
        """ Return the Test Name (i.e. the Test File Name without extension)
        """
        return os.path.splitext(self.__test_fn)[0]


    def get_test_file_name(self):
        """ Return the Test File Name
        """
        return self.__test_fn


    def path_workspace(self):
        """ Return Working area path
        """
        return self.__paths['WSPC']


    def path_test(self):
        """ Return Test area path
        """
        return self.__paths['TEST']


    def path_logs(self):
        """ Return Logs area path
        """
        return self.__paths['LOGS']


    def path_reporting(self):
        """ Return XML Reporting area path
        """
        return self.__paths['REPO']


    def path_collector(self):
        """ Return Collector area path
        """
        return self.__paths['TL1E']


    def clean_up(self):
        """
        Closing environment and release resources
        """
        if not self.__closed:
            self.__closed = True
            self.krepo.frame_close()



if __name__ == '__main__':
    print("DEBUG KEnvironment")

    KENV = KEnvironment()

    print("FINE")

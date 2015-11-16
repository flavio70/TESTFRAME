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
from katelibs.kunit     import *
from katelibs.kpreset   import *



class KEnvironment():
    """
    Describe a Test Context Execution
    """

    def __init__(self, basedir=None, testfilename=__file__):
        """
        Costructor for KEnvironment.
        basedir      : (opt) home of test running enviromnent (see set_workspace() for details)
        testfilename : (only for debug) A test file name
        """
        # Public members:
        self.kprs               = None  # Presettings for test execution
        self.krepo              = None  # XML Reporting
        # Private members:
        self.__workspace        = None  # Test Execution Working area
        self.__path_test        = None  # Suite's test area
        self.__path_repo        = None  # Reporting area
        self.__path_logs        = None  # Logs area
        self.__path_tl1e        = None  # TL1 Event collect area
        self.__test_file_name   = None  # Test File Name

        # Settings Working Area using standard rules (see set_workspace())
        self.set_workspace(basedir)

        # Test File Name
        self.__test_file_name = os.path.basename(testfilename)

        # Presets Management
        self.kprs = KPreset(self.__path_test, self.__test_file_name)

        # Reporting Management
        self.krepo = Kunit(self.__path_repo, self.__test_file_name)

        # Log Management
        # ...


    def get_test_file_name(self):
        """ Return the Test File Name
        """
        return self.__test_file_name


    def path_workspace(self):
        """ Return Working area path
        """
        return self.__workspace


    def path_test(self):
        """ Return Test area path
        """
        return self.__path_test


    def path_logs(self):
        """ Return Logs area path
        """
        return self.__path_logs


    def path_reporting(self):
        """ Return XML Reporting area path
        """
        return self.__path_repo


    def path_collector(self):
        """ Return Collector area path
        """
        return self.__path_tl1e


    def clean_up(self):
        """
        Closing environment and release resources
        """
        self.krepo.frame_close()


    def set_workspace(self, basedir):
        """
        Set or change current working area
        If called passing None, the working area could be:
        - a Jenkins project's workspace (checking WORKSPACE environment variable)
        - a local area on user home directory (i.e. '~/K_WORKSPACE')
        """
        if basedir is None:
            # Get path from $WORKSPACE
            try:
                basedir = os.environ['WORKSPACE']
            except:
                basedir = None

        if basedir is None:
            # Get Path from HOME directory
            home_dir = os.path.expanduser("~")
            basedir = "{:s}/K_WORKSPACE".format(home_dir)

        print("WS: [{:s}]".format(basedir))

        if not os.path.exists(basedir):
            os.system("mkdir {:s}".format(basedir))
        else:
            if not os.path.isdir(basedir):
                print("ERROR CONFIGURING WORKING AREA")
                print("'{:s}' isn't a directory".format(basedir))
                self.__workspace = None
                return

        self.__workspace = basedir
        self.__path_test = "{:s}/suite".format(self.__workspace)
        self.__path_repo = "{:s}/test-reports".format(self.__workspace)
        self.__path_logs = "{:s}/logs".format(self.__workspace)
        self.__path_tl1e = "{:s}/events".format(self.__workspace)

        # Configure file system on working area
        os.system("mkdir -p {:s} {:s} {:s} {:s}".format(self.__path_test,
                                                        self.__path_repo,
                                                        self.__path_logs,
                                                        self.__path_tl1e))



if __name__ == '__main__':
    print("DEBUG KEnvironment")

    kenv = KEnvironment()

    print("FINE")

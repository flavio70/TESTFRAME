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

    def __init__(self, test_file_name=__file__):
        """
        Costructor for KEnvironment.
        """
        self.__test_file_name   = test_file_name    # Test File Name
        self.__workspace        = None              # Working area
        self.__path_repo        = None              # Reporting area
        self.__path_logs        = None              # Logs area

        # Settings Working Area using standard rules (see set_workspace())
        self.set_workspace()

        # Presets Management
        self.__prs = KPreset(self.__test_file_name)

        # Reporting Management
        self.__krepo = Kunit(self.__path_repo, self.__test_file_name)

        # Log Management
        # ...


    def set_workspace(self, the_path=None):
        """
        Set or change current working area
        Called without paramenters, the working area could be:
        - a Jenkins project's workspace (checking WORKSPACE environment variable)
        - a local area on user home directory (i.e. '~/K_WORKSPACE')
        """
        if the_path is None:
            # Get path from $WORKSPACE
            try:
                the_path = os.environ['WORKSPACE']
            except:
                the_path = None

        if the_path is None:
            # Get Path from HOME directory
            home_dir = os.path.expanduser("~")
            the_path = "{:s}/K_WORKSPACE".format(home_dir)

        print("WS: [{:s}]".format(the_path))

        if not os.path.exists(the_path):
            os.system("mkdir {:s}".format(the_path))
        else:
            if not os.path.isdir(the_path):
                print("ERROR CONFIGURING WORKING AREA")
                print("'{:s}' isn't a directory".format(the_path))
                self.__workspace = None
                return

        self.__workspace = the_path
        self.__path_repo = "{:s}/test-reports".format(self.__workspace)
        self.__path_logs = "{:s}/logs".format(self.__workspace)

        # Configure file system on working area
        os.system("mkdir -p {:s}".format(self.__path_repo))
        os.system("mkdir -p {:s}".format(self.__path_logs))



if __name__ == '__main__':
    print("DEBUG KEnvironment")

    testfilename = "~/TestExample.py"

    kenv = KEnvironment(testfilename)

    print("FINE")

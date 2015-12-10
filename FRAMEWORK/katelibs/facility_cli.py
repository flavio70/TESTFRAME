#!/usr/bin/env python
"""
###############################################################################
# MODULE: facility_cli.py
#
# AUTHOR: C.Ghelfi
# DATE  : 01/12/2015
#
###############################################################################
"""

import sys
import json



class CLIcheck():
    """ CLI Message Scanner
    """

    def __init__(self):
        """ Constructor for a CLI Scanner
        """
        self.__ports    = []    # List of Ports (could be contains Regular Expression)
        self.__filters  = {}    # Dictionary of <ATTR,VALUE> couple to search on a TL1 Message


    def add_filter(self, value):
        """ Insert a new filter.
        """
        try:
            self.__filters[attr].append(value)
        except KeyError:
            self.__filters[attr] = [value]


    def res_filter(self, value=None):
        """ Remove a filter.
            A None for VALUE remove all filters
        """
        if attr is None:
            self.__filters = {}
        else:
            if value is not None:
                self.__filters[attr] = [x for x in self.__filters[attr] if x != value]
            else:
                self.__filters.pop(attr)


    def add_port(self, port):
        """ Insert a port filter.
        """
        self.__ports.append(port)


    def res_port(self, port=None):
        """ Remove a specified AID from list. A None for aid cause list cleanup
        """
        if port is None:
            self.__ports = []
        else:
            self.__ports.remove(port)


    def evaluate_msg(self, msg):
        """ Perform a filter check on supplied CLI message
            A tuple <True/False, result_list> is returned.
            If any condition has been match on CLI Message, a True is returned.
            Moreover a list of match conditions (almost one element) is returned
        """
        result = False

        res_list = []

        print("UNMANAGED SCENARIO")
        return False,None


    def debug(self):
        """ INTERNAL USAGE
        """
        print("filters    : {}".format(self.__filters))
        print("conditions : {}".format(self.__conds))




if __name__ == "__main__":
    print("DEBUG")

    mm = """
"""

    print("[{:s}]\n".format(mm)

    filt = CLIcheck()
    filt.debug()
    print(filt.evaluate_msg(mm))

    print("FINE")

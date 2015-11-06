#!/usr/bin/env python
"""
###############################################################################
#
# MODULE:  instrumentONT.py
# 
# AUTHOR:  L.Cutilli
#
# DATE  :  16/10/2015
#
#
# DETAILS: Python management module of the following test equipments:
#          - 5xx... Ont-50, Ont-506, Ont-512
#          - 6xx... Ont-601 
#          created to drive the connections and common low-level operations
#          involving JDSU Optical Network Tester ONT-506/600
#
###############################################################################
"""


import os
import sys
import time
import string
import getpass
import inspect
import telnetlib

from katelibs.equipment import Equipment
from katelibs.kunit import Kunit
from katelibs.database import *


class InstrumentONT(Equipment):
    """
    ONT Instrument Family descriptor. Implements specific operations
    """

    def __init__(self, label, ID, krepo=None):
        """ label   : Intrument name used on Report file
            ID      : instrument ID (see T_EQUIPMENT table on K@TE DB)
            krepo   : reference to kunit report instance
        """
        # ...
        # ...

        super().__init__(label, ID)

        self.__get_eqpt_info_from_db(ID)

        # ...
        # ...


    def __get_eqpt_info_from_db(self, ID):
        print("CONFIGURATION EQUIPMENT ID = " + str(ID))
        tabEqpt  = TEquipment
        # ....




#######################################################################
# 
#   MODULE TEST - Test sequences used fot ONT5xx testing  
#
####################################################################### 
if __name__ == "__main__xxx":   #now skip this part
    print(" ")
    print("=============================")
    print("ontXXXDriver 5xx module debug")
    print("=============================")

    myInstrument = InstrumentONT("myInstrument", 21, None)

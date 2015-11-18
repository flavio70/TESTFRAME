#!/usr/bin/env python
"""
###############################################################################
# MODULE: kpreset.py
#  Read and manage a Presettings file iin JSON format for a test script.
#  A generic preset foreseens almost an entry, named by an Equipment Label.
#  For each Equipment, using Label string it is possible to get:
#  - the equipment ID on K@TE DB 'get_id()'          (mandatory element)
#  - the equipment type from K@TE DB 'get_type()'    (mandatory element)
#  - a generic attribute for the equipment 'get_elem()'
#  - a generic attribute from a list for the equipment 'get_from_list()'
#
# AUTHOR: C.Ghelfi
# DATE  : 13/11/2015
#
###############################################################################
"""

import os
import json



class KPreset():
    """
    Describe a Preset for specified Test file
    """

    def __init__(self, test_area, test_file_name):
        """ Recover the Presettings for specified Test
            test_area      : base path for suite test area
            test_file_name : the test file name
        """
        prs_file_name = "{:s}/{:s}.prs".format(os.path.expanduser(test_area), test_file_name)

        preset_file = open(prs_file_name)

        self.__presets = json.load(preset_file)
        print("-- PRESETTING VALUES ----------------")
        print(self.__presets)
        print("-------------------------------------\n")


    def get_all_ids(self):
        """ Return a list of ID for current preset file
        """
        id_list = [ ]

        for key in self.__presets:
            id_list.append(self.get_id(key))

        return id_list


    def get_id(self, equip_name):
        """
            Return the equipment Identifier (see K@TE DB, table T_EQUIPMENT)
        """
        try:
            res = self.__presets[equip_name]["ID"]
        except Exception:
            res = ""

        return int(res)


    def get_type(self, equip_name):
        """
            Return the equipment Type (see K@TE DB, table T_EQUIPMENT_TYPE)
        """
        try:
            res = self.__presets[equip_name]["TYPE"]
        except Exception:
            res = ""

        return res


    def get_elem(self, equip_name, elem):
        """
            Return a generic element value for specified equipment
        """
        try:
            res = self.__presets[equip_name][elem]
        except Exception:
            res = ""

        return res


    def get_from_list(self, equip_name, a_list, elem):
        """
            Return a generic element value for specified equipment (list scenario)
        """
        try:
            res = self.__presets[equip_name][a_list][elem]
        except Exception:
            res = ""

        return res


if __name__ == '__main__':
    print("DEBUG KPreset")

    testarea = "~/K_WORKSPACE/suite"
    testfilename = "TestExample.py"

    kprs = KPreset(testarea, testfilename)

    print("-" * 80)

    print("NE1 id   := " + str(kprs.get_id("NE1")))
    print("NE1 type := " + kprs.get_type("NE1"))

    print("ONT1 id    := " + str(kprs.get_id("ONT1")))
    print("ONT1 type  := " + kprs.get_type("ONT1"))
    print("ONT1 USER  := " + str(kprs.get_elem("ONT1", "USER")))
    print("ONT1 PWD   := " + str(kprs.get_elem("ONT1", "PWD")))
    print("ONT1 APPL  := " + str(kprs.get_elem("ONT1", "APPL")))
    print("ONT1 P1    := " + str(kprs.get_from_list("ONT1", "PORTS", "P1")))
    print("ONT1 P2    := " + str(kprs.get_from_list("ONT1", "PORTS", "P2")))
    print("ONT1 P3    := " + str(kprs.get_from_list("ONT1", "PORTS", "P3")))

    print("ONT2 Port2 := " + str(kprs.get_from_list("ONT2", "PORTS", "Port2")))

    print(kprs.get_all_ids())

#!/usr/bin/env python
"""
###############################################################################
# MODULE: kpreset.py
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

    def __init__(self, test_file_name):
        prs_file_name = "{:s}.prs".format(os.path.expanduser(test_file_name))

        preset_file = open(prs_file_name)

        self.__presets = json.load(preset_file)
        print(self.__presets)


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
            res = int(self.__presets[equip_name]["TYPE"])
        except Exception:
            res = 0

        return res


if __name__ == '__main__':
    print("DEBUG KPreset")

    testfilename = "~/TestExample.py"

    kprs = KPreset(testfilename)

    print("-" * 80)

    print("NE1 id   := " + kprs.get_id("NE1"))
    print("NE1 type := " + kprs.get_type("NE1"))

    print("FINE")

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

from katelibs.database import *
from django.db import connection



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



class KPresetBuilder():
    """ Define a new preset file
    """

    def __init__(self, test_dir, id_suite, id_preset):
        """ Create an empty preset file for specified test file
            test_dir  : base path for suite test area
            id_suite  : DB ID for suite
            id_preset : DB ID for presetting
        """
        self.__test_dir  = test_dir
        self.__id_suite  = id_suite
        self.__id_preset = id_preset
        self.__test_list = [ ]  # Dictionary as { 'test_name' : ( test_id, topology_id) }

        self.__get_test_list()

        self.__generate_preset_file()


    def __get_test_list(self):
        cursor = connection.cursor()

        query = ' '.join( ( "SELECT test_id, test_name, topology",
                            "FROM   T_TEST",
                            "  JOIN T_SUITES_BODY",
                            "  JOIN T_TEST_REVS",
                            "WHERE  T_SUITES_id_suite={:d}".format(self.__id_suite),
                            "GROUP BY test_name" ) )

        cursor.execute(query)

        for row in cursor.fetchall():
            test_ref = { }
            test_ref[row[1]] = (row[0], int(row[2]))
            self.__test_list.append(test_ref)


    def __get_attr_value(self, id_entity):
        print("id_entity := {:d}".format(id_entity))
        pass


    def __evaluate_entity(self, id_topo):
        id_topo = 3 # solo per debug
        tab_tpy_body = TTpyEntity

        elem = { }

        for r in tab_tpy_body.objects.all():
            if r.t_topology_id_topology.id_topology == id_topo:
                # creo un elemento di chiave r.entityname
                if not r.entityname in elem:
                    elem[r.entityname] = [ ]
                # inserisco coppie <attr,val>
                atval = { }
                if r.entityname.find("#") != -1:
                    # trovato tipo di equipaggiamento
                    atval = ("TYPE", r.elemname.replace("#",""))
                else:
                    val = self.__get_attr_value(r.id_entity)
                    atval = (r.elemname, val)
                elem[r.entityname].append(atval)

        print(elem)


    def __test_presets(self, test_ref):
        name = list(test_ref.keys())[0]
        id_test = test_ref[name][0]
        id_topo = test_ref[name][1]

        print("{:s} / {:d} / {:d}".format(name, id_test, id_topo))

        self.__evaluate_entity(id_topo)


    def __generate_preset_file(self):
        for test_ref in self.__test_list:
            self.__test_presets(test_ref)
            break
        


if __name__ == '__main__':
    print("DEBUG KPreset")

    testarea = "~/TESTFRAME/FRAMEWORK/examples"

    if False:
        testfilename = "Test1NE.py"

        kprs = KPreset(testarea, testfilename)

        print("-" * 80)

        print("NE1 id   := " + str(kprs.get_id("NE1")))
        print("NE1 type := " + kprs.get_type("NE1"))

        print("ONT1 id    := " + str(kprs.get_id("ONT1")))
        print("ONT1 type  := " + kprs.get_type("ONT1"))
        print("ONT1 USER  := " + str(kprs.get_elem("ONT1", "USER")))
        print("ONT1 PWD   := " + str(kprs.get_elem("ONT1", "PWD")))
        print("ONT1 APPL  := " + str(kprs.get_elem("ONT1", "APPL")))
        print("ONT1 P1    := " + str(kprs.get_elem("ONT1", "P1")))
        print("ONT1 P2    := " + str(kprs.get_elem("ONT1", "P2")))
        print("ONT1 P3    := " + str(kprs.get_elem("ONT1", "P3")))

        print("ONT2 Port2 := " + str(kprs.get_elem("ONT2", "Port2")))

        print(kprs.get_all_ids())
    else:
        newprs = KPresetBuilder(testarea, id_suite=65, id_preset=48)

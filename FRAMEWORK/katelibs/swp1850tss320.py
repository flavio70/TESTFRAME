#!/usr/bin/env python
"""
###############################################################################
# MODULE: swp1850tss320.py
#
# AUTHOR: C.Ghelfi
# DATE  : 12/11/2015
#
###############################################################################
"""

from katelibs.database import *



class SWP1850TSS():
    """
    Describe a Software Package for 1850TSS320/1850TSS160 equipment (all shelves)
    """

    def __init__(self):
        self.__swp_id           = {}    # (dict) SQL ID
        self.__swp_prod         = {}    # (dict) Product (string as "1850TSS320H", "1850TSS320V")
        self.__swp_release      = None  # Release Identifier (string, as "V7.10.25")
        self.__swp_rel_label    = None  # Release Label (string, as "V7.10.25-N007")
        self.__swp_label        = None  # Reference FLV Label
        #self.__swp_arch         = None  # (dict) Architecture (string, as "gccpp", "gccwrp")
        self.__swp_author       = None  # Author of swp build
        self.__swp_notes        = None  # Free note field
        self.__swp_ts_build     = None  # Time stamp (build time)
        self.__swp_ts_devel     = None  # Time stamp (internal delivery time - when a label is attached to swp)
        self.__swp_ts_valid     = None  # Time stamp (swp available for Valitation activities)
        self.__swp_ts_final     = None  # Time stamp (end of Validation Activities)
        self.__swp_reference    = {}    # (dict) Installation string (StartApp string)


    def get_release_from_db(self, rel_id):
        cursor = connection.cursor()
        query = "SELECT sw_rel_name FROM T_SW_REL WHERE id_sw_rel='{}'".format(rel_id)
        cursor.execute(query)

        return cursor.fetchone()[0]


    def get_product_from_db(self, prod_id):
        cursor = connection.cursor()
        query = "SELECT product FROM T_PROD WHERE id_prod='{}'".format(prod_id)
        cursor.execute(query)

        return cursor.fetchone()[0]



    def init_manual(self, str_std=None, str_enh=None, str_sim=None):
        """
        Manual SWP configuration. Almost one of supported architecture must be supplied
        str_std : startapp string for 1850TSS320 legacy shelf
        str_enh : startapp string for 1850TSS320 enhanced shelf
        str_sim : startapp string for 1850TSS320 emulated shelf
        """

        self.__swp_reference = {}

        if   str_std is not None:
            the_string = str_std
            self.__swp_reference["STD"] = the_string
        elif str_enh is not None:
            the_string = str_enh
            self.__swp_reference["ENH"] = the_string
        elif str_sim is not None:
            the_string = str_sim
            self.__swp_reference["SIM"] = the_string
        else:
            print("Almost one of str_std/str_enh/str_sim must be supplied")
            return False

        self.__swp_rel_label   = the_string.split()[4]
        self.__swp_release  = self.__swp_rel_label.split('-')[0]
        self.__swp_label      = None

        return True


    def init_from_db_generic(self, author, build_time, label_ref):
        """
        Recover SWP information from DB for a generic SWP. It is possible to specify a FLV label
        or a release reference, and an author of build
        author    : author of build (use "integration" for official swp)
        build_time: Compilation time stamp
        label_ref : Any SWP identifier (string, as "V7.10.20-0491")
        """
        cursor = connection.cursor()

        query = "SELECT * FROM T_PACKAGES WHERE author='{}' AND ts_build='{}'".format(author, build_time)

        if label_ref is not None:
            query = query + " AND label_ref='{}'".format(label_ref)

        print(query)

        cursor.execute(query)
        for row in cursor.fetchall():
            arch = row[5]
            self.__swp_id[arch]         = row[0]
            self.__swp_prod[arch]       = self.get_product_from_db(row[1])
            self.__swp_release          = self.get_release_from_db(row[2])
            self.__swp_rel_label        = row[3]
            self.__swp_label            = row[4]
            self.__swp_author           = row[6]
            self.__swp_notes            = row[7]
            self.__swp_ts_build         = row[8]
            self.__swp_ts_devel         = row[9]
            self.__swp_ts_valid         = row[10]
            self.__swp_ts_final         = row[11]
            self.__swp_reference[arch]  = row[12]


    def init_from_db_official(self, release, delivery):
        """
        Recover SWP information from DB for an Official SWP
        release  : release identifier (as "7.10.15")
        delivery : "DEVEL", "VALIDATION", "FINAL"
        """
        if delivery not in ["DEVEL", "VALIDATION", "FINAL"]:
            print("Invalid delivery qualifier")
            return False
        pass


    def get_startapp(self, shelf_type):
        """
        Return the startapp string for current SWP and specified shelf type
        shelf_type : "STD" / "ENH" / "SIM"
        """
        return self.__swp_reference[shelf_type]


    def get_swp_ref(self, arch):
        """
        Return SWP reference
        """
        try:
            return self.__swp_rel_label[arch]
        except Exception as eee:
            print("invalid architecture [{}]".format(arch))
            return ""


    def get_release(self):
        """
        Return the Release Identifier for current SWP
        """
        try:
            return self.__swp_release[arch]
        except Exception as eee:
            print("invalid architecture [{}]".format(arch))
            return ""


    def get_swp_label(self, arch):
        """
        Return the FLV Label for current SWP
        """
        try:
            return self.__swp_label[arch]
        except Exception as eee:
            print("invalid architecture [{}]".format(arch))
            return ""


    def debug(self):
        """
        Print internal status
        """
        print("swp_release   : ", self.__swp_release     )
        print("swp_rel_label : ", self.__swp_rel_label   )
        print("swp_label     : ", self.__swp_label       )
        print("swp_author    : ", self.__swp_author      )
        print("swp_notes     : ", self.__swp_notes       )
        print("swp_ts_build  : ", self.__swp_ts_build    )
        print("swp_ts_devel  : ", self.__swp_ts_devel    )
        print("swp_ts_valid  : ", self.__swp_ts_valid    )
        print("swp_ts_final  : ", self.__swp_ts_final    )
        print("swp_id        : ", self.__swp_id          )
        print("swp_prod      : ", self.__swp_prod        )
        print("swp_reference : ", self.__swp_reference   )



if __name__ == '__main__':
    print("DEBUG SWP1850TSS")

    my_swp1 = SWP1850TSS()

    my_swp1.init_from_db_generic("integration", "2016-02-04 12:23:17", "V7.10.25-N007")

    my_swp1.debug()

    if False:
        my_swp1.init_from_db(swp_flv="FLV_ALC-TSS__BASE00.25.FD0491__VM")

        my_swp2 = SWP1850TSS()

        my_swp2.init_manual(str_enh=swpstr, str_std=None, str_sim=None)

        print(my_swp1.get_swp_label())
        print(my_swp1.get_release())
        print(my_swp1.get_swp_ref())
        print(my_swp1.get_startapp("ENH"))

    print("FINE")

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
        self.__swp_id           = None  # (dict) SQL ID
        self.__swp_prod         = None  # (dict) Product (string as "1850TSS320H", "1850TSS320V")
        self.__swp_release      = None  # Release Identifier (string, as "V7.10.25")
        self.__swp_rel_label    = None  # Release Label (string, as "V7.10.25-N007")
        self.__swp_label        = None  # Reference FLV Label
        self.__swp_arch         = None  # (dict) Architecture (string, as "gccpp", "gccwrp")
        self.__swp_author       = None  # Author of swp build
        self.__swp_notes        = None  # Free note field
        self.__swp_ts_build     = None  # Time stamp (build time)
        self.__swp_ts_devel     = None  # Time stamp (internal delivery time - when a label is attached to swp)
        self.__swp_ts_valid     = None  # Time stamp (swp available for Valitation activities)
        self.__swp_ts_final     = None  # Time stamp (end of Validation Activities)
        self.__swp_reference    = None  # (dict) Installation string (StartApp string)



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
            print(row)


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



    def init_from_db(self, swp_dr4=None, swp_ref=None, swp_flv=None):
        """
        Recover SWP information from DB for specified SWP Reference. It is possible to specify a reference
        using a FLV label, a complete SWP Reference or a DR4 SWP Release
        swp_flv : Any FLV label
        swp_ref : Any SWP identifier (string, as "V7.10.20-0491")
        swp_dr4 : The official DR4-validated SWP (string, as "V7.00.00")
        """
        if   swp_dr4 is not None:
            return True

        elif swp_ref is not None:
            return True

        elif swp_flv is not None:
            if swp_flv == "FLV_ALC-TSS__BASE00.25.FD0491__VM":
                self.__swp_label = swp_flv
                self.__swp_rel_label = "V7.10.20-0491"
                self.__swp_release = "V7.10.20"
                self.__swp_reference["ENH"] = "StartApp DWL 1850TSS320HM 1850TSS320HM V7.10.20-0491 151.98.16.7 0 /users/TOOLS/SCRIPTS/pkgStore_04/pkgStoreArea4x/alc-tss/base00/int/LIV_ALC-TSS__BASE00.25__VM_PKG011/target/MAIN_RELEASE_71/swp_gccwrp/1850TSS320H-7.10.20-0491 4gdwl 4gdwl2k12 true"
                self.__swp_reference["STD"] = "StartApp DWL 1850TSS320M 1850TSS320M V7.10.20-0491 151.98.16.7 0 /users/TOOLS/SCRIPTS/pkgStore_04/pkgStoreArea4x/alc-tss/base00/int/LIV_ALC-TSS__BASE00.25__VM_PKG011/target/MAIN_RELEASE_71/swp_gccpp/1850TSS320-7.10.20-0491 4gdwl 4gdwl2k12 true"
                self.__swp_reference["SIM"] = "StartApp DWL 1850TSS320M 1850TSS320M V7.10.20-0491 151.98.16.7 0 /users/TOOLS/SCRIPTS/pkgStore_04/pkgStoreArea4x/alc-tss/base00/int/LIV_ALC-TSS__BASE00.25__VM_PKG011/host/MAIN_RELEASE_71/swp_gccli/1850TSS320-7.10.20-0491 4gdwl 4gdwl2k12 true"

            return True

        else:
            print("Exacly one of swp_dr4/swp_ref/swp_flv must be supplied")
            return False


    def get_startapp(self, shelf_type):
        """
        Return the startapp string for current SWP and specified shelf type
        shelf_type : "STD" / "ENH" / "SIM"
        """
        return self.__swp_reference[shelf_type]

    def get_swp_ref(self):
        """
        Return SWP reference
        """
        return self.__swp_rel_label

    def get_release(self):
        """
        Return the Release Identifier for current SWP
        """
        return self.__swp_release

    def get_swp_label(self):
        """
        Return the FLV Label for current SWP
        """
        return self.__swp_label



if __name__ == '__main__':
    print("DEBUG SWP1850TSS")

    swpstr = "StartApp DWL 1850TSS320HM 1850TSS320HM V7.10.20-0491 151.98.16.7 0 /users/TOOLS/SCRIPTS/pkgStore_04/pkgStoreArea4x/alc-tss/base00/int/LIV_ALC-TSS__BASE00.25__VM_PKG011/target/MAIN_RELEASE_71/swp_gccwrp/1850TSS320H-7.10.20-0491 4gdwl 4gdwl2k12 true"

    my_swp1 = SWP1850TSS()

    my_swp1.init_from_db_generic("integration", "2016-02-04 12:23:17", "V7.10.25-N007")

    if False:
        my_swp1.init_from_db(swp_flv="FLV_ALC-TSS__BASE00.25.FD0491__VM")

        my_swp2 = SWP1850TSS()

        my_swp2.init_manual(str_enh=swpstr, str_std=None, str_sim=None)

        print(my_swp1.get_swp_label())
        print(my_swp1.get_release())
        print(my_swp1.get_swp_ref())
        print(my_swp1.get_startapp("ENH"))

    print("FINE")

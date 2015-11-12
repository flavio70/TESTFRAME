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

#from katelibs.database import *



class SWP1850TSS():
    """
    Describe a Software Package for 1850TSS320/1850TSS160 equipment (all shelves)
    """

    def __init__(self):
        self.__swp_rel  = None  # Release Identifier (string, as "V7.10.20")
        self.__swp_id   = None  # SWP Identifier (string, as "V7.10.20-0491")
        self.__flv      = None  # Reference FLV Label
        self.__startapp = {}    # dictionary for StartApp strings


    def init_manual(self, str_std=None, str_enh=None, str_sim=None):
        """
        Manual SWP configuration. Almost one of supported architecture must be supplied
        str_std : startapp string for 1850TSS320 legacy shelf
        str_enh : startapp string for 1850TSS320 enhanced shelf
        str_sim : startapp string for 1850TSS320 emulated shelf
        """

        self.__startapp = {}

        if   str_std is not None:
            the_string = str_std
            self.__startapp["STD"] = the_string
        elif str_enh is not None:
            the_string = str_enh
            self.__startapp["ENH"] = the_string
        elif str_sim is not None:
            the_string = str_sim
            self.__startapp["SIM"] = the_string
        else:
            print("Almost one of str_std/str_enh/str_sim must be supplied")
            return False

        self.__swp_id   = the_string.split()[4]
        self.__swp_rel  = self.__swp_id.split('-')[0]
        self.__flv      = None

        return True


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
                self.__flv = swp_flv
                self.__swp_id = "V7.10.20-0491"
                self.__swp_rel = "V7.10.20"
                self.__startapp["ENH"] = "StartApp DWL 1850TSS320HM 1850TSS320HM V7.10.20-0491 151.98.16.7 0 /users/TOOLS/SCRIPTS/pkgStore_04/pkgStoreArea4x/alc-tss/base00/int/LIV_ALC-TSS__BASE00.25__VM_PKG011/target/MAIN_RELEASE_71/swp_gccwrp/1850TSS320H-7.10.20-0491 4gdwl 4gdwl2k12 true"
                self.__startapp["STD"] = "StartApp DWL 1850TSS320M 1850TSS320M V7.10.20-0491 151.98.16.7 0 /users/TOOLS/SCRIPTS/pkgStore_04/pkgStoreArea4x/alc-tss/base00/int/LIV_ALC-TSS__BASE00.25__VM_PKG011/target/MAIN_RELEASE_71/swp_gccpp/1850TSS320-7.10.20-0491 4gdwl 4gdwl2k12 true"
                self.__startapp["SIM"] = "StartApp DWL 1850TSS320M 1850TSS320M V7.10.20-0491 151.98.16.7 0 /users/TOOLS/SCRIPTS/pkgStore_04/pkgStoreArea4x/alc-tss/base00/int/LIV_ALC-TSS__BASE00.25__VM_PKG011/host/MAIN_RELEASE_71/swp_gccli/1850TSS320-7.10.20-0491 4gdwl 4gdwl2k12 true"

            return True

        else:
            print("Exacly one of swp_dr4/swp_ref/swp_flv must be supplied")
            return False


    def get_startapp(self, shelf_type):
        """
        Return the startapp string for current SWP and specified shelf type
        shelf_type : "STD" / "ENH" / "SIM"
        """
        return self.__startapp[shelf_type]

    def get_swp_ref(self):
        """
        Return SWP reference
        """
        return self.__swp_id

    def get_swp_ver(self):
        """
        Return the Release Identifier for current SWP
        """
        return self.__swp_rel

    def get_swp_label(self):
        """
        Return the FLV Label for current SWP
        """
        return self.__flv



if __name__ == '__main__':
    print("DEBUG SWP1850TSS")

    swpstr = "StartApp DWL 1850TSS320HM 1850TSS320HM V7.10.20-0491 151.98.16.7 0 /users/TOOLS/SCRIPTS/pkgStore_04/pkgStoreArea4x/alc-tss/base00/int/LIV_ALC-TSS__BASE00.25__VM_PKG011/target/MAIN_RELEASE_71/swp_gccwrp/1850TSS320H-7.10.20-0491 4gdwl 4gdwl2k12 true"

    my_swp1 = SWP1850TSS()

    my_swp1.init_from_db(swp_flv="FLV_ALC-TSS__BASE00.25.FD0491__VM")

    my_swp2 = SWP1850TSS()

    my_swp2.init_manual(str_enh=swpstr, str_std=None, str_sim=None)

    print(my_swp1.get_swp_label())
    print(my_swp1.get_swp_ver())
    print(my_swp1.get_swp_ref())
    print(my_swp1.get_startapp("ENH"))

    print("FINE")

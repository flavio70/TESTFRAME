#!/usr/bin/env python
'''
TestCase template for K@TE test developers

[DESCRIPTION]
    Put your test decription here
[DESCRIPTION]
[TOPOLOGY] 1 [TOPOLOGY]
[DEPENDENCY]
    Insert Test dependencies
[DEPENDENCY]
[LAB] Insert the lab referneces i.e. SW,SVT [LAB]
[TPS]
    insert here the Test mapping
[TPS]
[RUNSECTIONS]
    Insert here the sections developed in this test i.e.
    DUTSet,testSet,testBody,testClean,DutClean,all
[RUNSECTIONS]
[AUTHOR] ippolf [AUTHOR]

'''

from katelibs.testcase          import TestCase
from katelibs.eqpt1850tss320    import Eqpt1850TSS320
from katelibs.instrumentONT     import InstrumentONT
#from katelibs.instrumentIXIA     import InstrumentIXIA
#from katelibs.instrumentSPIRENT  import InstrumentSPIRENT
from katelibs.swp1850tss320     import SWP1850TSS
from katelibs.facility_tl1      import *


class Test(TestCase):
    '''
    this class implements the current test case behaviour by using
    the five methods (runSections):
        DUTSetUp: used for DUT configuration
        testSetup: used for Test Configuration
        testBody: used for main test pourposes
        testCleanUp: used to finalize test and clear the configuration
        DUTCleanUp: used for DUT cleanUp

        all these runSections can be either run or skipped using inline optional input parameters

        --DUTSet     Run the DUTs SetUp
        --testSet    Run the Test SetUp
        --testBody   Run the Test Main Body
        --testClean  Run the Test Clean Up
        --DUTClean   Run the DUTs Clean Up

        all runSections will be executed if run Test without input parameters
    '''


    def dut_setup(self):
        '''
        DUT Setup section Implementation
        insert DUT SetUp code for your test below
        '''
        #THE_SWP = SWP1850TSS()
        # temporaneo
        #THE_SWP.init_from_db(swp_flv="FLV_ALC-TSS__BASE00.25.FD0491__VM")

        #NE1.flc_ip_config()

        #NE1.flc_load_swp(THE_SWP)

        #NE1.flc_scratch_db()
        #NE1.flc_reboot()
        #NE1.slc_reboot(11)
        #NE1.flc_ip_config()
        #NE1.flc_wait_in_service()


        #NE1.tl1.do("ACT-USER::admin:::Root1850;")
        #NE1.tl1.do("ED-PID::admin:::Root1850,Alcatel1,Alcatel1;")
        #NE1.tl1.do("SET-PRMTR-NE::::::REGION=ETSI,PROVMODE=MANEQ-AUTOFC;")
        #NE1.tl1.do("RTRV-PRMTR-NE;")
        #NE1.tl1.do("SET-ATTR-SECUDFLT::::::MAXSESSION=6;")
        #NE1.tl1.do("ENT-EQPT::SHELF-1-1::::PROVISIONEDTYPE=UNVRSL320,SHELFNUM=1,SHELFROLE=MAIN;")
        #NE1.tl1.do("ENT-EQPT::SHELF-1-1::::PROVISIONEDTYPE=160H,SHELFNUM=1,SHELFROLE=MAIN;")


    def test_setup(self):
        '''
        test Setup Section implementation
        insert general SetUp code for your test below
        '''
        NE1.tl1.event_collection_start()
        NE1.tl1.do("ACT-USER::admin:::Alcatel1;")
        # questo genera volutamente un errore
        NE1.tl1.do("ACT-USER::admin:::Alcatel1;")


    def test_body(self):
        '''
        test Body Section implementation
        insert Main body code for your test below
        '''
        filt_is = TL1check()
        filt_is.add_pst("IS")
        ###NE1.tl1.do("ENT-EQPT::PP1GE-1-1-16::::PROVISIONEDTYPE=PP1GESY;")
        #NE1.tl1.do("ENT-EQPT::PP10GEX2-1-1-15::::PROVISIONEDTYPE=PP10GE2E;")
        NE1.tl1.do("ENT-EQPT::8XSO-1-1-14::::PROVISIONEDTYPE=8PSO,AINSMODE=NOWAIT;")
        NE1.tl1.do_until("RTRV-EQPT::8XSO-1-1-14;", filt_is)
        print("@@@@@  DOPO UNTIL   @@@@")
        
        #NE1.tl1.do("RTRV-ASAP-PROF::ASAPEQPT-0;")
        #self.trc_inf(NE1.tl1.get_last_outcome())

    def test_cleanup(self):
        '''
        test Cleanup Section implementation
        insert CleanUp code for your test below
        '''
        self.start_tps_block(NE1.id, "EM", "1-2-3")
        NE1.tl1.do("RMV-EQPT::8XSO-1-1-14;")
        NE1.tl1.do("DLT-EQPT::8XSO-1-1-14;")
        NE1.tl1.do("RTRV-EQPT::MDL-1-1-14;")
        #  print(NE1.tl1.get_last_outcome())
        ###NE1.tl1.do("RMV-EQPT::PP1GE-1-1-16;")
        ###NE1.tl1.do("DLT-EQPT::PP1GE-1-1-16;")
        NE1.tl1.event_collection_stop()
        import time
        #time.sleep(5)
        #NE1.nonesiste()
        NE1.tl1.do("CANC-USER;")


    def dut_cleanup(self):
        '''
        DUT CleanUp Section implementation
        insert DUT CleanUp code for your test below
        '''
        self.trc_inf('@DUT CleanUP')

        eve_size = int(NE1.tl1.event_collection_size("A", aid="8XSO-1-1-14"))
        print("filtered events for 8XSO-1-1-14 : {}".format(eve_size))
        if eve_size > 0:
            for elem in NE1.tl1.event_collection_get("A", aid="8XSO-1-1-14"):
                print("  EVENT : {} - {}".format(elem.get_eve_type(), elem.get_eve_body()))

        eve_size = int(NE1.tl1.event_collection_size("A", cmd="RMV-EQPT"))
        print("filtered events for RMV-EQPT : {}".format(eve_size))
        if eve_size > 0:
            for elem in NE1.tl1.event_collection_get("A", cmd="RMV-EQPT"):
                print("  EVENT : {} - {}".format(elem.get_eve_type(), elem.get_eve_body()))


        eve_size = int(NE1.tl1.event_collection_size("A", aid="8XSO-1-1-14", cmd="RMV-EQPT"))
        print("filtered events for 8XSO-1-1-14 and RMV-EQPT: {}".format(eve_size))
        if eve_size > 0:
            for elem in NE1.tl1.event_collection_get("A", aid="8XSO-1-1-14", cmd="RMV-EQPT"):
                print("  EVENT : {} - {}".format(elem.get_eve_type(), elem.get_eve_body()))


        self.stop_tps_block(NE1.id, "EM", "1-2-3")




#########################################################################
# Please don't change the code below                                    #

if __name__ == "__main__":

    #####################################################################
    # Initializing the Test object instance, do not remove              #
    CTEST = Test(__file__)

    #####################################################################
    # Initializing all local variable and constants used by Test object #
    # For current Topology, an instance for each Equipment and          #
    # Instrument is defined below.                                      #
    # The equipment references must be notified with CTEST.add_eqpt()   #

    NE1 = Eqpt1850TSS320('NE1', CTEST.kenvironment)
    CTEST.add_eqpt(NE1)

    #####################################################################
    # Run Test main flow                                                #

    CTEST.run()

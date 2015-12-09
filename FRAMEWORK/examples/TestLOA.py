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
        THE_SWP = SWP1850TSS()
        # temporaneo
        THE_SWP.init_from_db(swp_flv="FLV_ALC-TSS__BASE00.25.FD0491__VM")

        #NE1.flc_ip_config()

        NE1.flc_load_swp(THE_SWP)

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
        #self.start_tps_block("EM", "1-2-3")
        #NE1.tl1.do("ACT-USER::admin:::Alcatel1;")


    def test_body(self):
        '''
        test Body Section implementation
        insert Main body code for your test below
        '''

        NE1.tl1.do("ACT-USER::admin:::Alcatel1;")
        NE1.tl1.do("RTRV-PTF::MVC4-1-1-36-1&&-64::::PTFTYPE=MODVC4,PTFRATE=VC4;")
        #NE1.tl1.do("RTRV-TU3::MVC4TU3-1-1-1&&-64-1&&-3;")
        self.trc_inf(NE1.tl1.get_last_outcome())

    def test_cleanup(self):
        '''
        test Cleanup Section implementation
        insert CleanUp code for your test below
        '''


    def dut_cleanup(self):
        '''
        DUT CleanUp Section implementation
        insert DUT CleanUp code for your test below
        '''
        self.trc_inf('@DUT CleanUP')

        self.stop_tps_block("EM", "1-2-3")


#Please don't change the code below#
if __name__ == "__main__":
    #initializing the Test object instance, do not remove
    CTEST = Test(__file__)

    #initializing all local variable and constants used by Test object
    NE1 = Eqpt1850TSS320('NE1', CTEST.kenvironment)
    #ONT5xx = InstrumentONT('ONT5xx', CTEST.kenvironment)
    #ONT6xx = InstrumentONT('ONT6xx', CTEST.kenvironment)

    # Run Test main flow
    # Please don't touch this code
    CTEST.run()

    #ONT6xx.clean_up()
    #ONT5xx.clean_up()
    NE1.clean_up()

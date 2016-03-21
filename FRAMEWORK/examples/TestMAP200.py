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
from katelibs.instrumentIXIA    import InstrumentIXIA
from katelibs.instrumentMAP200  import InstrumentMAP
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


    def test_setup(self):
        '''
        test Setup Section implementation
        insert general SetUp code for your test below
        '''
        map200_1.init_instrument()









    def test_body(self):
        '''
        test Body Section implementation
        insert Main body code for your test below
        '''
        #=========================================
        # LCS Slot 2 Get/Set examples
        #=========================================
        # Get Device 1/2
        map200_1.get_set_switch_state(2,1,1)
        # Get Device 2/2
        #map200_1.get_set_switch_state(2,2,1)
        # SET  Device 1/2 to positions 0-4
        map200_1.get_set_switch_state(2,1,1,0)
        map200_1.get_set_switch_state(2,1,1,1)
        map200_1.get_set_switch_state(2,1,1,2)
        map200_1.get_set_switch_state(2,1,1,3)
        map200_1.get_set_switch_state(2,1,1,4)
        # SET  Device 2/2 to positions 0-4
        #map200_1.get_set_switch_state(2,2,1,0)
        #map200_1.get_set_switch_state(2,2,1,1)
        #map200_1.get_set_switch_state(2,2,1,2)
        #map200_1.get_set_switch_state(2,2,1,3)
        #map200_1.get_set_switch_state(2,2,1,4)

        #=========================================
        # SCS/4 Slot 5 Get/Set examples
        #=========================================
        # Get Device 1/4
        map200_1.get_set_switch_state(5,1,1)
        # Get Device 2/4
        #map200_1.get_set_switch_state(5,2,1)
        # Get Device 3/4
        #map200_1.get_set_switch_state(5,3,1)
        # Get Device 4/4
        #map200_1.get_set_switch_state(5,4,1)

        # SET Device 1/4 To positions 1/2
        map200_1.get_set_switch_state(5,1,1,1)
        map200_1.get_set_switch_state(5,1,1,2)
        # SET Device 2/4 To positions 1/2
        #map200_1.get_set_switch_state(5,2,1,1)
        #map200_1.get_set_switch_state(5,2,1,2)
        # SET Device 3/4 To positions 1/2
        #map200_1.get_set_switch_state(5,3,1,1)
        #map200_1.get_set_switch_state(5,3,1,2)
        # SET Device 4/4 To positions 1/2
        #map200_1.get_set_switch_state(5,4,1,1)
        #map200_1.get_set_switch_state(5,4,1,2)


        #=========================================
        # SCS/8  Slot 8 Get/Set examples
        #=========================================
        # Get Device 1/8
        map200_1.get_set_switch_state(8,1,1)
        # Get Device 2/8
        #map200_1.get_set_switch_state(8,2,1)
        # Get Device 3/8
        #map200_1.get_set_switch_state(8,3,1)
        # Get Device 4/8
        #map200_1.get_set_switch_state(8,4,1)
        # Get Device 5/8
        #map200_1.get_set_switch_state(8,5,1)
        # Get Device 6/8
        #map200_1.get_set_switch_state(8,6,1)
        # Get Device 7/8
        #map200_1.get_set_switch_state(8,7,1)
        # Get Device 8/8
        #map200_1.get_set_switch_state(8,8,1)


        # SET Device 1/8 To positions 1/2
        map200_1.get_set_switch_state(8,1,1,1)
        map200_1.get_set_switch_state(8,1,1,2)
        # SET Device 2/8 To positions 1/2
        #map200_1.get_set_switch_state(8,2,1,1)
        #map200_1.get_set_switch_state(8,2,1,2)
        # SET Device 3/8 To positions 1/2
        #map200_1.get_set_switch_state(8,3,1,1)
        #map200_1.get_set_switch_state(8,3,1,2)
        # SET Device 4/8 To positions 1/2
        #map200_1.get_set_switch_state(8,4,1,1)
        #map200_1.get_set_switch_state(8,4,1,2)
        # SET Device 1/8 To positions 1/2
        #map200_1.get_set_switch_state(8,5,1,1)
        #map200_1.get_set_switch_state(8,5,1,2)
        # SET Device 2/8 To positions 1/2
        #map200_1.get_set_switch_state(8,6,1,1)
        #map200_1.get_set_switch_state(8,6,1,2)
        # SET Device 3/8 To positions 1/2
        #map200_1.get_set_switch_state(8,7,1,1)
        #map200_1.get_set_switch_state(8,7,1,2)
        # SET Device 4/8 To positions 1/2
        #map200_1.get_set_switch_state(8,8,1,1)
        #map200_1.get_set_switch_state(8,8,1,2)




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

    #ID=1046
    map200_1 = InstrumentMAP("map200_1", CTEST.kenvironment)
    #ID=1047
    #map200_2 = InstrumentMAP("map200_2", CTEST.kenvironment)

    #####################################################################
    # Run Test main flow                                                #

    CTEST.run()

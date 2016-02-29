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


    def test_setup(self):
        '''
        test Setup Section implementation
        insert general SetUp code for your test below
        '''
        IXIA.connect_bridge()


    def test_body(self):
        '''
        test Body Section implementation
        insert Main body code for your test below
        '''
        IXIA.add_chassis()
        IXIA.clear_slot_ownership(9)
        #IXIA.init_chassis_cards_handle_list()
        #IXIA.init_chassis_ports_handle_list()
        #IXIA.get_card_handler(9)
        #IXIA.get_slot_port_handle_list(9)
        #IXIA.clear_port_ownership(9,1)
        #IXIA.clear_port_ownership(9,44)
        #IXIA.add_vport(9,12)
        #IXIA.add_vport(9,1)
        #IXIA.remove_vport(9,12)
        #IXIA.remove_vport(9,1)
        #IXIA.remove_vport(9,2)
        #IXIA.add_vport(9,1)
        #IXIA.add_vport(9,1) 
        #print (risultato)
  

        IXIA.create_vport(9,1)
        IXIA.create_vport(9,2)
        IXIA.create_vport(9,3)
        IXIA.create_vport(9,4)
        IXIA.create_vport(9,5)
        IXIA.create_vport(9,6)


        IXIA.connect_vport_to_physical_port(9,1)
        IXIA.connect_vport_to_physical_port(9,2)
        IXIA.connect_vport_to_physical_port(9,3)
        IXIA.connect_vport_to_physical_port(9,4)
        IXIA.connect_vport_to_physical_port(9,5)
        IXIA.connect_vport_to_physical_port(9,6)



    def test_cleanup(self):
        '''
        test Cleanup Section implementation
        insert CleanUp code for your test below
        '''
        IXIA.disconnect_bridge()




    def dut_cleanup(self):
        '''
        DUT CleanUp Section implementation
        insert DUT CleanUp code for your test below
        '''
        IXIA.clean_up()


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

    IXIA = InstrumentIXIA('IXIA', CTEST.kenvironment)

    #####################################################################
    # Run Test main flow                                                #

    CTEST.run()

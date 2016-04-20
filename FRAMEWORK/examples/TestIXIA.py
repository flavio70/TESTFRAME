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
        IXIA.connect_ixnetwork()


    def test_body(self):
        '''
        test Body Section implementation
        insert Main body code for your test below
        '''

        IXIA.start_all_protocols()


        # EXAMPLE WITH PORT 2/1 LOOPED TX->RX
        nomeTraffico = "Traffico di Test PORTA 1 LOOP"
        testPortList  = [('135.221.113.142', 2, 1)]
        IXIA.create_all_vports(testPortList)
        
        IXIA.create_traffic(vPortIdTx   = ('135.221.113.142', 2, 1), 
                            vPortIdRx   = ('135.221.113.142', 2, 1),
                            trafficName = nomeTraffico,
                            TCframeCount           = 9876)  # 9876 frames for this traffic (default 10000)
        IXIA.bind_all_phy_ports_to_vports(testPortList)

        IXIA.start_traffic()
        IXIA.stop_traffic(20)


        
        # EXAMPLE WITH PORT 2/2->TX and PORT 2/3-RX with VLAN creation
        nomeTraffico = "Traffico di Test PORTA 2->3"
        testPortList  = [('135.221.113.142', 2, 2), ('135.221.113.142', 2, 3)]
        IXIA.create_all_vports(testPortList)
        IXIA.create_traffic(vPortIdTx   = ('135.221.113.142', 2, 2), 
                            vPortIdRx   = ('135.221.113.142', 2, 3),
                            trafficName = nomeTraffico,
                            VLanId                 = 144,
                            VLanCFI                = 1,
                            VLanPriority           = 5,
                            VLanSrcMacAddr         = "00:20:60:00:00:03",
                            VLanDestMacAddr        = "00:20:60:00:00:04")
        IXIA.bind_all_phy_ports_to_vports(testPortList)

        IXIA.start_traffic()
        IXIA.stop_traffic(20)


        # EXAMPLE WITH PORT 2/4 LOOPED TX->RX
        nomeTraffico = "Traffico di Test PORTA 4 LOOP"
        testPortList  = [('135.221.113.142', 2, 4)]
        IXIA.create_all_vports(testPortList)
        
        IXIA.create_traffic(vPortIdTx    = ('135.221.113.142', 2, 4), 
                            vPortIdRx    = ('135.221.113.142', 2, 4),
                            trafficName  = nomeTraffico,
                            TCframeCount = 20000)  # 20000 frames for this traffic (default 10000)
        IXIA.bind_all_phy_ports_to_vports(testPortList)

        IXIA.start_traffic()
        IXIA.stop_traffic(20)
  
  
  
  
        #IXIA.check_traffic()
        #dizionario=dict()
        #dizionario = IXIA.get_port_statistic('135.221.113.142', 2, 2)[1]
        #print("=======================================")
        #print("{}".format(dizionario))
        #print("=======================================")
        #print("Tx Frames port 2 [{}]".format(dizionario.get("Frames Tx.")))

        #dizionario = IXIA.get_port_statistic('135.221.113.142', 2, 3)[1]
        #print("=======================================")
        #print("{}".format(dizionario))
        #print("=======================================")
        #print("Rx Frames port 3[{}]".format(dizionario.get("Valid Frames Rx.")))
        
        #dizionario = IXIA.get_flow_statistic(nomeTraffico)[1]
        #print("=======================================")
        #print("{}".format(dizionario))
        #print("=======================================")
        
        #dizionario = IXIA.get_traffic_item_statistic(nomeTraffico)[1]
        #print("=======================================")
        #print("{}".format(dizionario))
        #print("=======================================")
        
        #
        #   SI blocca: forse va invocato a traffico running...boh
        #
        #dizionario = IXIA.get_txrx_frame_rate_statistic(nomeTraffico)[1]
        #print("=======================================")
        #print("{}".format(dizionario))
        #print("=======================================")
        
        
        #dizionario = IXIA.get_port_cpu_statistic('135.221.113.142', 2, 2)[1]
        #print("=======================================")
        #print("{}".format(dizionario))
        #print("=======================================")
        
         
        
        #dizionario = IXIA.get_global_protocol_statistic('135.221.113.142', 2, 2)[1]
        #print("=======================================")
        #print("{}".format(dizionario))
        #print("=======================================")
         
        
        #dizionario = IXIA.get_l2l3_test_summary_statistic('135.221.113.142', 2, 2)[1]
        #print("=======================================")
        #print("{}".format(dizionario))
        #print("=======================================")
        
               
        #
        #   SI blocca: forse va invocato a traffico running...boh
        #
        #dizionario = IXIA.get_flow_detective_statistic('135.221.113.142', 2, 2)[1]
        #print("=======================================")
        #print("{}".format(dizionario))
        #print("=======================================")
        
        
        #dizionario = IXIA.get_data_plane_port_statistic("Ethernet - 001")[1]
        #print("=======================================")
        #print("{}".format(dizionario))
        #print("=======================================")
        
        
        
        
        #dizionario = IXIA.get_user_defined_statistic("prova")[1]
        #print("=======================================")
        #print("{}".format(dizionario))
        #print("=======================================")
        
        
         


    def test_cleanup(self):
        '''
        test Cleanup Section implementation
        insert CleanUp code for your test below
        '''
        ####IXIA.disconnect_bridge()




    def dut_cleanup(self):
        '''
        DUT CleanUp Section implementation
        insert DUT CleanUp code for your test below
        '''
        ####IXIA.clean_up()


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

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
[RUNSECTIONS]
[TPS]
    insert here the Test mapping
[TPS]
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

import time


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


        # CARD 1/PORT 1 Test config
        #IdPort_1=('151.98.130.42', 1, 1)
        #IXIA.add_single_vport(IdPort_1, enabledFlowControl=False, autoNegotiate=False, speed="speed1000") 
        #IXIA.bind_new_vports()        
        #IXIA.enable_disable_lacp_protocol(IdPort_1,enable=True)    
        ##IXIA.init_traffic()  ##Chiamata OPZIONALE utile solo nel caso occorrano parametri non di default. altrimenti chiamata dalla add_L2_3_Quick_Flow_Group()
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_1)
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_1)
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_1,flowGroupName="FlowGroup Nome a manina")



        # Riproduzione Setup Valeria Sanvito su 16 porte per check opzioni di config dei flow group
        # porte 1-16
        IdPort_1=('151.98.130.42', 1, 1)
        IdPort_2=('151.98.130.42', 1, 2)
        IdPort_3=('151.98.130.42', 1, 3)
        IdPort_4=('151.98.130.42', 1, 4)
        IdPort_5=('151.98.130.42', 1, 5)
        IdPort_6=('151.98.130.42', 1, 6)
        IdPort_7=('151.98.130.42', 1, 7)
        IdPort_8=('151.98.130.42', 1, 8)
        IdPort_9=('151.98.130.42', 1, 9)
        IdPort_10 =('151.98.130.42', 1,10)
        IdPort_11 =('151.98.130.42', 1,11)
        IdPort_12 =('151.98.130.42', 1,12)
        IdPort_13 =('151.98.130.42', 1,13)
        IdPort_14 =('151.98.130.42', 1,14)
        IdPort_15 =('151.98.130.42', 1,15)
        IdPort_16 =('151.98.130.42', 1,16)
        
        IdPort_1A=('151.98.130.42', 2, 1)
        IdPort_2A=('151.98.130.42', 2, 2)
        IdPort_3A=('151.98.130.42', 2, 3)
        IdPort_4A=('151.98.130.42', 2, 4)
        
        
        FlowGroupName_1 ="Flusso 1"
        FlowGroupName_2 ="Flusso 2"
        FlowGroupName_3 ="Flusso 3"
        FlowGroupName_4 ="Flusso 4"
        FlowGroupName_5 ="Flusso 5"
        FlowGroupName_6 ="Flusso 6"
        FlowGroupName_7 ="Flusso 7"
        FlowGroupName_8 ="Flusso 8"
        FlowGroupName_9 ="Flusso 9 - random"
        IXIA.add_single_vport(IdPort_1, enabledFlowControl=False, autoNegotiate=False, speed="speed1000",customName="PortaLore 1 1") 
        IXIA.add_single_vport(IdPort_2, enabledFlowControl=False, autoNegotiate=False, speed="speed1000",customName="PortaLore 1 2") 
        IXIA.add_single_vport(IdPort_3, enabledFlowControl=False, autoNegotiate=False, speed="speed1000") 
        IXIA.add_single_vport(IdPort_4, enabledFlowControl=False, autoNegotiate=False, speed="speed1000") 
        IXIA.add_single_vport(IdPort_5, enabledFlowControl=False, autoNegotiate=False, speed="speed1000") 
        IXIA.add_single_vport(IdPort_6, enabledFlowControl=False, autoNegotiate=False, speed="speed1000") 
        IXIA.add_single_vport(IdPort_7, enabledFlowControl=False, autoNegotiate=False, speed="speed1000") 
        IXIA.add_single_vport(IdPort_8, enabledFlowControl=False, autoNegotiate=False, speed="speed1000") 
        IXIA.add_single_vport(IdPort_9, enabledFlowControl=False, autoNegotiate=False, speed="speed1000") 
        IXIA.add_single_vport(IdPort_10,enabledFlowControl=False, autoNegotiate=False, speed="speed1000") 
        IXIA.add_single_vport(IdPort_11,enabledFlowControl=False, autoNegotiate=False, speed="speed1000") 
        IXIA.add_single_vport(IdPort_12,enabledFlowControl=False, autoNegotiate=False, speed="speed1000") 
        IXIA.add_single_vport(IdPort_13,enabledFlowControl=False, autoNegotiate=False, speed="speed1000") 
        IXIA.add_single_vport(IdPort_14,enabledFlowControl=False, autoNegotiate=False, speed="speed1000") 
        IXIA.add_single_vport(IdPort_15,enabledFlowControl=False, autoNegotiate=False, speed="speed1000") 
        IXIA.add_single_vport(IdPort_16,enabledFlowControl=False, autoNegotiate=False, speed="speed1000") 
        
        IXIA.add_single_vport(IdPort_1A, enabledFlowControl=False, autoNegotiate=False, speed="speed1000",customName="PortaLore 2 1")  
        IXIA.add_single_vport(IdPort_2A, enabledFlowControl=False, autoNegotiate=False, speed="speed1000",customName="PortaLore 2 2")  
        IXIA.add_single_vport(IdPort_3A, enabledFlowControl=False, autoNegotiate=False, speed="speed1000",customName="PortaLore 2 3")  
        IXIA.add_single_vport(IdPort_4A, enabledFlowControl=False, autoNegotiate=False, speed="speed1000",customName="PortaLore 2 4")  
        
        
        
        IXIA.bind_new_vports()        
        IXIA.enable_disable_lacp_protocol(IdPort_1, enable=True,administrativeKey=1)    
        IXIA.enable_disable_lacp_protocol(IdPort_2, enable=True,administrativeKey=1)    
        IXIA.enable_disable_lacp_protocol(IdPort_3, enable=True,administrativeKey=2)    
        IXIA.enable_disable_lacp_protocol(IdPort_4, enable=True,administrativeKey=2)    
        IXIA.enable_disable_lacp_protocol(IdPort_5, enable=True,administrativeKey=1)    
        IXIA.enable_disable_lacp_protocol(IdPort_6, enable=True,administrativeKey=1)    
        IXIA.enable_disable_lacp_protocol(IdPort_7, enable=True,administrativeKey=1)    
        IXIA.enable_disable_lacp_protocol(IdPort_8, enable=True,administrativeKey=1)    
        IXIA.enable_disable_lacp_protocol(IdPort_9, enable=True,administrativeKey=1)    
        IXIA.enable_disable_lacp_protocol(IdPort_10,enable=True,administrativeKey=1)    
        IXIA.enable_disable_lacp_protocol(IdPort_11,enable=True,administrativeKey=1)    
        IXIA.enable_disable_lacp_protocol(IdPort_12,enable=True,administrativeKey=1)    
        IXIA.enable_disable_lacp_protocol(IdPort_13,enable=True,administrativeKey=1)    
        IXIA.enable_disable_lacp_protocol(IdPort_14,enable=True,administrativeKey=1)    
        IXIA.enable_disable_lacp_protocol(IdPort_15,enable=True,administrativeKey=1)    
        IXIA.enable_disable_lacp_protocol(IdPort_16,enable=True,administrativeKey=1)    
        
        
        IXIA.enable_disable_lacp_protocol(IdPort_1A, enable=True,administrativeKey=1)    
        IXIA.enable_disable_lacp_protocol(IdPort_2A, enable=True,administrativeKey=1)    
        IXIA.enable_disable_lacp_protocol(IdPort_3A, enable=True,administrativeKey=1)    
        IXIA.enable_disable_lacp_protocol(IdPort_4A, enable=True,administrativeKey=1)    



        #IXIA.init_traffic()  ##Chiamata OPZIONALE utile solo nel caso occorrano parametri non di default. altrimenti chiamata dalla add_L2_3_Quick_Flow_Group()

        #=================================      
        # Esempi creazione quick flow (ad uso dei validatori)
        #=================================       
        # Esempio caso rateType = "lineRate"
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_1, flowGroupName = "FlowGroup 001 - lineRate", rateType = "lineRate", randomMin = 304, randomMax = 1212, 
        #                               frameSizeType = "random" rateValue    = 12.122222)                 
        # Esempio caso rateType = "packetRate"
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_1, flowGroupName = "FlowGroup 001 - packetRate",rateType = "packetRate",randomMin = 333,randomMax = 3333,
        #                               frameSizeType = "random",rateValue = 133323,24)                 
        # Esempio caso rateType = "layer2BitRate"
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_1, flowGroupName = "FlowGroup 001 - layer2BitRate",rateType = "layer2BitRate",randomMin = 300, randomMax = 2000, 
        #                               frameSizeType = "random", rateValue    = 1234,56)                 
        # Esempio caso rateType = "packetRate" payload "incrementByte"
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_1, flowGroupName = "FlowGroup 001 - packetRate - payload incrementByte",rateType = "packetRate", randomMin = 300,randomMax = 2000,
        #                               frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte")                 
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_1, flowGroupName = "FlowGroup 001 - packetRate - payload incrementByte",rateType = "packetRate", randomMin = 300,randomMax = 2000,
        #                               frameSizeType = "random",rateValue = 100000.24 )                 
        # Esempio caso rateType = "packetRate" payload "random"
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_1, flowGroupName = "FlowGroup 001 - packetRate - payload random",rateType = "packetRate", randomMin = 300,randomMax = 2000,
        #                               frameSizeType = "random",rateValue = 100000.24,payloadType = "random")                 
        # Esempio caso rateType = "packetRate" payload "custom"
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_1, flowGroupName = "FlowGroup 001 - packetRate - payload custom - no repeat",
        #                               rateType = "packetRate", randomMin = 300,randomMax = 2000,frameSizeType = "random",rateValue = 100000.24,
        #                               payloadType = "custom", payloadPattern="ABBAABBA", payloadPatternRepeat = False)                 
                                       
 
        # Esempio caso rateType = "packetRate" payload "incrementByte - Flow groups transmission mode defaults"
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_1, flowGroupName = "FlowGroup 001 - packetRate - payload incrementByte",
        #                               rateType = "packetRate", randomMin = 300,randomMax = 2000,
        #                               frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte")                 


        # Esempio caso rateType = "packetRate" payload "incrementByte - Flow groups transmission mode defaults - transm mode edited fixed packet"
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_1, flowGroupName = "FlowGroup 001 - packetRate - payload incrementByte",
        #                               rateType = "packetRate", randomMin = 300,randomMax = 2000,
        #                               frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte",
        #                               transmissionMode = "fixedPacketCount", 
        #                               transmissionStopAfter = 4, 
        #                               transmissionStartDelay=2, transmissionStartDelayUnit="nanoseconds",
        #                               transmissionMinimumGap=14)                 

        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_1, flowGroupName = "FlowGroup 001 - packetRate - payload incrementByte - transm mode continuous",
        #                               rateType = "packetRate", randomMin = 300,randomMax = 2000,
        #                               frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte",
        #                               transmissionMode = "continuous", 
        #                               transmissionStopAfter =3, 
        #                               transmissionStartDelay=3, transmissionStartDelayUnit="bytes",
        #                               transmissionMinimumGap=13)                 

        # esempio di aggiunta di  vLan id 10 prio 4
        IXIA.add_L2_3_Quick_Flow_Group(IdPort_1, flowGroupName = "FlowGroup 001 -Single vlan",
                                       rateType = "packetRate", randomMin = 300,randomMax = 2000,
                                       frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte",
                                       vLanId=10, vLanPrio=4,                
                                       innerVLanId= 12, innerVLanPrio=5)                 

        # esempio di aggiunta di  vLan id 10 prio 4 e INNER vlan id 12 prio 5
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_2, flowGroupName = "FlowGroup 002 - Vlan and Inner vlan",
        #                               rateType = "packetRate", randomMin = 300,randomMax = 2000,
        #                               frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte",
        #                               vLanId=3, vLanPrio=2)                 










        # esempio di aggiunta di  MPLS con PW label 333
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_1, flowGroupName = "FlowGroup 001 - Pseudowire 333 only",
        #                               rateType = "packetRate", randomMin = 300,randomMax = 2000,
        #                               frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte",
        #                               mplsPWLabel=333)                 



        # esempio di aggiunta di  MPLS con PW label 234, Experimental Bit 4 e TTL 45
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_1, flowGroupName = "FlowGroup 001 - Pseudowire 234 only",
        #                               rateType = "packetRate", randomMin = 300,randomMax = 2000,
        #                               frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte",
        #                               mplsPWLabel  = 234,
        #                               mplsPWExpBit = 4,
        #                               mplsPWTTL    = 45)                 




        # esempio di aggiunta di  MPLS con TUNNEL label 444 e PW label 555
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_2, flowGroupName = "FlowGroup 002 - Tunnel 444 + Pseudowire 333",
        #                               rateType = "packetRate", randomMin = 300,randomMax = 2000,
        #                               frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte",
        #                               mplsTunnelLabel=444,
        #                               mplsPWLabel=555)                 
        


        # esempio di aggiunta di  MPLS con Tunnel Label 123,Expbit 4, TTL=55  e PW  Label 321, Expbit 2, TTL=37 
        IXIA.add_L2_3_Quick_Flow_Group(IdPort_2, flowGroupName = "FlowGroup 002 - Tunnel 123 + Pseudowire 321",
                                       rateType = "packetRate", randomMin = 300,randomMax = 2000,
                                       frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte",
                                       mplsTunnelLabel  = 123,
                                       mplsTunnelExpBit = 4,
                                       mplsTunnelTTL    = 55,                 
                                       mplsPWLabel  = 321,
                                       mplsPWExpBit = 2,
                                       mplsPWTTL    = 37)                 
        
        



        # on the fly parameters change for  the flow identified by  flowGroupName = "FlowGroup 001 -Single vlan"       
        IXIA.modify_MPLS_VLAN_L2_3_Quick_Flow_Group(flowGroupName = "FlowGroup 001 -Single vlan",
                                       vLanId=11, vLanPrio=2,                
                                       innerVLanId= 10, innerVLanPrio=1)                 
        
   
        # on the fly parameters change for  the flow identified by  flowGroupName = "FlowGroup 002 - Tunnel 123 + Pseudowire 321"     
        IXIA.modify_MPLS_VLAN_L2_3_Quick_Flow_Group(flowGroupName = "FlowGroup 002 - Tunnel 123 + Pseudowire 321",
                                       mplsTunnelLabel  = 111,
                                       mplsTunnelExpBit = 2,
                                       mplsTunnelTTL    = 22,                 
                                       mplsPWLabel  = 33,
                                       mplsPWExpBit = 3,
                                       mplsPWTTL    = 33)                 




        # Esempio assegnamento source/destination MAC address   
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_1, flowGroupName = "FlowGroup 001 - packetRate - payload incrementByte",
        #                               rateType = "packetRate", randomMin = 300,randomMax = 2000,
        #                               frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte",
        #                               sourceMacAddressFixed="00:AA:BB:00:00:00",destinationMacAddressFixed="00:CC:DD:00:00:00")                 
        
        # Esempio di aggiunta di  vLan id 10 prio 4 con assegnamento source/destination MAC address 
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_1, flowGroupName = "FlowGroup 001 - packetRate - payload incrementByte",
        #                               rateType = "packetRate", randomMin = 300,randomMax = 2000,
        #                               frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte",
        #                               vLanId=10, vLanPrio=4,
        #                               sourceMacAddressFixed="00:AA:DD:00:00:00", destinationMacAddressFixed="00:CC:aa:00:00:00")                 

        # esempio di aggiunta di  MPLS con label 234 con assegnamento source/destination MAC address 
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_1, flowGroupName = "FlowGroup 001 - packetRate - payload incrementByte",
        #                               rateType = "packetRate", randomMin = 300,randomMax = 2000,
        #                               frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte",
        #                               mplsPWLabel=234,                  
        #                               sourceMacAddressFixed="00:AA:AA:FF:00:00", destinationMacAddressFixed="00:BB:BB:FF:00:00")                 
 

        # esempio di aggiunta di CUSTOM  Ether Type. con label 234 con assegnamento source/destination MAC address 
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_1,
        #                               rateType = "packetRate", randomMin = 300,randomMax = 2000,
        #                               frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte",
        #                               etherType="0b0b",
        #                               sourceMacAddressFixed="AA:AA:AA:00:00:00", destinationMacAddressFixed="BB:BB:BB:00:00:00")                 




        # FLOW 1 - esempio di specifiche differenti di SOURCE/DEST mac addresses FIXED 
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_1,flowGroupName =FlowGroupName_1,
                                       #rateType = "packetRate", randomMin = 300,randomMax = 2000,
                                       #frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte",
                                       #etherType="0b0b",
                                       #sourceMacAddressFixed="AA:AA:AA:00:00:00", 
                                       #destinationMacAddressFixed="BB:BB:BB:00:00:00")      
        
        ## FLOW 2 - esempio di specifiche differenti di SOURCE INCREMENT/DEST DECREMENT mac addresses   
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_2,flowGroupName =FlowGroupName_2,
                                       #rateType = "packetRate", randomMin = 300,randomMax = 2000,
                                       #frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte",
                                       #etherType="c0c0",
                                       #sourceMacAddressMode="increment", 
                                       #sourceMacAddressFixed="AA:AA:AA:00:00:00", 
                                       #sourceMacAddressStart="BB:BB:BB:00:00:00", 
                                       #sourceMacAddressStep="00:00:00:00:00:02", 
                                       #sourceMacAddressCount=2, 
                                       #destinationMacAddressMode="decrement", 
                                       #destinationMacAddressFixed="CC:CC:CC:00:00:00",
                                       #destinationMacAddressStart="DD:DD:DD:00:00:00",
                                       #destinationMacAddressStep="00:00:00:00:00:03",
                                       #destinationMacAddressCount=3)

        ## FLOW 2 - esempio di specifiche differenti di SOURCE INCREMENT/DEST DECREMENT mac addresses   
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_2,flowGroupName =FlowGroupName_3,
                                       #rateType = "packetRate", randomMin = 300,randomMax = 2000,
                                       #frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte",
                                       #etherType="c0c0",
                                       #sourceMacAddressMode="increment", 
                                       #sourceMacAddressFixed="AA:AA:AA:00:00:00", 
                                       #sourceMacAddressStart="BB:BB:BB:00:00:00", 
                                       #sourceMacAddressStep="00:00:00:00:00:02", 
                                       #sourceMacAddressCount=2, 
                                       #destinationMacAddressMode="decrement", 
                                       #destinationMacAddressFixed="CC:CC:CC:00:00:00",
                                       #destinationMacAddressStart="DD:DD:DD:00:00:00",
                                       #destinationMacAddressStep="00:00:00:00:00:03",
                                       #destinationMacAddressCount=3)

        ## FLOW 2 - esempio di specifiche differenti di SOURCE INCREMENT/DEST DECREMENT mac addresses   
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_2,flowGroupName =FlowGroupName_4,
                                       #rateType = "packetRate", randomMin = 300,randomMax = 2000,
                                       #frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte",
                                       #etherType="c0c0",
                                       #sourceMacAddressMode="increment", 
                                       #sourceMacAddressFixed="AA:AA:AA:00:00:00", 
                                       #sourceMacAddressStart="BB:BB:BB:00:00:00", 
                                       #sourceMacAddressStep="00:00:00:00:00:02", 
                                       #sourceMacAddressCount=2, 
                                       #destinationMacAddressMode="decrement", 
                                       #destinationMacAddressFixed="CC:CC:CC:00:00:00",
                                       #destinationMacAddressStart="DD:DD:DD:00:00:00",
                                       #destinationMacAddressStep="00:00:00:00:00:03",
                                       #destinationMacAddressCount=3)


        ## FLOW 2 - esempio di specifiche differenti di SOURCE INCREMENT/DEST DECREMENT mac addresses   
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_2,flowGroupName =FlowGroupName_5,
                                       #rateType = "packetRate", randomMin = 300,randomMax = 2000,
                                       #frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte",
                                       #etherType="c0c0",
                                       #sourceMacAddressMode="increment", 
                                       #sourceMacAddressFixed="AA:AA:AA:00:00:00", 
                                       #sourceMacAddressStart="BB:BB:BB:00:00:00", 
                                       #sourceMacAddressStep="00:00:00:00:00:02", 
                                       #sourceMacAddressCount=2, 
                                       #destinationMacAddressMode="decrement", 
                                       #destinationMacAddressFixed="CC:CC:CC:00:00:00",
                                       #destinationMacAddressStart="DD:DD:DD:00:00:00",
                                       #destinationMacAddressStep="00:00:00:00:00:03",
                                       #destinationMacAddressCount=3)


        ## FLOW 2 - esempio di specifiche differenti di SOURCE INCREMENT/DEST DECREMENT mac addresses   
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_2,flowGroupName =FlowGroupName_6,
                                       #rateType = "packetRate", randomMin = 300,randomMax = 2000,
                                       #frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte",
                                       #etherType="c0c0",
                                       #sourceMacAddressMode="increment", 
                                       #sourceMacAddressFixed="AA:AA:AA:00:00:00", 
                                       #sourceMacAddressStart="BB:BB:BB:00:00:00", 
                                       #sourceMacAddressStep="00:00:00:00:00:02", 
                                       #sourceMacAddressCount=2, 
                                       #destinationMacAddressMode="decrement", 
                                       #destinationMacAddressFixed="CC:CC:CC:00:00:00",
                                       #destinationMacAddressStart="DD:DD:DD:00:00:00",
                                       #destinationMacAddressStep="00:00:00:00:00:03",
                                       #destinationMacAddressCount=3)


        ## FLOW 2 - esempio di specifiche differenti di SOURCE INCREMENT/DEST DECREMENT mac addresses   
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_2,flowGroupName =FlowGroupName_7,
                                       #rateType = "packetRate", randomMin = 300,randomMax = 2000,
                                       #frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte",
                                       #etherType="c0c0",
                                       #sourceMacAddressMode="increment", 
                                       #sourceMacAddressFixed="AA:AA:AA:00:00:00", 
                                       #sourceMacAddressStart="BB:BB:BB:00:00:00", 
                                       #sourceMacAddressStep="00:00:00:00:00:02", 
                                       #sourceMacAddressCount=2, 
                                       #destinationMacAddressMode="decrement", 
                                       #destinationMacAddressFixed="CC:CC:CC:00:00:00",
                                       #destinationMacAddressStart="DD:DD:DD:00:00:00",
                                       #destinationMacAddressStep="00:00:00:00:00:03",
                                       #destinationMacAddressCount=3)


        # FLOW 2 - esempio di specifiche differenti di SOURCE INCREMENT/DEST DECREMENT mac addresses   
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_2,flowGroupName =FlowGroupName_8,
                                       #rateType = "packetRate", randomMin = 300,randomMax = 2000,
                                       #frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte",
                                       #etherType="c0c0",
                                       #sourceMacAddressMode="increment", 
                                       #sourceMacAddressFixed="AA:AA:AA:00:00:00", 
                                       #sourceMacAddressStart="BB:BB:BB:00:00:00", 
                                       #sourceMacAddressStep="00:00:00:00:00:02", 
                                       #sourceMacAddressCount=2, 
                                       #destinationMacAddressMode="decrement", 
                                       #destinationMacAddressFixed="CC:CC:CC:00:00:00",
                                       #destinationMacAddressStart="DD:DD:DD:00:00:00",
                                       #destinationMacAddressStep="00:00:00:00:00:03",
                                       #destinationMacAddressCount=3)



        ## FLOW 2 - esempio di specifiche differenti di SOURCE INCREMENT/DEST DECREMENT mac addresses   
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_2,flowGroupName =FlowGroupName_9,
                                       #rateType = "packetRate", randomMin = 300,randomMax = 2000,
                                       #frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte",
                                       #etherType="c0c0",
                                       #sourceMacAddressMode="random", 
                                       #sourceMacAddressFixed="AA:AA:AA:00:00:00", 
                                       #sourceMacAddressStart="BB:BB:BB:00:00:00", 
                                       #sourceMacAddressStep="00:00:00:00:00:02", 
                                       #sourceMacAddressCount=2, 
                                       #destinationMacAddressMode="random", 
                                       #destinationMacAddressFixed="CC:CC:CC:00:00:00",
                                       #destinationMacAddressStart="DD:DD:DD:00:00:00",
                                       #destinationMacAddressStep="00:00:00:00:00:03",
                                       #destinationMacAddressCount=3)








        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_1,flowGroupName ="Flusso1", rateType = "packetRate", randomMin = 300,randomMax = 2000, frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte", etherType="0b0b", sourceMacAddressFixed="AA:AA:AA:00:00:00", destinationMacAddressFixed="BB:BB:BB:00:00:00")                 
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_1,flowGroupName ="Flusso1", rateType = "packetRate", randomMin = 300,randomMax = 2000, frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte", etherType="0b0b", sourceMacAddressFixed="AA:AA:AA:00:00:00", destinationMacAddressFixed="BB:BB:BB:00:00:00")                 
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_1,rateType = "packetRate", randomMin = 300,randomMax = 2000, frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte", sourceMacAddressFixed="AA:AA:AA:00:00:00", destinationMacAddressFixed="BB:BB:BB:00:00:00")                 
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_1,rateType = "packetRate", randomMin = 300,randomMax = 2000, frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte", etherType="0b0b", sourceMacAddressFixed="AA:AA:AA:00:00:00", destinationMacAddressFixed="BB:BB:BB:00:00:00")                 
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_1,flowGroupName ="Flusso2", rateType = "packetRate", randomMin = 300,randomMax = 2000, frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte", etherType="0b0b", sourceMacAddressFixed="AA:AA:AA:00:00:00", destinationMacAddressFixed="BB:BB:BB:00:00:00")                 

        #
        # Check ON-THE-FLY etherType changes
        #

        # esempio modifica etherType
        #tempEtherType="BABA"  
        #print("tempEtherType == [{}]  <<<<<<<<########".format(tempEtherType))
        #IXIA.modify_Frame_Ethernet_Header_L2_3_Quick_Flow_Group(flowGroupName = FlowGroupName_1,
                                                                #etherType = tempEtherType,)     
        
        ## esempio modifica etherType
        #tempEtherType="CACA"  
        #print("tempEtherType == [{}]  <<<<<<<<########".format(tempEtherType))
        #IXIA.modify_Frame_Ethernet_Header_L2_3_Quick_Flow_Group(flowGroupName = FlowGroupName_2,
                                                                #etherType = "eeee",
                                                                #sourceMacAddressMode       = "singleValue",                              
                                                                #sourceMacAddressFixed      = "EE:FF:EE:FF:00:00",
                                                                #sourceMacAddressStart      = "AA:BB:CC:DD:00:00",
                                                                #sourceMacAddressStep       = "00:00:00:00:00:02",
                                                                #sourceMacAddressCount      = 3,
                                                                #destinationMacAddressMode  = None, 
                                                                #destinationMacAddressFixed = "00:00:00:00:00:00",
                                                                #destinationMacAddressStart = "00:00:00:00:00:00",
                                                                #destinationMacAddressStep  = "00:00:00:00:00:00",
                                                                #destinationMacAddressCount = 1)     
        ## analogo ma conciso... 
        #IXIA.modify_Frame_Ethernet_Header_L2_3_Quick_Flow_Group(flowGroupName = FlowGroupName_5,
                                                                #etherType = "eeee",
                                                                #sourceMacAddressMode       = "singleValue",                              
                                                                #sourceMacAddressFixed      = "EE:FF:EE:FF:00:00",
                                                                #sourceMacAddressStart      = "AA:BB:CC:DD:00:00",
                                                                #sourceMacAddressStep       = "00:00:00:00:00:02",
                                                                #sourceMacAddressCount      = 3)     
        
        ## esempio modifica etherType
        #tempEtherType="DADA"  
        #print("tempEtherType == [{}]  <<<<<<<<########".format(tempEtherType))
        #IXIA.modify_Frame_Ethernet_Header_L2_3_Quick_Flow_Group(flowGroupName = FlowGroupName_3,
                                                                #etherType = "eeee",
                                                                #sourceMacAddressMode       = "increment",                              
                                                                #sourceMacAddressFixed      = "EE:FF:EE:FF:00:00",
                                                                #sourceMacAddressStart      = "AA:BB:CC:DD:00:00",
                                                                #sourceMacAddressStep       = "00:00:00:00:00:02",
                                                                #sourceMacAddressCount      = 3,
                                                                #destinationMacAddressMode  = None, 
                                                                #destinationMacAddressFixed = "00:00:00:00:00:00",
                                                                #destinationMacAddressStart = "00:00:00:00:00:00",
                                                                #destinationMacAddressStep  = "00:00:00:00:00:00",
                                                                #destinationMacAddressCount = 1)     
        ## analogo ma conciso... 
        #IXIA.modify_Frame_Ethernet_Header_L2_3_Quick_Flow_Group(flowGroupName = FlowGroupName_6,
                                                                #etherType = "eeee",
                                                                #sourceMacAddressMode       = "increment",                              
                                                                #sourceMacAddressFixed      = "EE:FF:EE:FF:00:00",
                                                                #sourceMacAddressStart      = "AA:BB:CC:DD:00:00",
                                                                #sourceMacAddressStep       = "00:00:00:00:00:02",
                                                                #sourceMacAddressCount      = 3)     
        
        ## esempio modifica etherType
        #tempEtherType="FAFA"  
        #print("tempEtherType == [{}]  <<<<<<<<########".format(tempEtherType))
        #IXIA.modify_Frame_Ethernet_Header_L2_3_Quick_Flow_Group(flowGroupName = FlowGroupName_4,
                                                                #etherType = None,
                                                                #sourceMacAddressMode       = None,                              
                                                                #sourceMacAddressFixed      = "EE:FF:EE:FF:00:00",
                                                                #sourceMacAddressStart      = "AA:BB:CC:DD:00:00",
                                                                #sourceMacAddressStep       = "00:00:00:00:00:02",
                                                                #sourceMacAddressCount      = 3,
                                                                #destinationMacAddressMode  = "decrement",        
                                                                #destinationMacAddressFixed = "EE:FF:EE:FF:00:00",
                                                                #destinationMacAddressStart = "AA:BB:CC:DD:00:00",
                                                                #destinationMacAddressStep  = "00:00:00:00:00:02",
                                                                #destinationMacAddressCount = 1)     
        
        ## analogo ma conciso... 
        #IXIA.modify_Frame_Ethernet_Header_L2_3_Quick_Flow_Group(flowGroupName = FlowGroupName_7,
                                                                #destinationMacAddressMode  = "decrement",        
                                                                #destinationMacAddressFixed = "EE:FF:EE:FF:00:00",
                                                                #destinationMacAddressStart = "AA:BB:CC:DD:00:00",
                                                                #destinationMacAddressStep  = "00:00:00:00:00:02",
                                                                #destinationMacAddressCount = 1)     
        
        ## analogo ma conciso... 
        #IXIA.modify_Frame_Ethernet_Header_L2_3_Quick_Flow_Group(flowGroupName = FlowGroupName_7,
                                                                #destinationMacAddressMode  = "random",        
                                                                #sourceMacAddressMode       = "random")     
        
        #time.sleep(60)
        #tempEtherType="BBBB"  
        #print("Left one minute to check if tempEtherType == [{}]  <<<<<<<<########".format(tempEtherType))
        #IXIA.modify_Frame_Ethernet_Header_L2_3_Quick_Flow_Group(flowGroupName = FlowGroupName_1 ,etherType = tempEtherType)                
        #time.sleep(60)
        #tempEtherType="CCCC"  
        #print("Left one minute to check if tempEtherType == [{}]  <<<<<<<<########".format(tempEtherType))
        #IXIA.modify_Frame_Ethernet_Header_L2_3_Quick_Flow_Group(flowGroupName = FlowGroupName_1,etherType = tempEtherType)                
        #time.sleep(60)
        #tempEtherType="DDDD"  
        #print("Left one minute to check if tempEtherType == [{}]  <<<<<<<<########".format(tempEtherType))
        #IXIA.modify_Frame_Ethernet_Header_L2_3_Quick_Flow_Group(flowGroupName = FlowGroupName_1,etherType = tempEtherType)                
        ##time.sleep(60)
 
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_1, flowGroupId=11, rateType = "packetRate", randomMin = 300,randomMax = 2000, frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte", etherType="0b0b", sourceMacAddressFixed="AA:AA:AA:00:00:00", destinationMacAddressFixed="BB:BB:BB:00:00:00")                 
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_1, flowGroupId=12, rateType = "packetRate", randomMin = 300,randomMax = 2000, frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte", etherType="0b0b", sourceMacAddressFixed="AA:AA:AA:00:00:00", destinationMacAddressFixed="BB:BB:BB:00:00:00")                 
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_1, flowGroupId=10, rateType = "packetRate", randomMin = 300,randomMax = 2000, frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte", etherType="0b0b", sourceMacAddressFixed="AA:AA:AA:00:00:00", destinationMacAddressFixed="BB:BB:BB:00:00:00")                 
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_1, flowGroupId=11, rateType = "packetRate", randomMin = 300,randomMax = 2000, frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte", etherType="0b0b", sourceMacAddressFixed="AA:AA:AA:00:00:00", destinationMacAddressFixed="BB:BB:BB:00:00:00")                 
        #IXIA.add_L2_3_Quick_Flow_Group(IdPort_1, flowGroupId=12, rateType = "packetRate", randomMin = 300,randomMax = 2000, frameSizeType = "random",rateValue = 100000.24,payloadType = "incrementByte", etherType="0b0b", sourceMacAddressFixed="AA:AA:AA:00:00:00", destinationMacAddressFixed="BB:BB:BB:00:00:00")                 

        # la custom statistic view va inizializzata PRIMA di far partire il traffico per poter poi leggere i contatori 
        IXIA.init_custom_statistic_view()
 
        # Avvia il traffico e lo fa girare per 10 secondi
        IXIA.start_traffic(timeToWait=10)
        
        # Attende 0 secondi e stoppa il traffico
        #IXIA.stop_traffic(timeToStop=0)
        
        # Attende fine transitori e latenze per avere statistiche di porta consistenti
        #time.sleep(20)
        # Lettura statistiche Porta 1 e 2 (su viste di default, che non contengono tutti i contatori richiesti)
        #retCode1=IXIA.get_port_statistic(IdPort_1)
        #retCode2=IXIA.get_port_statistic(IdPort_2)

        # Attende altri 10 secondi
        time.sleep(10)
        # Lettura statistiche Porta 1 su vista CUSTOM, che contiene tutti i contatori richiesti (e qualcosa di piu'...)
        # non fermo il traffico per leggere i valori di rate.  
        retCode1=IXIA.get_port_custom_statistic(IdPort_1)
        port1CountersDict=retCode1[1]
        print("\nDICT port 1 ONLY:[{}]".format(port1CountersDict))  
        
        # Attende 0 secondi e stoppa il traffico
        IXIA.stop_traffic(timeToStop=0)
        time.sleep(15)

        retCode2=IXIA.get_port_custom_statistic(IdPort_2)
        port2CountersDict=retCode2[1]
        print("\nDICT port 2 ONLY:[{}]".format(port2CountersDict))  
        
        
        


        

        #retCode3=IXIA.check_traffic()
        #CountersDict=retCode3[1]
        #print("\nCheck_traffic DICT:[{}]".format(CountersDict))  
        #for chiave in CountersDict.keys():
            #print("[{}] = [{}] ".format(chiave,CountersDict[chiave]))
   


        #=================================================
        #
        #  ATTENZIONE: il codice rimanente viene lasciato 
        #  come template ed esempio di uso tipico e commentato 
        #  di invocazione dei metodi.
        #
        #=================================================

        #port1CountersDict=retCode1[1]
        #port2CountersDict=retCode2[1]
        #print("DICT port 1 ONLY:[{}]".format(port1CountersDict))  
        #print("DICT port 2 ONLY:[{}]".format(port2CountersDict))  

        #IXIA.get_flow_statistic("TEST")
        #IXIA.get_traffic_item_statistic("TEST")
        #IXIA.get_port_cpu_statistic(IdPort_1)
        #IXIA.get_global_protocol_statistic(IdPort_1)
        #IXIA.get_port_cpu_statistic(IdPort_2)
        #IXIA.get_global_protocol_statistic(IdPort_2)

        # CARD 1/PORT 1-4 configuration (lag 1/lag 2)
        ###IdPort_1=('151.98.130.42', 1, 1)
        #IdPort_2=('151.98.130.42', 1, 2)
        #IdPort_3=('151.98.130.42', 1, 3)
        #IdPort_4=('151.98.130.42', 1, 4)
        ###IXIA.add_single_vport(IdPort_1, enabledFlowControl=False, autoNegotiate=False, speed="speed1000") 
        #IXIA.add_single_vport(IdPort_2, enabledFlowControl=False, autoNegotiate=False, speed="speed1000") 
        #IXIA.add_single_vport(IdPort_3, enabledFlowControl=False, autoNegotiate=False, speed="speed1000") 
        #IXIA.add_single_vport(IdPort_4, enabledFlowControl=False, autoNegotiate=False, speed="speed1000") 
        # call bind_new_vports() to add new ports created with one or more add_single_vport() call
        ###IXIA.bind_new_vports()        
        ###IXIA.enable_disable_lacp_protocol(IdPort_1,enable=True)    
        ###IXIA.init_traffic()

        # enable LACP protocol for the specified  port
        #IXIA.enable_disable_lacp_protocol(IdPort_1)  
        ###IXIA.add_L2_3_Quick_Flow_Group(IdPort_1)
        #IXIA.enable_disable_lacp_protocol(IdPort_2)    
        #IXIA.enable_disable_lacp_protocol(IdPort_3,administrativeKey=2)    
        #IXIA.enable_disable_lacp_protocol(IdPort_4,administrativeKey=2)   
        
        #
        # creo porte da 5 a 16 per poter testare i setup suggeritimi da valeria per il traffico
        #
        """
        IdPort_5=('151.98.130.42', 1, 5)
        IdPort_6=('151.98.130.42', 1, 6)
        IdPort_7=('151.98.130.42', 1, 7)
        IdPort_8=('151.98.130.42', 1, 8)
        IdPort_9=('151.98.130.42', 1, 9)
        IdPort_10 =('151.98.130.42', 1,10)
        IdPort_11 =('151.98.130.42', 1,11)
        IdPort_12 =('151.98.130.42', 1,12)
        IdPort_13 =('151.98.130.42', 1,13)
        IdPort_14 =('151.98.130.42', 1,14)
        IdPort_15 =('151.98.130.42', 1,15)
        IdPort_16 =('151.98.130.42', 1,16)
        IXIA.add_single_vport(IdPort_5, enabledFlowControl=False, autoNegotiate=False, speed="speed1000") 
        IXIA.add_single_vport(IdPort_6, enabledFlowControl=False, autoNegotiate=False, speed="speed1000") 
        IXIA.add_single_vport(IdPort_7, enabledFlowControl=False, autoNegotiate=False, speed="speed1000") 
        IXIA.add_single_vport(IdPort_8, enabledFlowControl=False, autoNegotiate=False, speed="speed1000") 
        IXIA.add_single_vport(IdPort_9, enabledFlowControl=False, autoNegotiate=False, speed="speed1000") 
        IXIA.add_single_vport(IdPort_10,enabledFlowControl=False, autoNegotiate=False, speed="speed1000") 
        IXIA.add_single_vport(IdPort_11,enabledFlowControl=False, autoNegotiate=False, speed="speed1000") 
        IXIA.add_single_vport(IdPort_12,enabledFlowControl=False, autoNegotiate=False, speed="speed1000") 
        IXIA.add_single_vport(IdPort_13,enabledFlowControl=False, autoNegotiate=False, speed="speed1000") 
        IXIA.add_single_vport(IdPort_14,enabledFlowControl=False, autoNegotiate=False, speed="speed1000") 
        IXIA.add_single_vport(IdPort_15,enabledFlowControl=False, autoNegotiate=False, speed="speed1000") 
        IXIA.add_single_vport(IdPort_16,enabledFlowControl=False, autoNegotiate=False, speed="speed1000") 
        IXIA.bind_new_vports()      
        IXIA.enable_disable_lacp_protocol(IdPort_5 )
        IXIA.enable_disable_lacp_protocol(IdPort_6 )
        IXIA.enable_disable_lacp_protocol(IdPort_7 )
        IXIA.enable_disable_lacp_protocol(IdPort_8 )
        IXIA.enable_disable_lacp_protocol(IdPort_9 )
        IXIA.enable_disable_lacp_protocol(IdPort_10)
        IXIA.enable_disable_lacp_protocol(IdPort_11)
        IXIA.enable_disable_lacp_protocol(IdPort_12)
        IXIA.enable_disable_lacp_protocol(IdPort_13)
        IXIA.enable_disable_lacp_protocol(IdPort_14)
        IXIA.enable_disable_lacp_protocol(IdPort_15)
        IXIA.enable_disable_lacp_protocol(IdPort_16)
        """
        # inizializzo il branch trafficitem al quale attaccheremo i flussi per le porte (endpointset)
        #IXIA.init_traffic()
        
        ## call bind_new_vports() to add new ports created with one or more add_single_vport() call
        #IXIA.bind_new_vports()        
        ## enable LACP protocol for the specified  port
        #IXIA.enable_disable_lacp_protocol(IdPort_5,enable=True)    
        #IXIA.enable_disable_lacp_protocol(IdPort_6)    
        #IXIA.enable_disable_lacp_protocol(IdPort_7,enable=True,administrativeKey=2)    
        #IXIA.enable_disable_lacp_protocol(IdPort_8,administrativeKey=2)   
        
        # disable LACP protocol for the specified port
        #IXIA.enable_disable_lacp_protocol(IdPort_1,enable=False)    
        #IXIA.enable_disable_lacp_protocol(IdPort_2,enable=False)    
        #IXIA.enable_disable_lacp_protocol(IdPort_3,enable=False)    
        #IXIA.enable_disable_lacp_protocol(IdPort_4,enable=False)  

        """
        def enable_disable_lacp_protocol(self, vPortId,  
                                     enable=True,
                                     actorKey=1,
                                     actorPortNumber=1,
                                     actorPortPriority=1,
                                     actorSystemId='00:00:00:00:00:01',
                                     actorSystemPriority=1,
                                     administrativeKey=1,
                                     linkEnabled=True,
                                     portMac= '00:00:00:00:00:01'):    
        """
        #IXIA.enable_disable_lacp_protocol(IdPort_1,enable=True)    
        #IXIA.enable_disable_lacp_protocol(IdPort_2,enable=True)    
        #IXIA.enable_disable_lacp_protocol(IdPort_3,enable=True)    
        #IXIA.enable_disable_lacp_protocol(IdPort_4,enable=True)    
       
        """    
        IXIA.enable_disable_lacp_protocol( IdPort_1,  
                                     enable=True,
                                     actorPortPriority='1'
                                     actorSystemId='00:00:00:00:00:01',
                                     actorSystemPriority='1',
                                     administrativeKey='1',
                                     linkEnabled=True,
                                     portMac= '00:00:00:00:00:01'):         
        """
        # Examples of different ports setup
        # ALL OF THESE PROPERLY WORKS: use them as examples for your own setups
        """
        # CARD 1/PORT 5-9 configuration trials for different setups check 
        IdPort_5=('151.98.130.42', 1, 5)
        IdPort_6=('151.98.130.42', 1, 6)
        IdPort_7=('151.98.130.42', 1, 7)
        IdPort_8=('151.98.130.42', 1, 8)
        IdPort_9=('151.98.130.42', 1, 9)
        IdPort_10=('151.98.130.42', 1, 10)
        IdPort_11=('151.98.130.42', 1, 11)
        IXIA.add_single_vport(IdPort_5, customName="Porta Lore", enabledFlowControl=False, autoNegotiate=False, speed="speed100fd") 
        IXIA.add_single_vport(IdPort_6, enabledFlowControl=False, autoNegotiate=True,  speed="speed1000") 
        IXIA.add_single_vport(IdPort_7, customName="Porta receiveMode Capture",receiveMode="capture", enabledFlowControl=False, autoNegotiate=True,  speedAuto=['speed100fd', 'speed100hd', 'speed1000']) 
        IXIA.add_single_vport(IdPort_8, mediaType="copper") 
        IXIA.add_single_vport(IdPort_9, loopback=True) 
        IXIA.add_single_vport(IdPort_10, mediaType="copper") 
        IXIA.add_single_vport(IdPort_11) 
        # call bind_new_vports() to add new ports created with one or more add_single_vport() call
        IXIA.bind_new_vports()        
        # enable  LACP protocol for every port  (with custom setups, to better understand)       
        IXIA.enable_disable_lacp_protocol(IdPort_6,enable=True,actorKey=3,actorPortNumber=4,actorPortPriority=5,administrativeKey=6)    
        IXIA.enable_disable_lacp_protocol(IdPort_7,actorSystemId='00:00:AA:00:00:01',)    
        IXIA.enable_disable_lacp_protocol(IdPort_8,enable=True,administrativeKey=2,autoPickPortMac=False, portMac= 'AA:00:BB:00:00:01')    
        IXIA.enable_disable_lacp_protocol(IdPort_9,administrativeKey=2,autoPickPortMac=False, portMac= 'CC:CC:EE:EE:EE:EE')   
        # disable LACP protocol for the specified port
        IXIA.enable_disable_lacp_protocol(IdPort_6,enable=False)    
        IXIA.enable_disable_lacp_protocol(IdPort_7,enable=False)    
        IXIA.enable_disable_lacp_protocol(IdPort_8,enable=False)    
        IXIA.enable_disable_lacp_protocol(IdPort_9,enable=False)  
        """
        
        """
        nomeTraffico = "Traffico di Test PORTA 1 LOOP"
        testPortList = [('151.98.130.42', 2, 1)]
        IXIA.create_all_vports(testPortList)
        IXIA.create_traffic(vPortIdTx   = ('151.98.130.42', 2, 1), 
                            vPortIdRx   = ('151.98.130.42', 2, 1),
                            trafficName = nomeTraffico,
                            TCframeCount= 9876)  # 9876 frames for this traffic (default 10000)
        IXIA.bind_all_phy_ports_to_vports(testPortList)
        """

        #IXIA.start_traffic()
        #IXIA.stop_traffic(20)
         
        ## EXAMPLE WITH PORT 2/2->TX and PORT 2/3-RX with VLAN creation
        #nomeTraffico = "Traffico di Test PORTA 2->3"
        #testPortList  = [('151.98.130.42', 2, 2), ('151.98.130.42', 2, 3)]
        #IXIA.create_all_vports(testPortList)
        #IXIA.create_traffic(vPortIdTx   = ('151.98.130.42', 2, 2), 
                            #vPortIdRx   = ('151.98.130.42', 2, 3),
                            #trafficName = nomeTraffico,
                            #VLanId                 = 144,
                            #VLanCFI                = 1,
                            #VLanPriority           = 5,
                            #VLanSrcMacAddr         = "00:20:60:00:00:03",
                            #VLanDestMacAddr        = "00:20:60:00:00:04")
        #IXIA.bind_all_phy_ports_to_vports(testPortList)

        ##IXIA.start_traffic()
        ##IXIA.stop_traffic(20)

        ## EXAMPLE WITH PORT 2/4 LOOPED TX->RX
        #nomeTraffico = "Traffico di Test PORTA 4 LOOP"
        #testPortList  = [('151.98.130.42', 2, 4)]
        #IXIA.create_all_vports(testPortList)
        
        #IXIA.create_traffic(vPortIdTx    = ('151.98.130.42', 2, 4), 
                            #vPortIdRx    = ('151.98.130.42', 2, 4),
                            #trafficName  = nomeTraffico,
                            #TCframeCount = 20000)  # 20000 frames for this traffic (default 10000)
        #IXIA.bind_all_phy_ports_to_vports(testPortList)

        #IXIA.start_traffic()
        #IXIA.stop_traffic(20)
  
        #IXIA.check_traffic()
        #dizionario=dict()
        #dizionario = IXIA.get_port_statistic('151.98.130.42', 2, 2)[1]
        #print("=======================================")
        #print("{}".format(dizionario))
        #print("=======================================")
        #print("Tx Frames port 2 [{}]".format(dizionario.get("Frames Tx.")))

        #dizionario = IXIA.get_port_statistic('151.98.130.42', 2, 3)[1]
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
        
        #dizionario = IXIA.get_port_cpu_statistic('151.98.130.42', 2, 2)[1]
        #print("=======================================")
        #print("{}".format(dizionario))
        #print("=======================================")
        
        #dizionario = IXIA.get_global_protocol_statistic('151.98.130.42', 2, 2)[1]
        #print("=======================================")
        #print("{}".format(dizionario))
        #print("=======================================")
        
        #dizionario = IXIA.get_l2l3_test_summary_statistic('151.98.130.42', 2, 2)[1]
        #print("=======================================")
        #print("{}".format(dizionario))
        #print("=======================================")
               
        #
        #   SI blocca: forse va invocato a traffico running...boh
        #
        #dizionario = IXIA.get_flow_detective_statistic('151.98.130.42', 2, 2)[1]
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

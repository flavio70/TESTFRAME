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
from katelibs.instrumentSM3300  import InstrumentSM3300
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
        SM3300.init_instrument()
        


    def test_body(self):
        '''
        test Body Section implementation
        insert Main body code for your test below
        '''
        
        #
        # RESET INSTRUMENT  
        # *** ALREADY CALLED IN  init_instrument(), the following call is just an example *** 
        #
        #retcode = SM3300.reset_instrument()  
        #print("retcode[{}] success[{}] value[{}]".format(retcode, retcode[0], retcode[1]))


        #
        # REMOTE PROGRAMMING ENABLE  
        # *** ALREADY CALLED IN  init_instrument(), the following call is just an example *** 
        #
        #retcode = SM3300.instrument_access_enable()   
        #print("retcode[{}] success[{}] value[{}]".format(retcode, retcode[0], retcode[1]))


        # VOLTAGE LIMITS SETUP
        
        #
        # GET the maximum allowed voltage setup  
        # 
        retcode = SM3300.get_set_max_voltage()
        print("retcode[{}] success[{}] value[{}]".format(retcode, retcode[0], retcode[1]))

        #
        # SET the maximum allowed voltage  setup  
        #
        retcode = SM3300.get_set_max_voltage(voltageToSet=66)
        print("retcode[{}] success[{}] value[{}]".format(retcode, retcode[0], retcode[1]))


        # VOLTAGE OUTPUT SETUP 

        #
        # GET the output voltage setup  
        #
        retcode = SM3300.get_set_voltage()
        print("retcode[{}] success[{}] value[{}]".format(retcode, retcode[0], retcode[1]))

        #
        # SET the output voltage setup   
        # *** ALREADY CALLED IN  init_instrument(), the following call is just an example *** 
        #
        #retcode = SM3300.get_set_voltage(50.00)
        #print("retcode[{}] success[{}] value[{}]".format(retcode, retcode[0], retcode[1]))


        # VOLTAGE OUTPUT MEASUREMENT
        
        #
        # GET the output voltage measured  
        #
        retcode = SM3300.get_measured_voltage()
        print("retcode[{}] success[{}] value[{}]".format(retcode, retcode[0], retcode[1]))
 


        # CURRENT LIMITS SETUP
        
        #
        # GET the maximum allowed current setup   
        #
        retcode = SM3300.get_set_max_current()
        print("retcode[{}] success[{}] value[{}]".format(retcode, retcode[0], retcode[1]))

        #
        # SET the maximum allowed current  setup  
        #
        retcode = SM3300.get_set_max_current(currentToSet=66)
        print("retcode[{}] success[{}] value[{}]".format(retcode, retcode[0], retcode[1]))


        # CURRENT OUTPUT SETUP 

        #
        # GET the output current setup  
        #
        retcode = SM3300.get_set_current()
        print("retcode[{}] success[{}] value[{}]".format(retcode, retcode[0], retcode[1]))

        #
        # SET the output current setup   
        # *** ALREADY CALLED IN  init_instrument(), the following call is just an example *** 
        #
        #retcode = SM3300.get_set_current(59.50)
        #print("retcode[{}] success[{}] value[{}]".format(retcode, retcode[0], retcode[1]))


        # CURRENT OUTPUT MEASUREMENT
        
        #
        # GET the output current measured  
        #
        retcode = SM3300.get_measured_current()
        print("retcode[{}] success[{}] value[{}]".format(retcode, retcode[0], retcode[1]))



        # POWER OUTPUT MEASUREMENT
        
        #
        # GET the output current measured  
        #
        retcode = SM3300.get_measured_power()
        print("retcode[{}] success[{}] value[{}]".format(retcode, retcode[0], retcode[1]))
        supplied_power_before_power_on=retcode[1]


        # POWER SUPPLY CONTROL 
        
        #
        # GET the power supply state
        #
        retcode = SM3300.get_set_output_enable()
        print("retcode[{}] success[{}] value[{}]".format(retcode, retcode[0], retcode[1]))
        print("Supplied electric power before power on [{}] watt".format(supplied_power_before_power_on))


        #
        # POWER ON 
        #
        retcode = SM3300.get_set_output_enable("ON")
        print("retcode[{}] success[{}] value[{}]".format(retcode, retcode[0], retcode[1]))


        #
        # GET the power supply state @ the NE startup  
        #
        for i in range(1,20): 
            retcode = SM3300.get_measured_power()
            supplied_power_after_power_on=retcode[1]
            print("Supplied electric power now [{}] watt".format(supplied_power_after_power_on))

        #
        # POWER OFF 
        #
        retcode = SM3300.get_set_output_enable("OFF")
        print("retcode[{}] success[{}] value[{}]".format(retcode, retcode[0], retcode[1]))

 
        #
        # GET the power supply state @ the NE source power off...  
        #
        for i in range(1,5): 
            retcode = SM3300.get_measured_power()
            supplied_power_after_power_on=retcode[1]
            print("Supplied electric power now [{}] watt".format(supplied_power_after_power_on))
         


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

    SM3300 = InstrumentSM3300('SM3300', CTEST.kenvironment)


    #####################################################################
    # Run Test main flow                                                #

    CTEST.run()

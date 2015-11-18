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

from katelibs.testcase import TestCase
from katelibs.eqpt1850tss320 import *


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
        #self.kenv.krepo.start_tps_block("EM", "1-2-3")
        self.kenvironment.krepo.start_tps_block("EM", "1-2-3")
        NE1.tl1.do("ACT-USER::admin:::Alcatel1;")
        #self.report.add_success(None, "Test3 DUT SetUp", '0', "Test3 DUT SetUp Output")

    def test_setup(self):
        '''
        test Setup Section implementation
        insert general SetUp code for your test below
        '''


    def test_body(self):
        '''
        test Body Section implementation
        insert Main body code for your test below
        '''


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
        print('@DUT CleanUP')
        NE1.clean_up()
        #self.kenv.krepo.stop_tps_block("EM", "1-2-3")
        self.kenvironment.krepo.stop_tps_block("EM", "1-2-3")


#Please don't change the code below#
if __name__ == "__main__":
    #initializing the Test object instance, do not remove
    CTEST = Test(__file__)
    #initializing all local variable and constants used by Test object
    #CPARS = CTEST.prs_values
    #NE1 = Eqpt1850TSS320('NE1',int(CPARS['NE1']), krepo=CTEST.report )
    NE1 = Eqpt1850TSS320('NE1', CTEST.kenvironment)

    # Run Test main flow
    # Please don't touch this code
    CTEST.run()

    NE1.clean_up()
    #inst1.clean_up() # esempio
    #inst2.clean_up() # esempio
